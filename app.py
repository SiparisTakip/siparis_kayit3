from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from datetime import datetime, timedelta
import pytz
import requests
from bs4 import BeautifulSoup as BS
import json
from supabase import create_client, Client
import pandas as pd

# İller sözlüğünü doğrudan burada tanımla
iller = {
    'İstanbul': ['Adalar', 'Arnavutköy', 'Ataşehir', 'Avcılar', 'Bağcılar', 'Bahçelievler', 'Bakırköy', 'Başakşehir', 'Bayrampaşa', 'Beşiktaş', 'Beykoz', 'Beylikdüzü', 'Beyoğlu', 'Büyükçekmece', 'Çatalca', 'Çekmeköy', 'Esenler', 'Esenyurt', 'Eyüp', 'Fatih', 'Gaziosmanpaşa', 'Güngören', 'Kadıköy', 'Kağıthane', 'Kartal', 'Küçükçekmece', 'Maltepe', 'Pendik', 'Sancaktepe', 'Sarıyer', 'Silivri', 'Sultanbeyli', 'Sultangazi', 'Şile', 'Şişli', 'Tuzla', 'Ümraniye', 'Üsküdar', 'Zeytinburnu'],
    'Ankara': ['Akyurt', 'Altındağ', 'Ayaş', 'Bala', 'Beypazarı', 'Çamlıdere', 'Çankaya', 'Çubuk', 'Elmadağ', 'Etimesgut', 'Evren', 'Gölbaşı', 'Güdül', 'Haymana', 'Kahramankazan', 'Kalecik', 'Keçiören', 'Kızılcahamam', 'Mamak', 'Nallıhan', 'Polatlı', 'Pursaklar', 'Sincan', 'Şereflikoçhisar', 'Yenimahalle']
    # ... Diğer illeri de ekleyin
}

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Supabase bağlantı bilgileri
url = "https://ezyhoocwfrocaqsehler.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV6eWhvb2N3ZnJvY2Fxc2VobGVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjcyOTkzOTUsImV4cCI6MjA0Mjg3NTM5NX0.3A2pCuleW0RnGIlCaM5pALWw8fB_KW_y2-qsIJ1_FJI"
supabase_DB = "siparislistesi"

# Kargo bilgileri
kullanici_Adi = "seffafbutik@yesilkar.com"
sifre = "Ma123456"
sube_kodu = "SUL"

# Supabase Client oluştur
supabase: Client = create_client(url, key)

# Zaman dilimi ayarı
turkey_tz = pytz.timezone('Europe/Istanbul')

# İl ve ilçe kontrolü için yardımcı fonksiyon
def normalize_text(text):
    text = text.strip().lower()
    text = text.replace('i̇', 'i')  # Türkçe i harfi düzeltmesi
    text = text.replace('ş', 's')   # ş -> s
    text = text.replace('ğ', 'g')   # ğ -> g
    text = text.replace('ü', 'u')   # ü -> u
    text = text.replace('ö', 'o')   # ö -> o
    text = text.replace('ç', 'c')   # ç -> c
    text = text.replace('ı', 'i')   # ı -> i
    if text.startswith('i'):
        text = 'i' + text[1:]
    return text

# Debug için iller sözlüğünü kontrol et
print("Mevcut iller:", list(iller.keys()))

@app.route('/', methods=['GET', 'POST'])
def index():
    tarih = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")
    yukleme_tarihi = datetime.now(turkey_tz).strftime("%Y-%m-%d")
    form_data = None
    siparis = None
    
    # Aktif siparişleri çek ve sırala
    data = supabase.table(supabase_DB).select("*").eq("siparis_durumu", "1").order("id", desc=False).execute()
    siparisler = pd.DataFrame(data.data)
    
    # Sütun isimlerini düzelt ve sırala
    if not siparisler.empty:
        # Sütun isimlerini kontrol et ve düzelt
        if "İSİM SOYİSİM" not in siparisler.columns and "İSİM_SOYİSİM" in siparisler.columns:
            siparisler = siparisler.rename(columns={"İSİM_SOYİSİM": "İSİM SOYİSİM"})
        
        # İsme göre sırala
        siparisler = siparisler.sort_values(by="İSİM SOYİSİM")

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'yeni_siparis':
            text = request.form.get('text_input')
            form_data = text  # Hata durumunda formu korumak için
            
            lines = text.split('\n')
            if len(lines) >= 6:
                try:
                    isim_soyisim = lines[0].strip()
                    adres_bilgisi = lines[1].strip()
                    ilce_il = lines[2].strip().split()
                    
                    # İlçe ve il bilgilerini ayır
                    if len(ilce_il) >= 2:
                        ilce = ' '.join(ilce_il[:-1])  # Son kelime hariç hepsi ilçe
                        il = ilce_il[-1]  # Son kelime il
                        
                        # İl ve ilçe sıralamasını kontrol et ve gerekirse değiştir
                        if normalize_text(il) not in [normalize_text(valid_il) for valid_il in iller.keys()]:
                            ilce, il = il, ilce  # İl ve ilçeyi yer değiştir
                        
                        telefon = lines[3].strip()
                        ucret = lines[4].strip()
                        urun_bilgisi = '\n'.join(lines[6:]).strip()
                    else:
                        flash('İlçe ve il bilgisi yanlış formatta', 'error')
                        return render_template('index.html', form_data=form_data)
                    
                    # İl kontrolü
                    il_match = None
                    ilce_match = None
                    
                    # İl eşleştirme
                    for valid_il in iller:
                        if normalize_text(il) == normalize_text(valid_il):
                            il_match = valid_il
                            # İlçe eşleştirme
                            for valid_ilce in iller[valid_il]:
                                if normalize_text(ilce) == normalize_text(valid_ilce):
                                    ilce_match = valid_ilce
                                    break
                            break
                    
                    error = None
                    if not il_match:
                        error = f'İL DOĞRU DEĞİL: {il}'
                    elif not ilce_match:
                        error = f'İLÇE DOĞRU DEĞİL: {ilce} (İl: {il_match} için geçerli ilçeler: {", ".join(iller[il_match])})'
                    elif len(telefon) != 11:
                        error = f'Telefon Numarası Hatalı: {telefon}'
                    
                    if error:
                        flash(error, 'error')
                    else:
                        yeni_siparis = {
                            'tarih': tarih,
                            "İSİM SOYİSİM": isim_soyisim,
                            "İLÇE": ilce_match,
                            "İL": il_match,
                            "ADRES": adres_bilgisi,
                            "TELEFON": telefon,
                            "ŞUBE KOD": sube_kodu,
                            "MÜŞTERİ NO": "",
                            "TUTAR": ucret,
                            "ÜRÜN": urun_bilgisi,
                            "MİKTAR": "1",
                            "GRAM": "800",
                            "GTÜRÜ": "2",
                            "ÜCRETTÜRÜ": "6",
                            "EK HİZMET": " ",
                            "KDV": "8",
                            "SİP NO": telefon,
                            "ÇIKIŞ NO": "",
                            "SATICI": "",
                            "HATTAR": "",
                            "FATTAR": "",
                            "EN": "10",
                            "BOY": "15",
                            "YÜKSEKLİK": "10",
                            "siparis_durumu": "1",
                        }
                        
                        response = supabase.table(supabase_DB).insert(yeni_siparis).execute()
                        flash('Sipariş başarıyla kaydedildi', 'success')
                        return redirect(url_for('index'))
                        
                except Exception as e:
                    flash(f'Bilgi girişinde hata oluştu: {str(e)}', 'error')
                    print(f"Hata detayı: {str(e)}")
                    print(f"İl: {il}")
                    print(f"İlçe: {ilce}")
                    print(f"Normalize edilmiş il: {normalize_text(il)}")
                    print(f"Normalize edilmiş ilçe: {normalize_text(ilce)}")
                    print(f"Mevcut iller: {list(iller.keys())}")
            else:
                flash('Yetersiz bilgi girişi. Lütfen tüm alanları doldurun.', 'error')
        
        elif action == 'toplu_sil':
            try:
                response = supabase.table(supabase_DB).update({
                    'yazdirma_tarihi': yukleme_tarihi,
                    'siparis_durumu': '2'
                }).eq('siparis_durumu', '1').execute()
                
                flash('Tüm siparişler başarıyla silindi', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f'Hata oluştu: {str(e)}', 'error')
        
        elif action == 'guncelle_siparis':
            try:
                siparis_id = request.form.get('siparis_id')
                musteri_adi = request.form.get('musteri_adi')
                adres = request.form.get('adres')
                ilce = request.form.get('ilce')
                il = request.form.get('il')
                telefon = request.form.get('telefon')
                ucret = request.form.get('ucret')
                urun = request.form.get('urun')

                # İl ve ilçe kontrolü
                il_match = None
                ilce_match = None
                
                for valid_il in iller:
                    if normalize_text(il) == normalize_text(valid_il):
                        il_match = valid_il
                        for valid_ilce in iller[valid_il]:
                            if normalize_text(ilce) == normalize_text(valid_ilce):
                                ilce_match = valid_ilce
                                break
                        break

                if not il_match or not ilce_match:
                    flash('Geçersiz il veya ilçe bilgisi', 'error')
                else:
                    guncelleme = {
                        "İSİM SOYİSİM": musteri_adi,
                        "İLÇE": ilce_match,
                        "İL": il_match,
                        "ADRES": adres,
                        "TELEFON": telefon,
                        "TUTAR": ucret,
                        "ÜRÜN": urun,
                        "SİP NO": telefon
                    }
                    
                    response = supabase.table(supabase_DB).update(guncelleme).eq("id", siparis_id).execute()
                    flash('Sipariş başarıyla güncellendi', 'success')

            except Exception as e:
                flash(f'Güncelleme sırasında hata oluştu: {str(e)}', 'error')
                print(f"Güncelleme hatası: {str(e)}")  # Debug için

        elif action == 'sil_siparis':
            try:
                siparis_id = request.form.get('siparis_id')
                print(f"Silinecek sipariş ID: {siparis_id}")  # Debug için

                if siparis_id:
                    # Önce siparişin var olduğunu kontrol et
                    check = supabase.table(supabase_DB).select("*").eq("id", siparis_id).execute()
                    print(f"Bulunan sipariş: {check.data}")  # Debug için

                    if check.data:
                        response = supabase.table(supabase_DB).update({
                            'yazdirma_tarihi': datetime.now(turkey_tz).strftime("%Y-%m-%d"),
                            'siparis_durumu': '2'
                        }).eq("id", siparis_id).execute()
                        print(f"Güncelleme yanıtı: {response.data}")  # Debug için
                        flash('Sipariş başarıyla silindi', 'success')
                    else:
                        flash('Sipariş bulunamadı', 'error')
                else:
                    flash('Sipariş ID bulunamadı', 'error')
            except Exception as e:
                flash(f'Silme sırasında hata oluştu: {str(e)}', 'error')
                print(f"Silme hatası detayı: {str(e)}")  # Debug için

        return redirect(url_for('index'))
    
    return render_template('index.html', 
                         siparisler=siparisler.to_dict('records') if not siparisler.empty else [],
                         siparis=siparis,
                         form_data=form_data,
                         tarih=tarih)

if __name__ == '__main__':
    app.run(debug=True) 
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from datetime import datetime, timedelta
import pytz
import requests
from bs4 import BeautifulSoup as BS
import json
from supabase import create_client, Client
import pandas as pd

# İller sözlüğünü doğrudan burada tanımla
iller = {'Adana': ['Aladağ', 'Ceyhan', 'Çukurova', 'Feke', 'İmamoğlu', 'Karaisalı', 'Karataş', 'Kozan', 'Pozantı', 'Saimbeyli', 'Sarıçam', 'Seyhan', 'Tufanbeyli', 'Yumurtalık', 'Yüreğir'], 
'Adıyaman': ['Besni', 'Çelikhan', 'Gerger', 'Gölbaşı', 'Kahta', 'Merkez', 'Samsat', 'Sincik', 'Tut'], 
'Afyonkarahisar': ['Başmakçı', 'Bayat', 'Bolvadin', 'Çay', 'Çobanlar', 'Dazkırı', 'Dinar', 'Emirdağ', 'Evciler', 'Hocalar', 'İhsaniye', 'İscehisar', 'Kızılören', 'Merkez', 'Sandıklı', 'Sinanpaşa', 'Sultandağı', 'Şuhut'], 
'Ağrı': ['Diyadin', 'Doğubayazıt', 'Eleşkirt', 'Hamur', 'Merkez', 'Patnos', 'Taşlıçay', 'Tutak'], 
'Amasya': ['Göynücek', 'Gümüşhacıköy', 'Hamamözü', 'Merkez', 'Merzifon', 'Suluova', 'Taşova'], 
'Ankara': ['Akyurt', 'Altındağ', 'Ayaş', 'Bala', 'Beypazarı', 'Çamlıdere', 'Çankaya', 'Çubuk', 'Elmadağ', 'Etimesgut', 'Evren', 'Gölbaşı', 'Güdül', 'Haymana', 'Kahramankazan', 'Kalecik', 'Keçiören', 'Kızılcahamam', 'Mamak', 'Nallıhan', 'Polatlı', 'Pursaklar', 'Sincan', 'Şereflikoçhisar', 'Yenimahalle'], 
'Antalya': ['Akseki', 'Aksu', 'Alanya', 'Demre', 'Döşemealtı', 'Elmalı', 'Finike', 'Gazipaşa', 'Gündoğmuş', 'İbradı', 'Kaş', 'Kemer', 'Kepez', 'Konyaaltı', 'Korkuteli', 'Kumluca', 'Manavgat', 'Muratpaşa', 'Serik'], 
'Artvin': ['Kemalpaşa','Ardanuç', 'Arhavi', 'Borçka', 'Hopa', 'Merkez', 'Murgul', 'Şavşat', 'Yusufeli'], 
'Aydın': ['Bozdoğan', 'Buharkent', 'Çine', 'Didim', 'Efeler', 'Germencik', 'İncirliova', 'Karacasu', 'Karpuzlu', 'Koçarlı', 'Köşk', 'Kuşadası', 'Kuyucak', 'Nazilli', 'Söke', 'Sultanhisar', 'Yenipazar'], 
'Balıkesir': ['Altıeylül', 'Ayvalık', 'Balya', 'Bandırma', 'Bigadiç', 'Burhaniye', 'Dursunbey', 'Edremit', 'Erdek', 'Gömeç', 'Gönen', 'Havran', 'İvrindi', 'Karesi', 'Kepsut', 'Manyas', 'Marmara', 'Savaştepe', 'Sındırgı', 'Susurluk'],
'Bilecik': ['Bozüyük', 'Gölpazarı', 'İnhisar', 'Merkez', 'Osmaneli', 'Pazaryeri', 'Söğüt', 'Yenipazar'], 
'Bingöl': ['Adaklı', 'Genç', 'Karlıova', 'Kiğı', 'Merkez', 'Solhan', 'Yayladere', 'Yedisu'], 
'Bitlis': ['Adilcevaz', 'Ahlat', 'Güroymak', 'Hizan', 'Merkez', 'Mutki', 'Tatvan'], 
'Bolu': ['Dörtdivan', 'Gerede', 'Göynük', 'Kıbrıscık', 'Mengen', 'Merkez', 'Mudurnu', 'Seben', 'Yeniçağa'], 
'Burdur': ['Ağlasun', 'Altınyayla', 'Bucak', 'Çavdır', 'Çeltikçi', 'Gölhisar', 'Karamanlı', 'Kemer', 'Merkez', 'Tefenni', 'Yeşilova'], 
'Bursa': ['Büyükorhan', 'Gemlik', 'Gürsu', 'Harmancık', 'İnegöl', 'İznik', 'Karacabey', 'Keles', 'Kestel', 'Mudanya', 'Mustafakemalpaşa', 'Nilüfer', 'Orhaneli', 'Orhangazi', 'Osmangazi', 'Yenişehir', 'Yıldırım'], 
'Çanakkale': ['Ayvacık', 'Bayramiç', 'Biga', 'Bozcaada', 'Çan', 'Eceabat', 'Ezine', 'Gelibolu', 'Gökçeada', 'Lapseki', 'Merkez', 'Yenice'], 
'Çankırı': ['Atkaracalar', 'Bayramören', 'Çerkeş', 'Eldivan', 'Ilgaz', 'Kızılırmak', 'Korgun', 'Kurşunlu', 'Merkez', 'Orta', 'Şabanözü', 'Yapraklı'], 
'Çorum': ['Alaca', 'Bayat', 'Boğazkale', 'Dodurga', 'İskilip', 'Kargı', 'Laçin', 'Mecitözü', 'Merkez', 'Oğuzlar', 'Ortaköy', 'Osmancık', 'Sungurlu', 'Uğurludağ'],
'Denizli': ['Acıpayam', 'Babadağ', 'Baklan', 'Bekilli', 'Beyağaç', 'Bozkurt', 'Buldan', 'Çal', 'Çameli', 'Çardak', 'Çivril', 'Güney', 'Honaz', 'Kale', 'Merkezefendi', 'Pamukkale', 'Sarayköy', 'Serinhisar', 'Tavas'],
'Diyarbakır': ['Bağlar', 'Bismil', 'Çermik', 'Çınar', 'Çüngüş', 'Dicle', 'Eğil', 'Ergani', 'Hani', 'Hazro', 'Kayapınar', 'Kocaköy', 'Kulp', 'Lice', 'Silvan', 'Sur', 'Yenişehir'], 
'Edirne': ['Enez', 'Havsa', 'İpsala', 'Keşan', 'Lalapaşa', 'Meriç', 'Merkez', 'Süloğlu', 'Uzunköprü'], 
'Elazığ': ['Ağın', 'Alacakaya', 'Arıcak', 'Baskil', 'Karakoçan', 'Keban', 'Kovancılar', 'Maden', 'Merkez', 'Palu', 'Sivrice'], 
'Erzincan': ['Çayırlı', 'İliç', 'Kemah', 'Kemaliye', 'Merkez', 'Otlukbeli', 'Refahiye', 'Tercan', 'Üzümlü'], 
'Erzurum': ['Aşkale', 'Aziziye', 'Çat', 'Hınıs', 'Horasan', 'İspir', 'Karaçoban', 'Karayazı', 'Köprüköy', 'Narman', 'Oltu', 'Olur', 'Palandöken', 'Pasinler', 'Pazaryolu', 'Şenkaya', 'Tekman', 'Tortum', 'Uzundere', 'Yakutiye'],
'Eskişehir': ['Alpu', 'Beylikova', 'Çifteler', 'Günyüzü', 'Han', 'İnönü', 'Mahmudiye', 'Mihalgazi', 'Mihalıççık', 'Odunpazarı', 'Sarıcakaya', 'Seyitgazi', 'Sivrihisar', 'Tepebaşı'], 
'Gaziantep': ['Araban', 'İslahiye', 'Karkamış', 'Nizip', 'Nurdağı', 'Oğuzeli', 'Şahinbey', 'Şehitkamil', 'Yavuzeli'], 
'Giresun': ['Alucra', 'Bulancak', 'Çamoluk', 'Çanakçı', 'Dereli', 'Doğankent', 'Espiye', 'Eynesil', 'Görele', 'Güce', 'Keşap', 'Merkez', 'Piraziz', 'Şebinkarahisar', 'Tirebolu', 'Yağlıdere'],
'Gümüşhane': ['Kelkit', 'Köse', 'Kürtün', 'Merkez', 'Şiran', 'Torul'], 
'Hakkari': ['Çukurca', 'Merkez', 'Şemdinli', 'Yüksekova'], 
'Hatay': ['Altınözü', 'Antakya', 'Arsuz', 'Belen', 'Defne', 'Dörtyol', 'Erzin', 'Hassa', 'İskenderun', 'Kırıkhan', 'Kumlu', 'Payas', 'Reyhanlı', 'Samandağ', 'Yayladağı'], 
'Isparta': ['Aksu', 'Atabey', 'Eğirdir', 'Gelendost', 'Gönen', 'Keçiborlu', 'Merkez', 'Senirkent', 'Sütçüler', 'Şarkikaraağaç', 'Uluborlu', 'Yalvaç', 'Yenişarbademli'], 
'Mersin': ['Akdeniz', 'Anamur', 'Aydıncık', 'Bozyazı', 'Çamlıyayla', 'Erdemli', 'Gülnar', 'Mezitli', 'Mut', 'Silifke', 'Tarsus', 'Toroslar', 'Yenişehir'], 
'İstanbul': ['Adalar', 'Arnavutköy', 'Ataşehir', 'Avcılar', 'Bağcılar', 'Bahçelievler', 'Bakırköy', 'Başakşehir', 'Bayrampaşa', 'Beşiktaş', 'Beykoz', 'Beylikdüzü', 'Beyoğlu', 'Büyükçekmece', 'Çatalca', 'Çekmeköy', 'Esenler', 'Esenyurt', 'Eyüp', 'Fatih', 'Gaziosmanpaşa', 'Güngören', 'Kadıköy', 'Kağıthane', 'Kartal', 'Küçükçekmece', 'Maltepe', 'Pendik', 'Sancaktepe', 'Sarıyer', 'Silivri', 'Sultanbeyli', 'Sultangazi', 'Şile', 'Şişli', 'Tuzla', 'Ümraniye', 'Üsküdar', 'Zeytinburnu'], 
'İzmir': ['Aliağa', 'Balçova', 'Bayındır', 'Bayraklı', 'Bergama', 'Beydağ', 'Bornova', 'Buca', 'Çeşme', 'Çiğli', 'Dikili', 'Foça', 'Gaziemir', 'Güzelbahçe', 'Karabağlar', 'Karaburun', 'Karşıyaka', 'Kemalpaşa', 'Kınık', 'Kiraz', 'Konak', 'Menderes', 'Menemen', 'Narlıdere', 'Ödemiş', 'Seferihisar', 'Selçuk', 'Tire', 'Torbalı', 'Urla'], 
'Kars': ['Akyaka', 'Arpaçay', 'Digor', 'Kağızman', 'Merkez', 'Sarıkamış', 'Selim', 'Susuz'], 
'Kastamonu': ['Abana', 'Ağlı', 'Araç', 'Azdavay', 'Bozkurt', 'Cide', 'Çatalzeytin', 'Daday', 'Devrekani', 'Doğanyurt', 'Hanönü', 'İhsangazi', 'İnebolu', 'Küre', 'Merkez', 'Pınarbaşı', 'Seydiler', 'Şenpazar', 'Taşköprü', 'Tosya'], 
'Kayseri': ['Akkışla', 'Bünyan', 'Develi', 'Felahiye', 'Hacılar', 'İncesu', 'Kocasinan', 'Melikgazi', 'Özvatan', 'Pınarbaşı', 'Sarıoğlan', 'Sarız', 'Talas', 'Tomarza', 'Yahyalı', 'Yeşilhisar'], 
'Kırklareli': ['Babaeski', 'Demirköy', 'Kofçaz', 'Lüleburgaz', 'Merkez', 'Pehlivanköy', 'Pınarhisar', 'Vize'], 
'Kırşehir': ['Akçakent', 'Akpınar', 'Boztepe', 'Çiçekdağı', 'Kaman', 'Merkez', 'Mucur'], 
'Kocaeli': ['Başiskele', 'Çayırova', 'Darıca', 'Derince', 'Dilovası', 'Gebze', 'Gölcük', 'İzmit', 'Kandıra', 'Karamürsel', 'Kartepe', 'Körfez'], 
'Konya': ['Ahırlı', 'Akören', 'Akşehir', 'Altınekin', 'Beyşehir', 'Bozkır', 'Cihanbeyli', 'Çeltik', 'Çumra', 'Derbent', 'Derebucak', 'Doğanhisar', 'Emirgazi', 'Ereğli', 'Güneysınır', 'Hadim', 'Halkapınar', 'Hüyük', 'Ilgın', 'Kadınhanı', 'Karapınar', 'Karatay', 'Kulu', 'Meram', 'Sarayönü', 'Selçuklu', 'Seydişehir', 'Taşkent', 'Tuzlukçu', 'Yalıhüyük', 'Yunak'], 
'Kütahya': ['Altıntaş', 'Aslanapa', 'Çavdarhisar', 'Domaniç', 'Dumlupınar', 'Emet', 'Gediz', 'Hisarık', 'Merkez', 'Pazarlar', 'Simav', 'Şaphane', 'Tavşanlı'], 
'Malatya': ['Akçadağ', 'Arapgir', 'Arguvan', 'Battalgazi', 'Darende', 'Doğanşehir', 'Doğanyol', 'Hekimhan', 'Kale', 'Kuluncak', 'Pütürge', 'Yazıhan', 'Yeşilyurt'], 
'Manisa': ['Ahmetli', 'Akhisar', 'Alaşehir', 'Demirci', 'Gölmarmara', 'Gördes', 'Kırkağaç', 'Köprübaşı', 'Kula', 'Salihli', 'Sarıgöl', 'Saruhanlı', 'Selendi', 'Soma', 'Şehzadeler', 'Turgutlu', 'Yunusemre'], 
'Kahramanmaraş': ['Afşin', 'Andırın', 'Çağlayancerit', 'Dulkadiroğlu', 'Ekinözü', 'Elbistan', 'Göksun', 'Nurhak', 'Onikişubat', 'Pazarcık', 'Türkoğlu'], 
'Mardin': ['Artuklu', 'Dargeçit', 'Derik', 'Kızıltepe', 'Mazıdağı', 'Midyat', 'Nusaybin', 'Ömerli', 'Savur', 'Yeşilli'], 
'Muğla': ['Bodrum', 'Dalaman', 'Datça', 'Fethiye', 'Kavaklıdere', 'Köyceğiz', 'Marmaris', 'Menteşe', 'Milas', 'Ortaca', 'Seydikemer', 'Ula', 'Yatağan'], 
'Muş': ['Bulanık', 'Hasköy', 'Korkut', 'Malazgirt', 'Merkez', 'Varto'], 
'Nevşehir': ['Acıgöl', 'Avanos', 'Derinkuyu', 'Gülşehir', 'Hacıbektaş', 'Kozaklı', 'Merkez', 'Ürgüp'], 
'Niğde': ['Altunhisar', 'Bor', 'Çamardı', 'Çiftlik', 'Merkez', 'Ulukışla'], 
'Ordu': ['Akkuş', 'Altınordu', 'Aybastı', 'Çamaş', 'Çatalpınar', 'Çaybaşı', 'Fatsa', 'Gölköy', 'Gülyalı', 'Gürgentepe', 'İkizce', 'Kabadüz', 'Kabataş', 'Korgan', 'Kumru', 'Mesudiye', 'Perşembe', 'Ulubey', 'Ünye'], 
'Rize': ['Ardeşen', 'Çamlıhemşin', 'Çayeli', 'Derepazarı', 'Fındıklı', 'Güneysu', 'Hemşin', 'İkizdere', 'İyidere', 'Kalkandere', 'Merkez', 'Pazar'], 
'Sakarya': ['Adapazarı', 'Akyazı', 'Arifiye', 'Erenler', 'Ferizli', 'Geyve', 'Hendek', 'Karapürçek', 'Karasu', 'Kaynarca', 'Kocaali', 'Pamukova', 'Sapanca', 'Serdivan', 'Söğütlü', 'Taraklı'], 
'Samsun': ['Alaçam', 'Asarcık', 'Atakum', 'Ayvacık', 'Bafra', 'Canik', 'Çarşamba', 'Havza', 'İlkadım', 'Kavak', 'Ladik', 'Salıpazarı', 'Tekkeköy', 'Terme', 'Vezirköprü', 'Yakakent','19 Mayıs'], 
'Siirt': ['Baykan', 'Eruh', 'Kurtalan', 'Merkez', 'Pervari', 'Şirvan', 'Tillo'], 
'Sinop': ['Ayancık', 'Boyabat', 'Dikmen', 'Durağan', 'Erfelek', 'Gerze', 'Merkez', 'Saraydüzü', 'Türkeli'], 
'Sivas': ['Akıncılar', 'Altınyayla', 'Divriği', 'Doğanşar', 'Gemerek', 'Gölova', 'Gürün', 'Hafik', 'İmranlı', 'Kangal', 'Koyulhisar', 'Merkez', 'Suşehri', 'Şarkışla', 'Ulaş', 'Yıldızeli', 'Zara'], 
'Tekirdağ': ['Çerkezköy', 'Çorlu', 'Ergene', 'Hayrabolu', 'Kapaklı', 'Malkara', 'Marmaraereğlisi', 'Muratlı', 'Saray', 'Süleymanpaşa', 'Şarköy'], 
'Tokat': ['Almus', 'Artova', 'Başçiftlik', 'Erbaa', 'Merkez', 'Niksar', 'Pazar', 'Reşadiye', 'Sulusaray', 'Turhal', 'Yeşilyurt', 'Zile'], 
'Trabzon': ['Akçaabat', 'Araklı', 'Arsin', 'Beşikdüzü', 'Çarşıbaşı', 'Çaykara', 'Dernekpazarı', 'Düzköy', 'Hayrat', 'Köprübaşı', 'Maçka', 'Of', 'Ortahisar', 'Sürmene', 'Şalpazarı', 'Tonya', 'Vakfıkebir', 'Yomra'], 
'Tunceli': ['Çemişgezek', 'Hozat', 'Mazgirt', 'Merkez', 'Nazımiye', 'Ovacık', 'Pertek', 'Pülümür'], 
'Şanlıurfa': ['Akçakale', 'Birecik', 'Bozova', 'Ceylanpınar', 'Eyyübiye', 'Halfeti', 'Haliliye', 'Harran', 'Hilvan', 'Karaköprü', 'Siverek', 'Suruç', 'Viranşehir'], 
'Uşak': ['Banaz', 'Eşme', 'Karahallı', 'Merkez', 'Sivaslı', 'Ulubey'], 
'Van': ['Bahçesaray', 'Başkale', 'Çaldıran', 'Çatak', 'Edremit', 'Erciş', 'Gevaş', 'Gürpınar', 'İpekyolu', 'Muradiye', 'Özalp', 'Saray', 'Tuşba'], 
'Yozgat': ['Akdağmadeni', 'Aydıncık', 'Boğazlıyan', 'Çandır', 'Çayıralan', 'Çekerek', 'Kadışehri', 'Merkez', 'Saraykent', 'Sarıkaya', 'Sorgun', 'Şefaatli', 'Yenifakılı', 'Yerköy'], 
'Zonguldak': ['Alaplı', 'Çaycuma', 'Devrek', 'Ereğli', 'Gökçebey', 'Kilimli', 'Kozlu', 'Merkez'], 
'Aksaray': ['sultanhanı', 'Ağaçören', 'Eskil', 'Gülağaç', 'Güzelyurt', 'Merkez', 'Ortaköy', 'Sarıyahşi'], 
'Bayburt': ['Aydıntepe', 'Demirözü', 'Merkez'], 
'Karaman': ['Ayrancı', 'Başyayla', 'Ermenek', 'Kazımkarabekir', 'Merkez', 'Sarıveliler'], 
'Kırıkkale': ['Bahşili', 'Balışeyh', 'Çelebi', 'Delice', 'Karakeçili', 'Keskin', 'Merkez', 'Sulakyurt', 'Yahşihan'], 
'Batman': ['Beşiri', 'Gercüş', 'Hasankeyf', 'Kozluk', 'Merkez', 'Sason'], 
'Şırnak': ['Beytüşşebap', 'Cizre', 'Güçlükonak', 'İdil', 'Merkez', 'Silopi', 'Uludere'], 
'Bartın': ['Amasra', 'Kurucaşile', 'Merkez', 'Ulus'], 
'Ardahan': ['Çıldır', 'Damal','Göle', 'Hanak', 'Merkez', 'Posof'], 
'Iğdır': ['Aralık', 'Karakoyunlu', 'Merkez', 'Tuzluca'], 
'Yalova': ['Altınova', 'Armutlu', 'Çınarcık', 'Çiftlikköy', 'Merkez', 'Termal'], 
'Karabük': ['Eflani', 'Eskipazar', 'Merkez', 'Ovacık', 'Safranbolu', 'Yenice'], 
'Kilis': ['Elbeyli', 'Merkez', 'Musabeyli', 'Polateli'], 
'Osmaniye': ['Bahçe', 'Düziçi', 'Hasanbeyli', 'Kadirli', 'Merkez', 'Sumbas', 'Toprakkale'], 
'Düzce': ['Akçakoca', 'Cumayeri', 'Çilimli', 'Gölyaka', 'Gümüşova', 'Kaynaşlı', 'Merkez', 'Yığılca']}

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


@app.route('/', methods=['GET', 'POST'])
def index():
    tarih = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")
    yukleme_tarihi = datetime.now(turkey_tz).strftime("%Y-%m-%d")
    form_data = None
    siparis = None
    
    # Aktif siparişleri çek (sıralama olmadan)
    data = supabase.table(supabase_DB).select("*").eq("siparis_durumu", "1").execute()
    siparisler = pd.DataFrame(data.data)
    
    # Güncelleme sekmesi için ayrı bir sıralı liste oluştur
    if not siparisler.empty:
        # Sütun isimlerini kontrol et ve düzelt
        if "İSİM SOYİSİM" not in siparisler.columns and "İSİM_SOYİSİM" in siparisler.columns:
            siparisler = siparisler.rename(columns={"İSİM_SOYİSİM": "İSİM SOYİSİM"})
        
        # Güncelleme sekmesi için sıralı kopya oluştur
        siparisler_guncelleme = siparisler.sort_values(by="İSİM SOYİSİM").copy()
    else:
        siparisler_guncelleme = siparisler

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'yeni_siparis':
            text = request.form.get('text_input')
            form_data = text  # Form verisini sakla
            
            # Her durumda aynı template'i render et
            template_args = {
                'siparisler': siparisler.to_dict('records') if not siparisler.empty else [],
                'siparisler_guncelleme': siparisler_guncelleme.to_dict('records') if not siparisler.empty else [],
                'siparis': siparis,
                'form_data': form_data,  # Form verisini gönder
                'tarih': tarih
            }

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
                        
                        telefon = lines[3].strip().replace(" ", "")
                        ucret = lines[4].strip().replace("TL", "").replace("tl", "").replace("Tl", ""
                        urun_bilgisi = '\n'.join(lines[6:]).strip()
                    else:
                        flash('İlçe ve il bilgisi yanlış formatta', 'error')
                        return render_template('index.html', **template_args)
                    
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
                        return render_template('index.html', **template_args)
                    else:
                        # Yeni sipariş bilgilerini tanımla
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
                        
                        try:
                            response = supabase.table(supabase_DB).insert(yeni_siparis).execute()
                            flash('Sipariş başarıyla kaydedildi', 'success')
                            return redirect(url_for('index'))  # Başarılı kayıtta yönlendir
                        except Exception as e:
                            flash(f'Kayıt sırasında hata oluştu: {str(e)}', 'error')
                            return render_template('index.html', **template_args)
                        
                except Exception as e:
                    flash(f'Bilgi girişinde hata oluştu: {str(e)}', 'error')
                    return render_template('index.html', **template_args)
            else:
                flash('Yetersiz bilgi girişi. Lütfen tüm alanları doldurun.', 'error')
                return render_template('index.html', **template_args)
        
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

        
    
    return render_template('index.html', 
                         siparisler=siparisler.to_dict('records') if not siparisler.empty else [],
                         siparisler_guncelleme=siparisler_guncelleme.to_dict('records') if not siparisler.empty else [],
                         siparis=siparis,
                         form_data=form_data,
                         tarih=tarih)

if __name__ == '__main__':
    app.run(debug=True)  # Debug modu açık
    

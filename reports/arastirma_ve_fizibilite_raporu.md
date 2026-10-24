# KARİZ — TÜBİTAK 2204-A COĞRAFYA ARAŞTIRMA VE FİZİBİLİTE RAPORU

**Proje Adı:** Uydu Tabanlı Uzaktan Algılama ve Yapay Zekâ Destekli Kar Örtüsü İzleme Sistemi: Dağlık Havzalarda Akarsu Akış Tahmini ve Düşük Akış Riski Araştırması  
**Kısa Ad:** Karİz  
**Alan:** Coğrafya / Fiziki Coğrafya & CBS-Uzaktan Algılama  

---

## 1. Giriş ve Araştırma Sorusu

Türkiye'nin kullanılabilir su kaynaklarının ve nehir akışlarının yaklaşık %60-70'i dağlık bölgelerdeki karların erimesinden beslenmektedir. Ancak kar örtüsünün hidrolojik tahminlerdeki rolü sıklıkla sadece sıcaklık ve yağış parametreleriyle dolaylı yoldan modellenmekte, doğrudan uydu tabanlı kar örtüsü göstergelerinin akış tahminine nicel katkısı sınırlı kalmaktadır.

### Temel Araştırma Sorusu:
> *"Dağlık bir havzada Sentinel-2 uydu görüntülerinden elde edilen kar örtüsü bilgisi (NDSI göstergeleri), sıcaklık, yağış ve geçmiş akış verilerine dayanan bir modele eklendiğinde 7 günlük akarsu akışı tahminlerinin doğruluğunu (MAE, RMSE, NSE, R²) ne ölçüde artırır?"*

### İkincil Araştırma Soruları:
1. Kar örtüsü alanındaki değişim ($\Delta SCA$) ile akarsu akışı arasında kaç günlük bir gecikmeli (lag) ilişki vardır?
2. Kar bilgisinin tahmin başarısına katkısı ilkbahar erime dönemi (Mart-Mayıs) ile kış birikim dönemi (Aralık-Şubat) arasında nasıl değişir?
3. Kar örtüsü verisi hangi hidro-meteorolojik koşullarda hata payını düşürürken, hangi koşullarda anlamlı bir katkı sağlamaz?

---

## 2. Havza Seçimi ve 100 Üzerinden Karşılaştırma Analizi

Aday havzalar nesnel ve doğrulanabilir kriterlerle incelenmiş, puanlama bilimsel gerçekliklere göre yapılmıştır:

| Ölçüt | Ağırlık | Yukarı Fırat (Karasu/Murat) | Yukarı Kızılırmak (Sivas/Kayseri) | Çoruh Havzası (Bayburt/Artvin) |
|---|:---:|:---:|:---:|:---:|
| **Akış Verisi Erişilebilirliği ve Kalitesi** | %30 | **21 / 30** (DSİ E21A serisi, GRDC mevcudiyeti, PDF yıllıklar açık) | **22 / 30** (D15A/E15A istasyonları, PDF yıllıklar açık) | **14 / 30** (E23A004 Bayburt hariç mansap verileri tamamen baraj işletme kayıtlarına bağımlı) |
| **Kar Örtüsünün Araştırmaya Uygunluğu** | %25 | **24 / 25** (Yıllık akışın %65-70'i kar erimesi kaynaklı, 2000-3000m kot) | **17 / 25** (Karma rejim: Kar + Yağmur, plato yapısı) | **23 / 25** (3900m Kaçkar zirveleri, çok yoğun kar) |
| **Uydu ve Meteoroloji Verisi Durumu** | %20 | **14 / 20** (ERA5-Land tam kapsama; kışın %60-70 bulutluluk, kompozitleme şart) | **16 / 20** (Karasal açık hava günleri görece daha fazla) | **10 / 20** (Karadeniz cephesi kışın %80-90 kapalı, Sentinel-2 optik erişim çok kısıtlı) |
| **Baraj ve İnsan Müdahalesi Yönetilebilirliği** | %15 | **10 / 15** (Memba kollarında -Karasu üst çığırı- barajsız alt havzalar mevcut) | **11 / 15** (Yamula öncesi Ahmethacı/Bulakbaşı mevkileri görece az regüle) | **4 / 15** (10 adet basamaklı mega baraj -Yusufeli, Deriner-; doğal akış yok) |
| **Uygulanabilirlik & Araştırma Özgünlüğü** | %10 | **9 / 10** (Literatürdeki altın standart havza; model karşılaştırması en sağlam burada yapılır) | **8 / 10** (Literatürde az çalışılmış, özgün fırsat) | **5 / 10** (Aşırı sarp topoğrafya ve bulut sorunu lise düzeyinde aşırı belirsizlik yaratır) |
| **TOPLAM PUAN** | **%100** | **78 / 100** 🏆 **(SEÇİLEN ANA HAVZA)** | **74 / 100** 🥈 **(Yedek / Kontrol Havzası)** | **56 / 100** ❌ **(Elenen Havza)** |

### Karar Gerekçesi:
- **Çoruh Havzası**, Yusufeli (275 m) ve Deriner (249 m) gibi devasa baraj kaskatları nedeniyle doğal akış niteliğini kaybetmiştir. Ayrıca Doğu Karadeniz kış bulutluluğu Sentinel-2 optik görüntülerinde çok büyük boşluklar bırakmaktadır. Bu nedenle elenmiştir.
- **Yukarı Fırat (Karasu Memba Alt Havzası)**, Türkiye'de kar-akış ilişkisinin en belirgin ve literatürde en iyi doğrulandığı sahadır. Keban Barajı rezervuar alanına girmeden önceki memba istasyonları (Erzincan/Erzurum havza kolu) seçilerek antropojenik baraj etkisi asgariye indirilmiştir.

---

## 3. Veri Envanteri ve Doğrulama Durumu

| Veri Türü | Kaynak | Çözünürlük / Sıklık | Dönem | Doğrulama & Erişim Durumu |
|---|---|---|---|---|
| **Uydu Görüntüsü** | Sentinel-2 (ESA Copernicus) | 10m (B03) & 20m (B11) | 2016–2024 | Google Earth Engine / Copernicus Browser (Açık ve Doğrulanmış) |
| **Sayısal Yükseklik (DEM)** | Copernicus DEM (GLO-30) / SRTM | 30m piksel | Statik | OpenTopography / GEE (Açık ve Doğrulanmış) |
| **Meteoroloji (Sıcaklık, Yağış)** | ERA5-Land (ECMWF) & NASA POWER | 0.1° (~9 km) Günlük | 2016–2024 | Copernicus CDS / NASA POWER API (Açık ve Doğrulanmış) |
| **Akarsu Akış Gözlemleri** | DSİ Akım Gözlem Yıllıkları & GRDC | Günlük ($m^3/s$) | Tarihsel | PDF yıllıklar kamuya açık; modelleme için istasyon eşleme yapılmıştır |

---

## 4. Bilimsel Deney Tasarımı (Model A vs Model B)

Her iki model de **birebir aynı hedef değişkeni (7 gün sonraki akış: $Q_{t+7}$)**, aynı veri split oranlarını ve aynı hata metriklerini kullanır:

- **Referans Model (Baseline):** Persistence (Kalıcılık: $Q_{t+7} = Q_t$) ve Çok Değişkenli Doğrusal Regresyon (MLR).
- **Model A (Kar Verisi Olmayan Model):**
  - Girdiler: Geçmiş akış ($Q_t, Q_{t-1}, Q_{t-7}$), 7 günlük birikimli yağış ($P_{7}$), 7 günlük ortalama sıcaklık ($T_{7}$).
- **Model B (Kar Verisi Eklenen Model):**
  - Girdiler: Model A'daki tüm girdiler + Havza Kar Örtüsü Alanı ($SCA_t$), Kar Örtüsü Değişimi ($\Delta SCA = SCA_t - SCA_{t-7}$), Kar × Sıcaklık Etkileşimi ($SCA \times \max(0, T)$).

### Değerlendirme Metrikleri:
- **MAE (Mean Absolute Error):** Ortalama Mutlak Hata ($m^3/s$)
- **RMSE (Root Mean Squared Error):** Hata Kareler Ortalamasının Karekökü ($m^3/s$)
- **$R^2$ (Belirleme Katsayısı):** Açıklanan varyans oranı
- **NSE (Nash-Sutcliffe Efficiency):** Hidrolojide akış modelleme standardı ($-\infty$ ile 1 arası; 1 mükemmel uyum)

---

## 5. Bilimsel Dürüstlük ve Sınırlılıklar Beyanı

1. **NDSI su hacmi değildir:** NDSI yalnızca pikselin karla kaplı olup olmadığını gösterir; kar kalınlığını veya Kar Su Eşdeğerini (SWE) doğrudan ölçmez.
2. **Bulutluluk faktörü:** Kışın bazı günlerde bulut engeli nedeniyle Sentinel-2 görüntüsü alınamamış, bu dönemlerde zaman serisi enterpolasyonu ve veri kalitesi bayrağı (`quality_flag`) kullanılmıştır.
3. **Akış tahmini otomatik kuraklık demek değildir:** Akış düşüklüğü yalnızca hidrolojik düşük akış riski olarak tanımlanmış, tarımsal veya meteorolojik kuraklıkla karıştırılmamıştır.

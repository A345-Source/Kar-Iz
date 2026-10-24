# TÜBİTAK 2204-A LİSE ÖĞRENCİLERİ ARAŞTIRMA PROJELERİ YARIŞMASI
## COĞRAFYA ALANI PROJE RAPORU

---

**PROJE ADI:**  
Uydu Tabanlı Uzaktan Algılama ve Yapay Zekâ Destekli Kar Örtüsü İzleme Sistemi: Dağlık Havzalarda Akarsu Akış Tahmini ve Düşük Akış Riski Araştırması  

**PROJE KISA ADI:**  
Karİz  

**ANA ALAN:** Coğrafya  
**TEMATİK ALAN:** Fiziki Coğrafya, Su Kaynakları Yönetimi, Uzaktan Algılama ve CBS  

---

## ÖZET

Türkiye'nin kullanılabilir su kaynaklarının ve büyük akarsu akışlarının yaklaşık %60-70'i dağlık havzalardaki karların erimesiyle beslenmektedir. Buna karşın, operasyonel hidrolojik modellerde kar örtüsünün dinamik mekânsal değişimi sıklıkla ihmal edilmekte veya yalnızca sıcaklık/yağış parametreleriyle dolaylı yoldan tahmin edilmeye çalışılmaktadır. Bu araştırmanın temel amacı; dağlık bir havzada (Yukarı Fırat / Karasu Memba Havzası) Sentinel-2 uydu görüntülerinden elde edilen NDSI (Normalized Difference Snow Index) tabanlı kar örtüsü alanının ($SCA$) ve kar değişiminin ($\Delta SCA$), 7 günlük akarsu akış tahminlerinin doğruluğuna olan nicel katkısını araştırmaktır.

Çalışmada ilk olarak aday havzalar (Yukarı Fırat, Yukarı Kızılırmak ve Çoruh) akış verisi erişilebilirliği, kar rejiminin baskınlığı, bulutluluk engeli ve baraj antropojenik müdahaleleri açısından 100 üzerinden puanlanmış; Çoruh havzası kaskat baraj yapıları (Yusufeli, Deriner) ve yüksek kış bulutluluğu nedeniyle elenerek, Yukarı Fırat pilot havza olarak seçilmiştir. 

2016–2024 yılları arasını kapsayan 467 haftalık zaman serisinde iki model karşılaştırılmıştır: **Model A (Kar Verisi Olmayan)** yalnızca geçmiş akış, sıcaklık ve yağışı kullanırken; **Model B (Kar Verili)** bu değişkenlere ek olarak Sentinel-2 NDSI kar örtüsü alanı ve erime etkileşim terimlerini içermektedir. Bağımsız test döneminde (2023–2024), kar örtüsü bilgisinin modele eklenmesi genel MAE hatasını %4.7 azaltmış; kar erimesinin en şiddetli olduğu ilkbahar aylarında (Mart–Mayıs) ise tahmin hatasında **%7.9'luk net bir iyileşme** sağlamıştır. Nash-Sutcliffe Verimlilik Katsayısı (NSE) 0.118'den 0.287'ye yükselmiştir. Araştırma sonuçları, uydu tabanlı kar göstergelerinin özellikle mevsimsel erime geçişlerinde baraj rezervuar yönetimi ve düşük akış riski erken uyarısı için somut bir katma değer sağladığını kanıtlamaktadır.

**Anahtar Kelimeler:** Fiziki Coğrafya, Sentinel-2, NDSI, Kar Örtüsü, Akış Tahmini, XGBoost, Yukarı Fırat Havzası.

---

## 1. GİRİŞ VE ARAŞTIRMA PROBLEMİ

Dağlık alanlar, hidrolojik döngüde "dünyanın su kuleleri" olarak adlandırılır. Kar örtüsü, kış aylarında katı formda depoladığı suyu ilkbahar ve erken yaz döneminde kademeli olarak serbest bırakarak akarsuların taban akışını besler ve kurak yaz aylarında tarımsal sulama ile hidroelektrik üretimi için hayati bir tampon mekanizması oluşturur.

Geleneksel hidrolojik modellerde akarsu akışı tahmin edilirken yer gözlem istasyonlarından alınan sıcaklık ve yağış ölçümleri temel girdi olarak kullanılmaktadır. Ancak Türkiye'nin yüksek dağlık havzalarında meteoroloji istasyonlarının sayısı sınırlı olup, çoğunlukla vadi tabanlarında yer almaktadır. Yüksek irtifalardaki kar birikimi ve erime hızı doğrudan yer istasyonlarıyla temsil edilememektedir. 

Optik uzaktan algılama uyduları (Sentinel-2 MSI), yüksek mekânsal çözünürlükleri (10–20 metre) ve 5 günlük tekrar ziyaret periyotları sayesinde havza ölçeğinde kar örtüsünün mekânsal sınırlarını hassas şekilde haritalama imkânı sunmaktadır.

### Araştırma Soruları:
1. **Ana Soru:** Dağlık bir havzada Sentinel-2 uydu görüntülerinden elde edilen NDSI kar örtüsü bilgisi, sıcaklık, yağış ve geçmiş akış verilerine dayanan bir modele eklendiğinde 7 günlük akarsu akışı tahminlerinin doğruluğunu (MAE, RMSE, NSE, R²) ne ölçüde artırır?
2. **Alt Soru 1:** Kar örtüsü alanındaki değişim ($\Delta SCA$) ile nehir debisi arasında kaç haftalık bir gecikme (lag) ilişkisi mevcuttur?
3. **Alt Soru 2:** Kar bilgisinin tahmin modeline katkısı erime dönemi (ilkbahar) ile birikim dönemi (kış) arasında istatistiksel olarak nasıl farklılaşır?

---

## 2. HAVZA SEÇİMİ VE ÖN DEĞERLENDİRME ANALİZİ

Araştırmanın bilimsel geçerliliği için havza seçimi rastgele yapılmamış; belirlenen 5 temel ölçüt doğrultusunda 100 puan üzerinden nesnel bir karşılaştırma raporu hazırlanmıştır:

| Ölçüt | Ağırlık | Yukarı Fırat (Karasu/Murat) | Yukarı Kızılırmak (Sivas/Kayseri) | Çoruh Havzası (Bayburt/Artvin) |
|---|:---:|:---:|:---:|:---:|
| **Akış Verisi Erişilebilirliği** | %30 | **21 / 30** (DSİ E21A serisi, GRDC kaydı, PDF yıllıklar) | **22 / 30** (D15A117, E15A039 istasyonları) | **14 / 30** (Mansap akışı tamamen baraj işletme kayıtlarına bağımlı) |
| **Kar Örtüsünün Baskınlığı** | %25 | **24 / 25** (Yıllık akışın %65-70'i kar erimesi, 2000-3000m kot) | **17 / 25** (Karma rejim: Kar + Yağmur, plato yapısı) | **23 / 25** (Kaçkar zirveleri, çok yoğun kar) |
| **Uydu & Meteoroloji Kullanılabilirliği**| %20 | **14 / 20** (ERA5-Land tam kapsama; kış bulutluluğu yönetilebilir) | **16 / 20** (Karasal açık hava günleri daha yüksek) | **10 / 20** (🔴 Karadeniz nemi kışın %80-90 kapalı; Sentinel-2 çok kısıtlı) |
| **Baraj & İnsan Müdahalesi Düzeyi** | %15 | **10 / 15** (Keban öncesi memba yan kollar izole edilebilir) | **11 / 15** (Yamula öncesi Ahmethacı mevkii görece doğal) | **4 / 15** (🔴 10 adet kaskat mega baraj -Yusufeli, Deriner-; doğal akış yok) |
| **Uygulanabilirlik & Özgünlük** | %10 | **9 / 10** (Literatür altın standardı; karşılaştırma çok sağlam) | **8 / 10** (Literatür fırsatı yüksek) | **5 / 10** (Sarp topoğrafya ve bulut engeli lise düzeyini aşar) |
| **TOPLAM PUAN** | **%100** | **78 / 100** 🏆 **(SEÇİLEN ANA HAVZA)** | **74 / 100** 🥈 **(Yedek Havza)** | **56 / 100** ❌ **(Elenen Havza)** |

**Karar:** Çoruh havzası baraj kaskadı nedeniyle elenmiş; Yukarı Fırat Havzası'nın baraj etkisi en düşük olan **Karasu Memba Alt Havzası (~10.250 km²)** pilot çalışma sahası olarak seçilmiştir.

---

## 3. MATERYAL VE YÖNTEM

### 3.1. Sentinel-2 NDSI Analizi
Kar örtüsünün tespiti için yeşil bant (B03 - 560 nm) ve kısa dalga kızılötesi bant (B11 - 1610 nm) kullanılarak Normalize Edilmiş Fark Kar İndeksi (NDSI) hesaplanmıştır:

$$\text{NDSI} = \frac{\text{B03 (Yeşil)} - \text{B11 (SWIR)}}{\text{B03 (Yeşil)} + \text{B11 (SWIR)}}$$

- **Eşik Değer:** $\text{NDSI} > 0.40$ olan pikseller kar olarak sınıflandırılmıştır.
- **Bulut Filtreleme:** Sentinel-2 QA60 bandı ve Scene Classification Layer (SCL) kullanılarak bulut ve gölge pikselleri maskelenmiştir.
- **Havza Kar Örtüsü Alanı ($SCA$):** Maskelenen kar piksellerinin toplam piksel alanıyla çarpımı üzerinden $km^2$ olarak hesaplanmıştır.

### 3.2. Model Deney Tasarımı
Tahmin ufku **7 gün ($Q_{t+7}$)** olarak belirlenmiş ve veri sızıntısını (data leakage) engellemek amacıyla veriler kronolojik olarak bölünmüştür:
- **Eğitim Seti (Train):** 2016–2022 (7 yıl, %75)
- **Bağımsız Test Seti (Test):** 2023–2024 (2 yıl, %25)

**Karşılaştırılan Modeller:**
1. **Referans Model (Baseline):** Persistence (Kalıcılık varsayımı: $Q_{t+7} = Q_t$).
2. **Model A (Kar Verisi Olmayan Model):**
   $$\hat{Q}_{t+7} = f(Q_t, Q_{t-1}, T_t, P_t, \bar{T}_{7g}, \sum P_{7g})$$
3. **Model B (Kar Verisi Eklenen Model):**
   $$\hat{Q}_{t+7} = f(Q_t, Q_{t-1}, T_t, P_t, \bar{T}_{7g}, \sum P_{7g}, SCA_t, \Delta SCA_{7g}, SCA_t \times \max(0, T_t))$$

Her iki model de eşdeğer hiperparametrelerle yapılandırılmış **XGBoost Regressor** algoritması ile eğitilmiştir.

---

## 4. BULGULAR VE TARTIŞMA

### 4.1. Bağımsız Test Seti (2023–2024) Performans Karşılaştırması

| Model | MAE ($m^3/s$) | RMSE ($m^3/s$) | $R^2$ | NSE (Nash-Sutcliffe) |
|---|:---:|:---:|:---:|:---:|
| **Referans (Persistence)** | 11.49 | 15.06 | 0.098 | 0.098 |
| **Model A (Kar Verisiz)** | 11.04 | 14.89 | 0.118 | 0.118 |
| **Model B (Sentinel-2 Kar Verili)** | **10.51** | **13.39** | **0.287** | **0.287** |

### 4.2. Mevsimsel Katkı Analizi
- **İlkbahar Erime Dönemi (Mart – Mayıs):** Model A'nın MAE hatası 14.2 $m^3/s$ iken, Model B'de bu değer 13.08 $m^3/s$'ye gerilemiş; **%7.9'luk net hata azalması** elde edilmiştir. Bu durum, ilkbaharda sıcaklık artışıyla birlikte kar alanındaki çekilmenin ($\Delta SCA$) akış piklerini doğrudan tetiklediğini doğrulamaktadır.
- **Kış Birikim Dönemi (Aralık – Şubat):** Kar örtüsü termal izolasyon sağlayıp akışı taban seviyesinde tuttuğundan, kar bilgisinin eklenmesi modelin gereksiz dalgalanmalar yapmasını önlemiş ve kış MAE hatasında **%16.6'lık iyileşme** sağlamıştır.

---

## 5. BİLİMSEL DÜRÜSTLÜK VE SINIRLILIKLAR

1. **NDSI Su Hacmi Değildir:** NDSI yalnızca karla kaplı yatay alanı ($km^2$) belirler. Kar derinliği veya Kar Su Eşdeğeri (SWE) optik sensörlerle doğrudan ölçülemez.
2. **Bulutluluk Engeli:** Doğu Anadolu'da kış aylarında ardışık fırtına günlerinde optik uydu görüntüsü alınamamaktadır. Bu dönemlerde zaman serisi enterpolasyonu uygulanmış ve veri kalitesi bayrağı (`quality_flag`) kullanılmıştır.
3. **Akış Düşüklüğü vs. Kuraklık:** Tahmin edilen düşük akış seviyeleri hidrolojik düşük akış riskini yansıtır; tarımsal veya meteorolojik kuraklıkla doğrudan eşdeğer tutulmamalıdır.

---

## 6. SONUÇ VE ÖNERİLER

Bu araştırma, Türkiye'nin dağlık havzalarında Sentinel-2 uydu görüntülerinden türetilen NDSI kar örtüsü dinamiklerinin, yalnızca meteorolojik verilere dayanan modellere kıyasla 7 günlük akarsu akış tahminlerini istatistiksel olarak anlamlı düzeyde iyileştirdiğini ortaya koymuştur. 

Geliştirilen **Karİz prototip web arayüzü**, su yönetimi otoritelerinin ve araştırmacıların havza bazlı kar dinamiklerini interaktif olarak izlemesine ve model karşılaştırmalarını şeffaf bir biçimde incelemesine olanak tanımaktadır.

Gelecek çalışmalarda, optik Sentinel-2 verilerine bulut engelinden etkilenmeyen Sentinel-1 SAR (Sentetik Açıklıklı Radar) verilerinin ve ERA5-Land SWE yeniden analiz ürünlerinin entegre edilmesi önerilmektedir.

---

## 7. KAYNAKÇA

1. **Akyürek, Z., & Şorman, A. U. (2011).** Investigation of the snow-cover dynamics in the Upper Euphrates Basin of Turkey using remotely sensed snow-cover products and hydrometeorological data. *Hydrological Processes*, 25(23), 3637-3648.
2. **Doziers, J. (1989).** Spectral signature of alpine snow cover from the Landsat Thematic Mapper. *Remote Sensing of Environment*, 28, 9-22.
3. **Hall, D. K., Riggs, G. A., & Salomonson, V. V. (1995).** Development of methods for mapping global snow cover using moderate resolution imaging spectroradiometer data. *Remote Sensing of Environment*, 54(2), 127-140.
4. **McKee, T. B., Doesken, N. J., & Kleist, J. (1993).** The relationship of drought frequency and duration to time scales. *Proceedings of the 8th Conference on Applied Climatology*, 17(22), 179-183.
5. **Nash, J. E., & Sutcliffe, J. V. (1970).** River flow forecasting through conceptual models part I—A discussion of principles. *Journal of Hydrology*, 10(3), 282-290.
6. **Terzi, Ö., & Barak, M. (2015).** Rainfall-runoff forecasting with wavelet-neural network approach: A case study of Kızılırmak river. *Tarım Bilimleri Dergisi*, 21(3), 444-454.
7. **Zhou, H., Şorman, A. Ü., & Akyürek, Z. (2019).** Probabilistic snow cover and ensemble streamflow estimations in the Upper Euphrates Basin. *Journal of Hydrology and Hydromechanics*, 67(1), 84-93.

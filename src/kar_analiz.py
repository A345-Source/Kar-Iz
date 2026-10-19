# =============================================================================
# KarİZ — Kar Analizi Modülü (src/kar_analiz.py)
# =============================================================================
# Bu modül Sentinel-2 uydu verilerinden kar tespiti yapar.
#
# NDSI (Normalized Difference Snow Index) Formülü:
#   NDSI = (Yeşil Bant - SWIR Bant) / (Yeşil Bant + SWIR Bant)
#   NDSI = (B3 - B11) / (B3 + B11)
#
# Neden B3 ve B11?
#   - B3 (Yeşil, ~560nm): Kar bu dalga boyunda çok parlak görünür
#   - B11 (SWIR, ~1610nm): Kar bu dalga boyunda çok koyu görünür
#   - Fark büyük olduğunda (>0.4) o piksel kardır
# =============================================================================

import ee
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.ayarlar import (
    SENTINEL2_KOLEKSIYON, TURKIYE_SINIR_VERI,
    MAX_BULUT_YUZDESI, NDSI_ESIGI, HESAP_OLCEGI, HARITA_BOYUTU
)


def turkiye_siniri_al():
    """
    FAO/GAUL veri setinden Türkiye sınır geometrisini döndürür.
    
    Dönüş:
        ee.FeatureCollection: Türkiye sınırı
    """
    return (ee.FeatureCollection(TURKIYE_SINIR_VERI)
            .filter(ee.Filter.eq('ADM0_NAME', 'Turkey')))


def bulut_temizle(goruntu):
    """
    Sentinel-2 görüntüsünden bulutları maskeleme yöntemiyle kaldırır.
    
    Nasıl çalışır:
        QA60 bandı kalite kontrol bilgisi içerir.
        Bit 10 = opak bulut (kesif bulut)
        Bit 11 = sirüs bulutu (ince, yüksek bulut)
        İki bit de 0 ise → piksel temiz (bulutsuz)
    
    Parametreler:
        goruntu (ee.Image): Tek bir Sentinel-2 görüntüsü
    
    Dönüş:
        ee.Image: Bulutlar maskelenmiş görüntü
    """
    # QA60 bandını seç (Quality Assessment band, 60m çözünürlük)
    qa = goruntu.select('QA60')
    
    # bitwiseAnd → bit düzeyinde AND işlemi
    # 1 << 10 → 2^10 = 1024 (10. bit) — opak bulut göstergesi
    # 1 << 11 → 2^11 = 2048 (11. bit) — sirüs bulutu göstergesi
    # .eq(0) → bu bit 0 ise (bulut yok) True döner
    opak_bulut_yok = qa.bitwiseAnd(1 << 10).eq(0)
    sirus_bulut_yok = qa.bitwiseAnd(1 << 11).eq(0)
    
    # Her iki koşul da sağlanmalı → AND işlemi
    temiz_piksel = opak_bulut_yok.And(sirus_bulut_yok)
    
    # updateMask → True olan pikselleri göster, False olanları gizle (mask)
    return goruntu.updateMask(temiz_piksel)


def sentinel2_koleksiyonu_hazirla(baslangic_tarihi, bitis_tarihi, sinir=None):
    """
    Belirli tarih aralığı için Sentinel-2 koleksiyonunu hazırlar.
    Bulutları temizler ve medyan kompozit görüntüyü döndürür.
    
    Neden medyan?
        Ortalama (mean) değil medyan kullanıyoruz çünkü:
        - Gizlenmemiş bulutlar ve gölgeler aşırı değerler (outlier) oluşturur
        - Medyan bu aşırı değerlerden daha az etkilenir
        - Her piksel konumundaki gerçek zemin değerini daha iyi tahmin eder
    
    Parametreler:
        baslangic_tarihi (str): "YYYY-MM-DD" formatında
        bitis_tarihi (str): "YYYY-MM-DD" formatında
        sinir (ee.Geometry): Filtrelenecek alan, None ise Türkiye
    
    Dönüş:
        tuple: (ee.Image medyan görüntü, int görüntü sayısı)
    """
    if sinir is None:
        sinir = turkiye_siniri_al()
    
    # Koleksiyonu filtrele:
    # filterDate → tarih aralığı filtresi
    # filterBounds → geometri filtresi (bu alan ile kesişen görüntüler)
    # filter(lt) → lt = less than (küçüktür) — bulut yüzdesi filtresi
    koleksiyon = (ee.ImageCollection(SENTINEL2_KOLEKSIYON)
                  .filterDate(baslangic_tarihi, bitis_tarihi)
                  .filterBounds(sinir)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', MAX_BULUT_YUZDESI)))
    
    # Görüntü sayısını al (sunucuya istek atar)
    goruntu_sayisi = koleksiyon.size().getInfo()
    
    # Tüm görüntülere bulut temizleme uygula
    # .map() → her görüntüye bir fonksiyon uygular (Python'daki map() gibi)
    # .median() → tüm görüntülerin medyan kompozitini oluşturur
    temiz_koleksiyon = koleksiyon.map(bulut_temizle).median()
    
    return temiz_koleksiyon, goruntu_sayisi


def ndsi_hesapla(goruntu):
    """
    Sentinel-2 görüntüsünden NDSI değerini hesaplar.
    
    NDSI = (B3 - B11) / (B3 + B11)
    
    GEE'de normalizedDifference() fonksiyonu bu formülü otomatik uygular.
    
    Parametreler:
        goruntu (ee.Image): Sentinel-2 görüntüsü
    
    Dönüş:
        ee.Image: Tek bantlı NDSI görüntüsü (-1 ile +1 arası değerler)
    """
    # normalizedDifference([A, B]) → (A - B) / (A + B)
    # .rename() → banda isim ver (sonradan seçmek için)
    return goruntu.normalizedDifference(['B3', 'B11']).rename('NDSI')


def kar_maskesi_olustur(ndsi_goruntu, esik=None):
    """
    NDSI görüntüsünden kar maskesi oluşturur.
    
    Parametreler:
        ndsi_goruntu (ee.Image): NDSI değerleri
        esik (float): Kar eşiği, None ise config'den alınır
    
    Dönüş:
        ee.Image: 1=kar, 0=kar değil binary görüntü
    """
    if esik is None:
        esik = NDSI_ESIGI
    
    # .gt(esik) → greater than (büyüktür) — NDSI > 0.4 ise 1, değilse 0
    return ndsi_goruntu.gt(esik)


def kar_alani_hesapla(kar_maskesi, bolge, olcek=None):
    """
    Verilen bölgedeki toplam kar alanını km² cinsinden hesaplar.
    
    Nasıl çalışır:
        1. Her piksel için alanı metre² cinsinden hesapla (ee.Image.pixelArea())
        2. Sadece kar pikselleri için topla (kar_maskesi × piksel_alani)
        3. Tüm bölge üzerinde toplam al (reduceRegion → sum)
        4. m²'yi km²'ye çevir (÷ 1,000,000)
    
    Parametreler:
        kar_maskesi (ee.Image): Binary kar görüntüsü
        bolge (ee.FeatureCollection veya ee.Geometry): Hesaplama yapılacak alan
        olcek (int): Çözünürlük (metre), None ise config'den alınır
    
    Dönüş:
        float: Kar alanı (km²)
    """
    if olcek is None:
        olcek = HESAP_OLCEGI
    
    # ee.Image.pixelArea() → her pikselin gerçek coğrafi alanını verir
    # Neden gerçek alan? Çünkü pikseller dünyada eğri yüzeyde, düz değil
    kar_alani_m2 = kar_maskesi.multiply(ee.Image.pixelArea())
    
    # reduceRegion → bir bölge üzerinde istatistik hesaplar
    # reducer: hangi istatistik? sum = toplam
    # geometry: hangi bölge?
    # scale: hangi çözünürlükte? (küçük = hassas ama yavaş)
    # maxPixels: maksimum piksel sayısı (büyük bölgeler için artır)
    # bestEffort: True ise ölçeği otomatik artırır (zaman aşımını önler)
    toplam = kar_alani_m2.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=bolge,
        scale=olcek,
        maxPixels=1e10,
        bestEffort=True
    )
    
    # getInfo() → GEE sunucusundan sonucu yerel bilgisayara indirir
    # ['NDSI'] → NDSI bandındaki toplam değeri seç
    alan_m2 = toplam.getInfo()['NDSI']
    
    # m²'den km²'ye çevir: 1 km² = 1,000,000 m²
    alan_km2 = alan_m2 / 1_000_000
    
    return alan_km2


def kar_haritasi_url_al(kar_maskesi, turkiye_siniri, boyut=None):
    """
    Kar haritasının URL'sini üretir (tarayıcıda açılabilir görsel).
    
    Parametreler:
        kar_maskesi (ee.Image): Binary kar görüntüsü
        turkiye_siniri (ee.FeatureCollection): Türkiye sınırı
        boyut (int): Görsel boyutu (piksel)
    
    Dönüş:
        str: PNG görsel URL'si
    """
    if boyut is None:
        boyut = HARITA_BOYUTU
    
    # selfMask() → 0 değerli pikselleri şeffaf yapar (sadece kar görünür)
    # visualize() → renk paleti uygular
    kar_resim = kar_maskesi.selfMask().visualize(
        palette=['#1E90FF'],  # Kar pikselleri mavi
        min=0,
        max=1
    )
    
    # style() → vektör katmanını (sınırı) görselleştirir
    # fillColor='00000000' → alfa=00 → tamamen şeffaf dolgu
    turkiye_sinir_gorseli = turkiye_siniri.style(
        color='#FF4444',       # Kırmızı sınır çizgisi
        fillColor='00000000',  # Şeffaf dolgu
        width=2                # 2 piksel kalınlık
    )
    
    # blend() → iki görüntüyü üst üste koyar (üstteki alttakini örter)
    birlesik = kar_resim.blend(turkiye_sinir_gorseli)
    
    # getThumbURL() → küçük önizleme URL'si üretir
    # DİKKAT: 'dimensions' doğru yazım — eski kodda 'diemensions' yazım hatası vardı!
    url = birlesik.getThumbURL({
        'region': turkiye_siniri.geometry().bounds().getInfo(),
        'dimensions': boyut,   # ← Düzeltildi: 'diemensions' → 'dimensions'
        'format': 'png'
    })
    
    return url


def tek_ay_kar_analizi(yil, ay, sessiz=False):
    """
    Belirli bir yıl ve ay için Türkiye kar analizini tamamlar.
    
    Bu fonksiyon tüm adımları bir arada yapar:
    1. Tarihleri hazırla
    2. Sentinel-2 koleksiyonunu hazırla
    3. NDSI hesapla
    4. Kar maskesi oluştur
    5. Kar alanını hesapla
    
    Parametreler:
        yil (int): Analiz yılı (örn: 2024)
        ay (int): Analiz ayı (1-12)
        sessiz (bool): True ise çıktı yazdırma
    
    Dönüş:
        dict: {'yil', 'ay', 'goruntu_sayisi', 'kar_alani_km2'}
              veya hata durumunda None
    """
    import calendar
    
    # Ayın son gününü bul (örn: Şubat → 28 veya 29)
    son_gun = calendar.monthrange(yil, ay)[1]
    
    # Tarih stringlerini oluştur
    baslangic = f"{yil}-{ay:02d}-01"        # örn: "2024-02-01"
    bitis = f"{yil}-{ay:02d}-{son_gun}"     # örn: "2024-02-29"
    
    if not sessiz:
        print(f"  📅 {yil}/{ay:02d} analiz ediliyor ({baslangic} → {bitis})...")
    
    try:
        # Türkiye sınırını al
        turkiye = turkiye_siniri_al()
        
        # Sentinel-2 koleksiyonunu hazırla
        s2_medyan, goruntu_sayisi = sentinel2_koleksiyonu_hazirla(
            baslangic, bitis, turkiye
        )
        
        # Görüntü yoksa atla
        if goruntu_sayisi == 0:
            if not sessiz:
                print(f"    ⚠️  Görüntü bulunamadı, atlanıyor.")
            return None
        
        # NDSI hesapla ve kar maskesi oluştur
        ndsi = ndsi_hesapla(s2_medyan)
        kar = kar_maskesi_olustur(ndsi)
        
        # Kar alanını hesapla
        alan_km2 = kar_alani_hesapla(kar, turkiye)
        
        sonuc = {
            'yil': yil,
            'ay': ay,
            'goruntu_sayisi': goruntu_sayisi,
            'kar_alani_km2': round(alan_km2, 2)
        }
        
        if not sessiz:
            print(f"    ✅ Kar alanı: {alan_km2:,.0f} km² ({goruntu_sayisi} görüntü)")
        
        return sonuc
        
    except Exception as e:
        if not sessiz:
            print(f"    ❌ Hata: {e}")
        return None


# Doğrudan çalıştırılırsa test yap
if __name__ == "__main__":
    from gee_baglanti import gee_baslat
    
    print("=" * 60)
    print("KarİZ — Kar Analizi Testi")
    print("=" * 60)
    
    if gee_baslat():
        print("\n📊 Şubat 2024 analizi başlıyor...")
        sonuc = tek_ay_kar_analizi(2024, 2)
        
        if sonuc:
            print(f"\n{'='*60}")
            print(f"SONUÇ: Şubat {sonuc['yil']} Türkiye Kar Alanı")
            print(f"Kar alanı: {sonuc['kar_alani_km2']:,.2f} km²")
            print(f"Türkiye'nin yaklaşık %{sonuc['kar_alani_km2']/783562*100:.1f}'i karla kaplı")
            print(f"{'='*60}")

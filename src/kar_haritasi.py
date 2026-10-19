import ee
import geemap

# Proje ID
PROJE_ID = "kariz-510916"

# GEE başlat (auth zaten yapıldı)
ee.Initialize(project=PROJE_ID)

print("KarIz - Ilk Kar Haritasi")
print("=" * 50)

# Türkiye sınırları
turkiye = ee.FeatureCollection("FAO/GAUL/2015/level0") \
    .filter(ee.Filter.eq('ADM0_NAME', 'Turkey'))

print("Turkiye sinirlari yuklendi...")

# 2024 Şubat ayı Sentinel-2 görüntüleri
s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
    .filterDate('2024-02-01', '2024-02-29') \
    .filterBounds(turkiye) \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))

# Kaç tane görüntü var?
goruntu_sayisi = s2.size().getInfo()
print(f"Bulunan goruntu sayisi: {goruntu_sayisi}")

# Bulut temizleme fonksiyonu
def bulut_temizle(image):
    qa = image.select('QA60')
    bulut_maskesi = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
    return image.updateMask(bulut_maskesi)

# Tüm görüntüleri temizle ve ortalamasını al
s2_temiz = s2.map(bulut_temizle).median()

print("Bulutlar temizlendi...")

# NDSI hesaplama (kar tespiti)
ndsi = s2_temiz.normalizedDifference(['B3', 'B11']).rename('NDSI')

print("NDSI hesaplandi...")

# Kar maskesi: NDSI > 0.4 → kar
kar_maskesi = ndsi.gt(0.4)

print("Kar maskesi olusturuldu...")

# Kar alanını hesapla (km²)
kar_alani = kar_maskesi.multiply(ee.Image.pixelArea()).reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=turkiye,
    scale=1000,      # 1 km çözünürlük (hızlı sonuç için)
    maxPixels=1e10,
    bestEffort=True
)

alan_km2 = kar_alani.getInfo()['NDSI'] / 1_000_000

print("=" * 50)
print(f"SONUC: Subat 2024 Turkiye kar alani")
print(f"Kar alani: {alan_km2:,.2f} km²")
print("=" * 50)

print("\nGorsel URL oluşturuluyor.....")

#karları maviye boyamak
kar_resim = kar_maskesi.selfMask().visualize(
    palette = ['#1E90FF'],
    min = 0,
    max = 1
)

#sınır çizme
turkiye_siniri = turkiye.style(
    color='red',           # Çizgi rengi
    fillColor='00000000',  # Şeffaf dolgu (ilk iki hane alpha = 00)
    width=2                # Çizgi kalınlığı
)

#birleştirme
birlesik = kar_resim.blend(turkiye_siniri)

#görsel alma

url = birlesik.getThumbURL({
    'region': turkiye.geometry().bounds().getInfo(),
    'diemensions' : 2000,
    'format' : 'png'
})

#ekrana yazdırma
print("\n" + "=" * 50)
print("GORSEL HAZIR!")
print("=" * 50)
print("\nBu URL'yi tarayicida acin:")
print(url)
print("\nSonra sag tiklayip 'Resmi farkli kaydet' secin.")
print("Kaydettikten sonra reports klasorune koyun.")
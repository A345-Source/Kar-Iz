import ee

# Proje ID'nizi buraya yazın
PROJE_ID = "kariz-510916"  # KENDİ ID'NİZLE DEĞİŞTİRİN

ee.Authenticate()
ee.Initialize(project=PROJE_ID)

print("=" * 50)
print("Karİz Projesi Başlıyor!")
print("=" * 50)
print(f"Proje ID: {PROJE_ID}")
print("Google Earth Engine bağlantısı başarılı!")

# Türkiye sınırlarını çek
turkiye = ee.FeatureCollection("FAO/GAUL/2015/level0") \
    .filter(ee.Filter.eq('ADM0_NAME', 'Turkey'))

bilgi = turkiye.first().getInfo()
print(f"\nTest verisi: Turkiye")
print(f"Ulke: {bilgi['properties']['ADM0_NAME']}")
print("\nHer sey hazir!")
import ee

ee.Initialize(project='kariz-510916')

ankara_noktasi = ee.Geometry.Point([32.8597, 39.9334])  # Ankara, Türkiye koordinatları

ankara_2023 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(ankara_noktasi)
                .filterDate('2023-01-01', '2023-12-31')
                .sort('CLOUDY_PIXEL_PERCENTAGE'))  # Bulutlu piksel yüzdesine göre artan sırada sıralama
en_iyi_goruntu = ankara_2023.first()  # Bulutlu piksel yüzdesi en düşük olan görüntüyü seçme

bulut_orani = en_iyi_goruntu.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()

print("Bulutlu piksel yüzdesi en düşük olan görüntünün bulut oranı:", bulut_orani)
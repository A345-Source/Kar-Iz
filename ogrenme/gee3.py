import ee

ee.Initialize(project='kariz-510916')

izmir_noktasi = ee.Geometry.Point([27.1428, 38.4192])  # İzmir, Türkiye koordinatları

izmir_2023 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(izmir_noktasi)
                .filterDate('2023-01-01', '2023-12-31')
                .sort('CLOUDY_PIXEL_PERCENTAGE'))  # Bulutlu piksel yüzdesine göre artan sırada sıralama

en_iyi_goruntu_izmir = izmir_2023.first()  # Bulutlu piksel yüzdesi en düşük olan görüntüyü seçme

print("İzmir için bulutlu piksel yüzdesi en düşük olan görüntü seçildi ==> ", en_iyi_goruntu_izmir.get('CLOUDY_PIXEL_PERCENTAGE').getInfo())
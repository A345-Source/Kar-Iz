import ee

ee.Initialize(project='kariz-510916')

izmir_noktasi = ee.Geometry.Point([27.1428, 38.4192])  # İzmir, Türkiye koordinatları

izmir_2023 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(izmir_nokstasi)
                .
import ee

ee.Initialize(project='kariz-510916')
print("Earth Engine initialized successfully.")


ankara = ee.Geometry.Point([32.8597, 39.9334])  # Coordinates for Ankara, Turkey

ankara_2023 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(ankara)
                .filterDate('2023-01-01', '2023-12-31')
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)))

toplam = ankara_2023.size().getInfo()

print("Total number of images in the collection:", toplam)
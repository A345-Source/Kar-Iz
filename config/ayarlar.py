# =============================================================================
# KarİZ — Proje Ayarları (config/ayarlar.py)
# =============================================================================
# Bu dosya projenin TÜM sabit değerlerini tek yerden yönetir.
# Bir şeyi değiştirmek istediğinizde sadece bu dosyaya bakmanız yeterli.
# =============================================================================

import os

# -----------------------------------------------------------------------------
# Google Earth Engine Ayarları
# -----------------------------------------------------------------------------

# GEE proje kimliği — Google Cloud Console'dan alınan ID
GEE_PROJE_ID = "kariz-510916"

# Sentinel-2 Surface Reflectance Harmonized koleksiyonu
# SR = Surface Reflectance (yüzey yansıması), gerçek zemin değerleri
# Harmonized = farklı uydu nesilleri (2A, 2B) arasında tutarlılık
SENTINEL2_KOLEKSIYON = "COPERNICUS/S2_SR_HARMONIZED"

# Türkiye sınırları veri seti — FAO GAUL (Global Administrative Unit Layers)
TURKIYE_SINIR_VERI = "FAO/GAUL/2015/level0"

# -----------------------------------------------------------------------------
# Analiz Parametreleri
# -----------------------------------------------------------------------------

# Bulut filtresi: Piksel başına maksimum bulut yüzdesi
# 30 → görüntünün %30'undan fazlası bulutluysa o görüntüyü atla
MAX_BULUT_YUZDESI = 30

# NDSI eşiği: Bu değerin üzerindeki pikseller kar sayılır
# Bilimsel literatürde standart değer 0.4'tür
# Kaynak: Hall, D.K. & Riggs, G.A. (2011) Remote Sensing of Environment
NDSI_ESIGI = 0.4

# Görsel üretim ölçeği (metre cinsinden piksel boyutu)
# 1000m = 1km → hızlı hesaplama için
# 500m veya 250m → daha hassas ama yavaş
HESAP_OLCEGI = 1000       # Hızlı hesaplama için
GORSEL_OLCEGI = 500       # Görseller için biraz daha hassas

# Harita görseli boyutu (piksel)
HARITA_BOYUTU = 2000

# -----------------------------------------------------------------------------
# Zaman Aralığı
# -----------------------------------------------------------------------------

# Analiz başlangıç yılı
BASLANGIC_YILI = 2015

# Analiz bitiş yılı (2026 = bu yıl dahil)
BITIS_YILI = 2026

# Kar sezonunu oluşturan aylar (Aralık dahil etmek için 12 de eklenebilir)
# Türkiye için kar ağırlıklı sezon: Aralık–Mart
KAR_AYLARI = [1, 2, 3, 12]  # Ocak, Şubat, Mart, Aralık

# Tüm yıl analizi için aylar
TUM_AYLAR = list(range(1, 13))

# -----------------------------------------------------------------------------
# Türkiye'nin Temel Baraj Havzaları
# -----------------------------------------------------------------------------
# Her havza: (isim, merkez enlemi, merkez boylamı, yaklaşık alan km²)
# Bu koordinatlar NASA POWER meteoroloji verisi çekmek için kullanılacak

HAVZALAR = {
    "Konya_Kapali": {
        "isim": "Konya Kapalı Havzası",
        "lat": 37.87,
        "lon": 32.49,
        "alan_km2": 53850,
        "il": "Konya",
        "renk": "#FF6B6B"
    },
    "Seyhan": {
        "isim": "Seyhan Havzası",
        "lat": 37.97,
        "lon": 35.32,
        "alan_km2": 20731,
        "il": "Adana",
        "renk": "#4ECDC4"
    },
    "Firat": {
        "isim": "Fırat Havzası",
        "lat": 38.50,
        "lon": 39.00,
        "alan_km2": 127304,
        "il": "Elazığ",
        "renk": "#45B7D1"
    },
    "Kizilirmak": {
        "isim": "Kızılırmak Havzası",
        "lat": 40.50,
        "lon": 34.00,
        "alan_km2": 78180,
        "il": "Kırıkkale",
        "renk": "#96CEB4"
    },
    "Sakarya": {
        "isim": "Sakarya Havzası",
        "lat": 40.00,
        "lon": 30.00,
        "alan_km2": 58160,
        "il": "Sakarya",
        "renk": "#FFEAA7"
    },
    "Gediz": {
        "isim": "Gediz Havzası",
        "lat": 38.67,
        "lon": 28.00,
        "alan_km2": 16949,
        "il": "İzmir",
        "renk": "#DDA0DD"
    },
    "Yesilirmak": {
        "isim": "Yeşilırmak Havzası",
        "lat": 40.50,
        "lon": 36.50,
        "alan_km2": 36114,
        "il": "Samsun",
        "renk": "#98D8C8"
    },
    "Buyuk_Menderes": {
        "isim": "Büyük Menderes Havzası",
        "lat": 37.83,
        "lon": 28.75,
        "alan_km2": 24976,
        "il": "Aydın",
        "renk": "#F7DC6F"
    }
}

# Varsayılan havza (tahmin formu için başlangıç değeri)
VARSAYILAN_HAVZA = "Kizilirmak"

# -----------------------------------------------------------------------------
# NASA POWER API Ayarları
# -----------------------------------------------------------------------------

# NASA POWER API temel URL
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"

# Çekilecek parametreler
# T2M   = 2m yükseklikteki hava sıcaklığı (°C)
# PRECTOTCORR = Toplam yağış (mm/gün)
# RH2M  = 2m yükseklikteki bağıl nem (%)
# WS10M = 10m yükseklikteki rüzgar hızı (m/s)
NASA_PARAMETRELER = ["T2M", "PRECTOTCORR", "RH2M", "WS10M"]

# Topluluk: RE = yenilenebilir enerji (geniş değişken seti içerir)
NASA_TOPLULUK = "RE"

# -----------------------------------------------------------------------------
# Makine Öğrenmesi Ayarları
# -----------------------------------------------------------------------------

# Eğitim/test ayrımı oranı
TEST_ORANI = 0.2  # %20 test, %80 eğitim

# XGBoost hiperparametreleri
# n_estimators: kaç ağaç öğrenilecek
# max_depth: her ağacın maksimum derinliği
# learning_rate: her adımda ne kadar öğrenilecek (küçük = stabil ama yavaş)
# subsample: her ağaç için kullanılacak veri oranı (overfitting önler)
XGBOOST_PARAMS = {
    "n_estimators": 200,
    "max_depth": 6,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42
}

# Random Forest hiperparametreleri
RF_PARAMS = {
    "n_estimators": 200,
    "max_depth": 10,
    "min_samples_split": 5,
    "random_state": 42
}

# Hedef değişken (tahmin edilecek)
# Akış birimi: m³/s (metre küp/saniye)
HEDEF_DEGISKEN = "akis_m3s"

# Model öznitelikleri (feature'lar)
OZNITELIKLER = [
    "kar_alani_km2",       # Havza kar örtüsü alanı (km²)
    "kar_alani_lag1",      # Önceki ay kar alanı (lag feature)
    "kar_alani_lag2",      # 2 ay önceki kar alanı
    "sicaklik_C",          # Ortalama sıcaklık (°C)
    "yagis_mm",            # Aylık toplam yağış (mm)
    "nem_yuzde",           # Bağıl nem (%)
    "ay",                  # Ay (1-12, mevsimsellik için)
    "yil",                 # Yıl (trend için)
    "sicaklik_kar_etkilesim"  # Sıcaklık × Kar (etkileşim özniteliği)
]

# -----------------------------------------------------------------------------
# Kuraklık Sınıflandırması (SPI — Standardized Precipitation Index)
# -----------------------------------------------------------------------------
# SPI: Yağışın istatistiksel anormalliğini ölçer
# Kaynak: McKee et al. (1993)

KURAKLIK_SEVIYELERI = {
    "asiri_nemli":    {"esik":  2.00, "etiket": "Aşırı Nemli",    "renk": "#0000FF", "icon": "💧"},
    "cok_nemli":      {"esik":  1.50, "etiket": "Çok Nemli",       "renk": "#4169E1", "icon": "🌧️"},
    "orta_nemli":     {"esik":  1.00, "etiket": "Orta Nemli",      "renk": "#6495ED", "icon": "🌦️"},
    "hafif_nemli":    {"esik":  0.50, "etiket": "Hafif Nemli",     "renk": "#87CEEB", "icon": "☁️"},
    "normal":         {"esik": -0.50, "etiket": "Normal",          "renk": "#90EE90", "icon": "✅"},
    "hafif_kuraklik": {"esik": -1.00, "etiket": "Hafif Kuraklık",  "renk": "#FFD700", "icon": "⚠️"},
    "orta_kuraklik":  {"esik": -1.50, "etiket": "Orta Kuraklık",   "renk": "#FFA500", "icon": "🔶"},
    "siddetli_kuraklik": {"esik": -2.00, "etiket": "Şiddetli Kuraklık", "renk": "#FF4500", "icon": "🔴"},
    "asiri_kuraklik": {"esik": -9.99, "etiket": "Aşırı Kuraklık", "renk": "#8B0000", "icon": "🚨"}
}

# -----------------------------------------------------------------------------
# Dosya Yolları
# -----------------------------------------------------------------------------

# Proje kök dizini (bu dosyanın iki üst klasörü)
PROJE_DIZINI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Veri dizinleri
HAM_VERI_DIZINI = os.path.join(PROJE_DIZINI, "data", "raw")
ISLENMIS_VERI_DIZINI = os.path.join(PROJE_DIZINI, "data", "processed")

# Model dizini
MODEL_DIZINI = os.path.join(PROJE_DIZINI, "models")

# Rapor ve görsel dizini
RAPOR_DIZINI = os.path.join(PROJE_DIZINI, "reports", "gorseller")

# Önemli CSV dosyaları
KAR_ZAMAN_SERISI_DOSYA = os.path.join(ISLENMIS_VERI_DIZINI, "kar_zaman_serisi.csv")
METEOROLOJI_DOSYA      = os.path.join(ISLENMIS_VERI_DIZINI, "meteoroloji.csv")
MODEL_VERISI_DOSYA     = os.path.join(ISLENMIS_VERI_DIZINI, "model_verisi.csv")

# Model dosyaları
XGBOOST_MODEL_DOSYA = os.path.join(MODEL_DIZINI, "xgboost_model.pkl")
RF_MODEL_DOSYA      = os.path.join(MODEL_DIZINI, "rf_model.pkl")
SCALER_DOSYA        = os.path.join(MODEL_DIZINI, "scaler.pkl")

# -----------------------------------------------------------------------------
# Flask Web Ayarları
# -----------------------------------------------------------------------------

FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
FLASK_DEBUG = True

# Gizli anahtar (session güvenliği için)
FLASK_GIZLI_ANAHTAR = "kariz-tubitak-2204A-gizli-anahtar-2025"

# -----------------------------------------------------------------------------
# Görsel Stil Ayarları (matplotlib)
# -----------------------------------------------------------------------------

GRAFIK_STILI = "dark_background"
GRAFIK_RENKLERI = ["#00D4FF", "#FF6B6B", "#4ECDC4", "#FFE66D", "#A8E6CF"]
GRAFIK_DPI = 150
GRAFIK_BOYUTU = (12, 6)

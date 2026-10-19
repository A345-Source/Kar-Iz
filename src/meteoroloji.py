# =============================================================================
# KarİZ — Meteoroloji Veri Modülü (src/meteoroloji.py)
# =============================================================================
# NASA POWER API üzerinden aylık meteoroloji verisi çeker.
#
# NASA POWER (Prediction Of Worldwide Energy Resources):
#   NASA'nın açık verisi, tüm dünya için 1981'den günümüze
#   aylık/günlük meteoroloji parametreleri sunar.
#   API dökümantasyonu: https://power.larc.nasa.gov/docs/
#
# Çekilen değişkenler:
#   T2M          → 2m yükseklikteki hava sıcaklığı (°C)
#   PRECTOTCORR  → Düzeltilmiş toplam yağış (mm/gün)
#   RH2M         → 2m bağıl nem (%)
#   WS10M        → 10m rüzgar hızı (m/s)
# =============================================================================

import requests
import pandas as pd
import numpy as np
import os
import sys
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.ayarlar import (
    NASA_POWER_URL, NASA_PARAMETRELER, NASA_TOPLULUK,
    HAVZALAR, BASLANGIC_YILI, BITIS_YILI,
    METEOROLOJI_DOSYA
)


def nasa_power_veri_cek(lat, lon, baslangic_yili, bitis_yili, parametreler=None):
    """
    NASA POWER API'den belirli koordinat için aylık meteoroloji verisi çeker.
    
    API yapısı:
        GET /temporal/monthly/point?
            parameters=T2M,PRECTOTCORR,...
            community=RE
            longitude=lon
            latitude=lat
            start=YYYYYYYY
            end=YYYYYYYY
            format=JSON
    
    Parametreler:
        lat (float): Enlem (kuzey pozitif)
        lon (float): Boylam (doğu pozitif)
        baslangic_yili (int): Başlangıç yılı
        bitis_yili (int): Bitiş yılı
        parametreler (list): NASA değişken kodları
    
    Dönüş:
        dict: {parametre_kodu: {YYYYMM: değer}} formatında veri
    """
    if parametreler is None:
        parametreler = NASA_PARAMETRELER
    
    params = {
        'parameters': ','.join(parametreler),
        'community': NASA_TOPLULUK,
        'longitude': lon,
        'latitude': lat,
        'start': f"{baslangic_yili}0101",
        'end': f"{bitis_yili}1231",
        'format': 'JSON'
    }
    
    try:
        print(f"  🌡️ NASA POWER sorgusu: lat={lat}, lon={lon}...")
        
        # requests.get() → HTTP GET isteği yapar
        # timeout → maksimum bekleme süresi (saniye)
        yanit = requests.get(NASA_POWER_URL, params=params, timeout=60)
        
        # HTTP 200 = başarılı, diğerleri = hata
        yanit.raise_for_status()
        
        # JSON formatında yanıtı parse et
        veri = yanit.json()
        
        # Veriyi özellikler (properties) altından çek
        # NASA POWER yanıt yapısı:
        # {"properties": {"parameter": {"T2M": {"202401": 5.3, ...}}}}
        return veri['properties']['parameter']
        
    except requests.exceptions.Timeout:
        print(f"  ❌ NASA POWER zaman aşımı (60 saniye)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  ❌ NASA POWER API hatası: {e}")
        return None
    except KeyError as e:
        print(f"  ❌ NASA POWER veri yapısı beklenmedik: {e}")
        return None


def nasa_veriyi_dataframe_donustur(nasa_verisi, lat, lon, havza_adi):
    """
    NASA POWER'ın ham JSON verisini temiz bir DataFrame'e dönüştürür.
    
    Ham veri formatı: {"T2M": {"202401": 5.3, "202402": 7.1, ...}}
    Hedef format: DataFrame satırları = (yıl, ay, değerler)
    
    Parametreler:
        nasa_verisi (dict): NASA POWER API yanıtı
        lat, lon (float): Koordinatlar
        havza_adi (str): Havza adı (etiket için)
    
    Dönüş:
        pd.DataFrame: Temiz meteoroloji verisi
    """
    if nasa_verisi is None:
        return None
    
    satirlar = []
    
    # T2M verisi üzerinden tüm tarihleri bul
    # T2M her zaman var olduğundan referans alıyoruz
    referans_param = list(nasa_verisi.keys())[0]
    
    for tarih_str, _ in nasa_verisi[referans_param].items():
        # "202401" → yıl=2024, ay=1
        if tarih_str == 'ANN':  # Yıllık ortalama, atla
            continue
        
        yil = int(tarih_str[:4])
        ay = int(tarih_str[4:6])
        
        satir = {
            'havza': havza_adi,
            'lat': lat,
            'lon': lon,
            'yil': yil,
            'ay': ay,
        }
        
        # Her parametrenin değerini al
        # Parametre eşleştirmesi:
        param_eslesme = {
            'T2M': 'sicaklik_C',
            'PRECTOTCORR': 'yagis_mm_gun',
            'RH2M': 'nem_yuzde',
            'WS10M': 'ruzgar_ms'
        }
        
        for nasa_kod, kolon_adi in param_eslesme.items():
            if nasa_kod in nasa_verisi:
                deger = nasa_verisi[nasa_kod].get(tarih_str, np.nan)
                # NASA POWER -999 değeri eksik veri anlamına gelir
                satir[kolon_adi] = np.nan if deger == -999 else deger
        
        satirlar.append(satir)
    
    df = pd.DataFrame(satirlar)
    
    # Günlük yağışı aylık toplamlara çevir
    # NASA POWER yağışı mm/gün verir, biz aylık mm istiyoruz
    if 'yagis_mm_gun' in df.columns:
        import calendar
        df['gun_sayisi'] = df['ay'].apply(
            lambda ay: 30  # Basit yaklaşım; tam hesap: calendar.monthrange()
        )
        # Daha doğru: her satır için yıl-ay'dan gün sayısı bul
        df['gun_sayisi'] = df.apply(
            lambda r: calendar.monthrange(int(r['yil']), int(r['ay']))[1], axis=1
        )
        df['yagis_mm'] = df['yagis_mm_gun'] * df['gun_sayisi']
        df.drop(columns=['yagis_mm_gun', 'gun_sayisi'], inplace=True)
    
    return df


def tum_havzalar_meteoroloji_cek(gee_mod=True):
    """
    Tüm baraj havzaları için meteoroloji verisi çeker.
    
    Parametreler:
        gee_mod (bool): True ise NASA API'den çek, False ise sentetik üret
    
    Dönüş:
        pd.DataFrame: Tüm havzaların birleştirilmiş verisi
    """
    print("🌡️ Meteoroloji Verisi Toplama Başlıyor")
    print(f"   {len(HAVZALAR)} havza, {BASLANGIC_YILI}-{BITIS_YILI}")
    print("=" * 60)
    
    tum_veriler = []
    
    for havza_kod, havza_bilgi in HAVZALAR.items():
        print(f"\n📍 {havza_bilgi['isim']} ({havza_bilgi['lat']}°N, {havza_bilgi['lon']}°E)")
        
        if gee_mod:
            # Gerçek NASA API'den veri çek
            nasa_verisi = nasa_power_veri_cek(
                lat=havza_bilgi['lat'],
                lon=havza_bilgi['lon'],
                baslangic_yili=BASLANGIC_YILI,
                bitis_yili=BITIS_YILI
            )
            df = nasa_veriyi_dataframe_donustur(
                nasa_verisi, havza_bilgi['lat'], havza_bilgi['lon'], havza_kod
            )
            time.sleep(1)  # API'yi yormamak için bekle
        else:
            # Sentetik veri üret
            df = _sentetik_meteoroloji_uret(havza_kod, havza_bilgi)
        
        if df is not None:
            tum_veriler.append(df)
            print(f"   ✅ {len(df)} aylık veri")
        else:
            print(f"   ❌ Veri alınamadı")
    
    if not tum_veriler:
        print("❌ Hiç meteoroloji verisi toplanamadı!")
        return None
    
    # Tüm havzaları birleştir
    birlesik_df = pd.concat(tum_veriler, ignore_index=True)
    
    # Dosyaya kaydet
    os.makedirs(os.path.dirname(METEOROLOJI_DOSYA), exist_ok=True)
    birlesik_df.to_csv(METEOROLOJI_DOSYA, index=False, encoding='utf-8-sig')
    print(f"\n✅ Meteoroloji verisi kaydedildi: {METEOROLOJI_DOSYA}")
    print(f"   {len(birlesik_df)} kayıt, {birlesik_df['havza'].nunique()} havza")
    
    return birlesik_df


def _sentetik_meteoroloji_uret(havza_kod, havza_bilgi):
    """
    Gerçekçi sentetik meteoroloji verisi üretir.
    
    Her havzanın coğrafi konumuna göre farklı değerler:
    - Enlem → sıcaklık (kuzey daha soğuk)
    - Rakım → yağış ve nem
    """
    satirlar = []
    
    for yil in range(BASLANGIC_YILI, BITIS_YILI + 1):
        for ay in range(1, 13):
            np.random.seed(hash(havza_kod) % 10000 + yil * 100 + ay)
            
            # Sıcaklık modeli (mevsimsel + enlem etkisi)
            mevsim = np.cos(2 * np.pi * (ay - 1) / 12) * 15  # ±15°C salınım
            enlem_offset = (havza_bilgi['lat'] - 38) * (-0.6)  # Her derece için -0.6°C
            yil_trend = (yil - 2015) * 0.05  # Küresel ısınma: 0.05°C/yıl
            gurultu = np.random.normal(0, 1.5)
            sicaklik = 13 + mevsim + enlem_offset + yil_trend + gurultu
            
            # Yağış modeli (kış yağışlı, yaz kurak — Türkiye iklimi)
            if ay in [11, 12, 1, 2, 3]:  # Kış
                yagis_ort = 80
            elif ay in [4, 5, 10]:  # İlkbahar/Sonbahar
                yagis_ort = 45
            else:  # Yaz
                yagis_ort = 15
            
            yagis = max(0, np.random.gamma(2, yagis_ort/2))
            
            # Nem modeli
            nem = 65 + np.random.normal(0, 8)
            nem = np.clip(nem, 20, 100)
            
            # Rüzgar modeli
            ruzgar = max(0, np.random.normal(3.5, 0.8))
            
            satirlar.append({
                'havza': havza_kod,
                'lat': havza_bilgi['lat'],
                'lon': havza_bilgi['lon'],
                'yil': yil,
                'ay': ay,
                'sicaklik_C': round(sicaklik, 1),
                'yagis_mm': round(yagis, 1),
                'nem_yuzde': round(nem, 1),
                'ruzgar_ms': round(ruzgar, 2)
            })
    
    return pd.DataFrame(satirlar)


def meteoroloji_yukle():
    """
    Kaydedilmiş meteoroloji verisini yükler. Yoksa sentetik üretir.
    """
    if os.path.exists(METEOROLOJI_DOSYA):
        df = pd.read_csv(METEOROLOJI_DOSYA, encoding='utf-8-sig')
        print(f"✅ Meteoroloji verisi yüklendi: {len(df)} kayıt")
        return df
    else:
        print("⚠️  Meteoroloji dosyası bulunamadı. Sentetik veri üretiliyor...")
        return tum_havzalar_meteoroloji_cek(gee_mod=False)


# Doğrudan çalıştırılırsa test yap
if __name__ == "__main__":
    print("=" * 60)
    print("KarİZ — Meteoroloji Veri Testi")
    print("=" * 60)
    
    # Sentetik modda test
    df = tum_havzalar_meteoroloji_cek(gee_mod=False)
    
    if df is not None:
        print(f"\n📊 Özet İstatistikler:")
        print(df.groupby('havza')[['sicaklik_C', 'yagis_mm', 'nem_yuzde']].mean().round(2))

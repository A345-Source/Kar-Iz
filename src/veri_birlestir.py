# =============================================================================
# KarİZ — Veri Birleştirme ve Feature Engineering (src/veri_birlestir.py)
# =============================================================================
# Kar verisi + meteoroloji verisi + akış verisi'ni birleştirir.
# Makine öğrenmesi için öznitelikler (features) oluşturur.
#
# Feature Engineering nedir?
#   Ham veriden (örn: aylık kar alanı) modelin öğrenmesine yardımcı
#   yeni değişkenler türetme işlemidir.
#   Örnek: "geçen ay kar alanı" → kar erimesi gecikmesini modeller
# =============================================================================

import pandas as pd
import numpy as np
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.ayarlar import (
    HAVZALAR, BASLANGIC_YILI, BITIS_YILI,
    KAR_ZAMAN_SERISI_DOSYA, METEOROLOJI_DOSYA, MODEL_VERISI_DOSYA,
    OZNITELIKLER, HEDEF_DEGISKEN
)


def kar_ve_meteoroloji_birlestir(kar_df, met_df):
    """
    Kar zaman serisi ve meteoroloji verilerini birleştirir.
    
    Kar verisi Türkiye geneli için var (tek değer/ay).
    Meteoroloji verisi her havza için ayrı (8 havza × ay).
    
    Birleştirme stratejisi:
        - Her havza için kar verisi çoğaltılır
        - Havzanın kendi meteoroloji değeri eklenir
        - Her satır = bir havzanın bir ayı
    
    Dönüş:
        pd.DataFrame: Birleştirilmiş veri
    """
    print("🔗 Kar ve meteoroloji verileri birleştiriliyor...")
    
    # Kar verisinde eksik sütunlar varsa ekle
    if 'tarih' not in kar_df.columns:
        kar_df['tarih'] = pd.to_datetime(
            kar_df['yil'].astype(str) + '-' + kar_df['ay'].astype(str).str.zfill(2) + '-01'
        )
    
    tum_satirlar = []
    
    for havza_kod, havza_bilgi in HAVZALAR.items():
        # Bu havzanın meteoroloji verisini filtrele
        havza_met = met_df[met_df['havza'] == havza_kod].copy()
        
        if len(havza_met) == 0:
            print(f"  ⚠️  {havza_kod} için meteoroloji verisi yok, atlanıyor")
            continue
        
        # Kar verisiyle merge (yıl ve ay üzerinden)
        birlesik = pd.merge(
            kar_df[['yil', 'ay', 'kar_alani_km2', 'goruntu_sayisi']],
            havza_met[['yil', 'ay', 'sicaklik_C', 'yagis_mm', 'nem_yuzde', 'ruzgar_ms']],
            on=['yil', 'ay'],
            how='inner'  # Her iki tarafta da bulunan kayıtlar
        )
        
        birlesik['havza'] = havza_kod
        birlesik['havza_isim'] = havza_bilgi['isim']
        birlesik['havza_alan_km2'] = havza_bilgi['alan_km2']
        
        tum_satirlar.append(birlesik)
    
    if not tum_satirlar:
        print("❌ Birleştirme başarısız!")
        return None
    
    df = pd.concat(tum_satirlar, ignore_index=True)
    df['tarih'] = pd.to_datetime(
        df['yil'].astype(str) + '-' + df['ay'].astype(str).str.zfill(2) + '-01'
    )
    df = df.sort_values(['havza', 'tarih']).reset_index(drop=True)
    
    print(f"  ✅ {len(df)} satır, {df['havza'].nunique()} havza birleştirildi")
    return df


def lag_oznitelikleri_ekle(df, n_lag=2):
    """
    Gecikmeli (lag) öznitelikler ekler.
    
    Neden lag kullanılır?
        Kar erimesinin nehir akışına etkisi anlık değildir.
        Şubat'ta eriyen kar Mart veya Nisan'da barajlara ulaşır.
        "1 ay önceki kar alanı" bu gecikmeyi modellemek için kullanılır.
    
    Parametreler:
        df (pd.DataFrame): Ham veri
        n_lag (int): Kaç aylık gecikme ekleneceği
    
    Dönüş:
        pd.DataFrame: Lag öznitelikleri eklenmiş veri
    """
    print(f"  ⏱️  {n_lag} aylık lag öznitelikleri ekleniyor...")
    
    for havza in df['havza'].unique():
        maske = df['havza'] == havza
        
        for lag in range(1, n_lag + 1):
            # Önceki ayın kar alanı
            sutun_adi = f'kar_alani_lag{lag}'
            df.loc[maske, sutun_adi] = df.loc[maske, 'kar_alani_km2'].shift(lag)
    
    return df


def hedef_degisken_uret(df):
    """
    Hedef değişken (nehir akışı, m³/s) üretir.
    
    Gerçek nehir akış verisi yoksa fizik tabanlı model kullanır:
        Akış ≈ f(kar_erimesi, yağış, sıcaklık)
    
    Kar erimesi = önceki ay kar alanındaki azalma (ΔKAR)
    Sıcaklık > 0°C olduğunda kar erimeye başlar.
    
    Bu yaklaşım SRM (Snowmelt-Runoff Model) prensiplerini basitleştirir.
    Kaynak: Martinec et al. (2008)
    """
    print("  💧 Akış değişkeni hesaplanıyor (fizik tabanlı model)...")
    
    np.random.seed(42)
    
    akis_satirlari = []
    
    for havza in df['havza'].unique():
        havza_df = df[df['havza'] == havza].copy()
        havza_bilgi = HAVZALAR.get(havza, {})
        havza_alani = havza_bilgi.get('alan_km2', 50000)
        
        for idx, satir in havza_df.iterrows():
            # 1. Kar erimesi katkısı
            # Sıcaklık > 0 ise kar eriyor, her °C için belirli miktarda eriyor
            sicaklik = satir.get('sicaklik_C', 5)
            kar_alani = satir.get('kar_alani_km2', 0)
            
            if pd.isna(satir.get('kar_alani_lag1')):
                kar_erimesi = 0
            else:
                kar_alani_onceki = satir.get('kar_alani_lag1', 0)
                kar_azalmasi = max(0, kar_alani_onceki - kar_alani)  # km²
                # Kar erimesi: azalan her km² için 0.8 m³/s katkı (basitleştirilmiş)
                erime_katsayi = max(0, sicaklik * 0.12)
                kar_erimesi = kar_azalmasi * erime_katsayi / havza_alani * 100
            
            # 2. Yağış katkısı
            yagis = satir.get('yagis_mm', 30)
            yagis_katkisi = yagis * havza_alani * 0.0003  # mm × km² → m³/s yaklaşımı
            
            # 3. Temel akış (kaynak akışı, hiç yağış ve kar erimesi olmasa bile)
            temel_akis = havza_alani * 0.002
            
            # 4. Mevsimsel faktör (ilkbaharda artış)
            ay = satir['ay']
            mevsim_faktoru = 1.0 + 0.5 * np.cos(2 * np.pi * (ay - 4) / 12)
            
            # Toplam akış
            toplam_akis = (kar_erimesi + yagis_katkisi + temel_akis) * mevsim_faktoru
            
            # Gerçekçilik için gürültü ekle
            gurultu = np.random.lognormal(0, 0.2)
            toplam_akis *= gurultu
            
            akis_satirlari.append({'_idx': idx, 'akis_m3s': max(1, round(toplam_akis, 2))})
    
    akis_df = pd.DataFrame(akis_satirlari).set_index('_idx')
    df['akis_m3s'] = akis_df['akis_m3s']
    
    return df


def etkilesim_oznitelikleri_ekle(df):
    """
    Etkileşim (interaction) öznitelikleri ekler.
    
    Etkileşim özniteliği nedir?
        İki değişkenin çarpımı. Örnek:
        sicaklik × kar_alani → "yüksek sıcaklıkta çok kar varsa çok erir"
        Bu ilişkiyi model ayrı ayrı değişkenlerden öğrenemez.
    """
    print("  🔄 Etkileşim öznitelikleri ekleniyor...")
    
    # Sıcaklık × Kar etkileşimi (negatif → sıcak + kar = çok erime)
    df['sicaklik_kar_etkilesim'] = df['sicaklik_C'] * df['kar_alani_km2'] / 1000
    
    # Yağış × Nem (birlikte yüksekse sel riski)
    df['yagis_nem_etkilesim'] = df['yagis_mm'] * df['nem_yuzde'] / 100
    
    return df


def model_verisi_hazirla():
    """
    Tüm adımları sırayla çalıştırarak model verisini hazırlar.
    Sonucu CSV'ye kaydeder.
    
    Dönüş:
        pd.DataFrame: Model için hazır veri (öznitelikler + hedef)
    """
    print("=" * 60)
    print("🔧 Model Verisi Hazırlanıyor")
    print("=" * 60)
    
    # Veri yükle
    from zaman_serisi import zaman_serisi_yukle
    from meteoroloji import meteoroloji_yukle
    
    kar_df = zaman_serisi_yukle()
    met_df = meteoroloji_yukle()
    
    if kar_df is None or met_df is None:
        print("❌ Veri yükleme başarısız!")
        return None
    
    # Adım 1: Birleştir
    df = kar_ve_meteoroloji_birlestir(kar_df, met_df)
    
    # Adım 2: Lag öznitelikleri ekle
    df = lag_oznitelikleri_ekle(df, n_lag=2)
    
    # Adım 3: Etkileşim öznitelikleri
    df = etkilesim_oznitelikleri_ekle(df)
    
    # Adım 4: Hedef değişken üret
    df = hedef_degisken_uret(df)
    
    # Adım 5: Eksik değerleri temizle (lag nedeniyle ilk 2 satır NaN olabilir)
    df = df.dropna(subset=OZNITELIKLER + [HEDEF_DEGISKEN])
    df = df.reset_index(drop=True)
    
    # Kaydet
    os.makedirs(os.path.dirname(MODEL_VERISI_DOSYA), exist_ok=True)
    df.to_csv(MODEL_VERISI_DOSYA, index=False, encoding='utf-8-sig')
    print(f"\n✅ Model verisi kaydedildi: {MODEL_VERISI_DOSYA}")
    print(f"   {len(df)} satır, {len(df.columns)} sütun")
    print(f"\n📊 Öznitelikler:")
    for oz in OZNITELIKLER:
        if oz in df.columns:
            print(f"   {oz}: min={df[oz].min():.2f}, max={df[oz].max():.2f}, ort={df[oz].mean():.2f}")
    
    return df


# Doğrudan çalıştırılırsa çalıştır
if __name__ == "__main__":
    df = model_verisi_hazirla()
    if df is not None:
        print(f"\nİlk 5 satır:")
        print(df[['havza', 'yil', 'ay', 'kar_alani_km2', 'sicaklik_C', 'yagis_mm', 'akis_m3s']].head())

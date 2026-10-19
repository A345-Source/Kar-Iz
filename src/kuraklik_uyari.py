# =============================================================================
# KarİZ — Kuraklık Erken Uyarı Sistemi (src/kuraklik_uyari.py)
# =============================================================================
# SPI (Standardized Precipitation Index) tabanlı kuraklık tespiti.
#
# SPI Nedir?
#   Yağışın istatistiksel anormalliğini standart sapma cinsinden ifade eder.
#   SPI = (Gözlenen Yağış - Uzun Dönem Ortalama) / Standart Sapma
#   
#   SPI = +2.0 → Aşırı nemli (100 yılda bir)
#   SPI = +1.0 → Orta nemli
#   SPI =  0.0 → Normal
#   SPI = -1.0 → Hafif kuraklık
#   SPI = -1.5 → Orta kuraklık
#   SPI = -2.0 → Şiddetli kuraklık (100 yılda bir)
#
# Kaynak: McKee, T.B., Doesken, N.J., Kleist, J. (1993)
#         "The Relationship of Drought Frequency and Duration to Time Scales"
# =============================================================================

import pandas as pd
import numpy as np
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.ayarlar import (
    HAVZALAR, BASLANGIC_YILI, BITIS_YILI,
    KURAKLIK_SEVIYELERI, METEOROLOJI_DOSYA,
    RAPOR_DIZINI, GRAFIK_STILI, GRAFIK_DPI
)


def spi_hesapla(yagis_serisi, pencere=3):
    """
    SPI (Standardized Precipitation Index) hesaplar.
    
    Adımlar:
    1. Hareketli ortalama (rolling mean): N aylık birikimli yağış
       (SPI-3 = 3 aylık, SPI-6 = 6 aylık, SPI-12 = 12 aylık)
    2. Gamma dağılımına fit et (yağış sağa çarpık dağılıma sahip)
    3. Olasılık değerini standart normal'e dönüştür
    
    Not: Basit versiyonda normal dağılım varsayıyoruz (z-score)
    Gerçek uygulamada Gamma dağılımı kullanılır.
    
    Parametreler:
        yagis_serisi (pd.Series): Aylık yağış değerleri (mm)
        pencere (int): Kaç aylık hareketli ortalama (3=kısa, 12=uzun vadeli)
    
    Dönüş:
        pd.Series: SPI değerleri
    """
    # Hareketli ortalama: N aylık birikimli yağış
    # min_periods=1 → ilk pencere-1 aylar için de değer üret
    birikim = yagis_serisi.rolling(window=pencere, min_periods=1).mean()
    
    # Gamma dağılımına fit et (yağış dağılımı için uygun)
    # Sıfır ve NaN değerleri çıkar
    gecerli = birikim.dropna()
    gecerli = gecerli[gecerli > 0]
    
    if len(gecerli) < 4:  # Yeterli veri yoksa basit z-score
        ort = birikim.mean()
        std = birikim.std()
        if std == 0:
            return pd.Series(0, index=yagis_serisi.index)
        return (birikim - ort) / std
    
    try:
        # Gamma dağılımı parametrelerini tahmin et
        # shape (alpha) ve scale (beta)
        alpha, loc, beta = stats.gamma.fit(gecerli, floc=0)
        
        # Her değer için kümülatif olasılık (CDF)
        cdf_degerleri = stats.gamma.cdf(birikim.clip(lower=0.01), alpha, loc=0, scale=beta)
        
        # CDF'i standart normal'e dönüştür (ppf = percent point function)
        # 0 ve 1'e çok yakın değerleri kırp (sonsuzluk önlemek için)
        cdf_degerleri = np.clip(cdf_degerleri, 0.001, 0.999)
        spi = stats.norm.ppf(cdf_degerleri)
        
        return pd.Series(spi, index=yagis_serisi.index)
        
    except Exception:
        # Gamma fit başarısız olursa basit z-score
        ort = birikim.mean()
        std = birikim.std()
        if std == 0:
            return pd.Series(0, index=yagis_serisi.index)
        return (birikim - ort) / std


def kuraklik_siniflandir(spi_deger):
    """
    SPI değerine göre kuraklık sınıfını belirler.
    
    Parametreler:
        spi_deger (float): SPI değeri
    
    Dönüş:
        dict: {'seviye', 'etiket', 'renk', 'icon'}
    """
    # Seviyeleri büyükten küçüğe sırala
    sirali_seviyeler = sorted(
        KURAKLIK_SEVIYELERI.items(),
        key=lambda x: x[1]['esik'],
        reverse=True
    )
    
    for seviye_adi, seviye_bilgi in sirali_seviyeler:
        if spi_deger >= seviye_bilgi['esik']:
            return {
                'seviye': seviye_adi,
                'etiket': seviye_bilgi['etiket'],
                'renk': seviye_bilgi['renk'],
                'icon': seviye_bilgi['icon'],
                'spi': round(spi_deger, 3)
            }
    
    # En düşük seviye (aşırı kuraklık)
    return {
        'seviye': 'asiri_kuraklik',
        'etiket': 'Aşırı Kuraklık',
        'renk': '#8B0000',
        'icon': '🚨',
        'spi': round(spi_deger, 3)
    }


def kuraklik_analizi_yap(met_df=None):
    """
    Tüm havzalar için SPI hesaplar ve kuraklık analizini yapar.
    
    Parametreler:
        met_df (pd.DataFrame): Meteoroloji verisi, None ise dosyadan yükle
    
    Dönüş:
        pd.DataFrame: SPI değerleri ve kuraklık sınıfları eklenmiş veri
    """
    if met_df is None:
        from meteoroloji import meteoroloji_yukle
        met_df = meteoroloji_yukle()
    
    print("🌵 Kuraklık Analizi Başlıyor...")
    
    sonuclar = []
    
    for havza in met_df['havza'].unique():
        havza_df = met_df[met_df['havza'] == havza].copy()
        havza_df = havza_df.sort_values(['yil', 'ay']).reset_index(drop=True)
        
        # SPI-3 (3 aylık — kısa vadeli kuraklık)
        havza_df['SPI_3'] = spi_hesapla(havza_df['yagis_mm'], pencere=3)
        
        # SPI-6 (6 aylık — orta vadeli kuraklık)
        havza_df['SPI_6'] = spi_hesapla(havza_df['yagis_mm'], pencere=6)
        
        # SPI-12 (12 aylık — uzun vadeli, hidrological kuraklık)
        havza_df['SPI_12'] = spi_hesapla(havza_df['yagis_mm'], pencere=12)
        
        # Kuraklık sınıfı (SPI-3 üzerinden)
        havza_df['kuraklik_seviye'] = havza_df['SPI_3'].apply(
            lambda x: kuraklik_siniflandir(x)['etiket']
        )
        havza_df['kuraklik_renk'] = havza_df['SPI_3'].apply(
            lambda x: kuraklik_siniflandir(x)['renk']
        )
        
        sonuclar.append(havza_df)
    
    sonuc_df = pd.concat(sonuclar, ignore_index=True)
    print(f"✅ {len(sonuc_df['havza'].unique())} havza için SPI hesaplandı")
    
    return sonuc_df


def guncel_kuraklik_durumu(spi_df, hedef_havza=None):
    """
    En son tarihteki kuraklık durumunu döndürür.
    
    Parametreler:
        spi_df (pd.DataFrame): SPI verisi
        hedef_havza (str): Belirli bir havza, None ise tüm havzalar
    
    Dönüş:
        dict: Her havza için güncel kuraklık durumu
    """
    if hedef_havza:
        df = spi_df[spi_df['havza'] == hedef_havza]
    else:
        df = spi_df
    
    sonuclar = {}
    
    for havza in df['havza'].unique():
        havza_df = df[df['havza'] == havza]
        son_satir = havza_df.loc[havza_df[['yil', 'ay']].apply(
            lambda r: r['yil'] * 100 + r['ay'], axis=1
        ).idxmax()]
        
        spi3 = son_satir.get('SPI_3', 0)
        sinif = kuraklik_siniflandir(spi3)
        
        havza_bilgi = HAVZALAR.get(havza, {})
        sonuclar[havza] = {
            'isim': havza_bilgi.get('isim', havza),
            'yil': int(son_satir['yil']),
            'ay': int(son_satir['ay']),
            'SPI_3': round(float(spi3), 3),
            'SPI_6': round(float(son_satir.get('SPI_6', 0)), 3),
            'SPI_12': round(float(son_satir.get('SPI_12', 0)), 3),
            'seviye': sinif['seviye'],
            'etiket': sinif['etiket'],
            'renk': sinif['renk'],
            'icon': sinif['icon'],
            'yagis_son': round(float(son_satir.get('yagis_mm', 0)), 1),
            'sicaklik_son': round(float(son_satir.get('sicaklik_C', 0)), 1)
        }
    
    return sonuclar


def kuraklik_haritasi_grafigi(durum_dict, kaydet=True):
    """
    Türkiye haritasına benzer havza kuraklık durumu grafiği.
    """
    plt.style.use(GRAFIK_STILI)
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('#0D1117')
    ax.set_facecolor('#0D1117')
    
    # Havzaları koordinatlarına göre çiz (basit scatter plot)
    for havza_kod, durum in durum_dict.items():
        havza_bilgi = HAVZALAR.get(havza_kod, {})
        lat = havza_bilgi.get('lat', 39)
        lon = havza_bilgi.get('lon', 35)
        
        # Daire boyutu havza alanına orantılı
        boyut = havza_bilgi.get('alan_km2', 30000) / 1000
        
        ax.scatter(lon, lat, s=boyut, color=durum['renk'],
                   alpha=0.7, edgecolors='white', linewidths=0.5, zorder=5)
        
        ax.annotate(
            f"{durum['icon']}\n{durum['isim'].split(' ')[0]}\nSPI: {durum['SPI_3']:+.1f}",
            xy=(lon, lat), fontsize=7, color='white',
            ha='center', va='center', zorder=6,
            fontweight='bold'
        )
    
    # Türkiye sınırını basit dikdörtgen olarak belirt
    from matplotlib.patches import FancyBboxPatch
    ax.set_xlim(25, 45)
    ax.set_ylim(35.5, 43)
    ax.set_xlabel('Boylam (°D)', color='white', fontsize=11)
    ax.set_ylabel('Enlem (°K)', color='white', fontsize=11)
    ax.set_title('🌍 Türkiye Baraj Havzaları — Güncel Kuraklık Durumu (SPI-3)',
                 color='white', fontsize=14, fontweight='bold', pad=15)
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('#333')
    ax.spines['left'].set_color('#333')
    ax.spines['top'].set_color('#333')
    ax.spines['right'].set_color('#333')
    ax.grid(True, alpha=0.1, color='white')
    
    # Lejant
    lejant_ogeler = [
        mpatches.Patch(color='#4169E1', label='Nemli (SPI > +1)'),
        mpatches.Patch(color='#90EE90', label='Normal (-1 < SPI < +1)'),
        mpatches.Patch(color='#FFD700', label='Hafif Kuraklık (-1.5 < SPI < -1)'),
        mpatches.Patch(color='#FF4500', label='Şiddetli Kuraklık (SPI < -1.5)'),
    ]
    ax.legend(handles=lejant_ogeler, loc='lower right',
              facecolor='#1E2D3D', edgecolor='#00D4FF', labelcolor='white', fontsize=9)
    
    fig.text(0.5, 0.01, 'KarİZ Projesi — TÜBİTAK 2204-A | Veri: NASA POWER',
             ha='center', color='gray', fontsize=9)
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    
    if kaydet:
        os.makedirs(RAPOR_DIZINI, exist_ok=True)
        dosya = os.path.join(RAPOR_DIZINI, 'kuraklik_haritasi.png')
        plt.savefig(dosya, dpi=GRAFIK_DPI, bbox_inches='tight',
                    facecolor='#0D1117', edgecolor='none')
        plt.close()
        print(f"✅ Kuraklık haritası: {dosya}")
        return dosya


def spi_zaman_serisi_grafigi(spi_df, havza_kod, kaydet=True):
    """
    Belirli bir havza için SPI zaman serisi grafiği.
    """
    plt.style.use(GRAFIK_STILI)
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('#0D1117')
    ax.set_facecolor('#161B22')
    
    havza_df = spi_df[spi_df['havza'] == havza_kod].copy()
    havza_df['tarih'] = pd.to_datetime(
        havza_df['yil'].astype(str) + '-' + havza_df['ay'].astype(str).str.zfill(2) + '-01'
    )
    havza_df = havza_df.sort_values('tarih')
    
    havza_isim = HAVZALAR.get(havza_kod, {}).get('isim', havza_kod)
    
    # SPI çizgisi
    ax.plot(havza_df['tarih'], havza_df['SPI_3'], color='white',
            linewidth=1.2, alpha=0.9, label='SPI-3')
    ax.plot(havza_df['tarih'], havza_df['SPI_12'], color='#FFD700',
            linewidth=2, alpha=0.9, label='SPI-12 (Uzun Vadeli)')
    
    # Renk doldurma
    ax.fill_between(havza_df['tarih'], havza_df['SPI_3'],
                    where=havza_df['SPI_3'] >= 0,
                    interpolate=True, color='#4169E1', alpha=0.3, label='Nemli')
    ax.fill_between(havza_df['tarih'], havza_df['SPI_3'],
                    where=havza_df['SPI_3'] < 0,
                    interpolate=True, color='#FF4500', alpha=0.3, label='Kurak')
    
    # Eşik çizgileri
    ax.axhline(y=0, color='white', linestyle='-', linewidth=1, alpha=0.5)
    ax.axhline(y=-1.0, color='#FFD700', linestyle='--', linewidth=1, alpha=0.6)
    ax.axhline(y=-1.5, color='#FFA500', linestyle='--', linewidth=1, alpha=0.6)
    ax.axhline(y=-2.0, color='#FF0000', linestyle='--', linewidth=1, alpha=0.6)
    
    # Etiketler
    ax.text(havza_df['tarih'].iloc[-1], -1.0, ' Hafif', color='#FFD700', fontsize=8, va='center')
    ax.text(havza_df['tarih'].iloc[-1], -1.5, ' Orta', color='#FFA500', fontsize=8, va='center')
    ax.text(havza_df['tarih'].iloc[-1], -2.0, ' Şiddetli', color='#FF0000', fontsize=8, va='center')
    
    ax.set_xlabel('Tarih', color='white', fontsize=11)
    ax.set_ylabel('SPI Değeri', color='white', fontsize=11)
    ax.set_title(f'🌵 {havza_isim} — SPI Kuraklık İndeksi (2015–2026)',
                 color='white', fontsize=13, fontweight='bold', pad=12)
    ax.legend(facecolor='#1E2D3D', edgecolor='#00D4FF', labelcolor='white', fontsize=9)
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('#333')
    ax.spines['left'].set_color('#333')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, alpha=0.1, color='white')
    ax.set_ylim(-3, 3)
    
    fig.text(0.5, 0.01, 'KarİZ Projesi — TÜBİTAK 2204-A | SPI: McKee et al. (1993)',
             ha='center', color='gray', fontsize=9)
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    
    if kaydet:
        os.makedirs(RAPOR_DIZINI, exist_ok=True)
        dosya = os.path.join(RAPOR_DIZINI, f'spi_{havza_kod}.png')
        plt.savefig(dosya, dpi=GRAFIK_DPI, bbox_inches='tight',
                    facecolor='#0D1117', edgecolor='none')
        plt.close()
        print(f"✅ SPI grafiği: {dosya}")
        return dosya


# Doğrudan çalıştırılırsa test yap
if __name__ == "__main__":
    print("=" * 60)
    print("KarİZ — Kuraklık Erken Uyarı Sistemi")
    print("=" * 60)
    
    from meteoroloji import meteoroloji_yukle
    met_df = meteoroloji_yukle()
    
    # SPI hesapla
    spi_df = kuraklik_analizi_yap(met_df)
    
    # Güncel durum
    durum = guncel_kuraklik_durumu(spi_df)
    
    print("\n📊 Güncel Kuraklık Durumu:")
    print("-" * 50)
    for havza, bilgi in durum.items():
        print(f"  {bilgi['icon']} {bilgi['isim']}: {bilgi['etiket']} (SPI-3: {bilgi['SPI_3']:+.2f})")
    
    # Grafikler
    kuraklik_haritasi_grafigi(durum)
    spi_zaman_serisi_grafigi(spi_df, 'Kizilirmak')

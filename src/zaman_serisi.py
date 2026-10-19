# =============================================================================
# KarİZ — Zaman Serisi Analizi (src/zaman_serisi.py)
# =============================================================================
# 2015-2026 yılları arasında Türkiye kar örtüsü değişimini analiz eder.
# Her ay için kar alanını hesaplar ve CSV dosyasına kaydeder.
#
# Neden zaman serisi?
#   Tek bir anlık görüntü "şu an ne kadar kar var" sorusunu cevaplar.
#   Zaman serisi ise "kar azalıyor mu? Küresel ısınmanın etkisi var mı?"
#   sorularını cevaplar. Bu projenin bilimsel katkısı buradadır.
# =============================================================================

import sys
import os
import time
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # GUI olmadan çalışmak için (sunucu ortamı)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.ayarlar import (
    BASLANGIC_YILI, BITIS_YILI, KAR_AYLARI, TUM_AYLAR,
    KAR_ZAMAN_SERISI_DOSYA, RAPOR_DIZINI,
    GRAFIK_STILI, GRAFIK_RENKLERI, GRAFIK_DPI, GRAFIK_BOYUTU
)


def zaman_serisi_hesapla(yillar=None, aylar=None, gee_mod=True):
    """
    Belirtilen yıl ve aylar için aylık kar alanı hesaplar.
    
    Bu fonksiyon uzun sürebilir (örn: 11 yıl × 12 ay = 132 GEE isteği).
    Sonuçlar otomatik olarak CSV'ye kaydedilir.
    
    Parametreler:
        yillar (list): Analiz edilecek yıllar, None ise tüm yıllar (2015-2026)
        aylar (list): Analiz edilecek aylar, None ise kar ayları (1,2,3,12)
        gee_mod (bool): True ise GEE'den gerçek veri çek, False ise sentetik
    
    Dönüş:
        pd.DataFrame: Zaman serisi verisi
    """
    if yillar is None:
        yillar = list(range(BASLANGIC_YILI, BITIS_YILI + 1))
    if aylar is None:
        aylar = KAR_AYLARI
    
    toplam_istek = len(yillar) * len(aylar)
    print(f"📊 Zaman Serisi Analizi Başlıyor")
    print(f"   Yıllar: {yillar[0]} - {yillar[-1]}")
    print(f"   Aylar: {aylar}")
    print(f"   Toplam hesaplama: {toplam_istek} ay")
    print(f"   Tahmini süre: {toplam_istek * 8:.0f} saniye ({toplam_istek * 8 / 60:.1f} dakika)")
    print("=" * 60)
    
    sonuclar = []
    tamamlanan = 0
    
    for yil in yillar:
        for ay in aylar:
            if gee_mod:
                # Gerçek GEE verisi
                from kar_analiz import tek_ay_kar_analizi
                sonuc = tek_ay_kar_analizi(yil, ay, sessiz=False)
                
                if sonuc:
                    sonuclar.append(sonuc)
                
                # API'yi yormamak için bekle
                time.sleep(2)
                
            else:
                # Sentetik mod (GEE olmadan test için)
                sonuc = _sentetik_kar_alani_uret(yil, ay)
                sonuclar.append(sonuc)
            
            tamamlanan += 1
            yuzde = tamamlanan / toplam_istek * 100
            print(f"   İlerleme: {tamamlanan}/{toplam_istek} ({yuzde:.1f}%)")
    
    # DataFrame'e çevir
    df = pd.DataFrame(sonuclar)
    
    if len(df) == 0:
        print("❌ Hiç veri toplanamadı!")
        return None
    
    # Tarih sütunu ekle (grafik çizimi için)
    df['tarih'] = pd.to_datetime(
        df['yil'].astype(str) + '-' + df['ay'].astype(str).str.zfill(2) + '-01'
    )
    
    # Sırala
    df = df.sort_values('tarih').reset_index(drop=True)
    
    # CSV'ye kaydet
    os.makedirs(os.path.dirname(KAR_ZAMAN_SERISI_DOSYA), exist_ok=True)
    df.to_csv(KAR_ZAMAN_SERISI_DOSYA, index=False, encoding='utf-8-sig')
    print(f"\n✅ Veri kaydedildi: {KAR_ZAMAN_SERISI_DOSYA}")
    print(f"   {len(df)} kayıt, {df['yil'].nunique()} yıl")
    
    return df


def _sentetik_kar_alani_uret(yil, ay):
    """
    GEE olmadan test için gerçekçi sentetik kar verisi üretir.
    
    Fiziksel model:
        - Kar alanı mevsimsellik gösterir (Ocak-Şubat en yüksek)
        - Yıllar içinde azalma trendi var (küresel ısınma etkisi)
        - Rastgele gürültü eklenir (gerçekçilik için)
    
    Bu fonksiyon bilimsel olarak makul değerler üretir.
    TÜBİTAK raporunda "sentetik veri ile ön test" olarak belirtilmelidir.
    """
    np.random.seed(yil * 100 + ay)  # Tekrarlanabilirlik için sabit seed
    
    # Mevsimsel bileşen (Ocak=1 → Aralık=12)
    # Sinüs fonksiyonu ile mevsimsellik modellenir
    # Pik: Ocak-Şubat, Minimum: Temmuz-Ağustos
    mevsim_radyan = 2 * np.pi * (ay - 1) / 12
    mevsim_etki = np.cos(mevsim_radyan)  # +1 → kış, -1 → yaz
    
    # Temel kar alanı (km²) — Türkiye'nin gerçek değer aralığı
    # Kış: ~120,000-180,000 km², Yaz: ~0-5,000 km²
    temel = 75000
    mevsim_genlik = 70000
    
    # Yıllık azalma trendi (küresel ısınma)
    # 2015-2026: yılda ortalama ~2000 km² azalma
    yil_trendi = (yil - 2015) * (-2000)
    
    # El Niño/La Niña benzeri yıllık değişkenlik
    yillik_degiskenlik = np.random.normal(0, 8000)
    
    # Toplam kar alanı
    kar_alani = temel + mevsim_genlik * mevsim_etki + yil_trendi + yillik_degiskenlik
    
    # Negatif olamaz
    kar_alani = max(0, kar_alani)
    
    return {
        'yil': yil,
        'ay': ay,
        'goruntu_sayisi': np.random.randint(30, 80),
        'kar_alani_km2': round(kar_alani, 2)
    }


def zaman_serisi_yukle():
    """
    Kaydedilmiş zaman serisi CSV'sini yükler.
    Dosya yoksa sentetik veri üretir.
    
    Dönüş:
        pd.DataFrame: Zaman serisi verisi
    """
    if os.path.exists(KAR_ZAMAN_SERISI_DOSYA):
        df = pd.read_csv(KAR_ZAMAN_SERISI_DOSYA, encoding='utf-8-sig')
        df['tarih'] = pd.to_datetime(df['tarih'])
        print(f"✅ Zaman serisi yüklendi: {len(df)} kayıt")
        return df
    else:
        print("⚠️  Zaman serisi dosyası bulunamadı. Sentetik veri üretiliyor...")
        return zaman_serisi_hesapla(
            yillar=list(range(BASLANGIC_YILI, BITIS_YILI + 1)),
            aylar=TUM_AYLAR,
            gee_mod=False
        )


def trend_analizi(df):
    """
    Zaman serisi üzerinde istatistiksel trend analizi yapar.
    
    Mann-Kendall testi yerine basit doğrusal regresyon kullanır
    (lise seviyesi için uygun).
    
    Dönüş:
        dict: Trend istatistikleri
    """
    from scipy import stats
    
    # Sadece kış aylarını kullan (trend için daha anlamlı)
    kis = df[df['ay'].isin([1, 2, 3])].copy()
    kis = kis.groupby('yil')['kar_alani_km2'].mean().reset_index()
    
    # Doğrusal regresyon
    egim, kesme, r_deger, p_deger, std_hata = stats.linregress(
        kis['yil'], kis['kar_alani_km2']
    )
    
    # Toplam değişim (2015-2026 arası)
    toplam_degisim = egim * (BITIS_YILI - BASLANGIC_YILI)
    
    return {
        'egim_km2_yil': round(egim, 2),           # Yıllık değişim (km²/yıl)
        'toplam_degisim_km2': round(toplam_degisim, 2),  # 11 yılda toplam
        'r_kare': round(r_deger**2, 4),            # Model uyumu (0-1)
        'p_degeri': round(p_deger, 4),             # İstatistiksel anlamlılık
        'anlamli': p_deger < 0.05,                 # %5 anlamlılık seviyesi
        'yon': 'azalıyor' if egim < 0 else 'artıyor'
    }


def zaman_serisi_grafigi_ciz(df, kaydet=True):
    """
    Zaman serisi grafiğini çizer ve kaydeder.
    
    Grafik içeriği:
        - Aylık kar alanı (çizgi grafik)
        - Yıllık ortalama (nokta)
        - Trend çizgisi (kesikli)
    
    Parametreler:
        df (pd.DataFrame): Zaman serisi verisi
        kaydet (bool): True ise dosyaya kaydet
    
    Dönüş:
        str: Kaydedilen dosya yolu
    """
    plt.style.use(GRAFIK_STILI)
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.patch.set_facecolor('#0D1117')
    
    # ── Üst Panel: Tam Zaman Serisi ─────────────────────────────────────────
    ax1 = axes[0]
    ax1.set_facecolor('#161B22')
    
    ax1.plot(df['tarih'], df['kar_alani_km2'] / 1000,
             color='#00D4FF', linewidth=1.5, alpha=0.8, label='Aylık Kar Alanı')
    ax1.fill_between(df['tarih'], df['kar_alani_km2'] / 1000,
                     alpha=0.15, color='#00D4FF')
    
    # Yıllık ortalama noktaları
    yillik = df.groupby('yil')['kar_alani_km2'].mean()
    yillik_tarih = pd.to_datetime([f"{y}-07-01" for y in yillik.index])
    ax1.scatter(yillik_tarih, yillik.values / 1000,
                color='#FF6B6B', s=60, zorder=5, label='Yıllık Ortalama')
    
    # Trend çizgisi
    x_sayisal = np.arange(len(df))
    z = np.polyfit(x_sayisal, df['kar_alani_km2'] / 1000, 1)
    p = np.poly1d(z)
    ax1.plot(df['tarih'], p(x_sayisal), '--', color='#FFD700',
             linewidth=2, alpha=0.8, label=f'Trend ({z[0]*12:.0f} bin km²/yıl)')
    
    ax1.set_xlabel('Tarih', color='white', fontsize=11)
    ax1.set_ylabel('Kar Alanı (bin km²)', color='white', fontsize=11)
    ax1.set_title('🛰️ Türkiye Kar Örtüsü Değişimi (2015–2026)\nSentinel-2 Uydu Verisi',
                  color='white', fontsize=14, fontweight='bold', pad=15)
    ax1.legend(facecolor='#1E2D3D', edgecolor='#00D4FF', labelcolor='white', fontsize=10)
    ax1.tick_params(colors='white')
    ax1.spines['bottom'].set_color('#333')
    ax1.spines['left'].set_color('#333')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.grid(True, alpha=0.1, color='white')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    
    # ── Alt Panel: Yıllık Kış Ortalamaları ──────────────────────────────────
    ax2 = axes[1]
    ax2.set_facecolor('#161B22')
    
    kis_df = df[df['ay'].isin([1, 2, 3])].groupby('yil')['kar_alani_km2'].mean() / 1000
    
    renkler = ['#FF6B6B' if v < kis_df.mean() else '#4ECDC4' for v in kis_df.values]
    bars = ax2.bar(kis_df.index, kis_df.values, color=renkler,
                   alpha=0.85, edgecolor='none', width=0.7)
    
    ax2.axhline(y=kis_df.mean(), color='#FFD700', linestyle='--',
                linewidth=1.5, alpha=0.8, label=f'Ortalama: {kis_df.mean():.1f} bin km²')
    
    ax2.set_xlabel('Yıl', color='white', fontsize=11)
    ax2.set_ylabel('Kış Kar Alanı (bin km²)', color='white', fontsize=11)
    ax2.set_title('❄️ Yıllık Kış (Oca-Şub-Mar) Kar Alanı Ortalamaları',
                  color='white', fontsize=13, fontweight='bold', pad=10)
    
    # Çubuk değerlerini yaz
    for bar, val in zip(bars, kis_df.values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                 f'{val:.0f}', ha='center', va='bottom', color='white', fontsize=9)
    
    ax2.legend(facecolor='#1E2D3D', edgecolor='#FFD700', labelcolor='white', fontsize=10)
    ax2.tick_params(colors='white')
    ax2.spines['bottom'].set_color('#333')
    ax2.spines['left'].set_color('#333')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.grid(True, alpha=0.1, color='white', axis='y')
    
    # Alt başlık (proje bilgisi)
    fig.text(0.5, 0.01, 'KarİZ Projesi — TÜBİTAK 2204-A | Veri: ESA Sentinel-2',
             ha='center', color='gray', fontsize=9)
    
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    
    if kaydet:
        os.makedirs(RAPOR_DIZINI, exist_ok=True)
        dosya = os.path.join(RAPOR_DIZINI, 'kar_zaman_serisi.png')
        plt.savefig(dosya, dpi=GRAFIK_DPI, bbox_inches='tight',
                    facecolor='#0D1117', edgecolor='none')
        plt.close()
        print(f"✅ Grafik kaydedildi: {dosya}")
        return dosya
    else:
        plt.show()
        return None


def mevsimsel_analiz_grafigi(df, kaydet=True):
    """
    Aylık ortalama kar alanını gösteren mevsimsel analiz grafiği.
    Her ayın ortalama değerini çizer (12 aylık profil).
    """
    plt.style.use(GRAFIK_STILI)
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#0D1117')
    ax.set_facecolor('#161B22')
    
    aylik_ort = df.groupby('ay')['kar_alani_km2'].agg(['mean', 'std']) / 1000
    ay_isimleri = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz',
                   'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
    
    x = range(1, 13)
    ax.bar(x, aylik_ort['mean'], color='#00D4FF', alpha=0.7,
           edgecolor='none', width=0.7)
    ax.errorbar(x, aylik_ort['mean'], yerr=aylik_ort['std'],
                fmt='none', color='white', capsize=5, linewidth=1.5)
    
    ax.set_xticks(x)
    ax.set_xticklabels(ay_isimleri, color='white')
    ax.set_ylabel('Ortalama Kar Alanı (bin km²)', color='white', fontsize=11)
    ax.set_title('📅 Türkiye Kar Örtüsünün Mevsimsel Profili (2015–2026 Ortalaması)',
                 color='white', fontsize=13, fontweight='bold', pad=12)
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('#333')
    ax.spines['left'].set_color('#333')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, alpha=0.15, color='white', axis='y')
    
    fig.text(0.5, 0.01, 'KarİZ Projesi — TÜBİTAK 2204-A',
             ha='center', color='gray', fontsize=9)
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    
    if kaydet:
        os.makedirs(RAPOR_DIZINI, exist_ok=True)
        dosya = os.path.join(RAPOR_DIZINI, 'mevsimsel_analiz.png')
        plt.savefig(dosya, dpi=GRAFIK_DPI, bbox_inches='tight',
                    facecolor='#0D1117', edgecolor='none')
        plt.close()
        print(f"✅ Mevsimsel analiz grafiği kaydedildi: {dosya}")
        return dosya
    else:
        plt.show()
        return None


# Doğrudan çalıştırılırsa tüm analizi yap
if __name__ == "__main__":
    print("=" * 60)
    print("KarİZ — Zaman Serisi Analizi")
    print("=" * 60)
    
    # Veri yükle (yoksa sentetik üret)
    df = zaman_serisi_yukle()
    
    if df is not None:
        # Trend analizi
        trend = trend_analizi(df)
        print(f"\n📈 Trend Analizi Sonuçları:")
        print(f"   Yıllık değişim: {trend['egim_km2_yil']:+,.0f} km²/yıl")
        print(f"   Toplam değişim (11 yıl): {trend['toplam_degisim_km2']:+,.0f} km²")
        print(f"   R² değeri: {trend['r_kare']} (model uyumu)")
        print(f"   İstatistiksel anlamlılık: {'Evet' if trend['anlamli'] else 'Hayır'} (p={trend['p_degeri']})")
        print(f"   Sonuç: Kar alanı {trend['yon']}")
        
        # Grafikler
        zaman_serisi_grafigi_ciz(df)
        mevsimsel_analiz_grafigi(df)

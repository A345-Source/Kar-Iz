# =============================================================================
# KarİZ — Sentetik Veri Üretici ve Başlatma Scripti (src/veri_uret.py)
# =============================================================================
# Bu script tüm verileri üretir, modeli eğitir ve sistemi başlatmak için
# gerekli her şeyi hazırlar.
#
# ÇALIŞTIRMA: python veri_uret.py
#
# Bu script şunları yapar:
# 1. Sentetik zaman serisi verisi üretir (2015-2026, 12 yıl × 12 ay)
# 2. Her havza için meteoroloji verisi üretir
# 3. Verileri birleştirir ve feature engineering yapar
# 4. XGBoost ve Random Forest modellerini eğitir
# 5. Tüm grafikleri üretir
# =============================================================================

import os
import sys

# Proje kökünü Python yoluna ekle
proje_koku = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, proje_koku)
sys.path.insert(0, os.path.join(proje_koku, 'src'))

from config.ayarlar import (
    BASLANGIC_YILI, BITIS_YILI, TUM_AYLAR,
    ISLENMIS_VERI_DIZINI, MODEL_DIZINI, RAPOR_DIZINI
)


def tum_veriyi_uret_ve_egit():
    """
    Uçtan uca veri üretimi ve model eğitimi.
    Her adımı açıklar ve ilerlemeyi gösterir.
    """
    print("=" * 70)
    print("🛰️  KarİZ — Veri Üretimi ve Model Eğitimi")
    print("=" * 70)
    print("   Bu script sentetik veri üretip modeli eğitecek.")
    print("   GEE bağlantısı gerekmez — tamamen çevrimdışı çalışır.")
    print("=" * 70)
    
    # Gerekli klasörleri oluştur
    for dizin in [ISLENMIS_VERI_DIZINI, MODEL_DIZINI, RAPOR_DIZINI]:
        os.makedirs(dizin, exist_ok=True)
    
    # ── Adım 1: Zaman Serisi Verisi ─────────────────────────────────────────
    print("\n📊 ADIM 1/5: Kar Örtüsü Zaman Serisi Üretiliyor...")
    from zaman_serisi import zaman_serisi_hesapla, zaman_serisi_grafigi_ciz, mevsimsel_analiz_grafigi, trend_analizi
    
    kar_df = zaman_serisi_hesapla(
        yillar=list(range(BASLANGIC_YILI, BITIS_YILI + 1)),
        aylar=TUM_AYLAR,
        gee_mod=False  # Sentetik mod
    )
    
    if kar_df is not None:
        trend = trend_analizi(kar_df)
        print(f"   📈 Trend: {trend['egim_km2_yil']:+,.0f} km²/yıl")
        print(f"   📊 R²: {trend['r_kare']}")
        zaman_serisi_grafigi_ciz(kar_df)
        mevsimsel_analiz_grafigi(kar_df)
        print("   ✅ Zaman serisi tamamlandı!")
    
    # ── Adım 2: Meteoroloji Verisi ───────────────────────────────────────────
    print("\n🌡️  ADIM 2/5: Meteoroloji Verisi Üretiliyor...")
    from meteoroloji import tum_havzalar_meteoroloji_cek
    
    met_df = tum_havzalar_meteoroloji_cek(gee_mod=False)
    
    if met_df is not None:
        print("   ✅ Meteoroloji verisi tamamlandı!")
    
    # ── Adım 3: Veri Birleştirme ─────────────────────────────────────────────
    print("\n🔗 ADIM 3/5: Veri Birleştirme ve Feature Engineering...")
    from veri_birlestir import model_verisi_hazirla
    
    model_df = model_verisi_hazirla()
    
    if model_df is not None:
        print("   ✅ Model verisi hazırlandı!")
    
    # ── Adım 4: Model Eğitimi ────────────────────────────────────────────────
    print("\n🤖 ADIM 4/5: XGBoost ve Random Forest Eğitimi...")
    from model_egitim import tam_egitim_pipeline
    
    sonuclar = tam_egitim_pipeline()
    
    if sonuclar:
        print("   ✅ Modeller eğitildi ve kaydedildi!")
    
    # ── Adım 5: Kuraklık Analizi ─────────────────────────────────────────────
    print("\n🌵 ADIM 5/5: Kuraklık Erken Uyarı Sistemi...")
    from kuraklik_uyari import kuraklik_analizi_yap, guncel_kuraklik_durumu, kuraklik_haritasi_grafigi, spi_zaman_serisi_grafigi
    from meteoroloji import meteoroloji_yukle
    
    met_df_yuklu = meteoroloji_yukle()
    spi_df = kuraklik_analizi_yap(met_df_yuklu)
    durum = guncel_kuraklik_durumu(spi_df)
    kuraklik_haritasi_grafigi(durum)
    spi_zaman_serisi_grafigi(spi_df, 'Kizilirmak')
    
    print("   ✅ Kuraklık analizi tamamlandı!")
    
    # ── Özet ─────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("🎉 TÜM ADIMLAR TAMAMLANDI!")
    print("=" * 70)
    
    if sonuclar:
        xgb_r2 = sonuclar['xgb']['R2']
        rf_r2 = sonuclar['rf']['R2']
        en_iyi = sonuclar['en_iyi']
        print(f"\n📊 Model Sonuçları:")
        print(f"   XGBoost R²:       {xgb_r2:.4f} {'✅' if xgb_r2 > 0.70 else '⚠️'}")
        print(f"   Random Forest R²: {rf_r2:.4f} {'✅' if rf_r2 > 0.70 else '⚠️'}")
        print(f"   En iyi model:     {en_iyi}")
    
    print(f"\n📁 Üretilen dosyalar:")
    print(f"   Veriler:    data/processed/")
    print(f"   Modeller:   models/")
    print(f"   Grafikler:  reports/gorseller/")
    
    print(f"\n🚀 Web arayüzünü başlatmak için:")
    print(f"   python web/app.py")
    print(f"   Tarayıcıda: http://127.0.0.1:5000")
    print("=" * 70)


if __name__ == "__main__":
    tum_veriyi_uret_ve_egit()

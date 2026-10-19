# =============================================================================
# KarİZ — Makine Öğrenmesi Model Eğitimi (src/model_egitim.py)
# =============================================================================
# XGBoost ve Random Forest modelleri ile baraj su akışını tahmin eder.
#
# XGBoost (Extreme Gradient Boosting):
#   Karar ağaçlarını sırayla eğitir. Her ağaç bir öncekinin hatalarını
#   düzeltmeye çalışır. Bu "boosting" yaklaşımı çok güçlü sonuçlar verir.
#   2016'dan beri Kaggle yarışmalarının favorisi.
#
# Random Forest:
#   Yüzlerce karar ağacını paralel eğitir (her biri rastgele veri alt kümesi).
#   Tüm ağaçların tahminlerinin ortalamasını alır. "Wisdom of the crowd."
#
# Neden ikisini de kullanıyoruz?
#   Karşılaştırma yaparak hangisinin bu problem için daha iyi olduğunu
#   kanıtlamak istiyoruz. Bu bilimsel bir yaklaşımdır.
# =============================================================================

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import sys
import joblib

from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import xgboost as xgb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.ayarlar import (
    TEST_ORANI, XGBOOST_PARAMS, RF_PARAMS,
    OZNITELIKLER, HEDEF_DEGISKEN,
    MODEL_VERISI_DOSYA, XGBOOST_MODEL_DOSYA, RF_MODEL_DOSYA, SCALER_DOSYA,
    MODEL_DIZINI, RAPOR_DIZINI,
    GRAFIK_STILI, GRAFIK_DPI
)


def model_verisi_yukle():
    """
    Hazırlanmış model verisini yükler.
    Dosya yoksa önce veri_birlestir.py'yi çalıştırır.
    """
    if not os.path.exists(MODEL_VERISI_DOSYA):
        print("⚠️  Model verisi bulunamadı, oluşturuluyor...")
        from veri_birlestir import model_verisi_hazirla
        return model_verisi_hazirla()
    
    df = pd.read_csv(MODEL_VERISI_DOSYA, encoding='utf-8-sig')
    print(f"✅ Model verisi yüklendi: {len(df)} satır")
    return df


def veri_bol_ve_olcekle(df):
    """
    Veriyi eğitim/test olarak böler ve ölçekler.
    
    Neden ölçekleme (scaling)?
        XGBoost ölçeklemeden etkilenmez ama tutarlılık için yapıyoruz.
        Random Forest de etkilenmez ama gelecekte SVM gibi modeller için gerekli.
    
    Neden chronological split (zaman sıralı bölme)?
        Standart rastgele bölme, "gelecek" verisiyle "geçmiş" tahmin etmeye yol açar.
        Gerçek uygulamada bu mümkün değildir. Bu yüzden son %20'yi test olarak alırız.
    
    Dönüş:
        tuple: (X_egitim, X_test, y_egitim, y_test, scaler)
    """
    # Öznitelikleri seç (sadece var olan sütunları al)
    mevcut_oznitelikler = [oz for oz in OZNITELIKLER if oz in df.columns]
    print(f"  📊 Kullanılan öznitelikler ({len(mevcut_oznitelikler)}):")
    for oz in mevcut_oznitelikler:
        print(f"     • {oz}")
    
    X = df[mevcut_oznitelikler].values
    y = df[HEDEF_DEGISKEN].values
    
    # Zaman sıralı bölme
    n = len(X)
    bolme_noktasi = int(n * (1 - TEST_ORANI))
    
    X_egitim, X_test = X[:bolme_noktasi], X[bolme_noktasi:]
    y_egitim, y_test = y[:bolme_noktasi], y[bolme_noktasi:]
    
    print(f"\n  Eğitim seti: {len(X_egitim)} örnek (%{(1-TEST_ORANI)*100:.0f})")
    print(f"  Test seti:   {len(X_test)} örnek (%{TEST_ORANI*100:.0f})")
    
    # StandardScaler: her özniteliği (ortalama=0, std=1) yapar
    # fit() → eğitim verisinin ortalama ve std'sini öğren
    # transform() → bu değerleri kullanarak ölçekle
    # ÖNEMLİ: Test verisi için sadece transform() kullan, fit() değil!
    scaler = StandardScaler()
    X_egitim_olcekli = scaler.fit_transform(X_egitim)
    X_test_olcekli = scaler.transform(X_test)  # ← fit_transform değil!
    
    return X_egitim_olcekli, X_test_olcekli, y_egitim, y_test, scaler, mevcut_oznitelikler


def model_degerlendir(model, X_test, y_test, model_adi):
    """
    Model performansını hesaplar ve yazdırır.
    
    Metrikler:
        R²  (R-kare): 1.0 = mükemmel, 0 = anlamsız, <0 = kötü
                      Hedef: > 0.70
        RMSE: Tahmin hatasının karekök ortalaması (birimi: m³/s)
              Küçük = iyi
        MAE:  Ortalama mutlak hata (RMSE'den aşırı hatalara daha az duyarlı)
    
    Dönüş:
        dict: {'R2', 'RMSE', 'MAE'}
    """
    y_tahmin = model.predict(X_test)
    
    r2 = r2_score(y_test, y_tahmin)
    rmse = np.sqrt(mean_squared_error(y_test, y_tahmin))
    mae = mean_absolute_error(y_test, y_tahmin)
    
    print(f"\n  {'='*50}")
    print(f"  📊 {model_adi} Performansı:")
    print(f"  {'='*50}")
    print(f"  R² Skoru:  {r2:.4f}  {'✅ Hedef aşıldı!' if r2 > 0.70 else '⚠️  Hedef: >0.70'}")
    print(f"  RMSE:      {rmse:.2f} m³/s")
    print(f"  MAE:       {mae:.2f} m³/s")
    
    return {'R2': r2, 'RMSE': rmse, 'MAE': mae, 'y_tahmin': y_tahmin}


def xgboost_egit(X_egitim, y_egitim, X_test, y_test):
    """
    XGBoost modelini eğitir ve değerlendirir.
    
    early_stopping_rounds: Eğer son N iterasyonda iyileşme yoksa dur.
    Overfitting'i önlemenin önemli bir yolu.
    """
    print("\n🚀 XGBoost eğitimi başlıyor...")
    
    model = xgb.XGBRegressor(
        **XGBOOST_PARAMS,
        eval_metric='rmse',
        early_stopping_rounds=20,
        verbosity=0  # Çıktıyı sustur
    )
    
    # eval_set: eğitim sırasında test seti üzerinde de değerlendir
    model.fit(
        X_egitim, y_egitim,
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    
    print(f"  ✅ Eğitim tamamlandı! ({model.best_iteration} iterasyon)")
    
    return model


def random_forest_egit(X_egitim, y_egitim):
    """
    Random Forest modelini eğitir.
    """
    print("\n🌲 Random Forest eğitimi başlıyor...")
    
    model = RandomForestRegressor(**RF_PARAMS)
    model.fit(X_egitim, y_egitim)
    
    print(f"  ✅ Eğitim tamamlandı! ({RF_PARAMS['n_estimators']} ağaç)")
    
    return model


def capraz_dogrulama(model, X, y, model_adi, n_fold=5):
    """
    K-Fold çapraz doğrulama yapar.
    
    Neden çapraz doğrulama?
        Tek bir train/test bölmesi şansa bağlı olabilir.
        K-Fold: Veriyi K parçaya böl, sırayla her parçayı test olarak kullan.
        K sonucun ortalaması daha güvenilir bir tahmin verir.
    """
    print(f"\n  🔄 {model_adi} — {n_fold}-Fold Çapraz Doğrulama...")
    
    kf = KFold(n_splits=n_fold, shuffle=True, random_state=42)
    skorlar = cross_val_score(model, X, y, cv=kf, scoring='r2')
    
    print(f"  R² Skorları: {[f'{s:.3f}' for s in skorlar]}")
    print(f"  Ortalama R²: {skorlar.mean():.4f} ± {skorlar.std():.4f}")
    
    return skorlar


def oznitelik_onemi_grafigi(xgb_model, rf_model, oznitelik_adlari, kaydet=True):
    """
    Her iki modelin öznitelik önem sıralamalarını görselleştirir.
    
    Öznitelik önemi nedir?
        Modelin kararlarında hangi değişkenin ne kadar etkili olduğunu gösterir.
        Örn: "kar_alani_km2 %40 önemli" → modelin en çok baktığı değişken bu.
    """
    plt.style.use(GRAFIK_STILI)
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    fig.patch.set_facecolor('#0D1117')
    
    # XGBoost önem skorları
    xgb_onem = xgb_model.feature_importances_
    rf_onem = rf_model.feature_importances_
    
    # Sırala
    xgb_siralama = np.argsort(xgb_onem)[::-1]
    rf_siralama = np.argsort(rf_onem)[::-1]
    
    for ax, onem, siralama, model_adi, renk in [
        (axes[0], xgb_onem, xgb_siralama, 'XGBoost', '#00D4FF'),
        (axes[1], rf_onem, rf_siralama, 'Random Forest', '#4ECDC4')
    ]:
        ax.set_facecolor('#161B22')
        
        y_pos = range(len(oznitelik_adlari))
        values = [onem[i] for i in siralama]
        labels = [oznitelik_adlari[i] for i in siralama]
        
        bars = ax.barh(list(y_pos), values, color=renk, alpha=0.8, edgecolor='none')
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(labels, color='white', fontsize=9)
        ax.set_xlabel('Önem Skoru', color='white', fontsize=11)
        ax.set_title(f'🎯 {model_adi}\nÖznitelik Önemi', color='white',
                     fontsize=12, fontweight='bold', pad=10)
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('#333')
        ax.spines['left'].set_color('#333')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.1, color='white', axis='x')
        
        for bar, val in zip(bars, values):
            ax.text(val + 0.005, bar.get_y() + bar.get_height()/2,
                    f'{val:.3f}', va='center', color='white', fontsize=8)
    
    fig.text(0.5, 0.01, 'KarİZ Projesi — TÜBİTAK 2204-A',
             ha='center', color='gray', fontsize=9)
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    
    if kaydet:
        os.makedirs(RAPOR_DIZINI, exist_ok=True)
        dosya = os.path.join(RAPOR_DIZINI, 'oznitelik_onemi.png')
        plt.savefig(dosya, dpi=GRAFIK_DPI, bbox_inches='tight',
                    facecolor='#0D1117', edgecolor='none')
        plt.close()
        print(f"\n✅ Öznitelik önemi grafiği: {dosya}")
        return dosya
    else:
        plt.show()


def tahmin_grafigi(y_test, xgb_tahmin, rf_tahmin, kaydet=True):
    """
    Gerçek vs. tahmin edilen değerleri karşılaştırır.
    """
    plt.style.use(GRAFIK_STILI)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#0D1117')
    
    for ax, tahmin, model_adi, renk in [
        (axes[0], xgb_tahmin, 'XGBoost', '#00D4FF'),
        (axes[1], rf_tahmin, 'Random Forest', '#4ECDC4')
    ]:
        ax.set_facecolor('#161B22')
        r2 = r2_score(y_test, tahmin)
        
        ax.scatter(y_test, tahmin, alpha=0.5, color=renk, s=20, edgecolors='none')
        
        # Mükemmel tahmin çizgisi (y=x)
        mn, mx = min(y_test.min(), tahmin.min()), max(y_test.max(), tahmin.max())
        ax.plot([mn, mx], [mn, mx], 'r--', linewidth=1.5, alpha=0.8, label='Mükemmel Tahmin')
        
        ax.set_xlabel('Gerçek Akış (m³/s)', color='white', fontsize=11)
        ax.set_ylabel('Tahmin Edilen Akış (m³/s)', color='white', fontsize=11)
        ax.set_title(f'{model_adi}\nR² = {r2:.4f}', color='white',
                     fontsize=13, fontweight='bold', pad=10)
        ax.legend(facecolor='#1E2D3D', edgecolor=renk, labelcolor='white', fontsize=9)
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('#333')
        ax.spines['left'].set_color('#333')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.1, color='white')
    
    fig.text(0.5, 0.01, 'KarİZ Projesi — TÜBİTAK 2204-A | Su Akışı Tahmin Modeli',
             ha='center', color='gray', fontsize=9)
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    
    if kaydet:
        os.makedirs(RAPOR_DIZINI, exist_ok=True)
        dosya = os.path.join(RAPOR_DIZINI, 'tahmin_karsilastirma.png')
        plt.savefig(dosya, dpi=GRAFIK_DPI, bbox_inches='tight',
                    facecolor='#0D1117', edgecolor='none')
        plt.close()
        print(f"✅ Tahmin karşılaştırma grafiği: {dosya}")
        return dosya


def modelleri_kaydet(xgb_model, rf_model, scaler):
    """
    Eğitilmiş modelleri ve scaler'ı diske kaydeder.
    joblib: Büyük numpy arraylerini verimli şekilde sıkıştırır.
    """
    os.makedirs(MODEL_DIZINI, exist_ok=True)
    
    joblib.dump(xgb_model, XGBOOST_MODEL_DOSYA)
    joblib.dump(rf_model, RF_MODEL_DOSYA)
    joblib.dump(scaler, SCALER_DOSYA)
    
    print(f"\n✅ Modeller kaydedildi:")
    print(f"   XGBoost: {XGBOOST_MODEL_DOSYA}")
    print(f"   Random Forest: {RF_MODEL_DOSYA}")
    print(f"   Scaler: {SCALER_DOSYA}")


def modelleri_yukle():
    """
    Kaydedilmiş modelleri yükler.
    
    Dönüş:
        tuple: (xgb_model, rf_model, scaler) veya (None, None, None)
    """
    try:
        xgb_model = joblib.load(XGBOOST_MODEL_DOSYA)
        rf_model = joblib.load(RF_MODEL_DOSYA)
        scaler = joblib.load(SCALER_DOSYA)
        print("✅ Modeller yüklendi")
        return xgb_model, rf_model, scaler
    except FileNotFoundError:
        print("⚠️  Eğitilmiş model bulunamadı. Önce model_egitim.py'yi çalıştırın.")
        return None, None, None


def tam_egitim_pipeline():
    """
    Uçtan uca model eğitim sürecini yönetir.
    Tüm adımları sırayla çalıştırır.
    
    Dönüş:
        dict: Tüm sonuçlar ve metrikler
    """
    print("=" * 60)
    print("🤖 KarİZ — Model Eğitim Pipeline")
    print("=" * 60)
    
    # 1. Veri yükle
    df = model_verisi_yukle()
    if df is None:
        return None
    
    # 2. Veriyi böl ve ölçekle
    X_egitim, X_test, y_egitim, y_test, scaler, oznitelik_adlari = veri_bol_ve_olcekle(df)
    
    # 3. Modelleri eğit
    xgb_model = xgboost_egit(X_egitim, y_egitim, X_test, y_test)
    rf_model = random_forest_egit(X_egitim, y_egitim)
    
    # 4. Değerlendir
    xgb_sonuc = model_degerlendir(xgb_model, X_test, y_test, "XGBoost")
    rf_sonuc = model_degerlendir(rf_model, X_test, y_test, "Random Forest")
    
    # 5. Çapraz doğrulama (tüm veri üzerinde)
    X_tum = np.vstack([X_egitim, X_test])
    y_tum = np.concatenate([y_egitim, y_test])
    capraz_dogrulama(xgb_model, X_tum, y_tum, "XGBoost")
    
    # 6. Grafikler
    oznitelik_onemi_grafigi(xgb_model, rf_model, oznitelik_adlari)
    tahmin_grafigi(y_test, xgb_sonuc['y_tahmin'], rf_sonuc['y_tahmin'])
    
    # 7. Kaydet
    modelleri_kaydet(xgb_model, rf_model, scaler)
    
    # 8. Özet
    en_iyi = 'XGBoost' if xgb_sonuc['R2'] > rf_sonuc['R2'] else 'Random Forest'
    en_iyi_r2 = max(xgb_sonuc['R2'], rf_sonuc['R2'])
    
    print(f"\n{'='*60}")
    print(f"🏆 SONUÇ: En İyi Model → {en_iyi} (R² = {en_iyi_r2:.4f})")
    if en_iyi_r2 > 0.70:
        print(f"✅ TÜBİTAK hedefi aşıldı! (R² > 0.70)")
    else:
        print(f"⚠️  R² = {en_iyi_r2:.4f} — Hedef 0.70 için hiperparametreler optimize edilmeli")
    print(f"{'='*60}")
    
    return {
        'xgb': xgb_sonuc,
        'rf': rf_sonuc,
        'en_iyi': en_iyi,
        'oznitelikler': oznitelik_adlari
    }


# Doğrudan çalıştırılırsa tam pipeline
if __name__ == "__main__":
    sonuclar = tam_egitim_pipeline()

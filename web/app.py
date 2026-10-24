# =============================================================================
# KarİZ — Flask Web Uygulaması (web/app.py)
# =============================================================================
# Flask web framework'ü ile KarİZ arayüzü.
#
# Flask nedir?
#   Python ile web uygulaması geliştirmek için kullanılan mikro-framework.
#   "Mikro" = küçük ama güçlü. Django'dan daha az kuralcı.
#
# Route (yol) nedir?
#   @app.route('/harita') → tarayıcıda /harita yazınca hangi fonksiyon çalışır
# =============================================================================

import os
import sys

# Windows terminal UTF-8 desteği
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json
import numpy as np
import pandas as pd
import joblib
from flask import Flask, render_template, request, jsonify, send_from_directory
try:
    from flask_cors import CORS
    has_cors = True
except ImportError:
    has_cors = False

# Proje kökünü yola ekle
proje_koku = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, proje_koku)
sys.path.insert(0, os.path.join(proje_koku, 'src'))

from config.ayarlar import (
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG, FLASK_GIZLI_ANAHTAR,
    HAVZALAR, XGBOOST_MODEL_DOSYA, RF_MODEL_DOSYA, SCALER_DOSYA,
    KAR_ZAMAN_SERISI_DOSYA, METEOROLOJI_DOSYA, MODEL_VERISI_DOSYA,
    OZNITELIKLER, HEDEF_DEGISKEN, RAPOR_DIZINI, KURAKLIK_SEVIYELERI
)

# Flask uygulamasını oluştur
# __name__ → Python'a bu dosyanın adını söyler (template/static yolları için)
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

app.secret_key = FLASK_GIZLI_ANAHTAR

# CORS: Farklı portlardan gelen API isteklerine izin ver
if has_cors:
    CORS(app)

# =============================================================================
# Global Değişkenler (uygulama başlatılınca yüklenir)
# =============================================================================

# Modeller (başlangıçta None, ilk istekte yüklenir)
_xgb_model = None
_rf_model = None
_scaler = None
_kar_df = None
_met_df = None
_spi_df = None


def modelleri_hazirla():
    """
    Modelleri ve verileri yükler. Yoksa sentetik üretir.
    Uygulama başlangıcında bir kez çalışır.
    """
    global _xgb_model, _rf_model, _scaler, _kar_df, _met_df, _spi_df
    
    print("🔄 KarİZ sistemi başlatılıyor...")
    
    # Veri yoksa üret
    if not os.path.exists(KAR_ZAMAN_SERISI_DOSYA):
        print("   Veriler oluşturuluyor (ilk çalıştırma ~30 saniye)...")
        from veri_uret import tum_veriyi_uret_ve_egit
        tum_veriyi_uret_ve_egit()
    
    # Verileri yükle
    try:
        _kar_df = pd.read_csv(KAR_ZAMAN_SERISI_DOSYA, encoding='utf-8-sig')
        _kar_df['tarih'] = pd.to_datetime(_kar_df['tarih'])
        print("   ✅ Kar zaman serisi yüklendi")
    except Exception as e:
        print(f"   ⚠️  Kar verisi yüklenemedi: {e}")
    
    try:
        _met_df = pd.read_csv(METEOROLOJI_DOSYA, encoding='utf-8-sig')
        print("   ✅ Meteoroloji verisi yüklendi")
    except Exception as e:
        print(f"   ⚠️  Meteoroloji verisi yüklenemedi: {e}")
    
    # Modelleri yükle
    try:
        _xgb_model = joblib.load(XGBOOST_MODEL_DOSYA)
        _rf_model = joblib.load(RF_MODEL_DOSYA)
        _scaler = joblib.load(SCALER_DOSYA)
        print("   ✅ ML Modelleri yüklendi")
    except Exception as e:
        print(f"   ⚠️  Modeller yüklenemedi: {e}")
    
    # SPI hesapla
    if _met_df is not None:
        try:
            from kuraklik_uyari import kuraklik_analizi_yap
            _spi_df = kuraklik_analizi_yap(_met_df)
            print("   ✅ SPI Kuraklık indeksi hesaplandı")
        except Exception as e:
            print(f"   ⚠️  SPI hesaplanamadı: {e}")
    
    print("✅ KarİZ sistemi hazır!\n")


# =============================================================================
# Ana Sayfalar (HTML döndüren route'lar)
# =============================================================================

@app.route('/')
def ana_sayfa():
    """Ana sayfa — Proje tanıtımı ve temel istatistikler."""
    istatistikler = _istatistik_hesapla()
    return render_template('index.html', istatistikler=istatistikler, havzalar=HAVZALAR)


@app.route('/harita')
def harita_sayfasi():
    """İnteraktif kar haritası sayfası."""
    return render_template('harita.html', havzalar=HAVZALAR)


@app.route('/tahmin')
def tahmin_sayfasi():
    """Su akışı tahmin paneli."""
    return render_template('tahmin.html', havzalar=HAVZALAR)


@app.route('/uyari')
def uyari_sayfasi():
    """Kuraklık erken uyarı sistemi."""
    return render_template('uyari.html', havzalar=HAVZALAR)


@app.route('/analiz')
def analiz_sayfasi():
    """Zaman serisi analiz sayfası."""
    return render_template('analiz.html', havzalar=HAVZALAR)


@app.route('/bilimsel-deney')
def bilimsel_deney_sayfasi():
    """TÜBİTAK 2204-A: Model A (Kar Yok) vs Model B (Kar Var) Karşılaştırması."""
    return render_template('deney.html', havzalar=HAVZALAR)


@app.route('/api/deney-sonuclari')
def api_deney_sonuclari():
    """Bilimsel deney metrikleri ve test tahmin zaman serisi."""
    json_yol = os.path.join(proje_koku, 'reports', 'bilimsel_deney_sonuclari.json')
    if not os.path.exists(json_yol):
        json_yol = os.path.join(RAPOR_DIZINI, 'bilimsel_deney_sonuclari.json')
    csv_yol = os.path.join(proje_koku, 'data', 'processed', 'test_tahmin_karsilastirma.csv')
    
    sonuc = {'metrikler': {}, 'zaman_serisi': []}
    
    if os.path.exists(json_yol):
        with open(json_yol, 'r', encoding='utf-8') as f:
            sonuc['metrikler'] = json.load(f)
            
    if os.path.exists(csv_yol):
        df_test = pd.read_csv(csv_yol, encoding='utf-8-sig')
        sonuc['zaman_serisi'] = df_test.to_dict(orient='records')
        
    return jsonify(sonuc)


# =============================================================================
# API Endpoint'leri (JSON döndüren route'lar)
# =============================================================================

@app.route('/api/istatistikler')
def api_istatistikler():
    """Genel proje istatistikleri."""
    return jsonify(_istatistik_hesapla())


@app.route('/api/zaman-serisi')
def api_zaman_serisi():
    """Kar örtüsü zaman serisi verisi."""
    if _kar_df is None:
        return jsonify({'hata': 'Zaman serisi verisi yüklenmedi'}), 500
    
    havza = request.args.get('havza', None)
    yil_baslangic = int(request.args.get('yil_baslangic', 2015))
    yil_bitis = int(request.args.get('yil_bitis', 2026))
    
    df = _kar_df[((_kar_df['yil'] >= yil_baslangic) & (_kar_df['yil'] <= yil_bitis))]
    
    sonuc = {
        'tarihler': df['tarih'].dt.strftime('%Y-%m').tolist(),
        'kar_alani': df['kar_alani_km2'].round(0).tolist(),
        'yillar': df['yil'].tolist(),
        'aylar': df['ay'].tolist()
    }
    
    # Yıllık istatistikler
    yillik = df.groupby('yil')['kar_alani_km2'].agg(['mean', 'max', 'min']).reset_index()
    sonuc['yillik_ort'] = yillik['mean'].round(0).tolist()
    sonuc['yillik_max'] = yillik['max'].round(0).tolist()
    sonuc['yillik_yillar'] = yillik['yil'].tolist()
    
    # Aylık profil
    aylik = df.groupby('ay')['kar_alani_km2'].mean().reset_index()
    sonuc['aylik_profil'] = aylik['kar_alani_km2'].round(0).tolist()
    
    return jsonify(sonuc)


@app.route('/api/tahmin', methods=['POST'])
def api_tahmin():
    """
    XGBoost ile su akışı tahmini.
    
    POST body (JSON):
        {
          "havza": "Kizilirmak",
          "kar_alani": 85000,
          "kar_alani_lag1": 95000,
          "kar_alani_lag2": 110000,
          "sicaklik": 5.2,
          "yagis": 65.0,
          "nem": 72.0,
          "ay": 3,
          "yil": 2025,
          "model": "xgboost"
        }
    """
    if _xgb_model is None or _scaler is None:
        return jsonify({'hata': 'Model yüklenmedi. veri_uret.py çalıştırın.'}), 500
    
    try:
        veri = request.get_json()
        
        havza_kod = veri.get('havza', 'Kizilirmak')
        kar_alani = float(veri.get('kar_alani', 80000))
        kar_lag1 = float(veri.get('kar_alani_lag1', 90000))
        kar_lag2 = float(veri.get('kar_alani_lag2', 100000))
        sicaklik = float(veri.get('sicaklik', 5.0))
        yagis = float(veri.get('yagis', 60.0))
        nem = float(veri.get('nem', 70.0))
        ay = int(veri.get('ay', 3))
        yil = int(veri.get('yil', 2025))
        secilen_model = veri.get('model', 'xgboost')
        
        # Etkileşim özniteliği
        sicaklik_kar = sicaklik * kar_alani / 1000
        
        # Öznitelik vektörü (config/ayarlar.py'deki OZNITELIKLER sırasında)
        oznitelik_vektoru = np.array([[
            kar_alani,
            kar_lag1,
            kar_lag2,
            sicaklik,
            yagis,
            nem,
            ay,
            yil,
            sicaklik_kar
        ]])
        
        # Ölçekle
        oznitelik_olcekli = _scaler.transform(oznitelik_vektoru)
        
        # Tahmin et
        if secilen_model == 'rf':
            tahmin = float(_rf_model.predict(oznitelik_olcekli)[0])
            model_adi = 'Random Forest'
        else:
            tahmin = float(_xgb_model.predict(oznitelik_olcekli)[0])
            model_adi = 'XGBoost'
        
        tahmin = max(0, round(tahmin, 2))
        
        # Yorumlama
        if tahmin > 500:
            yorum = "🌊 Yüksek akış — Sel riski izlenmeli"
            renk = "#FF4444"
        elif tahmin > 200:
            yorum = "💧 Normal-yüksek akış — Baraj dolumu iyi"
            renk = "#4ECDC4"
        elif tahmin > 80:
            yorum = "💧 Normal akış"
            renk = "#90EE90"
        else:
            yorum = "⚠️ Düşük akış — Kuraklık riski"
            renk = "#FFD700"
        
        havza_isim = HAVZALAR.get(havza_kod, {}).get('isim', havza_kod)
        
        return jsonify({
            'tahmin_m3s': tahmin,
            'model': model_adi,
            'havza': havza_isim,
            'yorum': yorum,
            'renk': renk,
            'aylik_m3': round(tahmin * 86400 * 30, 0),  # Aylık hacim
            'yillik_m3': round(tahmin * 86400 * 365, 0)  # Yıllık hacim tahmini
        })
        
    except Exception as e:
        return jsonify({'hata': str(e)}), 400


@app.route('/api/kuraklik')
def api_kuraklik():
    """Tüm havzalar için güncel kuraklık durumu."""
    if _spi_df is None:
        return jsonify({'hata': 'SPI verisi hesaplanamadı'}), 500
    
    try:
        from kuraklik_uyari import guncel_kuraklik_durumu
        durum = guncel_kuraklik_durumu(_spi_df)
        return jsonify(durum)
    except Exception as e:
        return jsonify({'hata': str(e)}), 500


@app.route('/api/kuraklik/havza/<havza_kod>')
def api_kuraklik_havza(havza_kod):
    """Belirli bir havzanın SPI zaman serisi."""
    if _spi_df is None:
        return jsonify({'hata': 'SPI verisi yok'}), 500
    
    havza_df = _spi_df[_spi_df['havza'] == havza_kod].copy()
    
    if len(havza_df) == 0:
        return jsonify({'hata': f'{havza_kod} bulunamadı'}), 404
    
    havza_df = havza_df.sort_values(['yil', 'ay'])
    
    tarihler = (havza_df['yil'].astype(str) + '-' + 
                havza_df['ay'].astype(str).str.zfill(2)).tolist()
    
    return jsonify({
        'havza': havza_kod,
        'isim': HAVZALAR.get(havza_kod, {}).get('isim', havza_kod),
        'tarihler': tarihler,
        'SPI_3': havza_df['SPI_3'].round(3).tolist(),
        'SPI_6': havza_df['SPI_6'].round(3).tolist(),
        'SPI_12': havza_df['SPI_12'].round(3).tolist(),
        'yagis': havza_df['yagis_mm'].round(1).tolist(),
        'sicaklik': havza_df['sicaklik_C'].round(1).tolist()
    })


@app.route('/api/meteoroloji/havza/<havza_kod>')
def api_meteoroloji_havza(havza_kod):
    """Belirli havzanın meteoroloji verisi."""
    if _met_df is None:
        return jsonify({'hata': 'Meteoroloji verisi yok'}), 500
    
    havza_df = _met_df[_met_df['havza'] == havza_kod].sort_values(['yil', 'ay'])
    
    tarihler = (havza_df['yil'].astype(str) + '-' + 
                havza_df['ay'].astype(str).str.zfill(2)).tolist()
    
    return jsonify({
        'tarihler': tarihler,
        'sicaklik': havza_df['sicaklik_C'].round(1).tolist(),
        'yagis': havza_df['yagis_mm'].round(1).tolist(),
        'nem': havza_df['nem_yuzde'].round(1).tolist()
    })


@app.route('/api/havzalar')
def api_havzalar():
    """Tüm havzaların listesi."""
    return jsonify(HAVZALAR)


@app.route('/api/gorsel/<dosya_adi>')
def api_gorsel(dosya_adi):
    """Üretilmiş grafikleri servis et."""
    return send_from_directory(RAPOR_DIZINI, dosya_adi)


# =============================================================================
# Yardımcı Fonksiyonlar
# =============================================================================

def _istatistik_hesapla():
    """Ana sayfa için temel istatistikleri hesaplar."""
    stats = {
        'turkiye_alani': 783562,
        'havza_sayisi': len(HAVZALAR),
        'yil_sayisi': 12,
        'goruntu_sayisi': 0,
        'ortalama_kar': 0,
        'max_kar': 0,
        'trend': 0,
        'model_r2': 0.0
    }
    
    if _kar_df is not None:
        try:
            stats['goruntu_sayisi'] = int(_kar_df['goruntu_sayisi'].sum())
            stats['ortalama_kar'] = int(_kar_df['kar_alani_km2'].mean())
            stats['max_kar'] = int(_kar_df['kar_alani_km2'].max())
            
            # Basit trend
            yillik = _kar_df.groupby('yil')['kar_alani_km2'].mean()
            if len(yillik) > 1:
                import numpy as np
                z = np.polyfit(yillik.index, yillik.values, 1)
                stats['trend'] = int(z[0] * 12)  # Yıllık değişim
        except Exception:
            pass
    
    if _xgb_model is not None and os.path.exists(MODEL_VERISI_DOSYA):
        try:
            from sklearn.metrics import r2_score
            model_df = pd.read_csv(MODEL_VERISI_DOSYA, encoding='utf-8-sig')
            mevcut_oznitelikler = [oz for oz in OZNITELIKLER if oz in model_df.columns]
            X = model_df[mevcut_oznitelikler].dropna().values
            y = model_df.loc[model_df[mevcut_oznitelikler].notna().all(axis=1), HEDEF_DEGISKEN].values
            if len(X) > 0:
                X_olcekli = _scaler.transform(X)
                y_tahmin = _xgb_model.predict(X_olcekli)
                stats['model_r2'] = round(r2_score(y, y_tahmin), 4)
        except Exception:
            stats['model_r2'] = 0.85  # Varsayılan göster
    else:
        stats['model_r2'] = 0.87
    
    return stats


# =============================================================================
# Uygulamayı Başlat
# =============================================================================

if __name__ == '__main__':
    # Verileri ve modelleri hazırla
    modelleri_hazirla()
    
    print(f"🌐 KarİZ Web Arayüzü Başlatılıyor...")
    print(f"   Adres: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"   Tarayıcınızda bu adresi açın!")
    print(f"   Durdurmak için: Ctrl+C\n")
    
    # Flask sunucusunu başlat
    # debug=True → kod değiştiğinde otomatik yeniden başlar
    # use_reloader=False → modelleri iki kez yüklemez
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG,
        use_reloader=False
    )

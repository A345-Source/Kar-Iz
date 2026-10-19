# =============================================================================
# KarİZ — Google Earth Engine Bağlantı Modülü (src/gee_baglanti.py)
# =============================================================================
# Bu modül Google Earth Engine'e bağlanmayı yönetir.
# Diğer tüm GEE modülleri bu dosyayı import eder.
# =============================================================================

import ee
import sys
import os

# config klasörünü Python yoluna ekle (import edebilmek için)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.ayarlar import GEE_PROJE_ID


def gee_baslat(sessiz=False):
    """
    Google Earth Engine'i başlatır.
    
    Parametreler:
        sessiz (bool): True ise başarı mesajı yazdırmaz
    
    Dönüş:
        bool: Bağlantı başarılı ise True, değilse False
    
    Nasıl çalışır:
        GEE'ye bağlanmak için önce kimlik doğrulaması (authentication) gerekir.
        Bu genellikle ilk çalıştırmada yapılır ve bir credential dosyası oluşturur.
        Sonraki çalıştırmalarda bu dosya otomatik kullanılır.
    """
    try:
        # ee.Initialize() → GEE API'yi başlatır
        # project parametresi → hangi Google Cloud projesinin kullanılacağını belirtir
        ee.Initialize(project=GEE_PROJE_ID)
        
        if not sessiz:
            print(f"✅ Google Earth Engine bağlantısı başarılı!")
            print(f"   Proje: {GEE_PROJE_ID}")
        
        return True
        
    except ee.EEException as e:
        # GEE'ye özgü hata: genellikle authentication sorunu
        print(f"❌ GEE Bağlantı Hatası: {e}")
        print("   Çözüm: Terminal'de şunu çalıştırın: earthengine authenticate")
        return False
        
    except Exception as e:
        # Genel hata
        print(f"❌ Beklenmedik hata: {e}")
        return False


def gee_kimlik_dogrula():
    """
    GEE kimlik doğrulaması yapar.
    Tarayıcı açılır, Google hesabınızla giriş yaparsınız.
    İlk kurulumda bir kez çalıştırılır.
    """
    try:
        print("🌐 Tarayıcı açılıyor — Google hesabınızla giriş yapın...")
        ee.Authenticate()
        print("✅ Kimlik doğrulama başarılı!")
        print("   Artık gee_baslat() fonksiyonunu kullanabilirsiniz.")
    except Exception as e:
        print(f"❌ Kimlik doğrulama hatası: {e}")


def gee_test():
    """
    GEE bağlantısını test eder — Türkiye sınırlarını çekerek kontrol eder.
    
    Dönüş:
        dict veya None: Türkiye özellik bilgileri veya hata durumunda None
    """
    try:
        # FAO/GAUL veri setinden Türkiye sınırlarını çek
        turkiye = (ee.FeatureCollection("FAO/GAUL/2015/level0")
                   .filter(ee.Filter.eq('ADM0_NAME', 'Turkey')))
        
        # .getInfo() → GEE sunucusundan veriyi yerel bilgisayara indirir
        # Bu işlem birkaç saniye sürebilir (internet bağlantısı gerektirir)
        bilgi = turkiye.first().getInfo()
        
        ulke_adi = bilgi['properties']['ADM0_NAME']
        print(f"✅ GEE Test Başarılı — Veri alındı: {ulke_adi}")
        return bilgi
        
    except Exception as e:
        print(f"❌ GEE Test Hatası: {e}")
        return None


# Doğrudan çalıştırılırsa test yap
if __name__ == "__main__":
    print("=" * 50)
    print("KarİZ — GEE Bağlantı Testi")
    print("=" * 50)
    
    if gee_baslat():
        gee_test()

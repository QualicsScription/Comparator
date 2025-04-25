import os
import logging
from datetime import datetime

# Loglama ayarları
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'setup_log_{timestamp}.txt'),
        logging.StreamHandler()
    ]
)

def create_directory_structure():
    """Proje klasör yapısını oluşturur"""
    directories = [
        # Ana klasörler
        "main/src/ui",
        "main/src/core",
        "main/src/utils",
        "main/src/config",
        "main/resources/images",
        "main/resources/icons",
        "main/resources/themes",
        "main/docs",
        
        # Geliştirici klasörleri
        "dev/tests/unit",
        "dev/tests/integration",
        "dev/tests/test_data",
        "dev/tools/benchmarks",
        "dev/tools/scripts",
        "dev/docs/api",
        "dev/docs/architecture",
        "dev/reports/performance",
        "dev/reports/analysis",
        
        # Eski dosyalar
        "old/v1",
        "old/v2",
        "old/archive"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"Klasör oluşturuldu: {directory}")
        except Exception as e:
            logging.error(f"Klasör oluşturma hatası ({directory}): {e}")

if __name__ == "__main__":
    logging.info("Klasör yapısı oluşturuluyor...")
    create_directory_structure()
    logging.info("Klasör yapısı oluşturuldu!")

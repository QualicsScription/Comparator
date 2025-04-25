import os

def create_main_files():
    # main.py içeriği
    main_content = """from main.src.ui.main_window import MainWindow

def main():
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()"""

    # main_window.py içeriği
    main_window_content = """import customtkinter as ctk
from ..core.comparator import FileComparator

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("File Comparator")
        self.geometry("800x600")
        self.setup_ui()
        
    def setup_ui(self):
        # Sol panel
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Sağ panel
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Dosya seçim butonları
        self.btn_select_file1 = ctk.CTkButton(self.left_frame, text="Dosya 1 Seç", command=self.select_file1)
        self.btn_select_file1.pack(pady=10)
        
        self.btn_select_file2 = ctk.CTkButton(self.right_frame, text="Dosya 2 Seç", command=self.select_file2)
        self.btn_select_file2.pack(pady=10)
        
        # Karşılaştırma butonu
        self.btn_compare = ctk.CTkButton(self, text="Karşılaştır", command=self.compare_files)
        self.btn_compare.pack(side="bottom", pady=20)
    
    def select_file1(self):
        # Dosya seçim işlemi
        pass
    
    def select_file2(self):
        # Dosya seçim işlemi
        pass
    
    def compare_files(self):
        # Karşılaştırma işlemi
        pass"""

    # comparator.py içeriği
    comparator_content = """from ..utils.helpers import get_file_info, calculate_similarity

class FileComparator:
    def __init__(self):
        self.file1_path = None
        self.file2_path = None
        self.comparison_results = {}
    
    def set_files(self, file1_path, file2_path):
        self.file1_path = file1_path
        self.file2_path = file2_path
    
    def compare(self):
        if not self.file1_path or not self.file2_path:
            raise ValueError("Dosya yolları ayarlanmamış!")
        
        # Dosya bilgilerini al
        file1_info = get_file_info(self.file1_path)
        file2_info = get_file_info(self.file2_path)
        
        # Karşılaştırma sonuçlarını hesapla
        self.comparison_results = {
            'similarity': calculate_similarity(file1_info, file2_info),
            'file1_info': file1_info,
            'file2_info': file2_info
        }
        
        return self.comparison_results"""

    # helpers.py içeriği
    helpers_content = """import os
from datetime import datetime

def get_file_info(filepath):
    \"\"\"Dosya hakkında temel bilgileri döndürür.\"\"\"
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dosya bulunamadı: {filepath}")
        
    stats = os.stat(filepath)
    return {
        'size': stats.st_size,
        'created': datetime.fromtimestamp(stats.st_ctime),
        'modified': datetime.fromtimestamp(stats.st_mtime),
        'name': os.path.basename(filepath),
        'extension': os.path.splitext(filepath)[1]
    }

def calculate_similarity(file1_info, file2_info):
    \"\"\"İki dosya arasındaki benzerlik oranını hesaplar.\"\"\"
    # Basit bir benzerlik hesaplaması
    similar_points = 0
    total_points = 0
    
    # Boyut karşılaştırması
    if abs(file1_info['size'] - file2_info['size']) < 100:
        similar_points += 1
    total_points += 1
    
    # Uzantı karşılaştırması
    if file1_info['extension'] == file2_info['extension']:
        similar_points += 1
    total_points += 1
    
    return (similar_points / total_points) * 100 if total_points > 0 else 0"""

    # Dosyaları oluştur
    files = {
        './main.py': main_content,  # Ana dizinde oluştur
        './main/src/ui/main_window.py': main_window_content,
        './main/src/core/comparator.py': comparator_content,
        './main/src/utils/helpers.py': helpers_content
    }

    for filepath, content in files.items():
        # Eğer dosya ana dizinde değilse klasör yolunu oluştur
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
            
        # Dosyayı oluştur
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"{filepath} oluşturuldu")

if __name__ == "__main__":
    create_main_files()

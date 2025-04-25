import customtkinter as ctk
from src.core.comparator import FileComparator

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
        pass
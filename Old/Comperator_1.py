# -*- coding: utf-8 -*-
# SOLIDWORKS DETAYLI KARŞILAŞTIRICI v7.0
# KRİTER BAZLI ANALİZ

import os
import sys
import hashlib
import difflib
import ctypes
import logging
import threading
import time
from tkinter import *
from tkinter import ttk, filedialog, messagebox

# Loglama sistemini başlat
logging.basicConfig(
    filename='comparator.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def hide_console():
    """Konsol penceresini gizler (Windows platformunda)"""
    try:
        # Windows için
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            ctypes.windll.user32.ShowWindow(whnd, 0)
    except Exception as e:
        logging.error(f"Konsol gizleme başarısız: {e}")

class FileComparator:
    """Gelişmiş kriter bazlı karşılaştırma sınıfı"""
    
    @staticmethod
    def compare_metadata(file1, file2):
        """Metadata benzerlik kontrolü"""
        try:
            stat1 = os.stat(file1)
            stat2 = os.stat(file2)
            
            # Son değişiklik tarihi (5 saniye tolerans)
            time_diff = abs(stat1.st_mtime - stat2.st_mtime) < 5
            
            # Dosya boyutu
            size_match = stat1.st_size == stat2.st_size
            
            return time_diff and size_match
        except:
            return False

    @staticmethod
    def compare_hash(file1, file2):
        """Hash değeri karşılaştırma"""
        def calculate_hash(file_path):
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        
        return calculate_hash(file1) == calculate_hash(file2)

    @staticmethod
    def compare_content(file1, file2):
        """İçerik karşılaştırma (metadata hariç)"""
        try:
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                content1 = f1.read()
                content2 = f2.read()
                
                # Son 1024 byte'ı atla (SolidWorks metadata)
                return content1[:-1024] == content2[:-1024]
        except:
            return False

    @staticmethod
    def full_compare(file1, file2):
        """Tüm kriterleri kontrol et"""
        return {
            'Metadata': FileComparator.compare_metadata(file1, file2),
            'Hash': FileComparator.compare_hash(file1, file2),
            'İçerik': FileComparator.compare_content(file1, file2),
            'Boyut': os.path.getsize(file1) == os.path.getsize(file2)
        }

class CompareApp(Tk):
    """Yeni arayüz ile karşılaştırma uygulaması"""
    
    def __init__(self):
        super().__init__()
        self.title("SolidWorks Detaylı Karşılaştırıcı v7.0")
        self.geometry("1400x800")
        
        # Değişkenler
        self.is_running = False
        self.results = []
        
        # Arayüzü oluştur
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        hide_console()

    def setup_ui(self):
        """Arayüz bileşenlerini oluştur"""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Kontrol paneli
        control_frame = ttk.LabelFrame(main_frame, text=" Kontrol Panel ", padding=10)
        control_frame.pack(fill=X, pady=5)
        
        ttk.Label(control_frame, text="Klasör:").grid(row=0, column=0, padx=5)
        self.folder_path = StringVar()
        ttk.Entry(control_frame, textvariable=self.folder_path, width=80).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="📁 Gözat", command=self.browse_folder).grid(row=0, column=2, padx=5)
        
        # İlerleme çubuğu
        self.progress = ttk.Progressbar(main_frame, orient=HORIZONTAL, mode='determinate')
        self.progress.pack(fill=X, pady=10)
        
        # Sonuçlar tablosu
        result_frame = ttk.LabelFrame(main_frame, text=" Detaylı Karşılaştırma Sonuçları ", padding=10)
        result_frame.pack(fill=BOTH, expand=True)
        
        columns = (
            'Dosya 1', 'Dosya 2', 
            'Metadata', 'Hash', 
            'İçerik', 'Boyut',
            'Sonuç'
        )
        
        self.tree = ttk.Treeview(result_frame, columns=columns, show='headings')
        
        # Sütun başlıkları
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor=CENTER)
        
        self.tree.column('Dosya 1', width=200)
        self.tree.column('Dosya 2', width=200)
        self.tree.column('Sonuç', width=200)
        
        # Scrollbar'lar
        vsb = ttk.Scrollbar(result_frame, orient=VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(result_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Yerleşim
        self.tree.grid(row=0, column=0, sticky=NSEW)
        vsb.grid(row=0, column=1, sticky=NS)
        hsb.grid(row=1, column=0, sticky=EW)
        
        # Grid ayarlamaları
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
        # Durum çubuğu
        self.status_var = StringVar(value="Hazır")
        ttk.Label(main_frame, textvariable=self.status_var).pack(fill=X)
        
        # Butonlar
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="▶️ Başlat", command=self.start_comparison).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="⏹ Durdur", command=self.stop_comparison).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 CSV Kaydet", command=self.export_results).pack(side=LEFT, padx=5)

    def browse_folder(self):
        folder = filedialog.askdirectory(title="SolidWorks Dosyalarını Seçin")
        if folder:
            self.folder_path.set(folder)

    def start_comparison(self):
        if self.is_running: return
        
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Hata", "Geçerli bir klasör seçin!")
            return
        
        self.is_running = True
        self.clear_results()
        threading.Thread(target=self.run_comparison, args=(folder,), daemon=True).start()

    def run_comparison(self, folder):
        try:
            files = [f for f in os.listdir(folder) 
                    if f.lower().endswith(('.sldprt', '.sldasm', '.slddrw'))]
            
            total = len(files)*(len(files)-1)//2
            processed = 0
            
            for i in range(len(files)):
                if not self.is_running: break
                for j in range(i+1, len(files)):
                    if not self.is_running: break
                    
                    file1 = os.path.join(folder, files[i])
                    file2 = os.path.join(folder, files[j])
                    
                    # Karşılaştırma yap
                    results = FileComparator.full_compare(file1, file2)
                    
                    # Sonuç değerlendirme
                    match_count = sum(results.values())
                    if match_count == 4:
                        final_result = "Tam Eşleşme"
                    elif match_count > 0:
                        final_result = f"Kısmi Eşleşme ({match_count}/4)"
                    else:
                        final_result = "Eşleşme Yok"
                    
                    # Sonuçları kaydet
                    self.results.append({
                        'Dosya 1': files[i],
                        'Dosya 2': files[j],
                        'Metadata': 'Evet' if results['Metadata'] else 'Hayır',
                        'Hash': 'Evet' if results['Hash'] else 'Hayır',
                        'İçerik': 'Evet' if results['İçerik'] else 'Hayır',
                        'Boyut': 'Evet' if results['Boyut'] else 'Hayır',
                        'Sonuç': final_result
                    })
                    
                    processed += 1
                    self.update_ui(processed, total)
            
            self.status_var.set(f"Tamamlandı! {processed} karşılaştırma yapıldı")
            
        except Exception as e:
            messagebox.showerror("Hata", str(e))
            logging.error(f"Karşılaştırma hatası: {e}")
        finally:
            self.is_running = False

    def update_ui(self, processed, total):
        # Thread-safe UI güncelleme
        progress_value = processed/total*100 if total > 0 else 0
        
        def update():
            self.progress['value'] = progress_value
            self.status_var.set(f"İşlem: {processed}/{total} ({progress_value:.1f}%)")
            self.show_results()
            
        self.after(0, update)

    def show_results(self):
        self.tree.delete(*self.tree.get_children())
        for res in self.results:
            self.tree.insert('', 'end', values=(
                res['Dosya 1'],
                res['Dosya 2'],
                res['Metadata'],
                res['Hash'],
                res['İçerik'],
                res['Boyut'],
                res['Sonuç']
            ))

    def stop_comparison(self):
        self.is_running = False
        self.status_var.set("Durduruldu")

    def clear_results(self):
        self.tree.delete(*self.tree.get_children())
        self.results = []
        self.progress['value'] = 0

    def export_results(self):
        if not self.results:
            messagebox.showwarning("Uyarı", "Dışa aktarılacak veri yok!")
            return
        
        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dosyaları", "*.csv")]
        )
        
        if file:
            try:
                import pandas as pd
                df = pd.DataFrame(self.results)
                df.to_csv(file, index=False, encoding='utf-8-sig')
                messagebox.showinfo("Başarılı", "Sonuçlar kaydedildi!")
            except Exception as e:
                messagebox.showerror("Hata", f"CSV dışa aktarma hatası: {e}")
                logging.error(f"CSV dışa aktarma hatası: {e}")

    def on_close(self):
        if self.is_running:
            if messagebox.askyesno("Çıkış", "Karşılaştırma devam ediyor. Çıkmak istediğinize emin misiniz?"):
                self.destroy()
        else:
            self.destroy()

if __name__ == "__main__":
    try:
        app = CompareApp()
        app.mainloop()
    except Exception as e:
        logging.error(f"Uygulama hatası: {e}")
        messagebox.showerror("Kritik Hata", f"Uygulama başlatılamadı: {e}")

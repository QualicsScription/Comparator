# -*- coding: utf-8 -*-
# GELİŞMİŞ DOSYA KARŞILAŞTIRICI v2.2
# MODERN ARAYÜZ VE TÜM ÖZELLİKLERLE

import os
import sys
import subprocess
import hashlib
import difflib
import logging
import threading
import time
import zipfile
import binascii
import numpy as np
from datetime import datetime
from collections import Counter
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import webbrowser

def install_deps():
    required = [
        'customtkinter',
        'matplotlib',
        'pandas',
        'pillow',
        'numpy',
        'python-docx',
        'openpyxl'
    ]

    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install'] + required,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"⚠️ Bağımlılık yükleme hatası: {str(e)}")
        print("⚠️ Bazı özellikler çalışmayabilir!")

install_deps()

# Loglama sistemini başlat
logging.basicConfig(
    filename='advanced_comparator.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AdvancedFileComparator:
    def __init__(self):
        self.supported_extensions = {
            'solidworks': ['.sldprt', '.sldasm', '.slddrw'],
            'cad': ['.step', '.stp', '.iges', '.igs', '.stl', '.obj', '.dxf'],
            'document': ['.docx', '.xlsx', '.pdf', '.txt'],
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'],
            'all': []
        }
        for exts in self.supported_extensions.values():
            self.supported_extensions['all'].extend(exts)

    @staticmethod
    def compare_metadata(file1, file2):
        try:
            stat1 = os.stat(file1)
            stat2 = os.stat(file2)
            time_diff = abs(stat1.st_mtime - stat2.st_mtime) < 10
            size1, size2 = stat1.st_size, stat2.st_size
            min_size = min(size1, size2)
            max_size = max(size1, size2)
            size_similarity = min_size / max_size if max_size != 0 else 0
            metadata_score = ((1 if time_diff else 0) + size_similarity) / 2 * 100
            return metadata_score
        except Exception as e:
            logging.error(f"Metadata hatası: {e}")
            return 0

    @staticmethod
    def compare_hash(file1, file2):
        try:
            def calculate_full_hash(file_path):
                hasher = hashlib.md5()
                with open(file_path, 'rb') as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
                return hasher.hexdigest()

            return 100 if calculate_full_hash(file1) == calculate_full_hash(file2) else 0
        except Exception as e:
            logging.error(f"Hash hatası: {e}")
            return 0

    @staticmethod
    def compare_binary_content(file1, file2):
        try:
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                content1 = f1.read()
                content2 = f2.read()
                similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
                return 100 if similarity >= 0.95 else 0
        except Exception as e:
            logging.error(f"İçerik karşılaştırma hatası: {e}")
            return 0

    @staticmethod
    def analyze_file_structure(file1, file2):
        try:
            file_ext = os.path.splitext(file1)[1].lower()

            if file_ext in ['.sldprt', '.sldasm', '.slddrw']:
                try:
                    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                        f1.seek(1024)  # Tasarım verilerinin başlangıç offset'i
                        f2.seek(1024)
                        return 100 if f1.read(4096) == f2.read(4096) else 0
                except Exception as e:
                    logging.error(f"SolidWorks yapı analizi hatası: {e}")
                    return 0

            elif file_ext in ['.docx', '.xlsx']:
                try:
                    with zipfile.ZipFile(file1) as z1, zipfile.ZipFile(file2) as z2:
                        important_files = {
                            '.docx': ['word/document.xml', 'docProps/core.xml'],
                            '.xlsx': ['xl/worksheets/sheet1.xml', 'docProps/core.xml']
                        }
                        files_to_check = important_files.get(file_ext, [])
                        for fname in files_to_check:
                            if z1.read(fname) != z2.read(fname):
                                return 0
                        return 100
                except:
                    return 0
            else:
                return 0
        except Exception as e:
            logging.error(f"Yapı analizi hatası: {e}")
            return 0

    @staticmethod
    def frequency_analysis(file1, file2, sample_size=1024*512):
        """Dosya içeriğinin frekans analizi"""
        try:
            # Her iki dosyadan örnek al
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                # İlk sample_size byte'ı oku
                sample1 = f1.read(sample_size)
                sample2 = f2.read(sample_size)

                # Byte frekans analizi
                freq1 = Counter(sample1)
                freq2 = Counter(sample2)

                # Frekans vektörleri oluştur
                vector1 = [freq1.get(b, 0) / len(sample1) if len(sample1) > 0 else 0 for b in range(256)]
                vector2 = [freq2.get(b, 0) / len(sample2) if len(sample2) > 0 else 0 for b in range(256)]

                # Kosinüs benzerliği hesapla
                dot_product = sum(v1 * v2 for v1, v2 in zip(vector1, vector2))
                magnitude1 = sum(v1 * v1 for v1 in vector1) ** 0.5
                magnitude2 = sum(v2 * v2 for v2 in vector2) ** 0.5

                if magnitude1 == 0 or magnitude2 == 0:
                    return 0

                return (dot_product / (magnitude1 * magnitude2)) * 100
        except Exception as e:
            logging.error(f"Frekans analizi hatası: {e}")
            return 0

    @staticmethod
    def full_compare(file1, file2, detailed=True):
        try:
            results = {
                'Metadata': AdvancedFileComparator.compare_metadata(file1, file2),
                'Hash': AdvancedFileComparator.compare_hash(file1, file2),
                'İçerik': AdvancedFileComparator.compare_binary_content(file1, file2),
                'Yapı': AdvancedFileComparator.analyze_file_structure(file1, file2),
                'Frekans': AdvancedFileComparator.frequency_analysis(file1, file2)
            }

            weights = {
                'Metadata': 0.1,
                'Hash': 0.15,
                'İçerik': 0.35,
                'Yapı': 0.25,
                'Frekans': 0.15
            }

            weighted_total = sum(results[key] * weights[key] for key in results)

            if weighted_total >= 95:
                similarity_category = "Tam Eşleşme"
            elif weighted_total >= 85:
                similarity_category = "Çok Yüksek Benzerlik"
            elif weighted_total >= 70:
                similarity_category = "Yüksek Benzerlik"
            elif weighted_total >= 50:
                similarity_category = "Orta Benzerlik"
            elif weighted_total >= 30:
                similarity_category = "Düşük Benzerlik"
            else:
                similarity_category = "Benzerlik Yok"

            if detailed:
                return {
                    'Skorlar': results,
                    'Toplam': weighted_total,
                    'Sonuç': similarity_category
                }
            else:
                return weighted_total
        except Exception as e:
            logging.error(f"Karşılaştırma hatası: {e}")
            if detailed:
                return {
                    'Skorlar': {k:0 for k in ['Metadata', 'Hash', 'İçerik', 'Yapı']},
                    'Toplam': 0,
                    'Sonuç': "Hata"
                }
            else:
                return 0

class ModernFileComparator(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gelişmiş Dosya Karşılaştırıcı v2.2")
        self.geometry("1400x800")
        self.minsize(1000, 700)
        self.after_handles = []
        self.textboxes = []  # Textbox widget'larını takip etmek için

        # CustomTkinter ayarları
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

        # Uygulama değişkenleri
        self.is_running = False
        self.results = []
        self.comparator = AdvancedFileComparator()
        self.current_sort_column = None
        self.current_sort_reverse = False
        self.selected_file_types = ctk.StringVar(value="solidworks")
        self.min_similarity = ctk.IntVar(value=0)

        # Arayüzü oluştur
        self.setup_ui()

        # Uygulama kapatıldığında çağrılacak fonksiyon
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Textbox'ların scrollbar güncelleme süresini artır
        self._configure_textboxes()

    def clear_results(self):
        """Tüm sonuçları temizle"""
        self.results = []

        # Tablo sonuçlarını temizle
        if hasattr(self, 'tree'):
            try:
                for item in self.tree.get_children():
                    self.tree.delete(item)
            except Exception:
                pass

        # İlerleme çubuğunu sıfırla
        if hasattr(self, 'progress'):
            try:
                self.progress.set(0)
            except Exception:
                pass

        # Durum metnini güncelle
        if hasattr(self, 'status_var'):
            try:
                self.status_var.set("Hazır")
            except Exception:
                pass

        # Görsel analizi sıfırla
        if hasattr(self, 'ax') and hasattr(self, 'canvas'):
            try:
                self.ax.clear()
                self.canvas.draw()
            except Exception:
                pass

        # İstatistik metnini temizle
        if hasattr(self, 'stats_text'):
            try:
                self.stats_text.delete("1.0", "end")
            except Exception:
                pass

        # Detay panellerini temizle
        for attr in ['file1_info', 'file2_info', 'comparison_text']:
            if hasattr(self, attr):
                try:
                    getattr(self, attr).delete("1.0", "end")
                except Exception:
                    pass

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Kontrol Paneli
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(fill="x", pady=5)

        # Klasör Seçimi
        ctk.CTkLabel(control_frame, text="Klasör:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.folder_path = ctk.CTkEntry(control_frame, width=500)
        self.folder_path.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(control_frame, text="📁 Gözat", command=self.browse_folder, width=100).grid(row=0, column=2, padx=5)

        # Dosya Tipi Seçimi
        file_types = {
            'solidworks': 'SolidWorks',
            'cad': 'CAD',
            'document': 'Döküman',
            'image': 'Görsel',
            'all': 'Tüm Dosyalar'
        }
        for i, (value, text) in enumerate(file_types.items()):
            ctk.CTkRadioButton(control_frame, text=text, variable=self.selected_file_types, value=value).grid(
                row=1, column=i, padx=5, pady=5, sticky="w")

        # Filtre Ayarları
        filter_frame = ctk.CTkFrame(control_frame)
        filter_frame.grid(row=1, column=4, padx=5, pady=5, sticky="e")
        ctk.CTkLabel(filter_frame, text="Min. Benzerlik:").pack(side="left", padx=5)
        ctk.CTkEntry(filter_frame, textvariable=self.min_similarity, width=50).pack(side="left", padx=5)
        ctk.CTkLabel(filter_frame, text="%").pack(side="left", padx=5)

        # İlerleme Çubuğu
        self.progress = ctk.CTkProgressBar(main_frame, orientation="horizontal")
        self.progress.pack(fill="x", pady=5)
        self.progress.set(0)
        self.status_var = ctk.StringVar(value="Hazır")
        ctk.CTkLabel(main_frame, textvariable=self.status_var).pack(pady=5)

        # Sonuçlar Paneli
        self.notebook = ctk.CTkTabview(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=10)

        # Tablo Görünümü
        self.table_tab = self.notebook.add("Tablo Görünümü")
        self.setup_table_view()

        # Görsel Analiz
        self.visual_tab = self.notebook.add("Görsel Analiz")
        self.setup_visual_analysis()

        # Detaylı Analiz
        self.detail_tab = self.notebook.add("Detaylı Analiz")
        self.setup_detail_panel()

        # Alt Butonlar
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=10, fill="x", expand=True)
        ctk.CTkButton(button_frame, text="▶️ Başlat", command=self.start_comparison).grid(row=0, column=0, padx=5)
        ctk.CTkButton(button_frame, text="⏹ Durdur", command=self.stop_comparison).grid(row=0, column=1, padx=5)
        ctk.CTkButton(button_frame, text="🗑️ Temizle", command=self.clear_results).grid(row=0, column=2, padx=5)
        ctk.CTkButton(button_frame, text="📊 Rapor", command=self.generate_report).grid(row=0, column=3, padx=5)
        ctk.CTkButton(button_frame, text="💾 CSV", command=self.export_results).grid(row=0, column=4, padx=5)
        button_frame.grid_columnconfigure((0,1,2,3,4), weight=1)

    def setup_table_view(self):
        columns = ('Dosya 1', 'Dosya 2', 'Metadata', 'Hash', 'İçerik', 'Yapı', 'Frekans', 'Toplam', 'Sonuç')
        self.tree = ttk.Treeview(self.table_tab, columns=columns, show='headings')

        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            self.tree.column(col, width=100 if col not in ['Dosya 1', 'Dosya 2', 'Sonuç'] else 150)

        self.tree.tag_configure('high', background='#a8e6cf')
        self.tree.tag_configure('medium', background='#dcedc1')
        self.tree.tag_configure('low', background='#ffd3b6')
        self.tree.tag_configure('none', background='#ffaaa5')

        vsb = ttk.Scrollbar(self.table_tab, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.table_tab, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.table_tab.grid_rowconfigure(0, weight=1)
        self.table_tab.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.show_detail_view)

    def show_detail_view(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return

        selected_values = self.tree.item(item, 'values')
        if not selected_values or len(selected_values) < 8:  # Sütun sayısı güncellendi
            return

        selected_files = None
        for res in self.results:
            if (res['Dosya 1'] == selected_values[0] and
                res['Dosya 2'] == selected_values[1]):
                selected_files = res
                break

        if not selected_files:
            return

        self.notebook.set("Detaylı Analiz")
        self.update_file_info(selected_files)
        self.update_comparison_details(selected_files)

    def setup_visual_analysis(self):
        # Matplotlib figürü oluştur
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=80)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.visual_tab)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        # İstatistik metni için textbox
        self.stats_text = self._create_textbox(self.visual_tab, wrap="word")
        self.stats_text.pack(fill="both", expand=True, padx=5, pady=5)

    @staticmethod
    def format_size(size_bytes):
        """Bayt cinsinden boyutu okunabilir formata dönüştür"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def _configure_textboxes(self):
        """Textbox widget'larını yapılandır"""
        # Tüm textbox'ları döngüyle kontrol et
        for textbox in self.textboxes:
            if hasattr(textbox, '_scrollbar_update_time'):
                # Scrollbar güncelleme süresini artır (varsayılan 100ms)
                textbox._scrollbar_update_time = 500  # 500ms'ye çıkar

    def _create_textbox(self, parent, **kwargs):
        """Takip edilen bir textbox oluştur"""
        textbox = ctk.CTkTextbox(parent, **kwargs)
        self.textboxes.append(textbox)
        return textbox

    def setup_detail_panel(self):
        detail_paned = ctk.CTkTabview(self.detail_tab)
        detail_paned.pack(fill="both", expand=True)

        # Dosya Bilgileri
        file_info_tab = detail_paned.add("Dosya Bilgileri")
        file_frame = ctk.CTkFrame(file_info_tab)
        file_frame.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(file_frame, text="Dosya 1:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.file1_info = self._create_textbox(file_frame, wrap="word")
        self.file1_info.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(file_frame, text="Dosya 2:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.file2_info = self._create_textbox(file_frame, wrap="word")
        self.file2_info.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        file_frame.grid_rowconfigure(1, weight=1)
        file_frame.grid_columnconfigure(0, weight=1)
        file_frame.grid_columnconfigure(1, weight=1)

        # Karşılaştırma Detayları
        comparison_tab = detail_paned.add("Karşılaştırma Detayları")
        self.comparison_text = self._create_textbox(comparison_tab, wrap="word")
        self.comparison_text.pack(fill="both", expand=True, padx=5, pady=5)

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Klasör Seçin")
        if folder:
            self.folder_path.delete(0, "end")
            self.folder_path.insert(0, folder)

    def start_comparison(self):
        if self.is_running:
            return

        folder = self.folder_path.get()
        if not os.path.isdir(folder):
            messagebox.showerror("Hata", "Geçerli bir klasör seçin!")
            return

        self.is_running = True
        self.clear_results()
        self.status_var.set("Dosyalar taranıyor...")
        self.progress.set(0)

        threading.Thread(target=self.run_comparison, args=(folder,), daemon=True).start()

    def run_comparison(self, folder):
        try:
            file_type = self.selected_file_types.get()
            min_similarity = self.min_similarity.get()
            extensions = self.comparator.supported_extensions[file_type]

            all_files = [f for f in os.listdir(folder)
                        if os.path.isfile(os.path.join(folder, f)) and
                        (not extensions or os.path.splitext(f)[1].lower() in extensions)]

            total_comparisons = len(all_files) * (len(all_files) - 1) // 2
            processed = 0
            last_update = time.time()
            update_interval = 0.2

            self.results = []

            for i in range(len(all_files)):
                if not self.is_running:
                    break

                file1 = os.path.join(folder, all_files[i])

                for j in range(i + 1, len(all_files)):
                    if not self.is_running:
                        break

                    file2 = os.path.join(folder, all_files[j])
                    comparison_result = self.comparator.full_compare(file1, file2)

                    if comparison_result['Toplam'] >= min_similarity:
                        result_data = {
                            'Dosya 1': all_files[i],
                            'Dosya 2': all_files[j],
                            'Metadata': f"{comparison_result['Skorlar']['Metadata']:.1f}",
                            'Hash': f"{comparison_result['Skorlar']['Hash']:.1f}",
                            'İçerik': f"{comparison_result['Skorlar']['İçerik']:.1f}",
                            'Yapı': f"{comparison_result['Skorlar']['Yapı']:.1f}",
                            'Frekans': f"{comparison_result['Skorlar']['Frekans']:.1f}",
                            'Toplam': f"{comparison_result['Toplam']:.1f}",
                            'Sonuç': comparison_result['Sonuç'],
                            'Path1': file1,
                            'Path2': file2
                        }

                        self.results.append(result_data)

                    processed += 1

                    if time.time() - last_update > update_interval:
                        progress_value = processed / total_comparisons * 100

                        # İlerleme çubuğunu güncelle
                        try:
                            handle = self.after(0, lambda p=progress_value: self.progress.set(p / 100))
                            self.after_handles.append(handle)
                        except Exception as e:
                            logging.error(f"İlerleme çubuğu güncelleme hatası: {e}")

                        # Durum metnini güncelle
                        try:
                            status_text = f"İşlem: {processed}/{total_comparisons} ({progress_value:.1f}%)"
                            handle = self.after(0, lambda s=status_text: self.status_var.set(s))
                            self.after_handles.append(handle)
                        except Exception as e:
                            logging.error(f"Durum metni güncelleme hatası: {e}")

                        last_update = time.time()

            # Sonuçları göster
            try:
                handle = self.after(0, self.show_results)
                self.after_handles.append(handle)
            except Exception as e:
                logging.error(f"Sonuçları gösterme hatası: {e}")

            # Görsel analizi güncelle
            try:
                handle = self.after(0, self.update_visual_analysis)
                self.after_handles.append(handle)
            except Exception as e:
                logging.error(f"Görsel analiz güncelleme hatası: {e}")

            # Durum metnini güncelle
            try:
                status_text = f"Tamamlandı! {len(self.results)} benzer dosya çifti bulundu."
                handle = self.after(0, lambda s=status_text: self.status_var.set(s))
                self.after_handles.append(handle)
            except Exception as e:
                logging.error(f"Durum metni güncelleme hatası: {e}")

            # İlerleme çubuğunu tamamla
            try:
                handle = self.after(0, lambda: self.progress.set(1))
                self.after_handles.append(handle)
            except Exception as e:
                logging.error(f"İlerleme çubuğu güncelleme hatası: {e}")

        except Exception as e:
            # Hata mesajını göster
            try:
                error_msg = str(e)
                handle = self.after(0, lambda msg=error_msg: messagebox.showerror("Hata", msg))
                self.after_handles.append(handle)
            except Exception:
                pass

            # Hatayı logla
            logging.error(f"Karşılaştırma hatası: {e}")
        finally:
            # İşlemi durdur
            self.is_running = False

    def stop_comparison(self):
        """Karşılaştırma işlemini durdur"""
        # Önce işlemi durdur
        self.is_running = False

        # Tüm bekleyen after işlemlerini iptal et
        try:
            for handle in self.after_handles:
                try:
                    self.after_cancel(handle)
                except Exception:
                    pass
            self.after_handles = []
        except Exception:
            pass

        # Durum metnini güncelle
        try:
            if hasattr(self, 'status_var'):
                self.status_var.set("İşlem durduruldu!")
        except Exception:
            pass

    def update_file_info(self, file_data):
        """Dosya bilgi panelini güncelle"""
        try:
            # Dosya yollarını al
            file1_path = file_data['Path1']
            file2_path = file_data['Path2']

            # Temel dosya bilgilerini topla
            def get_file_info(file_path):
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                file_ext = os.path.splitext(file_path)[1].lower()

                info = f"📄 {file_name}\n"
                info += f"📏 Boyut: {self.format_size(file_size)}\n"
                info += f"🕒 Son Değişiklik: {file_modified}\n"
                info += f"📁 Konum: {os.path.dirname(file_path)}\n\n"

                # Dosya türüne özel bilgiler
                if file_ext in ['.sldprt', '.sldasm', '.slddrw']:
                    info += "📊 SolidWorks Dosya Bilgileri:\n"
                    try:
                        with open(file_path, 'rb') as f:
                            header = f.read(256)
                            if b'SldWorks' in header or b'SOLIDWORKS' in header:
                                info += "   ✓ Geçerli SolidWorks imzası\n"
                            binary_info = binascii.hexlify(header[:16]).decode('ascii')
                            info += f"   🔑 Dosya İmzası: {binary_info}...\n"
                    except:
                        info += "   ❌ Dosya başlığı okunamadı\n"

                # Genel dosya özellikleri
                try:
                    # Dosyanın ilk 1KB'lık kısmını al
                    with open(file_path, 'rb') as f:
                        content = f.read(1024)

                    # ASCII metin oranı
                    ascii_ratio = sum(1 for b in content if 32 <= b <= 126) / len(content) if content else 0
                    info += f"📝 ASCII Metin Oranı: {ascii_ratio:.1%}\n"

                    # Binary/text dosya tahmini
                    if ascii_ratio > 0.75:
                        info += "✓ Muhtemelen metin dosyası\n"
                    else:
                        info += "✓ Muhtemelen binary dosya\n"
                except:
                    pass

                return info

            # Dosya bilgilerini göster
            self.file1_info.delete("1.0", "end")
            self.file1_info.insert("end", get_file_info(file1_path))

            self.file2_info.delete("1.0", "end")
            self.file2_info.insert("end", get_file_info(file2_path))

        except Exception as e:
            messagebox.showerror("Hata", f"Dosya bilgileri alınamadı: {str(e)}")

    def update_comparison_details(self, file_data):
        """Karşılaştırma detay panelini güncelle"""
        try:
            self.comparison_text.delete("1.0", "end")

            details = f"""🔍 DETAYLI KARŞILAŞTIRMA ANALİZİ 🔍
=======================================

📑 Karşılaştırılan Dosyalar:
    - Dosya 1: {file_data['Dosya 1']}
    - Dosya 2: {file_data['Dosya 2']}

📊 Benzerlik Sonucu: {file_data['Sonuç']} ({file_data['Toplam']}%)

=======================================

📈 KRİTER BAZLI BENZERLIK ANALİZİ:

1️⃣ Metadata Benzerliği: {file_data['Metadata']}%
   - Bu kriter dosya boyutu ve değiştirilme tarihi gibi meta verileri analiz eder.
   - Yüksek benzerlik, dosyaların aynı zamanda veya yakın süreçte oluşturulduğunu gösterir.

2️⃣ Hash Benzerliği: {file_data['Hash']}%
   - Bu kriter dosyaların içeriğinin tam eşleşip eşleşmediğini kontrol eder.
   - 100% değeri, dosyaların birebir aynı olduğunu gösterir.

3️⃣ İçerik Benzerliği: {file_data['İçerik']}%
   - Bu kriter dosya içeriğinin benzerliğini analiz eder.
   - Yüksek değer, dosyaların içeriğinin çok benzer olduğunu gösterir.

4️⃣ Yapı Benzerliği: {file_data['Yapı']}%
   - Bu kriter dosya yapısını ve formatını analiz eder.
   - Özellikle CAD ve ofis dosyaları için önemlidir.

5️⃣ Frekans Benzerliği: {file_data['Frekans']}%
   - Bu kriter dosya içeriğindeki byte frekans dağılımını analiz eder.
   - Benzer içeriğe sahip dosyalar benzer frekans dağılımı gösterir.
"""

            # Dosyaların ne kadar benzer olduğuna dair yorum
            total_score = float(file_data['Toplam'])
            if total_score >= 95:
                details += """

Bu dosyalar neredeyse birebir aynıdır. Aynı dosyanın farklı adlarla kaydedilmiş kopyaları olabilir
veya çok küçük değişiklikler içerebilir. Bunlar:
- "Farklı Kaydet" ile oluşturulmuş kopyalar
- Aynı dosyanın farklı konumlarda saklanması
- Metadata değişikliği dışında içeriği aynı olan dosyalar
"""
            elif total_score >= 85:
                details += """

Bu dosyalar çok yüksek benzerlik göstermektedir. Büyük olasılıkla:
- Birbirinin biraz değiştirilmiş versiyonları
- Aynı parçanın küçük revizyonları
- Son ölçü ayarlamaları yapılmış kopyalar
- Dosya formatı dönüşümü yapılmış versiyonlar
"""
            elif total_score >= 70:
                details += """

Bu dosyalar yüksek benzerlik göstermektedir. Muhtemelen:
- Aynı temel tasarımın farklı versiyonları
- Benzer parçaların farklı varyasyonları
- Aynı şablondan türetilmiş dosyalar
"""
            elif total_score >= 50:
                details += """

Bu dosyalar orta derecede benzerlik göstermektedir. Bunlar:
- Benzer yapıda ancak farklı içeriğe sahip dosyalar
- Aynı tür dosyalar ancak farklı tasarımlar
- Ortak bileşenleri olan farklı dosyalar
"""
            elif total_score >= 30:
                details += """

Bu dosyalar düşük benzerlik göstermektedir. Bunlar:
- Aynı formatta ancak farklı içeriğe sahip dosyalar
- Bazı ortak özellikleri olan farklı dosyalar
"""
            else:
                details += """

Bu dosyalar arasında anlamlı bir benzerlik bulunmamaktadır. Bunlar:
- Tamamen farklı içeriğe sahip dosyalar
- Sadece format olarak benzer dosyalar
"""

            self.comparison_text.insert("end", details)

        except Exception as e:
            messagebox.showerror("Hata", f"Karşılaştırma detayları alınamadı: {str(e)}")

    def update_visual_analysis(self):
        """Görsel analiz panelini güncelle"""
        if not self.results:
            return

        # Grafiği temizle
        self.ax.clear()

        # Veri hazırlığı
        scores = [float(r['Toplam']) for r in self.results]
        similarity_ranges = {
            '90-100': 0,
            '70-90': 0,
            '50-70': 0,
            '30-50': 0,
            '0-30': 0
        }

        # Verileri kategorize et
        for score in scores:
            if score >= 90:
                similarity_ranges['90-100'] += 1
            elif score >= 70:
                similarity_ranges['70-90'] += 1
            elif score >= 50:
                similarity_ranges['50-70'] += 1
            elif score >= 30:
                similarity_ranges['30-50'] += 1
            else:
                similarity_ranges['0-30'] += 1

        # Pasta grafiği çiz
        if sum(similarity_ranges.values()) > 0:
            labels = []
            sizes = []
            colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336']
            explode = (0.1, 0, 0, 0, 0)  # Yüksek benzerlik dilimini vurgula

            for i, (label, count) in enumerate(similarity_ranges.items()):
                if count > 0:
                    labels.append(f"{label}% ({count})")
                    sizes.append(count)

            if sizes:
                self.ax.pie(sizes, explode=explode[:len(sizes)], labels=labels, colors=colors[:len(sizes)],
                        autopct='%1.1f%%', shadow=True, startangle=90)
                self.ax.axis('equal')  # Dairesel görünüm için
                self.ax.set_title('Benzerlik Dağılımı')

                # Grafiği güncelle
                self.canvas.draw()

        # İstatistik metnini güncelle
        self.stats_text.delete("1.0", "end")

        stats_text = """📊 BENZERLİK İSTATİSTİKLERİ
=======================================

"""

        if self.results:
            # Toplam karşılaştırma sayısı
            stats_text += f"💾 Toplam Benzer Dosya Çifti: {len(self.results)}\n\n"

            # Ortalama benzerlik
            avg_similarity = sum(scores) / len(scores) if scores else 0
            stats_text += f"📋 Ortalama Benzerlik: {avg_similarity:.2f}%\n"

            # En yüksek benzerlik
            max_similarity = max(scores) if scores else 0
            stats_text += f"📈 En Yüksek Benzerlik: {max_similarity:.2f}%\n"

            # En düşük benzerlik
            min_similarity = min(scores) if scores else 0
            stats_text += f"📉 En Düşük Benzerlik: {min_similarity:.2f}%\n\n"

            # Benzerlik dağılımı
            stats_text += "📊 BENZERLİK DAĞILIMI:\n"
            for label, count in similarity_ranges.items():
                percentage = count / len(self.results) * 100 if self.results else 0
                stats_text += f"  • {label}%: {count} dosya çifti ({percentage:.1f}%)\n"

            # Dosya türü dağılımı
            file_types = {}
            for res in self.results:
                ext1 = os.path.splitext(res['Dosya 1'])[1].lower()
                ext2 = os.path.splitext(res['Dosya 2'])[1].lower()

                if ext1 not in file_types:
                    file_types[ext1] = 0
                if ext2 not in file_types:
                    file_types[ext2] = 0

                file_types[ext1] += 1
                file_types[ext2] += 1

            if file_types:
                stats_text += "\n📁 DOSYA TÜRÜ DAĞILIMI:\n"
                for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
                    stats_text += f"  • {ext}: {count} dosya\n"
        else:
            stats_text += "Henüz sonuç bulunmamaktadır."

        self.stats_text.insert("end", stats_text)

    def show_results(self):
        """Sonuçları tabloda göster"""
        # Mevcut sonuçları temizle
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Yeni sonuçları ekle
        for res in self.results:
            tag = ''
            total = float(res['Toplam'])

            if total >= 85:
                tag = 'high'
            elif total >= 50:
                tag = 'medium'
            elif total >= 30:
                tag = 'low'
            else:
                tag = 'none'

            self.tree.insert('', 'end', values=(
                res['Dosya 1'],
                res['Dosya 2'],
                res['Metadata'],
                res['Hash'],
                res['İçerik'],
                res['Yapı'],
                res['Frekans'],
                res['Toplam'],
                res['Sonuç']
            ), tags=(tag,))

    def generate_report(self):
        """Detaylı rapor oluştur"""
        if not self.results:
            messagebox.showinfo("Bilgi", "Rapor oluşturmak için önce karşılaştırma yapın!")
            return

        try:
            report_file = filedialog.asksaveasfilename(
                title="Raporu Kaydet",
                defaultextension=".html",
                filetypes=[("HTML Dosyası", "*.html"), ("Tüm Dosyalar", "*.*")]
            )

            if not report_file:
                return

            # HTML rapor oluştur
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Dosya Karşılaştırma Raporu</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #2c3e50; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .high {{ background-color: #a8e6cf; }}
                    .medium {{ background-color: #dcedc1; }}
                    .low {{ background-color: #ffd3b6; }}
                    .none {{ background-color: #ffaaa5; }}
                    .summary {{ margin-bottom: 30px; }}
                </style>
            </head>
            <body>
                <h1>Gelişmiş Dosya Karşılaştırma Raporu</h1>
                <div class="summary">
                    <p><strong>Oluşturulma Tarihi:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Karşılaştırılan Klasör:</strong> {self.folder_path.get()}</p>
                    <p><strong>Toplam Benzer Dosya Çifti:</strong> {len(self.results)}</p>
                </div>

                <h2>Benzerlik Sonuçları</h2>
                <table>
                    <tr>
                        <th>Dosya 1</th>
                        <th>Dosya 2</th>
                        <th>Metadata</th>
                        <th>Hash</th>
                        <th>İçerik</th>
                        <th>Yapı</th>
                        <th>Frekans</th>
                        <th>Toplam</th>
                        <th>Sonuç</th>
                    </tr>
            """

            # Sonuçları tabloya ekle
            for res in self.results:
                total = float(res['Toplam'])
                css_class = ""

                if total >= 85:
                    css_class = "high"
                elif total >= 50:
                    css_class = "medium"
                elif total >= 30:
                    css_class = "low"
                else:
                    css_class = "none"

                html_content += f"""
                    <tr class="{css_class}">
                        <td>{res['Dosya 1']}</td>
                        <td>{res['Dosya 2']}</td>
                        <td>{res['Metadata']}%</td>
                        <td>{res['Hash']}%</td>
                        <td>{res['İçerik']}%</td>
                        <td>{res['Yapı']}%</td>
                        <td>{res['Frekans']}%</td>
                        <td>{res['Toplam']}%</td>
                        <td>{res['Sonuç']}</td>
                    </tr>
                """

            html_content += """
                </table>

                <h2>Özet İstatistikler</h2>
                <p>Bu rapor, dosyalar arasındaki benzerliği çeşitli kriterler kullanarak analiz etmektedir.</p>
                <ul>
                    <li><strong>Metadata:</strong> Dosya boyutu ve değiştirilme tarihi gibi meta verileri analiz eder.</li>
                    <li><strong>Hash:</strong> Dosyaların içeriğinin tam eşleşip eşleşmediğini kontrol eder.</li>
                    <li><strong>İçerik:</strong> Dosya içeriğinin benzerliğini analiz eder.</li>
                    <li><strong>Yapı:</strong> Dosya yapısını ve formatını analiz eder.</li>
                    <li><strong>Frekans:</strong> Dosya içeriğindeki byte frekans dağılımını analiz eder.</li>
                </ul>
            </body>
            </html>
            """

            # HTML dosyasını kaydet
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Raporu tarayıcıda aç
            webbrowser.open(report_file)

        except Exception as e:
            logging.error(f"Rapor oluşturma hatası: {e}")
            messagebox.showerror("Hata", f"Rapor oluşturulamadı: {str(e)}")

    def export_results(self):
        """Sonuçları CSV olarak dışa aktar"""
        if not self.results:
            messagebox.showinfo("Bilgi", "Dışa aktarmak için önce karşılaştırma yapın!")
            return

        try:
            csv_file = filedialog.asksaveasfilename(
                title="CSV Olarak Kaydet",
                defaultextension=".csv",
                filetypes=[("CSV Dosyası", "*.csv"), ("Tüm Dosyalar", "*.*")]
            )

            if not csv_file:
                return

            # Pandas DataFrame oluştur
            df = pd.DataFrame(self.results)

            # CSV olarak kaydet
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')

            messagebox.showinfo("Başarılı", f"Sonuçlar başarıyla dışa aktarıldı:\n{csv_file}")

        except Exception as e:
            logging.error(f"CSV dışa aktarma hatası: {e}")
            messagebox.showerror("Hata", f"CSV dışa aktarılamadı: {str(e)}")

    def sort_treeview(self, column):
        """TreeView sütunlarını sırala"""
        # Mevcut sıralama durumu
        if self.current_sort_column == column:
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            self.current_sort_reverse = False
            self.current_sort_column = column

        # Sıralama işlevi
        def get_sort_key(item):
            value = self.tree.set(item, column)
            try:
                # Sayısal değerler için
                if column in ['Metadata', 'Hash', 'İçerik', 'Yapı', 'Frekans', 'Toplam']:
                    return float(value)
                return value
            except ValueError:
                return value

        # Sıralamayı uygula
        items = self.tree.get_children('')
        items = sorted(items, key=get_sort_key, reverse=self.current_sort_reverse)

        # TreeView düzenini güncelle
        for i, item in enumerate(items):
            self.tree.move(item, '', i)

        # Başlığı güncelle
        self.tree.heading(column, text=f"{column} {'↓' if self.current_sort_reverse else '↑'}")

    def on_close(self):
        """Uygulama kapatıldığında çağrılan fonksiyon"""
        # Önce tüm işlemleri durdur
        self.stop_comparison()

        # Eğer işlem devam ediyorsa kullanıcıya sor
        if self.is_running:
            if not messagebox.askyesno("Çıkış", "İşlem devam ediyor. Çıkmak istediğinize emin misiniz?"):
                return  # Kullanıcı hayır derse çıkma

        # Tüm textbox'ların scrollbar güncellemelerini durdur
        for textbox in self.textboxes:
            try:
                # Textbox'un tüm after işlemlerini iptal et
                if hasattr(textbox, '_after_id') and textbox._after_id is not None:
                    try:
                        self.after_cancel(textbox._after_id)
                        textbox._after_id = None
                    except Exception:
                        pass
                # Textbox'un after işlemlerini iptal et
                for attr_name in dir(textbox):
                    if attr_name.startswith('_after_'):
                        try:
                            after_id = getattr(textbox, attr_name)
                            if after_id is not None:
                                self.after_cancel(after_id)
                                setattr(textbox, attr_name, None)
                        except Exception:
                            pass
            except Exception:
                pass

        # Tüm bekleyen after işlemlerini iptal et
        try:
            for after_id in self.after_handles:
                try:
                    self.after_cancel(after_id)
                except Exception:
                    pass
            self.after_handles = []

            # Genel after işlemlerini kontrol et
            for widget in self.winfo_children():
                if hasattr(widget, 'after_ids') and isinstance(widget.after_ids, list):
                    for after_id in widget.after_ids:
                        try:
                            self.after_cancel(after_id)
                        except Exception:
                            pass
        except Exception:
            pass

        # Matplotlib figürünü kapat
        if hasattr(self, 'fig') and self.fig is not None:
            try:
                plt.close(self.fig)
                self.fig = None
            except Exception:
                pass

        # Uygulamayı kapat
        try:
            # Önce quit() çağır
            self.quit()
            # Sonra destroy()
            self.destroy()
        except Exception as e:
            print(f"Uygulama kapatılırken hata: {e}")
            # Son çare olarak sys.exit kullan
            try:
                import sys
                sys.exit(0)
            except Exception:
                pass

if __name__ == "__main__":
    app = ModernFileComparator()
    app.mainloop()
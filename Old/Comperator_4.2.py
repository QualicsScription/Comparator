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

# Bağımlılık kontrolü ve kurulum
def install_deps():
    required = [
        'customtkinter>=5.2.0',  # Ensure we use the latest stable version
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
            def calculate_segmented_hash(file_path, segments=10):
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    return ["d41d8cd98f00b204e9800998ecf8427e"]
                segment_size = max(file_size // segments, 1)
                hashes = []
                with open(file_path, 'rb') as f:
                    for i in range(segments):
                        segment_pos = (i * file_size) // segments
                        f.seek(segment_pos)
                        chunk = f.read(segment_size)
                        hasher = hashlib.md5()
                        hasher.update(chunk)
                        hashes.append(hasher.hexdigest())
                return hashes

            hashes1 = calculate_segmented_hash(file1)
            hashes2 = calculate_segmented_hash(file2)
            matches = sum(1 for h1, h2 in zip(hashes1, hashes2) if h1 == h2)
            return (matches / len(hashes1)) * 100 if hashes1 else 0
        except Exception as e:
            logging.error(f"Hash hatası: {e}")
            return 0

    @staticmethod
    def compare_binary_content(file1, file2, sample_rate=0.1):
        try:
            file_size1 = os.path.getsize(file1)
            file_size2 = os.path.getsize(file2)

            if min(file_size1, file_size2) == 0:
                return 0

            size_ratio = min(file_size1, file_size2) / max(file_size1, file_size2)
            if size_ratio < 0.5:
                return size_ratio * 50

            sample_size = min(int(max(file_size1, file_size2) * sample_rate), 1024*1024)
            num_samples = 20
            matches = 0
            samples_taken = 0

            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                for i in range(num_samples):
                    if file_size1 <= sample_size or file_size2 <= sample_size:
                        f1.seek(0)
                        f2.seek(0)
                        chunk1 = f1.read()
                        chunk2 = f2.read()
                        samples_taken = 1
                        break
                    else:
                        if file_size1 > file_size2:
                            max_pos = file_size1 - sample_size
                            pos = int((max_pos / num_samples) * i)
                            f1.seek(pos)
                            f2.seek(min(pos, file_size2 - sample_size))
                        else:
                            max_pos = file_size2 - sample_size
                            pos = int((max_pos / num_samples) * i)
                            f1.seek(min(pos, file_size1 - sample_size))
                            f2.seek(pos)

                        chunk1 = f1.read(sample_size)
                        chunk2 = f2.read(sample_size)
                        samples_taken += 1

                if samples_taken == 1:
                    similarity = difflib.SequenceMatcher(None, chunk1, chunk2).ratio() * 100
                else:
                    similarity_sum = 0
                    for i in range(0, len(chunk1), len(chunk1)//100):
                        end = min(i + len(chunk1)//100, len(chunk1))
                        if end > i:
                            sample1 = chunk1[i:end]
                            sample2 = chunk2[i:min(end, len(chunk2))]
                            if sample1 and sample2:
                                similarity_sum += difflib.SequenceMatcher(None, sample1, sample2).ratio()

                    similarity = (similarity_sum / (samples_taken * 100)) * 100

                file_ext = os.path.splitext(file1)[1].lower()
                if file_ext in ['.sldprt', '.sldasm', '.slddrw']:
                    similarity = min(similarity * 1.15, 100)

                return similarity
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
                        header1 = f1.read(512)
                        header2 = f2.read(512)
                        header_similarity = difflib.SequenceMatcher(None, header1, header2).ratio() * 100
                        return header_similarity
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
        try:
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                sample1 = f1.read(sample_size)
                sample2 = f2.read(sample_size)
                freq1 = Counter(sample1)
                freq2 = Counter(sample2)
                vector1 = [freq1.get(b, 0) / len(sample1) if len(sample1) > 0 else 0 for b in range(256)]
                vector2 = [freq2.get(b, 0) / len(sample2) if len(sample2) > 0 else 0 for b in range(256)]
                dot_product = sum(v1 * v2 for v1, v2 in zip(vector1, vector2))
                magnitude1 = sum(v1 * v1 for v1 in vector1) ** 0.5
                magnitude2 = sum(v2 * v2 for v2 in vector2) ** 0.5
                return (dot_product / (magnitude1 * magnitude2)) * 100 if magnitude1 and magnitude2 else 0
        except Exception as e:
            logging.error(f"Frekans analizi hatası: {e}")
            return 0

    def full_compare(self, file1, file2, detailed=True):
        try:
            results = {
                'Metadata': self.compare_metadata(file1, file2),
                'Hash': self.compare_hash(file1, file2),
                'İçerik': self.compare_binary_content(file1, file2),
                'Yapı': self.analyze_file_structure(file1, file2),
                'Frekans': self.frequency_analysis(file1, file2)
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

            return {
                'Skorlar': results,
                'Toplam': weighted_total,
                'Sonuç': similarity_category
            } if detailed else weighted_total

        except Exception as e:
            logging.error(f"Karşılaştırma hatası: {e}")
            return {'Skorlar': {k:0 for k in results}, 'Toplam':0, 'Sonuç':"Hata"}

class ModernFileComparator(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gelişmiş Dosya Karşılaştırıcı v2.2")
        self.geometry("1400x800")
        self.minsize(1000, 700)

        # Set appearance mode and theme
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

        # Configure error handling for Tkinter
        self.report_callback_exception = self.handle_exception

        # Patch CustomTkinter TextBox to avoid scrollbar issues
        self.patch_customtkinter()

        self.is_running = False
        self.results = []
        self.comparator = AdvancedFileComparator()
        self.current_sort_column = None
        self.current_sort_reverse = False
        self.selected_file_types = ctk.StringVar(value="solidworks")
        self.min_similarity = ctk.IntVar(value=20)

        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

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

        # Use validate command to ensure only numbers are entered
        def validate_number(text):
            if text == "":
                return True
            try:
                int(text)
                return True
            except ValueError:
                return False

        min_sim_entry = ctk.CTkEntry(filter_frame, width=50)
        min_sim_entry.pack(side="left", padx=5)
        min_sim_entry.insert(0, str(self.min_similarity.get()))

        # Update IntVar when entry changes
        def update_min_similarity(event=None):
            try:
                value = min_sim_entry.get()
                if value and value.isdigit():
                    self.min_similarity.set(int(value))
            except Exception as e:
                logging.error(f"Error updating min similarity: {e}")

        min_sim_entry.bind("<FocusOut>", update_min_similarity)
        min_sim_entry.bind("<Return>", update_min_similarity)

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
        button_frame.pack(pady=10, fill="x")
        ctk.CTkButton(button_frame, text="▶️ Başlat", command=self.start_comparison).grid(row=0, column=0, padx=5)
        ctk.CTkButton(button_frame, text="⏹ Durdur", command=self.stop_comparison).grid(row=0, column=1, padx=5)
        ctk.CTkButton(button_frame, text="🗑️ Temizle", command=self.clear_results).grid(row=0, column=2, padx=5)
        ctk.CTkButton(button_frame, text="📊 Rapor", command=self.generate_report).grid(row=0, column=3, padx=5)
        ctk.CTkButton(button_frame, text="💾 CSV", command=self.export_results).grid(row=0, column=4, padx=5)

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

    def setup_visual_analysis(self):
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.visual_tab)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        # Add height parameter to avoid TextBox scrollbar issues
        self.stats_text = ctk.CTkTextbox(self.visual_tab, wrap="word", height=150)
        self.stats_text.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_detail_panel(self):
        detail_paned = ctk.CTkTabview(self.detail_tab)
        detail_paned.pack(fill="both", expand=True)

        # Dosya Bilgileri
        file_info_tab = detail_paned.add("Dosya Bilgileri")
        file_frame = ctk.CTkFrame(file_info_tab)
        file_frame.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(file_frame, text="Dosya 1:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.file1_info = ctk.CTkTextbox(file_frame, wrap="word", height=200)
        self.file1_info.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(file_frame, text="Dosya 2:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.file2_info = ctk.CTkTextbox(file_frame, wrap="word", height=200)
        self.file2_info.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        file_frame.grid_rowconfigure(1, weight=1)
        file_frame.grid_columnconfigure(0, weight=1)
        file_frame.grid_columnconfigure(1, weight=1)

        # Karşılaştırma Detayları
        comparison_tab = detail_paned.add("Karşılaştırma Detayları")
        self.comparison_text = ctk.CTkTextbox(comparison_tab, wrap="word", height=200)
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
                    progress_value = (processed / total_comparisons) * 100 if total_comparisons > 0 else 0

                    if time.time() - last_update > 0.1:
                        self.update_progress(progress_value, processed, total_comparisons)
                        last_update = time.time()

            self.update_progress(100, processed, total_comparisons)
            self.show_results()
            self.update_visual_analysis()
            self.status_var.set(f"Tamamlandı! {len(self.results)} benzer dosya çifti bulundu.")
            self.progress.set(1)

        except Exception as e:
            messagebox.showerror("Hata", str(e))
            logging.error(f"Karşılaştırma hatası: {e}")
        finally:
            self.is_running = False

    def update_progress(self, progress_value, processed, total):
        self.progress.set(progress_value / 100)
        self.status_var.set(f"İşlem: {processed}/{total} ({progress_value:.1f}%)")

    def show_results(self):
        self.tree.delete(*self.tree.get_children())

        for res in self.results:
            total_score = float(res['Toplam'])
            tag = 'none'
            if total_score >= 85:
                tag = 'high'
            elif total_score >= 50:
                tag = 'medium'
            elif total_score >= 30:
                tag = 'low'

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

    def sort_treeview(self, column):
        if self.current_sort_column == column:
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            self.current_sort_reverse = False
            self.current_sort_column = column

        def get_sort_key(item):
            value = self.tree.set(item, column)
            try:
                if column in ['Metadata', 'Hash', 'İçerik', 'Yapı', 'Frekans', 'Toplam']:
                    return float(value)
                return value
            except ValueError:
                return value

        items = sorted(self.tree.get_children(''), key=get_sort_key, reverse=self.current_sort_reverse)

        for i, item in enumerate(items):
            self.tree.move(item, '', i)

        self.tree.heading(column, text=f"{column} {'↓' if self.current_sort_reverse else '↑'}")

    def update_visual_analysis(self):
        if not self.results:
            return

        self.ax.clear()
        scores = [float(r['Toplam']) for r in self.results]
        similarity_ranges = Counter()
        for score in scores:
            if score >= 90: similarity_ranges['90-100'] += 1
            elif score >= 70: similarity_ranges['70-90'] += 1
            elif score >= 50: similarity_ranges['50-70'] += 1
            elif score >= 30: similarity_ranges['30-50'] += 1
            else: similarity_ranges['0-30'] += 1

        labels, sizes = zip(*[(f"{k}% ({v})", v) for k, v in similarity_ranges.items() if v > 0])

        if sizes:
            self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
            self.ax.axis('equal')
            self.canvas.draw()

        self.update_statistics()

    def update_statistics(self):
        self.stats_text.delete("1.0", "end")
        if not self.results:
            return

        stats_text = f"""📊 BENZERLIK İSTATISTIKLERI 📊
==============================
Toplam Karşılaştırma: {len(self.results)}
Ortalama Benzerlik: {np.mean([float(r['Toplam']) for r in self.results]):.2f}%
Maksimum: {max(float(r['Toplam']) for r in self.results):.2f}%
Minimum: {min(float(r['Toplam']) for r in self.results):.2f}%
=============================="""

        self.stats_text.insert("end", stats_text)

    def show_detail_view(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return

        selected = self.tree.item(item, 'values')
        if not selected:
            return

        for res in self.results:
            if res['Dosya 1'] == selected[0] and res['Dosya 2'] == selected[1]:
                self.notebook.set("Detaylı Analiz")
                self.update_file_info(res)
                self.update_comparison_details(res)
                break

    def update_file_info(self, file_data):
        def get_info(path):
            try:
                stat = os.stat(path)
                return (
                    f"📄 {os.path.basename(path)}\n"
                    f"📏 Boyut: {self.format_size(stat.st_size)}\n"
                    f"🕒 Değiştirilme: {datetime.fromtimestamp(stat.st_mtime)}\n"
                )
            except Exception as e:
                return f"Hata: {str(e)}"

        self.file1_info.delete("1.0", "end")
        self.file1_info.insert("end", get_info(file_data['Path1']))
        self.file2_info.delete("1.0", "end")
        self.file2_info.insert("end", get_info(file_data['Path2']))

    @staticmethod
    def format_size(size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"

    def update_comparison_details(self, file_data):
        self.comparison_text.delete("1.0", "end")
        details = f"""
        🔍 Detaylı Karşılaştırma 🔍
        Dosya 1: {file_data['Dosya 1']}
        Dosya 2: {file_data['Dosya 2']}
        Toplam Benzerlik: {file_data['Toplam']}%
        Sonuç: {file_data['Sonuç']}
        """
        self.comparison_text.insert("end", details)

    def clear_results(self):
        self.results = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.ax.clear()
        self.canvas.draw()
        self.stats_text.delete("1.0", "end")
        self.file1_info.delete("1.0", "end")
        self.file2_info.delete("1.0", "end")
        self.comparison_text.delete("1.0", "end")
        self.status_var.set("Hazır")
        self.progress.set(0)

    def stop_comparison(self):
        self.is_running = False
        self.status_var.set("İşlem durduruldu!")

    def generate_report(self):
        """Generate a detailed HTML report of comparison results"""
        if not self.results:
            messagebox.showinfo("Bilgi", "Rapor oluşturmak için sonuç bulunmuyor!")
            return

        try:
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML Dosyası", "*.html")],
                title="Rapor Dosyasını Kaydet"
            )

            if not file_path:
                return  # User cancelled

            # Get current date and time
            now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            folder_name = os.path.basename(self.folder_path.get()) if self.folder_path.get() else "Bilinmeyen Klasör"

            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html lang="tr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Dosya Karşılaştırma Raporu</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #2c3e50; }}
                    .header {{ background-color: #3498db; color: white; padding: 10px; border-radius: 5px; }}
                    .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .high {{ background-color: #a8e6cf; }}
                    .medium {{ background-color: #dcedc1; }}
                    .low {{ background-color: #ffd3b6; }}
                    .none {{ background-color: #ffaaa5; }}
                    .footer {{ margin-top: 30px; font-size: 0.8em; color: #7f8c8d; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Gelişmiş Dosya Karşılaştırma Raporu</h1>
                    <p>Oluşturulma Tarihi: {now}</p>
                </div>

                <div class="summary">
                    <h2>Rapor Özeti</h2>
                    <p><strong>Klasör:</strong> {folder_name}</p>
                    <p><strong>Toplam Karşılaştırma:</strong> {len(self.results)}</p>
                    <p><strong>Ortalama Benzerlik:</strong> {np.mean([float(r['Toplam']) for r in self.results]):.2f}%</p>
                </div>

                <h2>Karşılaştırma Sonuçları</h2>
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

            # Add rows for each result
            for result in self.results:
                total_score = float(result['Toplam'])
                css_class = 'none'
                if total_score >= 85:
                    css_class = 'high'
                elif total_score >= 50:
                    css_class = 'medium'
                elif total_score >= 30:
                    css_class = 'low'

                html_content += f"""
                    <tr class="{css_class}">
                        <td>{result['Dosya 1']}</td>
                        <td>{result['Dosya 2']}</td>
                        <td>{result['Metadata']}</td>
                        <td>{result['Hash']}</td>
                        <td>{result['İçerik']}</td>
                        <td>{result['Yapı']}</td>
                        <td>{result['Frekans']}</td>
                        <td>{result['Toplam']}</td>
                        <td>{result['Sonuç']}</td>
                    </tr>
                """

            # Close HTML content
            html_content += """
                </table>

                <div class="footer">
                    <p>Bu rapor Gelişmiş Dosya Karşılaştırıcı v2.2 tarafından oluşturulmuştur.</p>
                </div>
            </body>
            </html>
            """

            # Write HTML to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Open the report in the default browser
            webbrowser.open('file://' + os.path.realpath(file_path))

            messagebox.showinfo("Başarılı", f"Rapor başarıyla oluşturuldu ve açıldı:\n{file_path}")

        except Exception as e:
            logging.error(f"Rapor oluşturma hatası: {e}")
            messagebox.showerror("Hata", f"Rapor oluşturma sırasında hata oluştu:\n{str(e)}")

    def export_results(self):
        """Export comparison results to CSV file"""
        if not self.results:
            messagebox.showinfo("Bilgi", "Dışa aktarmak için sonuç bulunmuyor!")
            return

        try:
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Dosyası", "*.csv")],
                title="CSV Dosyasını Kaydet"
            )

            if not file_path:
                return  # User cancelled

            # Create CSV content
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                import csv
                fieldnames = ['Dosya 1', 'Dosya 2', 'Metadata', 'Hash', 'İçerik', 'Yapı', 'Frekans', 'Toplam', 'Sonuç']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for result in self.results:
                    # Create a copy of the result without the path keys
                    row = {k: result[k] for k in fieldnames if k in result}
                    writer.writerow(row)

            messagebox.showinfo("Başarılı", f"Sonuçlar başarıyla dışa aktarıldı:\n{file_path}")

        except Exception as e:
            logging.error(f"CSV dışa aktarma hatası: {e}")
            messagebox.showerror("Hata", f"CSV dışa aktarma sırasında hata oluştu:\n{str(e)}")

    def patch_customtkinter(self):
        """Patch CustomTkinter TextBox to avoid scrollbar issues"""
        try:
            # Try to patch the _check_if_scrollbars_needed method in CTkTextbox
            if hasattr(ctk.CTkTextbox, '_check_if_scrollbars_needed'):
                original_method = ctk.CTkTextbox._check_if_scrollbars_needed

                def safe_check_scrollbars(self, *args, **kwargs):
                    try:
                        return original_method(self, *args, **kwargs)
                    except Exception as e:
                        logging.error(f"Scrollbar check error: {e}")
                        return None

                ctk.CTkTextbox._check_if_scrollbars_needed = safe_check_scrollbars
                logging.info("CustomTkinter TextBox patched successfully")
        except Exception as e:
            logging.error(f"Failed to patch CustomTkinter: {e}")

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle exceptions in Tkinter callbacks"""
        logging.error("Tkinter exception:", exc_info=(exc_type, exc_value, exc_traceback))
        error_message = f"Hata: {exc_type.__name__}: {exc_value}"
        print(error_message)

        # Only show message box if it's not a KeyboardInterrupt
        if exc_type is not KeyboardInterrupt:
            messagebox.showerror("Uygulama Hatası", error_message)

    def on_close(self):
        try:
            # Stop any running comparison first
            self.is_running = False

            if self.is_running and messagebox.askyesno("Çıkış", "İşlem devam ediyor. Çıkmak istediğinize emin misiniz?"):
                self.destroy()
            elif not self.is_running:
                self.destroy()
        except Exception as e:
            logging.error(f"Kapatma hatası: {e}")
            self.destroy()  # Force close if there's an error

if __name__ == "__main__":
    try:
        app = ModernFileComparator()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nUygulama kullanıcı tarafından durduruldu.")
        logging.info("Uygulama kullanıcı tarafından durduruldu.")
        sys.exit(0)  # Clean exit for keyboard interrupt
    except Exception as e:
        logging.error(f"Uygulama hatası: {e}")
        print(f"Uygulama hatası: {e}")
        # If the app crashes, ensure we exit cleanly
        sys.exit(1)
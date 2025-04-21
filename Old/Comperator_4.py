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
from PIL import Image, ImageTk
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
        # PIP'in güncel olduğundan emin ol
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        
        # Tüm bağımlılıkları direkt kurmayı dene
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install'] + required,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"⚠️ Bağımlılık yükleme hatası: {str(e)}")
        print("⚠️ Bazı özellikler çalışmayabilir!")

install_deps()  # Uygulama başlarken direkt kurulum dene

# Diğer import'lar KURULDUKTAN SONRA yapılmalı
import tkinter as tk
from tkinter import filedialog, messagebox
import hashlib
# ... diğer kütüphane import'ları ...
import customtkinter as ctk

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
            metadata_score = ((1 if time_diff else 0) + size_similarity / 2) / 1.5 * 100
            return metadata_score
        except Exception as e:
            logging.error(f"Metadata hatası: {e}")
            return 0

    @staticmethod
    def compare_hash(file1, file2, chunk_size=8192):
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
                structure_similarity = 0
                try:
                    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                        header1 = f1.read(512)
                        header2 = f2.read(512)
                        header_similarity = difflib.SequenceMatcher(None, header1, header2).ratio() * 100
                        sig1 = header1[:16]
                        sig2 = header2[:16]
                        sig_match = sig1 == sig2
                        
                        f1.seek(0)
                        f2.seek(0)
                        content1 = f1.read(1024*1024)
                        content2 = f2.read(1024*1024)
                        
                        freq1 = Counter([content1[i:i+4] for i in range(0, len(content1)-4, 4)])
                        freq2 = Counter([content2[i:i+4] for i in range(0, len(content2)-4, 4)])
                        common_patterns = set(freq1.keys()) & set(freq2.keys())
                        pattern_similarity = len(common_patterns) / max(len(freq1), len(freq2)) * 100 if freq1 and freq2 else 0
                        
                        structure_similarity = header_similarity * 0.3 + pattern_similarity * 0.7
                        if sig_match:
                            structure_similarity = min(structure_similarity * 1.2, 100)
                except Exception as e:
                    logging.error(f"SolidWorks yapı analizi hatası: {e}")
                    structure_similarity = 0
                return structure_similarity
                
            elif file_ext in ['.zip', '.docx', '.xlsx', '.pptx']:
                try:
                    with zipfile.ZipFile(file1) as z1, zipfile.ZipFile(file2) as z2:
                        names1 = set(z1.namelist())
                        names2 = set(z2.namelist())
                        common = names1.intersection(names2)
                        total = len(names1.union(names2))
                        return len(common) / total * 100 if total != 0 else 0
                except:
                    return 0
            else:
                return AdvancedFileComparator.compare_binary_content(file1, file2, sample_rate=0.05)
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
                all_bytes = set(freq1.keys()).union(set(freq2.keys()))
                vector1 = [freq1.get(b, 0) / len(sample1) if len(sample1) > 0 else 0 for b in range(256)]
                vector2 = [freq2.get(b, 0) / len(sample2) if len(sample2) > 0 else 0 for b in range(256)]
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
                    'Skorlar': {k: 0 for k in ['Metadata', 'Hash', 'İçerik', 'Yapı', 'Frekans']},
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
        
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")
        
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
        button_frame.pack(pady=10)
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
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=80)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.visual_tab)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        self.stats_text = ctk.CTkTextbox(self.visual_tab, wrap="word")
        self.stats_text.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_detail_panel(self):
        detail_paned = ctk.CTkTabview(self.detail_tab)
        detail_paned.pack(fill="both", expand=True)
        
        # Dosya Bilgileri
        file_info_tab = detail_paned.add("Dosya Bilgileri")
        file_frame = ctk.CTkFrame(file_info_tab)
        file_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(file_frame, text="Dosya 1:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.file1_info = ctk.CTkTextbox(file_frame, wrap="word")
        self.file1_info.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        ctk.CTkLabel(file_frame, text="Dosya 2:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.file2_info = ctk.CTkTextbox(file_frame, wrap="word")
        self.file2_info.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        file_frame.grid_rowconfigure(1, weight=1)
        file_frame.grid_columnconfigure(0, weight=1)
        file_frame.grid_columnconfigure(1, weight=1)
        
        # Karşılaştırma Detayları
        comparison_tab = detail_paned.add("Karşılaştırma Detayları")
        self.comparison_text = ctk.CTkTextbox(comparison_tab, wrap="word")
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
                        self.after(0, lambda: self.progress.set(progress_value / 100))
                        self.after(0, lambda: self.status_var.set(
                            f"İşlem: {processed}/{total_comparisons} ({progress_value:.1f}%)"
                        ))
                        last_update = time.time()
            
            self.after(0, self.show_results)
            self.after(0, self.update_visual_analysis)
            self.after(0, lambda: self.status_var.set(
                f"Tamamlandı! {len(self.results)} benzer dosya çifti bulundu."
            ))
            self.after(0, lambda: self.progress.set(1))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Hata", str(e)))
            logging.error(f"Karşılaştırma hatası: {e}")
        finally:
            self.is_running = False

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
        
        items = self.tree.get_children('')
        items = sorted(items, key=get_sort_key, reverse=self.current_sort_reverse)
        
        for i, item in enumerate(items):
            self.tree.move(item, '', i)
        
        self.tree.heading(column, text=f"{column} {'↓' if self.current_sort_reverse else '↑'}")

    def update_visual_analysis(self):
        if not self.results:
            return
        
        self.ax.clear()
        scores = [float(r['Toplam']) for r in self.results]
        similarity_ranges = {
            '90-100': 0,
            '70-90': 0,
            '50-70': 0,
            '30-50': 0,
            '0-30': 0
        }
        
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
        
        if sum(similarity_ranges.values()) > 0:
            labels = []
            sizes = []
            colors = ['#2ecc71', '#3498db', '#f1c40f', '#e67e22', '#e74c3c']
            
            for label, count in similarity_ranges.items():
                if count > 0:
                    labels.append(f"{label}% ({count})")
                    sizes.append(count)
            
            if sizes:
                self.ax.pie(sizes, labels=labels, colors=colors[:len(sizes)],
                           autopct='%1.1f%%', shadow=True, startangle=90)
                self.ax.axis('equal')
                self.ax.set_title('Benzerlik Dağılımı')
                self.canvas.draw()
        
        self.update_statistics()

    def update_statistics(self):
        if not self.results:
            return
        
        self.stats_text.delete("1.0", "end")
        
        total_comparisons = len(self.results)
        total_scores = [float(r['Toplam']) for r in self.results]
        
        avg_score = sum(total_scores) / total_comparisons if total_comparisons > 0 else 0
        min_score = min(total_scores) if total_scores else 0
        max_score = max(total_scores) if total_scores else 0
        median_score = sorted(total_scores)[len(total_scores) // 2] if total_scores else 0
        
        categories = {
            'Tam Eşleşme': 0,
            'Çok Yüksek Benzerlik': 0,
            'Yüksek Benzerlik': 0,
            'Orta Benzerlik': 0,
            'Düşük Benzerlik': 0,
            'Benzerlik Yok': 0
        }
        
        for result in self.results:
            categories[result['Sonuç']] = categories.get(result['Sonuç'], 0) + 1
        
        stats_text = f"""📊 BENZERLIK İSTATISTIKLERI 📊
==============================

Toplam Karşılaştırma: {total_comparisons}

Benzerlik Puanları:
- Ortalama: {avg_score:.2f}%
- Minimum: {min_score:.2f}%
- Maksimum: {max_score:.2f}%
- Medyan: {median_score:.2f}%

Benzerlik Kategorileri:
- Tam Eşleşme: {categories['Tam Eşleşme']}
- Çok Yüksek Benzerlik: {categories['Çok Yüksek Benzerlik']}
- Yüksek Benzerlik: {categories['Yüksek Benzerlik']}
- Orta Benzerlik: {categories['Orta Benzerlik']}
- Düşük Benzerlik: {categories['Düşük Benzerlik']}
- Benzerlik Yok: {categories.get('Benzerlik Yok', 0)}

==============================

En Benzer Dosya Çiftleri:
"""
        
        top_matches = sorted(self.results, key=lambda x: float(x['Toplam']), reverse=True)[:5]
        for i, match in enumerate(top_matches, 1):
            stats_text += f"""
{i}. {match['Dosya 1']} - {match['Dosya 2']}
   - Toplam Benzerlik: {match['Toplam']}%
   - Kategori: {match['Sonuç']}"""
        
        self.stats_text.insert("end", stats_text)

    def show_detail_view(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        selected_values = self.tree.item(item, 'values')
        if not selected_values or len(selected_values) < 9:
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

    def update_file_info(self, file_data):
        try:
            file1_path = file_data['Path1']
            file2_path = file_data['Path2']
            
            def get_file_info(file_path):
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                file_ext = os.path.splitext(file_path)[1].lower()
                
                info = f"📄 {file_name}\n"
                info += f"📏 Boyut: {self.format_size(file_size)}\n"
                info += f"🕒 Son Değişiklik: {file_modified}\n"
                info += f"📁 Konum: {os.path.dirname(file_path)}\n\n"
                
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
                
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read(1024)
                        ascii_ratio = sum(1 for b in content if 32 <= b <= 126) / len(content) if content else 0
                        info += f"📝 ASCII Metin Oranı: {ascii_ratio:.1%}\n"
                        info += "✓ " + ("Metin" if ascii_ratio > 0.75 else "Binary") + " dosyası\n"
                except:
                    pass
                
                return info
            
            self.file1_info.delete("1.0", "end")
            self.file1_info.insert("end", get_file_info(file1_path))
            
            self.file2_info.delete("1.0", "end")
            self.file2_info.insert("end", get_file_info(file2_path))
            
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya bilgileri alınamadı: {str(e)}")

    def update_comparison_details(self, file_data):
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
   - Dosya boyutu ve değiştirilme tarihi analizi

2️⃣ Hash Benzerliği: {file_data['Hash']}%
   - Dosyaların özet (hash) değerlerinin karşılaştırılması

3️⃣ İçerik Benzerliği: {file_data['İçerik']}%
   - Binary içerik karşılaştırma sonucu

4️⃣ Yapı Benzerliği: {file_data['Yapı']}%
   - Dosya formatı ve yapısal özelliklerin benzerliği

5️⃣ Frekans Analizi: {file_data['Frekans']}%
   - Bayt değerlerinin dağılımının benzerliği

=======================================

💡 GENEL DEĞERLENDİRME:
"""
            total_score = float(file_data['Toplam'])
            if total_score >= 95:
                details += "\nBu dosyalar neredeyse birebir aynıdır."
            elif total_score >= 85:
                details += "\nBu dosyalar çok yüksek benzerlik göstermektedir."
            elif total_score >= 70:
                details += "\nBu dosyalar yüksek derecede benzerdir."
            elif total_score >= 50:
                details += "\nBu dosyalar orta derecede benzerlik gösteriyor."
            elif total_score >= 30:
                details += "\nBu dosyalar düşük düzeyde benzerlik gösteriyor."
            else:
                details += "\nBu dosyalar büyük olasılıkla tamamen farklıdır."
            
            self.comparison_text.insert("end", details)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Karşılaştırma detayları gösterilemedi: {str(e)}")

    def stop_comparison(self):
        self.is_running = False
        self.status_var.set("İşlem durduruldu!")

    def clear_results(self):
        self.results = []
        self.tree.delete(*self.tree.get_children())
        self.ax.clear()
        self.canvas.draw()
        self.stats_text.delete("1.0", "end")
        self.file1_info.delete("1.0", "end")
        self.file2_info.delete("1.0", "end")
        self.comparison_text.delete("1.0", "end")
        self.status_var.set("Hazır")
        self.progress.set(0)

    def generate_report(self):
        if not self.results:
            messagebox.showinfo("Bilgi", "Rapor oluşturmak için önce bir karşılaştırma yapın!")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML Dosyası", "*.html")],
                title="Raporu Kaydet"
            )
            
            if not file_path:
                return
            
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Dosya Karşılaştırma Raporu</title>
    <style>
        body {{ font-family: Arial; margin: 20px; }}
        h1 {{ color: #2980b9; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .high {{ background-color: #a8e6cf; }}
        .medium {{ background-color: #dcedc1; }}
        .low {{ background-color: #ffd3b6; }}
    </style>
</head>
<body>
    <h1>Dosya Karşılaştırma Raporu</h1>
    <p>Oluşturulma Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Klasör: {self.folder_path.get()}</p>
    <p>Toplam Benzer Çift: {len(self.results)}</p>
    
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
        </tr>"""
            
            for res in self.results:
                total_score = float(res['Toplam'])
                row_class = ''
                if total_score >= 85:
                    row_class = 'high'
                elif total_score >= 50:
                    row_class = 'medium'
                elif total_score >= 30:
                    row_class = 'low'
                
                html_content += f"""
        <tr class="{row_class}">
            <td>{res['Dosya 1']}</td>
            <td>{res['Dosya 2']}</td>
            <td>{res['Metadata']}</td>
            <td>{res['Hash']}</td>
            <td>{res['İçerik']}</td>
            <td>{res['Yapı']}</td>
            <td>{res['Frekans']}</td>
            <td>{res['Toplam']}</td>
            <td>{res['Sonuç']}</td>
        </tr>"""
            
            html_content += """
    </table>
</body>
</html>"""
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            webbrowser.open(file_path)
            messagebox.showinfo("Başarılı", f"Rapor oluşturuldu:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor oluşturulamadı:\n{str(e)}")

    def export_results(self):
        if not self.results:
            messagebox.showinfo("Bilgi", "Dışa aktarmak için önce bir karşılaştırma yapın!")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Dosyası", "*.csv")],
                title="CSV Olarak Kaydet"
            )
            
            if not file_path:
                return
            
            df = pd.DataFrame(self.results)
            if 'Path1' in df.columns and 'Path2' in df.columns:
                df = df.drop(['Path1', 'Path2'], axis=1)
            
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            messagebox.showinfo("Başarılı", f"CSV dosyası kaydedildi:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Hata", f"CSV dışa aktarılamadı:\n{str(e)}")

    @staticmethod
    def format_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def on_close(self):
        if self.is_running:
            if messagebox.askyesno("Çıkış", "İşlem devam ediyor. Çıkmak istediğinize emin misiniz?"):
                self.destroy()
        else:
            self.destroy()

if __name__ == "__main__":
    app = ModernFileComparator()
    app.mainloop()
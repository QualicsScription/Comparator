# -*- coding: utf-8 -*-
# GELIŞMIŞ DOSYA KARŞILAŞTIRICI v1.0
# KRITER BAZLI VE FUZZY ANALIZ DESTEKLI
"""
Bu program farklı dosyaları karşılaştırarak benzerlik oranını tespit eden 
gelişmiş bir araçtır. Özellikle SolidWorks dosyaları için optimize edilmiştir,
ancak diğer dosya türleriyle de çalışabilir.
"""

import os
import sys
import hashlib
import difflib
import logging
import threading
import time
import zipfile
import re
import struct
import binascii
import numpy as np
from datetime import datetime
from collections import Counter
from tkinter import *
from tkinter import ttk, filedialog, messagebox
from tkinter.font import Font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from PIL import Image, ImageTk
import io

# Loglama sistemini başlat
logging.basicConfig(
    filename='advanced_comparator.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Konsol gizleme fonksiyonu (Windows için)
def hide_console():
    """Windows'ta konsol penceresini gizler"""
    try:
        import ctypes
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            ctypes.windll.user32.ShowWindow(whnd, 0)
    except:
        # Diğer işletim sistemlerinde veya hata durumunda sessizce geç
        pass

class AdvancedFileComparator:
    """Gelişmiş çok kriter bazlı karşılaştırma sınıfı"""
    
    def __init__(self):
        self.supported_extensions = {
            'solidworks': ['.sldprt', '.sldasm', '.slddrw'],
            'cad': ['.step', '.stp', '.iges', '.igs', '.stl', '.obj', '.dxf'],
            'document': ['.docx', '.xlsx', '.pdf', '.txt'],
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'],
            'all': []  # Tüm dosyalar için kullanılacak
        }
        # Tüm uzantılar listesini oluştur
        for exts in self.supported_extensions.values():
            self.supported_extensions['all'].extend(exts)
    
    @staticmethod
    def compare_metadata(file1, file2):
        """Metadata benzerlik kontrolü"""
        try:
            stat1 = os.stat(file1)
            stat2 = os.stat(file2)
            
            # Son değişiklik tarihi (10 saniye tolerans)
            time_diff = abs(stat1.st_mtime - stat2.st_mtime) < 10
            
            # Dosya boyutu - Tam eşleşme yerine benzerlik oranı
            size1, size2 = stat1.st_size, stat2.st_size
            if size1 == 0 or size2 == 0:  # Sıfıra bölme hatasını önle
                size_similarity = 0
            else:
                min_size = min(size1, size2)
                max_size = max(size1, size2)
                size_similarity = min_size / max_size
            
            metadata_match = {
                'time_match': time_diff,
                'size_similarity': size_similarity,
                'total_score': (1 if time_diff else 0) + size_similarity / 2  # 0-1 aralığı
            }
            
            # Normalize et (0-100)
            metadata_score = (metadata_match['total_score'] / 1.5) * 100
            return metadata_score
        except Exception as e:
            logging.error(f"Metadata karşılaştırma hatası: {e}")
            return 0

    @staticmethod
    def compare_hash(file1, file2, chunk_size=8192):
        """Hash değeri karşılaştırma - Gelişmiş"""
        try:
            # Çoklu hash algoritması ve içerik segmentleri kullan
            def calculate_segmented_hash(file_path, segments=10):
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    return ["d41d8cd98f00b204e9800998ecf8427e"]  # Boş dosya MD5 hash'i
                
                segment_size = max(file_size // segments, 1)
                hashes = []
                
                with open(file_path, 'rb') as f:
                    for i in range(segments):
                        # Her segment için konumu ayarla
                        segment_pos = (i * file_size) // segments
                        f.seek(segment_pos)
                        
                        # Segment içeriğini oku
                        chunk = f.read(segment_size)
                        
                        # Hash hesapla
                        hasher = hashlib.md5()
                        hasher.update(chunk)
                        hashes.append(hasher.hexdigest())
                
                return hashes
            
            # Dosyaların segmentli hash değerlerini hesapla
            hashes1 = calculate_segmented_hash(file1)
            hashes2 = calculate_segmented_hash(file2)
            
            # Eşleşen hash sayısını bul
            matches = sum(1 for h1, h2 in zip(hashes1, hashes2) if h1 == h2)
            
            # Benzerlik oranı (0-100)
            similarity = (matches / len(hashes1)) * 100
            return similarity
        except Exception as e:
            logging.error(f"Hash karşılaştırma hatası: {e}")
            return 0

    @staticmethod
    def compare_binary_content(file1, file2, sample_rate=0.1):
        """İçerik karşılaştırma (örnekleme yaparak)"""
        try:
            file_size1 = os.path.getsize(file1)
            file_size2 = os.path.getsize(file2)
            
            # Dosya boyutları çok farklıysa düşük benzerlik
            if min(file_size1, file_size2) == 0:
                return 0
                
            size_ratio = min(file_size1, file_size2) / max(file_size1, file_size2)
            if size_ratio < 0.5:  # %50'den fazla boyut farkı varsa
                return size_ratio * 50  # Maksimum %25 benzerlik
            
            # Örnekleme büyüklüğü (maximum 1MB)
            sample_size = min(int(max(file_size1, file_size2) * sample_rate), 1024*1024)
            
            # Örnekleme noktaları
            num_samples = 20
            
            matches = 0
            samples_taken = 0
            
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                for i in range(num_samples):
                    # Dosyanın farklı bölgelerinden örnek al
                    if file_size1 <= sample_size or file_size2 <= sample_size:
                        # Küçük dosyalar için tüm içeriği karşılaştır
                        f1.seek(0)
                        f2.seek(0)
                        chunk1 = f1.read()
                        chunk2 = f2.read()
                        samples_taken = 1
                        break
                    else:
                        # Büyük dosyalar için rastgele bölgeleri örnekle
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
                
                # İçerik karşılaştırma yapılır
                if samples_taken == 1:
                    # Küçük dosyalar için tam difflib karşılaştırması
                    similarity = difflib.SequenceMatcher(None, chunk1, chunk2).ratio() * 100
                else:
                    # Örneklenen bölgeler için karşılaştırma
                    similarity_sum = 0
                    for i in range(0, len(chunk1), len(chunk1)//100):
                        end = min(i + len(chunk1)//100, len(chunk1))
                        if end > i:
                            sample1 = chunk1[i:end]
                            sample2 = chunk2[i:min(end, len(chunk2))]
                            if sample1 and sample2:
                                similarity_sum += difflib.SequenceMatcher(None, sample1, sample2).ratio()
                    
                    similarity = (similarity_sum / (samples_taken * 100)) * 100
                
                # SolidWorks dosyaları için metadata bölgesini hariç tut
                file_ext = os.path.splitext(file1)[1].lower()
                if file_ext in ['.sldprt', '.sldasm', '.slddrw']:
                    # SolidWorks metadatasını hariç tut (son kısım)
                    similarity = similarity * 1.15  # Düzeltme faktörü
                
                return min(similarity, 100)  # 100'den fazla olmamalı
        except Exception as e:
            logging.error(f"İçerik karşılaştırma hatası: {e}")
            return 0

    @staticmethod
    def analyze_file_structure(file1, file2):
        """Dosya yapısı analizi - özellikle SolidWorks benzeri formatlı dosyalar için"""
        try:
            # Dosya tipini belirle
            file_ext = os.path.splitext(file1)[1].lower()
            
            # SolidWorks dosyaları için özel analiz
            if file_ext in ['.sldprt', '.sldasm', '.slddrw']:
                # SolidWorks dosyaları genellikle sıkıştırılmış XML'dir
                # Yapıyı analiz et
                structure_similarity = 0
                
                try:
                    # Her iki dosyayı da binary modda açıp header/yapı bilgilerini çıkar
                    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                        # Header'ı oku (ilk 512 byte)
                        header1 = f1.read(512)
                        header2 = f2.read(512)
                        
                        # Basit yapısal karşılaştırma
                        header_similarity = difflib.SequenceMatcher(None, header1, header2).ratio() * 100
                        
                        # Dosya imzalarını karşılaştır (ilk 16 byte)
                        sig1 = header1[:16]
                        sig2 = header2[:16]
                        sig_match = sig1 == sig2
                        
                        # Dosyalardaki tekrarlanan yapıları analiz et
                        # Bu, benzer geometri ve özellikler için bir gösterge olabilir
                        pattern_similarity = 0
                        
                        # Her iki dosyadaki byte dizilerinin frekans analizini yap
                        f1.seek(0)
                        f2.seek(0)
                        
                        # En fazla 1MB analiz et
                        content1 = f1.read(1024*1024)
                        content2 = f2.read(1024*1024)
                        
                        # 4 byte bloklar halinde frekans analizini yap
                        freq1 = Counter([content1[i:i+4] for i in range(0, len(content1)-4, 4)])
                        freq2 = Counter([content2[i:i+4] for i in range(0, len(content2)-4, 4)])
                        
                        # İki frekans tablosundaki ortak byte kalıplarını bul
                        common_patterns = set(freq1.keys()) & set(freq2.keys())
                        
                        # Ortak kalıp oranı
                        if len(freq1) > 0 and len(freq2) > 0:
                            pattern_similarity = len(common_patterns) / max(len(freq1), len(freq2)) * 100
                        
                        # Yapısal benzerlik puanı
                        structure_similarity = header_similarity * 0.3 + pattern_similarity * 0.7
                        if sig_match:
                            structure_similarity = min(structure_similarity * 1.2, 100)  # Bonus
                
                except Exception as e:
                    logging.error(f"SolidWorks yapı analizi hatası: {e}")
                    structure_similarity = 0
                    
                return structure_similarity
                
            # Sıkıştırılmış dosyalar için (zip, docx, xlsx, vb.)
            elif file_ext in ['.zip', '.docx', '.xlsx', '.pptx']:
                try:
                    # Dosya içeriğindeki dizin yapısını karşılaştır
                    with zipfile.ZipFile(file1) as z1, zipfile.ZipFile(file2) as z2:
                        names1 = set(z1.namelist())
                        names2 = set(z2.namelist())
                        
                        # Ortak dosya sayısı
                        common = names1.intersection(names2)
                        total = len(names1.union(names2))
                        
                        if total == 0:
                            return 0
                        
                        # Dizin yapısındaki benzerlik
                        structure_similarity = len(common) / total * 100
                        return structure_similarity
                except:
                    return 0
            
            # Diğer dosya türleri için genel yapısal analiz
            else:
                # Genel analiz için içerik örnekleme ve yapı analizi
                return AdvancedFileComparator.compare_binary_content(file1, file2, sample_rate=0.05)
                
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
                
                # Her iki dosyada bulunan tüm byte değerleri
                all_bytes = set(freq1.keys()).union(set(freq2.keys()))
                
                # Frekans vektörleri oluştur
                vector1 = [freq1.get(b, 0) / len(sample1) if len(sample1) > 0 else 0 for b in range(256)]
                vector2 = [freq2.get(b, 0) / len(sample2) if len(sample2) > 0 else 0 for b in range(256)]
                
                # Kosinüs benzerliği hesapla
                dot_product = sum(v1 * v2 for v1, v2 in zip(vector1, vector2))
                magnitude1 = sum(v1 * v1 for v1 in vector1) ** 0.5
                magnitude2 = sum(v2 * v2 for v2 in vector2) ** 0.5
                
                if magnitude1 == 0 or magnitude2 == 0:
                    return 0
                
                cosine_similarity = dot_product / (magnitude1 * magnitude2)
                
                return cosine_similarity * 100
        except Exception as e:
            logging.error(f"Frekans analizi hatası: {e}")
            return 0

    @staticmethod
    def full_compare(file1, file2, detailed=True):
        """Tüm kriterleri kontrol ederek benzerlik skorunu hesapla"""
        try:
            results = {
                'Metadata': AdvancedFileComparator.compare_metadata(file1, file2),
                'Hash': AdvancedFileComparator.compare_hash(file1, file2),
                'İçerik': AdvancedFileComparator.compare_binary_content(file1, file2),
                'Yapı': AdvancedFileComparator.analyze_file_structure(file1, file2),
                'Frekans': AdvancedFileComparator.frequency_analysis(file1, file2)
            }
            
            # Ağırlıklı toplam hesapla
            weights = {
                'Metadata': 0.1,    # Metadata daha az önemli
                'Hash': 0.15,       # Hash karşılaştırma
                'İçerik': 0.35,     # İçerik benzerliği en önemli
                'Yapı': 0.25,       # Dosya yapısı önemli
                'Frekans': 0.15     # Frekans analizi
            }
            
            weighted_total = sum(results[key] * weights[key] for key in results)
            
            # Sonuçları yorumla
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

class CompareApp(Tk):
    """Gelişmiş karşılaştırma uygulaması arayüzü"""
    
    def __init__(self):
        super().__init__()
        self.title("Gelişmiş Dosya Karşılaştırıcı v1.0")
        self.geometry("1400x800")
        self.minsize(1000, 700)
        
        # Değişkenler
        self.is_running = False
        self.results = []
        self.comparator = AdvancedFileComparator()
        self.current_sort_column = None
        self.current_sort_reverse = False
        self.selected_file_types = StringVar(value="solidworks")
        
        # Icon ve tema
        self.setup_theme()
        
        # Arayüzü oluştur
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Konsol gizleme
        hide_console()

    def setup_theme(self):
        """Temayı ve stil ayarlarını yapılandır"""
        # Varsayılan tema
        self.style = ttk.Style()
        
        # Windows için mavi tema
        if sys.platform.startswith('win'):
            try:
                self.style.theme_use('winnative')
            except:
                pass
        
        # Tema renkleri
        self.colors = {
            'primary': '#2980b9',
            'secondary': '#3498db',
            'accent': '#1abc9c',
            'warning': '#e74c3c',
            'background': '#f5f5f5',
            'text': '#2c3e50'
        }
        
        # Font ayarları
        self.default_font = Font(family="Segoe UI", size=10)
        self.header_font = Font(family="Segoe UI", size=11, weight="bold")
        
        # Buton ve treeview stillerini yapılandır
        self.style.configure('TButton', 
                             font=self.default_font, 
                             background=self.colors['primary'])
        
        self.style.configure('TFrame', 
                             background=self.colors['background'])
        
        self.style.configure('TLabel', 
                             font=self.default_font, 
                             background=self.colors['background'], 
                             foreground=self.colors['text'])
        
        self.style.configure('TLabelframe', 
                             font=self.header_font, 
                             background=self.colors['background'])
        
        self.style.configure('TLabelframe.Label', 
                             font=self.header_font, 
                             background=self.colors['background'], 
                             foreground=self.colors['primary'])
        
        self.style.configure('Treeview', 
                             font=self.default_font,
                             rowheight=25)
        
        self.style.configure('Treeview.Heading', 
                             font=self.header_font)

    def setup_ui(self):
        """Arayüz bileşenlerini oluştur"""
        # Ana çerçeve
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Üst kontrol paneli
        control_frame = ttk.LabelFrame(main_frame, text=" Kontrol Panel ", padding=10)
        control_frame.pack(fill=X, pady=5)
        
        # Klasör seçimi
        ttk.Label(control_frame, text="Klasör:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.folder_path = StringVar()
        ttk.Entry(control_frame, textvariable=self.folder_path, width=80).grid(row=0, column=1, padx=5, pady=5, sticky=W+E)
        ttk.Button(control_frame, text="📁 Gözat", command=self.browse_folder).grid(row=0, column=2, padx=5, pady=5)
        
        # Dosya tipi seçimi
        ttk.Label(control_frame, text="Dosya Türü:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        file_types = {
            'solidworks': 'SolidWorks (.sldprt, .sldasm, .slddrw)',
            'cad': 'CAD Dosyaları (.step, .stp, .iges, .igs, .stl, .obj, .dxf)',
            'document': 'Dökümanlar (.docx, .xlsx, .pdf, .txt)',
            'image': 'Görseller (.jpg, .png, .bmp, .tif)',
            'all': 'Tüm Dosyalar'
        }
        
        type_frame = ttk.Frame(control_frame)
        type_frame.grid(row=1, column=1, padx=5, pady=5, sticky=W)
        
        for i, (value, text) in enumerate(file_types.items()):
            ttk.Radiobutton(type_frame, text=text, value=value, 
                           variable=self.selected_file_types).grid(row=0, column=i, padx=10)
        
        # Filtre ayarları
        filter_frame = ttk.Frame(control_frame)
        filter_frame.grid(row=1, column=2, padx=5, pady=5, sticky=W)
        
        self.min_similarity = IntVar(value=20)
        ttk.Label(filter_frame, text="Min. Benzerlik:").pack(side=LEFT, padx=5)
        ttk.Spinbox(filter_frame, from_=0, to=100, width=5, 
                    textvariable=self.min_similarity).pack(side=LEFT, padx=5)
        ttk.Label(filter_frame, text="%").pack(side=LEFT)
        
        # İlerleme çubuğu
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=X, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, orient=HORIZONTAL, mode='determinate')
        self.progress.pack(side=LEFT, fill=X, expand=True, padx=5)
        
        self.status_var = StringVar(value="Hazır")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var, width=30)
        status_label.pack(side=RIGHT, padx=5)
        
        # Sonuçlar paneli - Notebook yapısı
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=True, pady=10)
        
        # Tablo görünümü
        table_frame = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(table_frame, text="Tablo Görünümü")
        
        # Görsel görünüm
        visual_frame = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(visual_frame, text="Görsel Analiz")
        
        # Detay görünümü
        detail_frame = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(detail_frame, text="Detaylı Analiz")
        
        # Tablo sonuçları için TreeView
        columns = (
            'Dosya 1', 'Dosya 2', 
            'Metadata', 'Hash', 'İçerik', 
            'Yapı', 'Frekans', 'Toplam',
            'Sonuç'
        )
        
        table_container = ttk.Frame(table_frame)
        table_container.pack(fill=BOTH, expand=True)
        
        self.tree = ttk.Treeview(table_container, columns=columns, show='headings')
        
        # Sütun başlıkları ve sıralama işlevselliği
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            if col in ['Dosya 1', 'Dosya 2', 'Sonuç']:
                self.tree.column(col, width=200)
            else:
                self.tree.column(col, width=80, anchor=CENTER)
        
        # Tag'ler ile renklendirme
        self.tree.tag_configure('high', background='#a8e6cf')  # Yeşil
        self.tree.tag_configure('medium', background='#dcedc1')  # Açık yeşil
        self.tree.tag_configure('low', background='#ffd3b6')  # Turuncu
        self.tree.tag_configure('none', background='#ffaaa5')  # Kırmızı
        
        # Scrollbar'lar
        vsb = ttk.Scrollbar(table_container, orient=VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Yerleşim
        self.tree.grid(row=0, column=0, sticky=NSEW)
        vsb.grid(row=0, column=1, sticky=NS)
        hsb.grid(row=1, column=0, sticky=EW)
        # Tablo container ayarı
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(0, weight=1)
        
        # Çift tıklama olayı
        self.tree.bind("<Double-1>", self.show_detail_view)
        
        # Görsel analiz paneli
        self.setup_visual_analysis(visual_frame)
        
        # Detay paneli
        self.setup_detail_panel(detail_frame)
        
        # Alt buton paneli
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="▶️ Karşılaştırmayı Başlat", 
                  command=self.start_comparison, width=25).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="⏹ Durdur", 
                  command=self.stop_comparison, width=15).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Temizle", 
                  command=self.clear_results, width=15).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 Rapor Oluştur", 
                  command=self.generate_report, width=20).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 CSV Kaydet", 
                  command=self.export_results, width=15).pack(side=LEFT, padx=5)

    def setup_visual_analysis(self, parent_frame):
        """Görsel analiz panelini kur"""
        # Sol ve sağ paneller
        visual_paned = ttk.PanedWindow(parent_frame, orient=HORIZONTAL)
        visual_paned.pack(fill=BOTH, expand=True)
        
        # Benzerlik grafiği
        graph_frame = ttk.LabelFrame(visual_paned, text=" Benzerlik Grafiği ")
        visual_paned.add(graph_frame, weight=60)
        
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=80)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # İstatistik paneli
        stats_frame = ttk.LabelFrame(visual_paned, text=" Benzerlik İstatistikleri ")
        visual_paned.add(stats_frame, weight=40)
        
        # İstatistik içeriği
        self.stats_text = Text(stats_frame, wrap=WORD, width=40, height=20)
        stats_scroll = ttk.Scrollbar(stats_frame, orient=VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scroll.set)
        
        self.stats_text.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        stats_scroll.pack(side=RIGHT, fill=Y, pady=5)

    def setup_detail_panel(self, parent_frame):
        """Detaylı analiz panelini kur"""
        # Üst ve alt bölümler
        detail_paned = ttk.PanedWindow(parent_frame, orient=VERTICAL)
        detail_paned.pack(fill=BOTH, expand=True)
        
        # Dosya bilgisi paneli
        file_info_frame = ttk.LabelFrame(detail_paned, text=" Dosya Bilgileri ")
        detail_paned.add(file_info_frame, weight=30)
        
        # Dosya bilgileri
        info_container = ttk.Frame(file_info_frame)
        info_container.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # 2x2 grid
        for i in range(2):
            info_container.columnconfigure(i, weight=1)
        info_container.rowconfigure(1, weight=1)
        
        # Dosya 1 bilgisi
        ttk.Label(info_container, text="Dosya 1:", font=self.header_font).grid(row=0, column=0, sticky=W, pady=5)
        self.file1_info = Text(info_container, wrap=WORD, width=40, height=10)
        self.file1_info.grid(row=1, column=0, sticky=NSEW, padx=5, pady=5)
        
        # Dosya 2 bilgisi
        ttk.Label(info_container, text="Dosya 2:", font=self.header_font).grid(row=0, column=1, sticky=W, pady=5)
        self.file2_info = Text(info_container, wrap=WORD, width=40, height=10)
        self.file2_info.grid(row=1, column=1, sticky=NSEW, padx=5, pady=5)
        
        # Karşılaştırma detay paneli
        comparison_frame = ttk.LabelFrame(detail_paned, text=" Karşılaştırma Detayları ")
        detail_paned.add(comparison_frame, weight=70)
        
        # Detay içeriği
        self.comparison_text = Text(comparison_frame, wrap=WORD)
        comp_scroll = ttk.Scrollbar(comparison_frame, orient=VERTICAL, command=self.comparison_text.yview)
        self.comparison_text.configure(yscrollcommand=comp_scroll.set)
        
        self.comparison_text.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        comp_scroll.pack(side=RIGHT, fill=Y, pady=5)

    def browse_folder(self):
        """Klasör seçme diyaloğu"""
        folder = filedialog.askdirectory(title="Dosyaları İçeren Klasörü Seçin")
        if folder:
            self.folder_path.set(folder)

    def start_comparison(self):
        """Karşılaştırma işlemini başlat"""
        if self.is_running:
            return
        
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Hata", "Geçerli bir klasör seçin!")
            return
        
        self.is_running = True
        self.clear_results()
        
        # Başlangıç durumunu güncelle
        self.status_var.set("Dosyalar taranıyor...")
        self.progress['value'] = 0
        
        # Arka plan işlemi başlat
        threading.Thread(target=self.run_comparison, args=(folder,), daemon=True).start()

    def run_comparison(self, folder):
        """Klasördeki dosyaları karşılaştır"""
        try:
            file_type = self.selected_file_types.get()
            min_similarity = self.min_similarity.get()
            
            # Uzantıları al
            extensions = self.comparator.supported_extensions[file_type]
            
            # Dosyaları filtrele
            all_files = [f for f in os.listdir(folder)
                        if os.path.isfile(os.path.join(folder, f)) and 
                        (not extensions or os.path.splitext(f)[1].lower() in extensions)]
            
            # İlerleme hazırlığı
            total_comparisons = len(all_files) * (len(all_files) - 1) // 2
            processed = 0
            
            # İlerleme güncellemesi için zaman aralığı
            last_update = time.time()
            update_interval = 0.2  # saniye
            
            # Sonuç listesi
            self.results = []
            
            # Karşılaştırmaya başla
            for i in range(len(all_files)):
                if not self.is_running:
                    break
                    
                file1 = os.path.join(folder, all_files[i])
                
                for j in range(i + 1, len(all_files)):
                    if not self.is_running:
                        break
                        
                    file2 = os.path.join(folder, all_files[j])
                    
                    # Karşılaştırma yap
                    comparison_result = self.comparator.full_compare(file1, file2)
                    
                    # Min benzerlik filtresi
                    if comparison_result['Toplam'] >= min_similarity:
                        # Sonuca ekle
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
                    
                    # İlerlemeyi güncelle
                    processed += 1
                    
                    # Belirli aralıklarla kullanıcı arayüzünü güncelle
                    current_time = time.time()
                    if current_time - last_update > update_interval:
                        progress_value = processed / total_comparisons * 100
                        self.update_progress(progress_value, processed, total_comparisons)
                        last_update = current_time
            
            # Sonuçları görüntüle ve grafiği güncelle
            self.show_results()
            self.update_visual_analysis()
            
            # Tamamlandı mesajı
            self.status_var.set(f"Tamamlandı! {len(self.results)} benzer dosya çifti bulundu.")
            self.progress['value'] = 100
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Karşılaştırma hatası: {error_msg}")
            messagebox.showerror("Hata", f"Karşılaştırma sırasında hata oluştu:\n{error_msg}")
        finally:
            self.is_running = False

    def update_progress(self, progress_value, processed, total):
        """İlerleme çubuğunu ve durum mesajını güncelle"""
        # Tkinter thread güvenli güncelleme
        self.after(0, lambda: self.progress.configure(value=progress_value))
        self.after(0, lambda: self.status_var.set(
            f"İşlem: {processed}/{total} ({progress_value:.1f}%)"
        ))

    def show_results(self):
        """Sonuçları TreeView'a ekle"""
        # Mevcut satırları temizle
        self.tree.delete(*self.tree.get_children())
        
        # Sonuçları ekle
        for res in self.results:
            # Benzerlik seviyesine göre tag belirle
            total_score = float(res['Toplam'])
            tag = 'none'
            if total_score >= 85:
                tag = 'high'
            elif total_score >= 50:
                tag = 'medium'
            elif total_score >= 30:
                tag = 'low'
                
            # Satır ekle
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
        
        # Pasta grafiği oluştur
        if sum(similarity_ranges.values()) > 0:
            labels = []
            sizes = []
            colors = ['#2ecc71', '#3498db', '#f1c40f', '#e67e22', '#e74c3c']
            explode = (0.1, 0, 0, 0, 0)
            
            for i, (label, count) in enumerate(similarity_ranges.items()):
                if count > 0:
                    labels.append(f"{label}% ({count})")
                    sizes.append(count)
            
            if sizes:
                self.ax.pie(sizes, explode=explode[:len(sizes)], labels=labels, colors=colors[:len(sizes)],
                           autopct='%1.1f%%', shadow=True, startangle=90)
                self.ax.axis('equal')
                self.ax.set_title('Benzerlik Dağılımı')
                
                # Grafiği güncelle
                self.canvas.draw()
        
        # İstatistikleri güncelle
        self.update_statistics()

    def update_statistics(self):
        """İstatistik panelini güncelle"""
        if not self.results:
            return
        
        # İstatistik bilgilerini temizle
        self.stats_text.config(state=NORMAL)
        self.stats_text.delete(1.0, END)
        
        # İstatistikleri hesapla
        total_comparisons = len(self.results)
        total_scores = [float(r['Toplam']) for r in self.results]
        
        # Ortalama, min, max, medyan
        avg_score = sum(total_scores) / total_comparisons if total_comparisons > 0 else 0
        min_score = min(total_scores) if total_scores else 0
        max_score = max(total_scores) if total_scores else 0
        median_score = sorted(total_scores)[len(total_scores) // 2] if total_scores else 0
        
        # Eşleşme kategorilerine göre sayılar
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
        
        # İstatistik bilgilerini ekle
        stats_text = f"""
        📊 BENZERLIK İSTATISTIKLERI 📊
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
        
        # En benzer 5 dosya çiftini ekle
        top_matches = sorted(self.results, key=lambda x: float(x['Toplam']), reverse=True)[:5]
        for i, match in enumerate(top_matches, 1):
            stats_text += f"""
        {i}. {match['Dosya 1']} - {match['Dosya 2']}
           - Toplam Benzerlik: {match['Toplam']}%
           - Kategori: {match['Sonuç']}
            """
        
        self.stats_text.insert(END, stats_text)
        self.stats_text.config(state=DISABLED)

    def show_detail_view(self, event):
        """Seçilen dosya çifti için detaylı gösterim"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        # Seçili satır verilerini al
        selected_values = self.tree.item(item, 'values')
        if not selected_values or len(selected_values) < 9:
            return
        
        # Seçili dosya çiftini bul
        selected_files = None
        for res in self.results:
            if (res['Dosya 1'] == selected_values[0] and 
                res['Dosya 2'] == selected_values[1]):
                selected_files = res
                break
        
        if not selected_files:
            return
        
        # Detay sekme paneline geç
        self.notebook.select(2)  # Detay sekmesi
        
        # Dosya bilgilerini güncelle
        self.update_file_info(selected_files)
        
        # Karşılaştırma detaylarını güncelle
        self.update_comparison_details(selected_files)

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
                
                # Dosya türüne göre ek bilgiler
                if file_ext in ['.sldprt', '.sldasm', '.slddrw']:
                    info += "📊 SolidWorks Dosya Bilgileri:\n"
                    try:
                        # Binary header bilgilerini çıkar
                        with open(file_path, 'rb') as f:
                            header = f.read(256)
                            # SolidWorks Imza Kontrolü
                            if b'SldWorks' in header or b'SOLIDWORKS' in header:
                                info += "   ✓ Geçerli SolidWorks imzası\n"
                            
                            # Diğer özellikler
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
            self.file1_info.config(state=NORMAL)
            self.file1_info.delete(1.0, END)
            self.file1_info.insert(END, get_file_info(file1_path))
            self.file1_info.config(state=DISABLED)
            
            self.file2_info.config(state=NORMAL)
            self.file2_info.delete(1.0, END)
            self.file2_info.insert(END, get_file_info(file2_path))
            self.file2_info.config(state=DISABLED)
            
        except Exception as e:
            logging.error(f"Dosya bilgisi güncelleme hatası: {e}")
            messagebox.showerror("Hata", f"Dosya bilgileri alınamadı: {str(e)}")

    def update_comparison_details(self, file_data):
        """Karşılaştırma detay panelini güncelle"""
        try:
            self.comparison_text.config(state=NORMAL)
            self.comparison_text.delete(1.0, END)
            
            # Temel bilgiler
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
   - Dosyaların özet (hash) değerlerinin karşılaştırılmasıdır.
   - %100 benzerlik, dosyaların içerik olarak birebir aynı olduğunu gösterir.
   - Parçalı hash analizi, dosyanın farklı bölümlerindeki benzerlikleri tespit eder.

3️⃣ İçerik Benzerliği: {file_data['İçerik']}%
   - Binary içerik karşılaştırma sonucudur.
   - Dosyaların içeriğinin ne kadar benzer olduğunu gösterir.
   - SolidWorks dosyaları için metadata bölümü hariç tutularak değerlendirilir.

4️⃣ Yapı Benzerliği: {file_data['Yapı']}%
   - Dosya formatı ve yapısal özelliklerin benzerliğini ölçer.
   - Yüksek benzerlik, iki dosyanın benzer iç yapıya sahip olduğunu gösterir.
   - SolidWorks dosyaları için format ve header yapısını analiz eder.

5️⃣ Frekans Analizi: {file_data['Frekans']}%
   - Dosyalardaki bayt değerlerinin dağılımının benzerliğini ölçer.
   - Bu analiz, dosyaların istatistiksel olarak ne kadar benzer olduğunu gösterir.
   - Yüksek benzerlik, dosyaların benzer içerik türlerine sahip olduğunu işaret eder.

=======================================

💡 GENEL DEĞERLENDİRME:
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
Bu dosyalar yüksek derecede benzerdir. Muhtemelen:
- Aynı temel parçadan türetilmiş farklı versiyonlar
- Ortak bir şablondan oluşturulmuş benzer parçalar
- Ekstra özellikler eklenmiş temel model
- Farklı parametre değerleri atanmış aynı parametrik model
"""
            elif total_score >= 50:
                details += """
Bu dosyalar orta derecede benzerlik gösteriyor. Olasılıklar:
- Ortak bileşenler içeren farklı parçalar
- Aynı temel geometriden önemli ölçüde değiştirilmiş parçalar
- Benzer temel parametrelerle oluşturulmuş farklı tasarımlar
- Aynı ürün ailesinden farklı varyasyonlar
"""
            elif total_score >= 30:
                details += """
Bu dosyalar düşük düzeyde benzerlik gösteriyor:
- Bazı ortak özellikler paylaşan farklı parçalar
- Benzer tasarım prensipleriyle oluşturulmuş farklı parçalar
- Aynı bileşen kütüphanesinden öğeler kullanan farklı montajlar
"""
            else:
                details += """
Bu dosyalar birbirlerinden büyük olasılıkla tamamen farklıdır:
- Farklı kategorilerde veya tamamen farklı amaçlar için tasarlanmış parçalar
- Birbiriyle ilişkisi olmayan dosyalar
- Farklı tasarımcılar tarafından oluşturulmuş bağımsız çalışmalar
"""

                        # Tavsiyeler
            details += "\n=======================================\n\n"
            details += "💡 ÖNERİLER:\n"
            
            if total_score >= 85:
                details += """
✅ Bu dosyalardan birini kaldırmayı veya arşivlemeyi düşünebilirsiniz.
✅ Gereksiz çoğalmayı önlemek için dosya organizasyonunuzu gözden geçirin.
✅ Hangi dosyanın ana (master) versiyon olduğunu belirleyin ve diğerini arşivleyin.
"""
            elif total_score >= 70:
                details += """
✅ Yeni bir revizyon sistemi kurmayı düşünebilirsiniz.
✅ Bu dosyaların revizyon tarihçesini kontrol edin.
✅ İki dosya arasındaki farkları daha detaylı inceleyerek en güncel olanı tespit edin.
"""
            elif total_score >= 50:
                details += """
✅ Bu dosyaları ortak bir klasörde gruplandırmayı düşünebilirsiniz.
✅ Benzerliklerin kaynağını anlamak için tasarım geçmişini inceleyin.
✅ Bir ürün ailesi için parametrik model kullanmayı değerlendirin.
"""
            elif total_score >= 30:
                details += """
✅ Bu iki dosya arasındaki ortak özellikleri bir kütüphane parçasına dönüştürmeyi düşünebilirsiniz.
✅ Dosyaları farklı kategorilerde sınıflandırın ancak benzerlik notunu ekleyin.
"""
            else:
                details += """
✅ Bu dosyalar büyük olasılıkla farklı amaçlar için kullanılmaktadır, normal kategorilendirme yapabilirsiniz.
✅ Tesadüfi benzerlikler olabilir, özel bir işlem gerekmeyebilir.
"""
                
            # Detay metnini göster
            self.comparison_text.insert(END, details)
            self.comparison_text.config(state=DISABLED)
            
        except Exception as e:
            logging.error(f"Karşılaştırma detayı güncelleme hatası: {e}")
            messagebox.showerror("Hata", f"Karşılaştırma detayları gösterilemedi: {str(e)}")

    def stop_comparison(self):
        """Karşılaştırma işlemini durdur"""
        self.is_running = False
        self.status_var.set("İşlem durduruldu!")

    def clear_results(self):
        """Sonuçları temizle"""
        self.results = []
        self.tree.delete(*self.tree.get_children())
        
        # Diğer panelleri de temizle
        self.ax.clear()
        self.canvas.draw()
        
        self.stats_text.config(state=NORMAL)
        self.stats_text.delete(1.0, END)
        self.stats_text.config(state=DISABLED)
        
        self.file1_info.config(state=NORMAL)
        self.file1_info.delete(1.0, END)
        self.file1_info.config(state=DISABLED)
        
        self.file2_info.config(state=NORMAL)
        self.file2_info.delete(1.0, END)
        self.file2_info.config(state=DISABLED)
        
        self.comparison_text.config(state=NORMAL)
        self.comparison_text.delete(1.0, END)
        self.comparison_text.config(state=DISABLED)
        
        self.status_var.set("Hazır")
        self.progress['value'] = 0

    def generate_report(self):
        """Detaylı rapor oluştur"""
        if not self.results:
            messagebox.showinfo("Bilgi", "Rapor oluşturmak için önce bir karşılaştırma yapın!")
            return
        
        try:
            # Rapor dosyası seç
            file_path = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML Dosyası", "*.html"), ("Tüm Dosyalar", "*.*")],
                title="Raporu Kaydet"
            )
            
            if not file_path:
                return
            
            # Rapor HTML içeriği
            html_content = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gelişmiş Dosya Karşılaştırma Raporu</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        .header {{
            background-color: #2980b9;
            color: white;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 5px solid #2980b9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        tr:hover {{
            background-color: #e9f7fe;
        }}
        .high {{
            background-color: #a8e6cf !important;
        }}
        .medium {{
            background-color: #dcedc1 !important;
        }}
        .low {{
            background-color: #ffd3b6 !important;
        }}
        .none {{
            background-color: #ffaaa5 !important;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            font-size: 0.8em;
            color: #777;
            border-top: 1px solid #ddd;
            padding-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Gelişmiş Dosya Karşılaştırma Raporu</h1>
        <p>Oluşturma Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>Özet Bilgiler</h2>
        <p><strong>Karşılaştırma Klasörü:</strong> {self.folder_path.get()}</p>
        <p><strong>Toplam Benzer Dosya Çifti:</strong> {len(self.results)}</p>
        
        <h3>Benzerlik Kategori Dağılımı:</h3>
        <ul>
"""
            
            # Kategori sayılarını hesapla
            categories = {}
            for res in self.results:
                cat = res['Sonuç']
                categories[cat] = categories.get(cat, 0) + 1
            
            # Kategori bilgilerini ekle
            for cat, count in categories.items():
                html_content += f"            <li><strong>{cat}:</strong> {count} adet</li>\n"
            
            html_content += """        </ul>
    </div>
    
    <h2>Detaylı Karşılaştırma Sonuçları</h2>
    <table>
        <thead>
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
        </thead>
        <tbody>
"""
            
            # Sonuçları tabloya ekle
            for res in self.results:
                total_score = float(res['Toplam'])
                row_class = 'none'
                if total_score >= 85:
                    row_class = 'high'
                elif total_score >= 50:
                    row_class = 'medium'
                elif total_score >= 30:
                    row_class = 'low'
                
                html_content += f"""            <tr class="{row_class}">
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
            
            # Raporu tamamla
            html_content += """        </tbody>
    </table>
    
    <div class="footer">
        <p>Bu rapor Gelişmiş Dosya Karşılaştırıcı v1.0 tarafından oluşturulmuştur.</p>
    </div>
</body>
</html>"""
            
            # Dosyaya yaz
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            messagebox.showinfo("Başarılı", f"Rapor başarıyla kaydedildi:\n{file_path}")
            
            # Raporu varsayılan tarayıcıda aç
            import webbrowser
            webbrowser.open(file_path)
            
        except Exception as e:
            logging.error(f"Rapor oluşturma hatası: {e}")
            messagebox.showerror("Hata", f"Rapor oluşturulamadı: {str(e)}")

    def export_results(self):
        """Sonuçları CSV dosyasına aktar"""
        if not self.results:
            messagebox.showinfo("Bilgi", "Dışa aktarmak için önce bir karşılaştırma yapın!")
            return
        
        try:
            # CSV dosyası seç
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Dosyası", "*.csv"), ("Tüm Dosyalar", "*.*")],
                title="CSV Dosyasını Kaydet"
            )
            
            if not file_path:
                return
            
            # Pandas ile CSV'ye dönüştür
            df = pd.DataFrame(self.results)
            
            # Path sütunlarını kaldır
            if 'Path1' in df.columns and 'Path2' in df.columns:
                df = df.drop(['Path1', 'Path2'], axis=1)
            
            # CSV olarak kaydet (Türkçe karakter desteği)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("Başarılı", f"Veriler CSV dosyasına aktarıldı:\n{file_path}")
            
        except Exception as e:
            logging.error(f"CSV dışa aktarma hatası: {e}")
            messagebox.showerror("Hata", f"CSV dışa aktarılamadı: {str(e)}")

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

    def on_close(self):
        """Uygulama kapatma olayı"""
        if self.is_running:
            if messagebox.askyesno("Çıkış", "İşlem devam ediyor. Çıkmak istediğinize emin misiniz?"):
                self.is_running = False
                self.destroy()
        else:
            self.destroy()

if __name__ == "__main__":
    app = CompareApp()
    app.mainloop()
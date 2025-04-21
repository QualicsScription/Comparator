import os
import sys
import time
import hashlib
import difflib
import threading
import logging
import webbrowser
import json
import random
import zipfile
from datetime import datetime
from collections import Counter
from PIL import Image, ImageTk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import customtkinter as ctk

# Uygulama sürümü
__version__ = "2.0.0"

# Loglama ayarları
logging.basicConfig(
    filename='file_comparator.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SWFileParser:
    def __init__(self):
        self.feature_tree_offset = 0x1000
        self.sketch_data_offset = 0x3000
        self.geometry_offset = -0x3000

    def parse_features(self, file_path):
        """SolidWorks dosyasından feature tree, sketch ve geometri bilgilerini çıkar"""
        try:
            with open(file_path, 'rb') as f:
                # Feature tree bölümü
                f.seek(self.feature_tree_offset)
                feature_header = f.read(100)
                feature_data = f.read(500)

                # Sketch data bölümü
                f.seek(self.sketch_data_offset)
                sketch_data = f.read(1000)

                # Geometri bölümü
                f.seek(self.geometry_offset, os.SEEK_END)
                geometry_data = f.read(2000)

                # Basit feature parsing - gerçek uygulamada daha karmaşık olabilir
                features = self.extract_feature_names(feature_data)
                sketches = self.extract_sketch_data(sketch_data)
                geometry_stats = self.extract_geometry_stats(geometry_data)

                return {
                    'features': features,
                    'sketches': sketches,
                    'geometry_stats': geometry_stats,
                    'raw_data': {
                        'feature_tree': feature_data,
                        'sketch_data': sketch_data,
                        'geometry': geometry_data
                    }
                }
        except Exception as e:
            logging.error(f"SolidWorks dosya parsing hatası: {e}")
            return {
                'features': [],
                'sketches': [],
                'geometry_stats': {},
                'raw_data': {
                    'feature_tree': b'',
                    'sketch_data': b'',
                    'geometry': b''
                }
            }

    def extract_feature_names(self, data):
        """Binary veriden feature isimlerini çıkarmaya çalışır"""
        try:
            # Gerçek uygulamada daha karmaşık bir algoritma kullanılabilir
            # Burada basit bir yaklaşım kullanıyoruz
            features = []
            # ASCII karakterleri ara
            i = 0
            while i < len(data):
                if data[i] > 32 and data[i] < 127:  # Yazdırılabilir ASCII
                    start = i
                    while i < len(data) and data[i] > 32 and data[i] < 127:
                        i += 1
                    if i - start > 3:  # En az 3 karakter uzunluğunda
                        feature_name = data[start:i].decode('ascii', errors='ignore')
                        features.append({
                            'name': feature_name,
                            'offset': start,
                            'params': {}
                        })
                i += 1
            return features
        except Exception as e:
            logging.error(f"Feature çıkarma hatası: {e}")
            return []

    def extract_sketch_data(self, data):
        """Sketch verilerini çıkar"""
        try:
            # Basit bir yaklaşım - gerçek uygulamada daha karmaşık olabilir
            sketches = []
            # Sketch marker'ları ara
            markers = [b'SKET', b'LINE', b'CIRC', b'RECT']
            for marker in markers:
                pos = 0
                while True:
                    pos = data.find(marker, pos)
                    if pos == -1:
                        break
                    sketches.append({
                        'type': marker.decode('ascii'),
                        'offset': pos,
                        'data': data[pos:pos+20]  # Örnek veri
                    })
                    pos += len(marker)
            return sketches
        except Exception as e:
            logging.error(f"Sketch çıkarma hatası: {e}")
            return []

    def extract_geometry_stats(self, data):
        """Geometri istatistiklerini çıkar"""
        try:
            # Gerçek uygulamada, geometri verilerinden hacim, yüzey sayısı gibi bilgiler çıkarılabilir
            # Burada basit bir yaklaşım kullanıyoruz
            stats = {
                'signature': hashlib.md5(data).digest(),  # Geometri imzası
                'data_size': len(data)
            }

            # Basit bir "volume" tahmini
            volume_markers = [b'VOL', b'VOLUME']
            for marker in volume_markers:
                pos = data.find(marker)
                if pos != -1 and pos + len(marker) + 8 <= len(data):
                    # Marker'dan sonraki 8 byte'dan bir sayı oluşturmaya çalış
                    try:
                        import struct
                        stats['volume'] = abs(struct.unpack('d', data[pos+len(marker):pos+len(marker)+8])[0])
                        break
                    except:
                        pass

            # Volume bulunamadıysa varsayılan değer
            if 'volume' not in stats:
                stats['volume'] = 1.0

            return stats
        except Exception as e:
            logging.error(f"Geometri istatistikleri çıkarma hatası: {e}")
            return {'signature': b'', 'data_size': 0, 'volume': 1.0}

    def get_assembly_references(self, file_path):
        """Montaj referanslarını çıkar"""
        try:
            # Dosya uzantısını kontrol et
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ['.sldprt', '.sldasm', '.slddrw']:
                return []

            # Dosyayı binary modda aç
            with open(file_path, 'rb') as f:
                data = f.read()

                # Montaj referanslarını ara
                references = []

                # Referans marker'ları
                markers = [b'ASSY', b'REF', b'COMP']

                # Her marker için arama yap
                for marker in markers:
                    pos = 0
                    while True:
                        pos = data.find(marker, pos)
                        if pos == -1:
                            break

                        # Referans ID'sini çıkarmaya çalış
                        try:
                            # Marker'dan sonraki 20 byte'a bak
                            ref_data = data[pos:pos+100]

                            # ASCII karakterleri bul
                            ascii_chars = []
                            for i in range(len(ref_data)):
                                if 32 < ref_data[i] < 127:  # Yazdırılabilir ASCII
                                    ascii_chars.append(chr(ref_data[i]))

                            # ASCII karakterleri birleştir
                            ref_id = ''.join(ascii_chars)

                            # Geçerli bir referans ID'si ise ekle
                            if len(ref_id) > 3 and not ref_id.isdigit():
                                references.append(ref_id)
                        except:
                            pass

                        pos += len(marker)

                # Benzersiz referansları döndür
                return list(set(references))
        except Exception as e:
            logging.error(f"Montaj referansları çıkarma hatası: {e}")
            return []

class SolidWorksAnalyzer:
    def __init__(self):
        self.parser = SWFileParser()
        self.binary_cache = {}  # Binary veri önbelleği
        self.weights = {
            'metadata': 0.25,
            'hash': 0.15,
            'content': 0.30,
            'structure': 0.30
        }

    def _check_assembly_relation(self, file1, file2):
        """Montaj ilişkisi kontrolü"""
        try:
            asm1 = self._get_assembly_info(file1)
            asm2 = self._get_assembly_info(file2)

            # Ortak referansları bul
            common_refs = set(asm1['references']) & set(asm2['references'])

            return {
                'same_assembly': len(common_refs) > 0,
                'assembly_name': list(common_refs)[0] if common_refs else None,
                'common_refs': list(common_refs)
            }
        except Exception as e:
            logging.error(f"Montaj ilişkisi kontrolü hatası: {e}")
            return {'same_assembly': False, 'assembly_name': None, 'common_refs': []}

    def _get_assembly_info(self, file_path):
        """Dosyanın montaj bilgilerini al"""
        try:
            # Montaj referanslarını bul
            assembly_refs = self.parser.get_assembly_references(file_path)

            # Montaj içi parça mı?
            is_in_assembly = len(assembly_refs) > 0
            assembly_id = hashlib.md5(str(assembly_refs).encode()).hexdigest() if assembly_refs else None

            return {
                'is_in_assembly': is_in_assembly,
                'references': assembly_refs,
                'assembly_id': assembly_id,
                'assembly_name': assembly_refs[0] if assembly_refs else None
            }
        except Exception as e:
            logging.error(f"Montaj bilgisi alma hatası: {e}")
            return {'is_in_assembly': False, 'references': [], 'assembly_id': None, 'assembly_name': None}

    def compare(self, file1, file2):
        """İki SolidWorks dosyasını karşılaştırır"""
        try:
            # Hash kontrolü
            if self._compare_hash(file1, file2):
                return self._create_exact_match()

            # Metadata karşılaştırması
            metadata_sim = self._compare_metadata(file1, file2)

            # Feature tree karşılaştırması
            feature_sim = self._compare_features(
                self._extract_features(file1),
                self._extract_features(file2)
            )

            # Sketch karşılaştırması
            sketch_sim = self._compare_sketches(
                self._extract_sketches(file1),
                self._extract_sketches(file2)
            )

            # Geometri karşılaştırması
            geom_sim = self._compare_geometry(
                self._extract_geometry(file1),
                self._extract_geometry(file2)
            )

            # SaveAs kontrolü
            if self._is_save_as(metadata_sim, geom_sim, feature_sim):
                return self._create_save_as_match()

            # Montaj kontrolü
            asm_info = self._check_assembly_relation(file1, file2)
            assembly_bonus = None

            # Final skor hesaplama
            total_score = self._calculate_final_score(
                metadata_sim,
                feature_sim,
                sketch_sim,
                geom_sim
            )

            # Montaj bonusu uygula
            if asm_info['same_assembly']:
                # Montaj bonusu ile skor güncelleme
                total_score = self._apply_assembly_bonus(total_score, file1, file2)
                assembly_bonus = {
                    'assembly_name': asm_info['assembly_name'],
                    'common_refs': asm_info['common_refs'],
                    'bonus_applied': True
                }

            # Benzerlik değerlendirmesi
            similarity_category = self._categorize_similarity(total_score)

            result = {
                'score': total_score,
                'details': {
                    'metadata': metadata_sim,
                    'feature_tree': feature_sim,
                    'sketch_data': sketch_sim,
                    'geometry': geom_sim
                },
                'match': total_score > 95,
                'type': 'solidworks',
                'similarity_category': similarity_category
            }

            # Montaj bilgilerini ekle
            if assembly_bonus:
                result['assembly_relation'] = assembly_bonus

            return result

        except Exception as e:
            logging.error(f"SolidWorks karşılaştırma hatası: {e}")
            return self._create_error_result()

    def _extract_features(self, file_path):
        """Feature ağacını çıkar"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                # Feature ağacı bölümünü bul
                start = data.find(b'FeatureData')
                if start != -1:
                    end = data.find(b'EndFeatureData', start)
                    if end != -1:
                        return data[start:end]
            return None
        except Exception as e:
            logging.error(f"Feature çıkarma hatası: {e}")
            return None

    def _extract_sketches(self, file_path):
        """Sketch verilerini çıkar"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                # Sketch bölümünü bul
                start = data.find(b'SketchData')
                if start != -1:
                    end = data.find(b'EndSketchData', start)
                    if end != -1:
                        return data[start:end]
            return None
        except Exception as e:
            logging.error(f"Sketch çıkarma hatası: {e}")
            return None

    def _extract_geometry(self, file_path):
        """Geometri verilerini çıkar"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                # Geometri bölümünü bul
                start = data.find(b'GeometryData')
                if start != -1:
                    end = data.find(b'EndGeometryData', start)
                    if end != -1:
                        return data[start:end]
            return None
        except Exception as e:
            logging.error(f"Geometri çıkarma hatası: {e}")
            return None

    def _compare_metadata(self, file1, file2):
        """Metadata karşılaştırması"""
        try:
            # Dosya boyutu karşılaştırması
            size1 = os.path.getsize(file1)
            size2 = os.path.getsize(file2)
            size_ratio = min(size1, size2) / max(size1, size2) if max(size1, size2) > 0 else 0
            size_similarity = size_ratio * 100

            # Zaman damgası karşılaştırması
            stat1 = os.stat(file1)
            stat2 = os.stat(file2)
            time_diff = abs(stat1.st_mtime - stat2.st_mtime)
            time_similarity = max(0, 100 - (time_diff / 86400 * 100)) if time_diff < 86400 else 0

            # Ağırlıklı metadata benzerliği
            return size_similarity * 0.8 + time_similarity * 0.2
        except Exception as e:
            logging.error(f"Metadata karşılaştırma hatası: {e}")
            return 0.0

    def _compare_content(self, data1, data2):
        """İçerik karşılaştırması"""
        try:
            # Sketch karşılaştırması
            sketch_sim = self._compare_sketches(data1['sketches'], data2['sketches'])

            # Geometri karşılaştırması
            geom_sim = self._compare_geometry(data1['geometry_stats'], data2['geometry_stats'])

            # Ağırlıklı içerik benzerliği
            return sketch_sim * 0.4 + geom_sim * 0.6
        except Exception as e:
            logging.error(f"İçerik karşılaştırma hatası: {e}")
            return 0.0

    def _compare_structure(self, data1, data2):
        """Yapı karşılaştırması"""
        try:
            # Feature ağacı karşılaştırması
            feature_sim = self._compare_features(data1['features'], data2['features'])

            # Feature sayısı karşılaştırması
            count_sim = min(len(data1['features']), len(data2['features'])) / \
                        max(len(data1['features']), len(data2['features'])) * 100 if max(len(data1['features']), len(data2['features'])) > 0 else 0

            # Ağırlıklı yapı benzerliği
            return feature_sim * 0.7 + count_sim * 0.3
        except Exception as e:
            logging.error(f"Yapı karşılaştırma hatası: {e}")
            return 0.0

    def _is_save_as(self, metadata_sim, content_sim, structure_sim):
        """SaveAs kontrolü"""
        # SaveAs kriterleri güncellendi
        return (
            metadata_sim > 60 and    # Metadata benzer olmalı
            content_sim > 90 and     # Geometri neredeyse aynı olmalı
            structure_sim > 10       # Yapı biraz benzer olmalı
        )

    def _is_save_as_copy(self, file1, file2, data1, data2):
        """SaveAs kontrolü - Gelişmiş versiyon"""
        try:
            # Metadata kontrolü
            size_ratio = min(os.path.getsize(file1), os.path.getsize(file2)) / \
                        max(os.path.getsize(file1), os.path.getsize(file2))

            # Feature kontrolü
            feature_match = self._compare_features(data1['features'], data2['features'])

            # Geometri kontrolü
            geom_sim = self._compare_geometry(data1['geometry_stats'], data2['geometry_stats'])

            # Zaman damgası kontrolü
            time_diff = abs(os.path.getmtime(file1) - os.path.getmtime(file2))
            time_sim = 1.0 if time_diff < 3600 else 0.0  # 1 saat içinde

            # SaveAs kriterleri
            return (
                size_ratio > 0.95 and     # Boyut çok benzer
                feature_match > 70.0 and   # Feature yapısı benzer
                geom_sim > 95.0 and       # Geometri neredeyse aynı
                time_sim > 0.0            # Yakın zamanda oluşturulmuş
            )
        except Exception as e:
            logging.error(f"SaveAs kontrolü hatası: {e}")
            return False

    def _create_save_as_match(self):
        """SaveAs eşleşme sonucu"""
        return {
            'score': 95.0,
            'details': {
                'metadata': 95.0,
                'hash': 0.0,
                'content': 95.0,
                'structure': 90.0
            },
            'match': True,
            'type': 'save_as'
        }

    def _categorize_similarity(self, score):
        """Benzerlik kategorisini belirle"""
        if score >= 99:
            return "Tam Eşleşme"
        elif score >= 90:
            return "SaveAs Kopyası"
        elif score >= 70:
            return "Küçük Değişiklikler"
        elif score >= 40:
            return "Büyük Değişiklikler"
        elif score >= 20:
            return "Az Benzer"
        else:
            return "Farklı Dosyalar"

    def _evaluate_similarity(self, metadata_sim, content_sim, structure_sim):
        """Benzerlik değerlendirmesi"""
        if content_sim > 95:  # Geometri neredeyse aynı
            if metadata_sim > 90:  # Metadata da çok benzer
                return "SaveAs ile oluşturulmuş"
            elif structure_sim > 40:  # Yapı kısmen benzer
                return "Farklı yöntemle oluşturulmuş benzer parça"
            else:
                return "Benzer geometri, farklı oluşturma yöntemi"
        else:
            if structure_sim > 70:
                return "Benzer yapı, farklı geometri"
            elif metadata_sim > 90:
                return "Benzer kaynak, farklı parça"
            else:
                return "Farklı parçalar"

    def _apply_assembly_bonus(self, score, file1, file2):
        """Montaj ilişkisi bonusu"""
        try:
            # Aynı montajdan gelen parçalar için bonus
            if self._are_in_same_assembly(file1, file2):
                return min(100, score * 1.15)  # %15 bonus
            return score
        except Exception as e:
            logging.error(f"Montaj bonusu uygulama hatası: {e}")
            return score

    def _are_in_same_assembly(self, file1, file2):
        """Aynı montajda mı kontrolü"""
        try:
            # Montaj ilişkilerini kontrol et
            asm_info = self._check_assembly_relation(file1, file2)
            return asm_info['same_assembly']
        except Exception as e:
            logging.error(f"Montaj kontrolü hatası: {e}")
            return False

    def _compare_hash(self, file1, file2):
        """Hash karşılaştırması"""
        try:
            hash1 = hashlib.md5(open(file1, 'rb').read()).hexdigest()
            hash2 = hashlib.md5(open(file2, 'rb').read()).hexdigest()
            return hash1 == hash2
        except:
            return False

    def _compare_binary(self, file1, file2):
        """Binary karşılaştırma"""
        try:
            # Önbellek anahtarı
            cache_key = f"{file1}:{file2}"
            if cache_key in self.binary_cache:
                return self.binary_cache[cache_key]

            # Önce hızlı boyut kontrolü
            size1 = os.path.getsize(file1)
            size2 = os.path.getsize(file2)

            # Boyut oranı çok farklıysa, hızlıca düşük benzerlik döndür
            if min(size1, size2) / max(size1, size2) < 0.5:  # %50'den fazla boyut farkı
                self.binary_cache[cache_key] = 0.3  # Düşük benzerlik
                return 0.3

            # Önbellekte yoksa hesapla
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                # Çok büyük dosyalar için gelişmiş örnekleme
                if size1 > 5*1024*1024 or size2 > 5*1024*1024:  # 5MB'dan büyük
                    # Daha fazla örnekleme noktası kullan
                    sample_size = 4096  # 4KB örnekler
                    sample_count = 10    # 10 farklı noktadan örnekle

                    samples1 = []
                    samples2 = []

                    # Başlangıç örneği
                    f1.seek(0)
                    f2.seek(0)
                    samples1.append(f1.read(sample_size))
                    samples2.append(f2.read(sample_size))

                    # Dosya boyunca eşit aralıklarla örnekler al
                    for i in range(1, sample_count-1):
                        pos1 = (size1 * i) // sample_count
                        pos2 = (size2 * i) // sample_count

                        f1.seek(pos1)
                        f2.seek(pos2)

                        samples1.append(f1.read(sample_size))
                        samples2.append(f2.read(sample_size))

                    # Son örnek
                    try:
                        f1.seek(-sample_size, os.SEEK_END)
                        f2.seek(-sample_size, os.SEEK_END)
                    except:
                        f1.seek(0, os.SEEK_END)
                        f2.seek(0, os.SEEK_END)
                        f1.seek(max(0, f1.tell() - sample_size))
                        f2.seek(max(0, f2.tell() - sample_size))

                    samples1.append(f1.read(sample_size))
                    samples2.append(f2.read(sample_size))

                    # Tüm örnekleri birleştir
                    combined1 = b''.join(samples1)
                    combined2 = b''.join(samples2)

                    # Hızlı hash kontrolü
                    if hashlib.md5(combined1).digest() == hashlib.md5(combined2).digest():
                        ratio = 0.95  # Örnekler aynıysa, yüksek benzerlik
                    else:
                        # Örnekleri karşılaştır
                        ratio = difflib.SequenceMatcher(None, combined1, combined2).ratio()
                else:
                    # Küçük dosyalar için daha hızlı karşılaştırma
                    # Önce hash kontrolü
                    f1.seek(0)
                    f2.seek(0)
                    data1 = f1.read()
                    data2 = f2.read()

                    if hashlib.md5(data1).digest() == hashlib.md5(data2).digest():
                        ratio = 1.0  # Tam eşleşme
                    else:
                        # Boyut çok küçükse tam karşılaştırma, değilse örnekleme
                        if len(data1) < 1024*1024 and len(data2) < 1024*1024:  # 1MB'dan küçük
                            ratio = difflib.SequenceMatcher(None, data1, data2).ratio()
                        else:
                            # Örnekleme yap
                            sample_size = min(len(data1), len(data2), 4096)
                            samples = [
                                (data1[:sample_size], data2[:sample_size]),  # Başlangıç
                                (data1[len(data1)//2:len(data1)//2+sample_size], data2[len(data2)//2:len(data2)//2+sample_size]),  # Orta
                                (data1[-sample_size:], data2[-sample_size:])  # Son
                            ]

                            # Örneklerin benzerliklerini hesapla
                            similarities = [difflib.SequenceMatcher(None, s1, s2).ratio() for s1, s2 in samples]
                            ratio = sum(similarities) / len(similarities)

            # Sonuçları önbelleğe kaydet
            self.binary_cache[cache_key] = ratio
            return ratio
        except Exception as e:
            logging.error(f"Binary karşılaştırma hatası: {e}")
            return 0.0

    def _is_save_as_copy(self, file1, file2, data1, data2):
        """SaveAs kontrolü"""
        try:
            # Metadata kontrolü
            size_ratio = min(os.path.getsize(file1), os.path.getsize(file2)) / \
                        max(os.path.getsize(file1), os.path.getsize(file2))

            # Feature kontrolü
            feature_match = self._compare_features(data1['features'], data2['features'])

            # Geometri kontrolü
            geom_sim = self._compare_geometry(data1['geometry_stats'], data2['geometry_stats'])

            # SaveAs kriterleri güncellendi
            return (size_ratio > 0.90 and  # Boyut benzerliği
                    feature_match > 80.0 and  # Feature benzerliği
                    geom_sim > 85.0)  # Geometri benzerliği
        except Exception as e:
            logging.error(f"SaveAs kontrolü hatası: {e}")
            return False

    def _compare_features(self, features1, features2):
        """Feature karşılaştırması"""
        if not features1 or not features2:
            return 0.0

        return difflib.SequenceMatcher(None, features1, features2).ratio() * 100

    def _compare_parameters(self, params1, params2):
        """Parametre karşılaştırması"""
        if not params1 or not params2:
            return 0.0

        matches = 0
        total_params = max(len(params1), len(params2))

        for key in params1:
            if key in params2:
                if isinstance(params1[key], (int, float)) and isinstance(params2[key], (int, float)):
                    # Sayısal değerler için tolerans
                    tolerance = 0.001
                    if abs(params1[key] - params2[key]) <= tolerance * abs(params1[key] or 1):
                        matches += 1
                else:
                    # Diğer değerler için tam eşleşme
                    if params1[key] == params2[key]:
                        matches += 1

        return matches / total_params if total_params > 0 else 0

    def _compare_sketches(self, sketches1, sketches2):
        """Sketch karşılaştırması"""
        if not sketches1 or not sketches2:
            return 0.0

        return difflib.SequenceMatcher(None, sketches1, sketches2).ratio() * 100

    def _compare_geometry(self, geom1, geom2):
        """Geometri karşılaştırması"""
        if not geom1 or not geom2:
            return 0.0

        return difflib.SequenceMatcher(None, geom1, geom2).ratio() * 100

    def _calculate_final_score(self, metadata_sim, feature_sim, sketch_sim, geom_sim):
        """Final skor hesaplama"""
        weights = {
            'metadata': 0.15,
            'feature': 0.30,
            'sketch': 0.25,
            'geometry': 0.30
        }

        base_score = (
            metadata_sim * weights['metadata'] +
            feature_sim * weights['feature'] +
            sketch_sim * weights['sketch'] +
            geom_sim * weights['geometry']
        )

        # Geometri bonusu
        if geom_sim > 95:
            base_score *= 1.1  # %10 bonus

        # Feature tree bonusu
        if feature_sim > 90:
            base_score *= 1.05  # %5 bonus

        return min(100, base_score)

    def _create_exact_match(self):
        """Tam eşleşme sonucu"""
        return {
            'score': 100.0,  # 86.0'dan 100.0'a çıkarılmalı
            'details': {
                'metadata': 100.0,
                'hash': 100.0,
                'content': 100.0,
                'structure': 100.0,
                'feature_tree': 100.0,
                'sketch_data': 100.0,
                'geometry': 100.0
            },
            'size_similarity': 100.0,
            'match': True,
            'type': 'exact'
        }

    def _create_save_as_match(self):
        """SaveAs eşleşme sonucu"""
        return {
            'score': 95.0,
            'details': {
                'feature_tree': 95.0,
                'sketch_data': 95.0,
                'geometry': 95.0
            },
            'size_similarity': 95.0,
            'match': False,
            'type': 'solidworks'
        }

    def _create_error_result(self):
        """Hata sonucu"""
        return {
            'score': 0.0,
            'details': {
                'feature_tree': 0.0,
                'sketch_data': 0.0,
                'geometry': 0.0
            },
            'size_similarity': 0.0,
            'match': False,
            'type': 'solidworks'
        }

class GeneralComparator:
    def __init__(self):
        pass

    def compare(self, file1, file2):
        """Genel dosya karşılaştırması"""
        try:
            # Metadata karşılaştırması
            stat1 = os.stat(file1)
            stat2 = os.stat(file2)

            # Boyut benzerliği
            size_diff = abs(stat1.st_size - stat2.st_size)
            max_size = max(stat1.st_size, stat2.st_size)
            size_similarity = (1 - (size_diff / max_size)) * 100 if max_size > 0 else 0

            # Zaman damgası benzerliği
            time_diff = abs(stat1.st_mtime - stat2.st_mtime)
            time_similarity = max(0, 100 - (time_diff / 86400 * 100)) if time_diff < 86400 else 0

            # İçerik karşılaştırması
            content_similarity = 0
            try:
                with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                    # Dosya başlangıcı
                    header1 = f1.read(1024)
                    header2 = f2.read(1024)
                    header_similarity = difflib.SequenceMatcher(None, header1, header2).ratio() * 100

                    # Dosya ortası
                    f1.seek(stat1.st_size // 2)
                    f2.seek(stat2.st_size // 2)
                    mid1 = f1.read(1024)
                    mid2 = f2.read(1024)
                    mid_similarity = difflib.SequenceMatcher(None, mid1, mid2).ratio() * 100

                    content_similarity = (header_similarity * 0.6 + mid_similarity * 0.4)
            except:
                content_similarity = 0

            # Hash kontrolü
            hash_match = False
            if size_similarity > 99:
                try:
                    hash1 = hashlib.md5(open(file1, 'rb').read()).hexdigest()
                    hash2 = hashlib.md5(open(file2, 'rb').read()).hexdigest()
                    hash_match = (hash1 == hash2)
                except:
                    pass

            # Toplam skor
            total_score = (
                size_similarity * 0.3 +
                time_similarity * 0.2 +
                content_similarity * 0.5
            )

            return {
                'score': total_score,
                'size_similarity': size_similarity,
                'time_similarity': time_similarity,
                'content_similarity': content_similarity,
                'match': hash_match,
                'type': 'general'
            }
        except Exception as e:
            logging.error(f"Genel karşılaştırma hatası: {e}")
            return {'score': 0, 'match': False, 'type': 'general'}

class FileComparator:
    """Dosya karşılaştırma işlemlerini yöneten sınıf."""

    def __init__(self):
        self.supported_extensions = {
            'solidworks': ['.sldprt', '.sldasm', '.slddrw'],
            'cad': ['.step', '.stp', '.iges', '.igs', '.stl', '.obj', '.dxf'],
            'document': ['.docx', '.xlsx', '.pdf', '.txt'],
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'],
            'all': []
        }

        # Özel karşılaştırıcılar
        self.solidworks_comparator = SolidWorksAnalyzer()
        self.general_comparator = GeneralComparator()

        # Tüm uzantıları 'all' kategorisine ekle
        for exts in self.supported_extensions.values():
            self.supported_extensions['all'].extend(exts)

        # Karşılaştırma eşikleri
        self.thresholds = {
            'exact_match': 99.0,    # Birebir aynı
            'save_as': 85.0,        # SaveAs ile oluşturulmuş
            'high_similarity': 70.0, # Çok benzer
            'similar': 50.0,        # Benzer
            'low_similarity': 30.0,  # Az benzer
            'different': 10.0       # Farklı
        }

    def compare_files(self, file1, file2):
        """İki dosyayı kapsamlı şekilde karşılaştırır."""
        try:
            # Önce hızlı kontroller

            # Aynı dosya mı?
            if file1 == file2:
                return self._create_result(100.0, "Birebir Aynı", file1, file2, "Aynı dosya")

            # Dosya boyutu kontrolü
            size1 = os.path.getsize(file1)
            size2 = os.path.getsize(file2)

            # Boyut oranı çok farklıysa, hızlıca düşük benzerlik döndür
            if min(size1, size2) / max(size1, size2) < 0.3:  # %70'den fazla boyut farkı
                return self._create_result(20.0, "Farklı Dosyalar", file1, file2, "Dosya boyutları çok farklı")

            # Dosya türü kontrolü
            ext1 = os.path.splitext(file1)[1].lower()
            ext2 = os.path.splitext(file2)[1].lower()

            # Farklı uzantılı dosyaları karşılaştırmayı reddet
            if ext1 != ext2:
                return self._create_result(0.0, "Farklı Dosya Türleri", file1, file2, "Dosya uzantıları farklı")

            # Hızlı hash kontrolü (küçük dosyalar için)
            if size1 < 10*1024*1024 and size2 < 10*1024*1024:  # 10MB'dan küçük
                try:
                    hash1 = hashlib.md5(open(file1, 'rb').read()).hexdigest()
                    hash2 = hashlib.md5(open(file2, 'rb').read()).hexdigest()
                    if hash1 == hash2:
                        return self._create_result(100.0, "Birebir Aynı", file1, file2, "Hash değerleri aynı")
                except:
                    pass  # Hash kontrolü başarısız olursa normal karşılaştırmaya devam et

            # SolidWorks dosyaları için özel karşılaştırma
            if ext1 in self.supported_extensions['solidworks']:
                result = self._compare_solidworks_files(file1, file2)
            else:
                result = self._compare_general_files(file1, file2)

            return self._categorize_result(result, file1, file2)

        except Exception as e:
            logging.error(f"Dosya karşılaştırma hatası: {e}")
            return self._create_result(0.0, f"Hata: {str(e)}", file1, file2, f"Karşılaştırma hatası: {str(e)}")

    def _compare_solidworks_files(self, file1, file2):
        """SolidWorks dosyalarını karşılaştırır."""
        try:
            sw_result = self.solidworks_comparator.compare(file1, file2)

            # Binary karşılaştırma (hızlı kontrol)
            if sw_result.get('match', False):
                return {'score': 100.0, 'match': True}

            # Detaylı karşılaştırma
            feature_similarity = sw_result.get('details', {}).get('feature_tree', 0)
            sketch_similarity = sw_result.get('details', {}).get('sketch_data', 0)
            geometry_similarity = sw_result.get('details', {}).get('geometry', 0)
            metadata_similarity = sw_result.get('size_similarity', 0)

            # Ağırlıklı skorlama - değerleri ayarladım
            weights = {
                'feature_tree': 0.35,    # Feature ağacı benzerliği
                'sketch_data': 0.25,     # Sketch verileri
                'geometry': 0.30,        # Geometri benzerliği
                'metadata': 0.10         # Metadata
            }

            # Minimum benzerlik kontrolü
            if geometry_similarity > 90:  # Geometri çok benzerse
                feature_similarity = max(feature_similarity, 70)  # Feature tree minimum %70
                sketch_similarity = max(sketch_similarity, 70)    # Sketch data minimum %70

            total_score = (
                feature_similarity * weights['feature_tree'] +
                sketch_similarity * weights['sketch_data'] +
                geometry_similarity * weights['geometry'] +
                metadata_similarity * weights['metadata']
            )

            # SaveAs kontrolü
            if metadata_similarity > 90 and geometry_similarity > 80:
                total_score = max(total_score, 95)  # SaveAs için minimum %95

            return {
                'score': total_score,
                'match': total_score > 99,
                'details': {
                    'feature_tree': feature_similarity,
                    'sketch_data': sketch_similarity,
                    'geometry': geometry_similarity,
                    'metadata': metadata_similarity
                }
            }
        except Exception as e:
            logging.error(f"SolidWorks karşılaştırma hatası: {e}")
            return {'score': 0, 'match': False, 'details': {}}

    def _compare_general_files(self, file1, file2):
        """Genel dosya karşılaştırması yapar."""
        result = self.general_comparator.compare(file1, file2)

        # Hash kontrolü
        if result.get('match', False):
            return {'score': 100.0, 'match': True}

        # Ağırlıklı skorlama
        weights = {
            'content_similarity': 0.6,
            'size_similarity': 0.2,
            'time_similarity': 0.2
        }

        total_score = (
            result.get('content_similarity', 0) * weights['content_similarity'] +
            result.get('size_similarity', 0) * weights['size_similarity'] +
            result.get('time_similarity', 0) * weights['time_similarity']
        )

        return {'score': total_score, 'match': False}

    def _categorize_result(self, result, file1, file2):
        """Karşılaştırma sonucunu kategorize eder."""
        score = result['score']

        # Birebir kopya kontrolü
        if score >= self.thresholds['exact_match']:
            return self._create_result(100.0, "Birebir Aynı", file1, file2,
                                     "Dosyalar birebir aynı")

        # SaveAs kontrolü
        if score >= self.thresholds['save_as']:
            return self._create_result(95.0, "Save As Kopyası", file1, file2,
                                     "Dosya farklı kaydedilmiş")

        # Çok benzer dosyalar
        if score >= self.thresholds['high_similarity']:
            return self._create_result(score, "Çok Benzer", file1, file2,
                                     "Dosyalar çok benzer yapıda")

        # Benzer dosyalar
        if score >= self.thresholds['similar']:
            return self._create_result(score, "Benzer", file1, file2,
                                     "Dosyalar benzer özellikler içeriyor")

        # Az benzer dosyalar
        if score >= self.thresholds['low_similarity']:
            return self._create_result(score, "Az Benzer", file1, file2,
                                     "Dosyalar az benzerlik gösteriyor")

        # Farklı dosyalar
        if score >= self.thresholds['different']:
            return self._create_result(score, "Minimal Benzerlik", file1, file2,
                                     "Dosyalar minimal benzerlik gösteriyor")

        # Tamamen farklı dosyalar
        return self._create_result(score, "Farklı Dosyalar", file1, file2,
                                 "Dosyalar tamamen farklı")

    def _create_result(self, score, category, file1, file2, description="", match=False):
        """Standart sonuç sözlüğü oluşturur."""
        # Metadata, hash, content ve structure değerlerini hesapla
        metadata = min(score * 1.1, 100) if score > 0 else 0  # Metadata biraz daha yüksek
        hash_score = 100 if score > 99 else (score * 0.8)     # Hash düşük
        content = score * 0.9                                # İçerik biraz daha düşük
        structure = score * 1.1 if score < 90 else score      # Yapı biraz daha yüksek

        # Manipulasyon analizi
        manipulation = {
            'detected': False,
            'score': 0,
            'type': 'Yok'
        }

        # Eğer skor 90-99 arasındaysa, muhtemel SaveAs
        if 90 <= score < 99:
            manipulation = {
                'detected': True,
                'score': 80,
                'type': 'SaveAs'
            }

        return {
            'file1': os.path.basename(file1),
            'file2': os.path.basename(file2),
            'total': round(score, 2),
            'metadata': round(metadata, 2),
            'hash': round(hash_score, 2),
            'content': round(content, 2),
            'structure': round(structure, 2),
            'category': category,
            'description': description,
            'match': match,
            'manipulation': manipulation,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'file_type': os.path.splitext(file1)[1].lower()[1:] if os.path.splitext(file1)[1] else 'unknown'
        }

    """Dosya karşılaştırma işlemlerini yöneten sınıf."""

    def __init__(self):
        self.supported_extensions = {
            'solidworks': ['.sldprt', '.sldasm', '.slddrw'],
            'cad': ['.step', '.stp', '.iges', '.igs', '.stl', '.obj', '.dxf'],
            'document': ['.docx', '.xlsx', '.pdf', '.txt'],
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'],
            'all': []
        }

        # Özel karşılaştırıcılar
        self.solidworks_comparator = SolidWorksAnalyzer()
        self.general_comparator = GeneralComparator()

        # Tüm uzantıları 'all' kategorisine ekle
        for exts in self.supported_extensions.values():
            self.supported_extensions['all'].extend(exts)

    # Eski karşılaştırma metodları kaldırıldı ve özel karşılaştırıcı sınıfları ile değiştirildi

    def detect_manipulation(self, file1, file2, comparison_results):
        """Dosya manipülasyonlarını tespit eder."""
        try:
            # Metadata bilgilerini al
            stat1 = os.stat(file1)
            stat2 = os.stat(file2)

            # Manipülasyon göstergeleri
            indicators = {
                'size_ratio': min(stat1.st_size, stat2.st_size) / max(stat1.st_size, stat2.st_size) if max(stat1.st_size, stat2.st_size) > 0 else 0,
                'time_diff': 1 - (abs(stat1.st_mtime - stat2.st_mtime) / 86400 if abs(stat1.st_mtime - stat2.st_mtime) < 86400 else 0),
                'content_injection': max(0, comparison_results['semantic']['score'] - comparison_results['hash']['score']) / 100,
                'rename_pattern': difflib.SequenceMatcher(None, os.path.basename(file1), os.path.basename(file2)).ratio()
            }

            # Manipülasyon skoru
            weights = {
                'size_ratio': 0.2,
                'time_diff': 0.3,
                'content_injection': 0.3,
                'rename_pattern': 0.2
            }

            manipulation_score = sum(indicators[key] * weights[key] for key in indicators)

            # Manipülasyon türünü belirle
            manipulation_type = 'none'
            if manipulation_score > 0.7:
                if indicators['content_injection'] > 0.5:
                    manipulation_type = 'content_injection'
                elif indicators['time_diff'] > 0.8:
                    manipulation_type = 'quick_edit'
                elif indicators['rename_pattern'] > 0.7:
                    manipulation_type = 'rename'
                else:
                    manipulation_type = 'unknown'

            return {
                'detected': manipulation_score > 0.7,
                'score': manipulation_score * 100,
                'type': manipulation_type,
                'indicators': indicators
            }
        except Exception as e:
            logging.error(f"Manipülasyon tespit hatası: {e}")
            return {
                'detected': False,
                'score': 0,
                'type': 'none',
                'indicators': {}
            }

    def classify_result(self, score, hash_match, file_type):
        """Dosya tipine göre sınıflandırma"""
        if file_type == 'solidworks':
            if hash_match: return "Tam Eşleşme"
            elif score >= 98: return "Tam Eşleşme"
            elif score >= 85: return "Save As Kopyası"
            elif score >= 70: return "Küçük Değişiklikler"
            elif score >= 40: return "Büyük Değişiklikler"
            else: return "Farklı Dosyalar"
        else:
            # Diğer dosya tipleri için genel sınıflandırma
            if hash_match: return "Tam Eşleşme"
            elif score >= 95: return "Neredeyse Aynı"
            elif score >= 80: return "Çok Benzer"
            elif score >= 60: return "Orta Benzerlik"
            elif score >= 30: return "Zayıf Benzerlik"
            else: return "Farklı Dosyalar"

    def compare_files(self, file1, file2):
        """İki dosyayı kapsamlı şekilde karşılaştırır."""
        try:
            ext = os.path.splitext(file1)[1].lower()

            # Dosya tipine göre uygun karşılaştırıcıyı kullan
            if ext in ['.sldprt', '.sldasm', '.slddrw']:
                sw_result = self.solidworks_comparator.compare(file1, file2)
                file_type = 'solidworks'

                # SolidWorks için özel işleme
                # Metadata karşılaştırmayı kısıtla
                metadata_score = min(sw_result.get('size_similarity', 0), 30)

                # Detaylı sonuçları al
                details = sw_result.get('details', {})

                # Sonuç sözlüğünü oluştur
                result = {
                    'score': sw_result['score'] * 0.8 + metadata_score * 0.2,
                    'match': sw_result.get('match', False),
                    'size_similarity': sw_result.get('size_similarity', 0),
                    'feature_tree': details.get('feature_tree', 0),
                    'sketch_data': details.get('sketch_data', 0),
                    'geometry': details.get('geometry', 0),
                    'type': 'solidworks'
                }
            else:
                result = self.general_comparator.compare(file1, file2)
                file_type = result.get('type', 'general')

            # Manipülasyon tespiti
            manipulation = self.detect_manipulation(file1, file2, {
                'metadata': {'score': result.get('size_similarity', 0)},
                'hash': {'score': 100 if result.get('match', False) else 0},
                'semantic': {'score': result.get('content_similarity', 0) if file_type != 'solidworks' else result.get('geometry', 0)},
                'structure': {'score': result.get('feature_tree', 0) if file_type == 'solidworks' else 0}
            })

            # Sonuç kategorizasyonu
            category = self.classify_result(result['score'], result.get('match', False), file_type)

            # Sonuç sözlüğünü oluştur
            comparison_result = {
                'file1': file1,
                'file2': file2,
                'total': result['score'],
                'category': category,
                'manipulation': manipulation,
                'file_type': file_type,
                'match': result.get('match', False)
            }

            # Dosya tipine göre ek bilgileri ekle
            if file_type == 'solidworks':
                comparison_result.update({
                    'metadata': result.get('size_similarity', 0),
                    'hash': 100 if result.get('match', False) else 0,
                    'content': result.get('geometry', 0),  # Geometri verilerini içerik olarak göster
                    'structure': result.get('feature_tree', 0),  # Feature tree'yi yapı olarak göster
                    'details': {
                        'feature_tree': result.get('feature_tree', 0),
                        'sketch_data': result.get('sketch_data', 0),
                        'geometry': result.get('geometry', 0)
                    }
                })
            else:
                comparison_result.update({
                    'metadata': (result.get('size_similarity', 0) * 0.7 + result.get('time_similarity', 0) * 0.3),
                    'hash': 100 if result.get('match', False) else 0,
                    'content': result.get('content_similarity', 0),
                    'structure': 0  # Genel dosyalar için kullanılmıyor
                })

            return comparison_result
        except Exception as e:
            logging.error(f"Dosya karşılaştırma hatası: {e}")
            return {
                'file1': file1,
                'file2': file2,
                'metadata': 0,
                'hash': 0,
                'content': 0,
                'structure': 0,
                'total': 0,
                'category': "Hata",
                'manipulation': {'detected': False},
                'file_type': 'unknown',
                'match': False,
                'error': str(e)
            }

class ModernFileComparator(ctk.CTk):
    """Modern arayüzlü dosya karşılaştırma uygulaması."""

    def __init__(self):
        super().__init__()

        # Pencere ayarları
        self.title(f"Gelişmiş Dosya Karşılaştırıcı v{__version__}")
        self.geometry("1400x800")
        self.minsize(1200, 700)

        # Tema ayarları
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

        # Pencere kapatma protokolünü ayarla
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # After ID'lerini saklamak için liste
        self.after_ids = []

        # Özel başlık çubuğu
        self.create_custom_title_bar()

        # Karşılaştırıcı nesnesi
        self.comparator = FileComparator()
        self.results = []
        self.is_running = False

        # Kullanıcı arayüzü
        self.setup_ui()

        # Pencere boyutlandırma olayları
        self.bind("<Configure>", self.on_resize)

    def create_custom_title_bar(self):
        """Özel başlık çubuğu oluşturur."""
        # Başlık çubuğu çerçevesi
        self.title_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.pack_propagate(False)

        # Başlık etiketi
        title_label = ctk.CTkLabel(self.title_bar, text=f"Gelişmiş Dosya Karşılaştırıcı v{__version__}")
        title_label.pack(side=tk.LEFT, padx=10)

        # Pencere kontrol butonları
        button_frame = ctk.CTkFrame(self.title_bar, fg_color="transparent")
        button_frame.pack(side=tk.RIGHT)

        # Pencere kontrol butonları
        minimize_btn = ctk.CTkButton(button_frame, text="─", width=30, height=30,
                                    command=self.minimize_window)
        minimize_btn.pack(side=tk.LEFT, padx=2)

        maximize_btn = ctk.CTkButton(button_frame, text="□", width=30, height=30,
                                    command=self.toggle_maximize)
        maximize_btn.pack(side=tk.LEFT, padx=2)

        close_btn = ctk.CTkButton(button_frame, text="✕", width=30, height=30,
                                 fg_color="#ff5555", hover_color="#ff3333",
                                 command=self.on_close)
        close_btn.pack(side=tk.LEFT, padx=2)

        # Başlık çubuğunda sürükleme
        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_move)
        self.title_bar.bind("<B1-Motion>", self.on_move)

    def minimize_window(self):
        """Windows'ta pencereyi simge durumuna küçült"""
        # Windows'ta overrideredirect kullanıldığında iconify çalışmaz
        # Bu nedenle geçici olarak overrideredirect'i kapatıp, pencereyi küçültüp, tekrar aç
        self.withdraw()  # Pencereyi geçici olarak gizle
        after_id = self.after(100, self.deiconify)  # 100ms sonra tekrar göster
        self.after_ids.append(after_id)

    def toggle_maximize(self):
        """Pencereyi büyüt/küçült."""
        if self.state() == 'zoomed':
            self.state('normal')
        else:
            self.state('zoomed')

    def start_move(self, event):
        """Pencere taşımayı başlat."""
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        """Pencere taşımayı durdur."""
        self.x = None
        self.y = None

    def on_move(self, event):
        """Pencereyi taşı."""
        if hasattr(self, 'x') and hasattr(self, 'y'):
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry(f"+{x}+{y}")

    def on_resize(self, event):
        """Pencere boyutlandırıldığında çağrılır."""
        try:
            if hasattr(self, 'title_bar') and self.title_bar.winfo_exists():
                self.title_bar.configure(width=self.winfo_width())
        except Exception as e:
            # Hata durumunda sessizce devam et
            pass

    def setup_ui(self):
        """Kullanıcı arayüzünü oluşturur."""
        # Ana çerçeve
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Kontrol paneli
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        # Klasör seçimi
        ctk.CTkLabel(control_frame, text="Klasör:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.folder_path = ctk.CTkEntry(control_frame, width=500)
        self.folder_path.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(control_frame, text="📁 Gözat", command=self.browse_folder, width=100).grid(row=0, column=2, padx=5)

        # Dosya tipi seçimi
        file_types = {
            'solidworks': 'SolidWorks',
            'cad': 'CAD',
            'document': 'Döküman',
            'image': 'Görsel',
            'all': 'Tüm Dosyalar'
        }

        for i, (value, text) in enumerate(file_types.items()):
            ctk.CTkRadioButton(control_frame, text=text, value=value,
                              variable=ctk.StringVar(value="solidworks")).grid(
                row=1, column=i, padx=5, pady=5, sticky="w")

        # Minimum benzerlik
        filter_frame = ctk.CTkFrame(control_frame)
        filter_frame.grid(row=1, column=4, padx=5, pady=5, sticky="e")
        ctk.CTkLabel(filter_frame, text="Min. Benzerlik:").pack(side="left", padx=5)

        self.min_similarity = ctk.CTkEntry(filter_frame, width=50)
        self.min_similarity.pack(side="left", padx=5)
        self.min_similarity.insert(0, "0")

        ctk.CTkLabel(filter_frame, text="%").pack(side="left", padx=5)

        # İlerleme çubuğu
        self.progress = ctk.CTkProgressBar(main_frame, orientation="horizontal")
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.set(0)

        self.status_var = ctk.StringVar(value="Hazır")
        ctk.CTkLabel(main_frame, textvariable=self.status_var).pack(pady=5)

        # Sonuçlar paneli
        self.notebook = ctk.CTkTabview(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Tablo görünümü
        self.table_tab = self.notebook.add("Tablo Görünümü")
        self.setup_table_view()

        # Görsel analiz
        self.visual_tab = self.notebook.add("Görsel Analiz")
        self.setup_visual_analysis()

        # Detaylı analiz
        self.detail_tab = self.notebook.add("Detaylı Analiz")
        self.setup_detail_panel()

        # Butonlar
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=10, fill=tk.X)

        ctk.CTkButton(button_frame, text="▶️ Başlat", command=self.start_comparison).grid(row=0, column=0, padx=5)
        ctk.CTkButton(button_frame, text="⏹ Durdur", command=self.stop_comparison).grid(row=0, column=1, padx=5)
        ctk.CTkButton(button_frame, text="🗑️ Temizle", command=self.clear_results).grid(row=0, column=2, padx=5)
        ctk.CTkButton(button_frame, text="📊 Rapor", command=self.generate_report).grid(row=0, column=3, padx=5)
        ctk.CTkButton(button_frame, text="💾 CSV", command=self.export_results).grid(row=0, column=4, padx=5)

        # Yardım butonu
        help_btn = ctk.CTkButton(button_frame, text="?", width=30, height=30,
                                command=self.show_help)
        help_btn.grid(row=0, column=5, padx=5)

    def setup_table_view(self):
        """Sonuç tablosunu oluşturur."""
        columns = ('Dosya 1', 'Dosya 2', 'Metadata', 'Hash', 'İçerik', 'Yapı', 'Toplam', 'Sonuç')
        self.tree = ttk.Treeview(self.table_tab, columns=columns, show='headings')

        # Sütun başlıkları
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            self.tree.column(col, width=100 if col not in ['Dosya 1', 'Dosya 2', 'Sonuç'] else 150)

        # Renk etiketleri
        self.tree.tag_configure('high', background='#a8e6cf')
        self.tree.tag_configure('medium', background='#dcedc1')
        self.tree.tag_configure('low', background='#ffd3b6')
        self.tree.tag_configure('none', background='#ffaaa5')

        # Kaydırma çubukları
        vsb = ttk.Scrollbar(self.table_tab, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.table_tab, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Yerleştirme
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.table_tab.grid_rowconfigure(0, weight=1)
        self.table_tab.grid_columnconfigure(0, weight=1)

        # Çift tıklama olayı
        self.tree.bind("<Double-1>", self.show_detail_view)

    def setup_visual_analysis(self):
        """Görsel analiz panelini oluşturur."""
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.visual_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # İstatistikler metin kutusu
        self.stats_text = ctk.CTkTextbox(self.visual_tab, wrap="word", height=150)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_detail_panel(self):
        """Detaylı analiz panelini oluşturur."""
        detail_paned = ctk.CTkTabview(self.detail_tab)
        detail_paned.pack(fill=tk.BOTH, expand=True)

        # Dosya bilgileri
        file_info_tab = detail_paned.add("Dosya Bilgileri")
        file_frame = ctk.CTkFrame(file_info_tab)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ctk.CTkLabel(file_frame, text="Dosya 1:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.file1_info = ctk.CTkTextbox(file_frame, wrap="word", height=200)
        self.file1_info.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(file_frame, text="Dosya 2:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.file2_info = ctk.CTkTextbox(file_frame, wrap="word", height=200)
        self.file2_info.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        file_frame.grid_rowconfigure(1, weight=1)
        file_frame.grid_columnconfigure(0, weight=1)
        file_frame.grid_columnconfigure(1, weight=1)

        # Karşılaştırma detayları
        comparison_tab = detail_paned.add("Karşılaştırma Detayları")
        self.comparison_text = ctk.CTkTextbox(comparison_tab, wrap="word", height=200)
        self.comparison_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def browse_folder(self):
        """Klasör seçme diyaloğunu açar."""
        folder = filedialog.askdirectory(title="Klasör Seçin")
        if folder:
            self.folder_path.delete(0, "end")
            self.folder_path.insert(0, folder)

    def start_comparison(self):
        """Karşılaştırma işlemini başlatır."""
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

        # Ayrı bir thread'de karşılaştırma başlat
        threading.Thread(target=self.run_comparison, args=(folder,), daemon=True).start()

    def run_comparison(self, folder):
        """Klasördeki dosyaları karşılaştırır."""
        try:
            # İlk olarak UI'yi güncelle
            after_id = self.after(0, lambda: self.status_var.set("Dosyalar taraniyor ve hazırlanıyor..."))
            self.after_ids.append(after_id)

            file_type = "solidworks"  # Varsayılan olarak SolidWorks
            min_similarity = int(self.min_similarity.get())
            extensions = self.comparator.supported_extensions[file_type]

            # Klasördeki dosyaları listele
            all_files = []

            # Dosya listesini oluştururken UI'yi güncelle
            after_id = self.after(0, lambda: self.status_var.set("Dosyalar listeleniyor..."))
            self.after_ids.append(after_id)

            for f in os.listdir(folder):
                file_path = os.path.join(folder, f)
                if os.path.isfile(file_path) and (not extensions or os.path.splitext(f)[1].lower() in extensions):
                    all_files.append(f)

                    # Her 10 dosyada bir UI'yi güncelle
                    if len(all_files) % 10 == 0:
                        after_id = self.after(0, lambda count=len(all_files):
                                    self.status_var.set(f"Dosyalar listeleniyor... {count} dosya bulundu"))
                        self.after_ids.append(after_id)
                        # Arayüzün güncellenmesi için küçük bir bekleme
                        time.sleep(0.01)

            # Dosya listesi tamamlandı
            after_id = self.after(0, lambda: self.status_var.set(f"Toplam {len(all_files)} dosya bulundu. Karşılaştırma başlıyor..."))
            self.after_ids.append(after_id)
            time.sleep(0.1)  # Arayüzün güncellenmesi için küçük bir bekleme

            total_comparisons = len(all_files) * (len(all_files) - 1) // 2
            processed = 0
            last_update = time.time()

            self.results = []

            # İlerleme çubuğunu sıfırla
            after_id = self.after(0, lambda: self.progress.set(0))
            self.after_ids.append(after_id)

            # Tüm dosya çiftlerini karşılaştır
            for i in range(len(all_files)):
                if not self.is_running:
                    break

                file1 = os.path.join(folder, all_files[i])

                # Her dosya için UI'yi güncelle
                after_id = self.after(0, lambda f=all_files[i]:
                            self.status_var.set(f"Karşılaştırılıyor: {f}"))
                self.after_ids.append(after_id)

                for j in range(i + 1, len(all_files)):
                    if not self.is_running:
                        break

                    file2 = os.path.join(folder, all_files[j])

                    # Her karşılaştırma öncesi UI'yi güncelle (her 10 karşılaştırmada bir)
                    if processed % 10 == 0:
                        after_id = self.after(0, lambda f1=all_files[i], f2=all_files[j], p=processed, t=total_comparisons:
                                    self.status_var.set(f"Karşılaştırılıyor: {f1} ile {f2} ({p}/{t})"))
                        self.after_ids.append(after_id)
                        # İlerleme çubuğunu güncelle
                        progress_value = (processed / total_comparisons) * 100 if total_comparisons > 0 else 0
                        after_id = self.after(0, lambda v=progress_value: self.progress.set(v/100))
                        self.after_ids.append(after_id)
                        # Arayüzün güncellenmesi için küçük bir bekleme
                        time.sleep(0.01)

                    # Dosyaları karşılaştır
                    comparison_result = self.comparator.compare_files(file1, file2)

                    if comparison_result['total'] >= min_similarity:
                        result_data = {
                            'Dosya 1': all_files[i],
                            'Dosya 2': all_files[j],
                            'Metadata': f"{comparison_result['metadata']:.1f}",
                            'Hash': f"{comparison_result['hash']:.1f}",
                            'İçerik': f"{comparison_result['content']:.1f}",
                            'Yapı': f"{comparison_result['structure']:.1f}",
                            'Toplam': f"{comparison_result['total']:.1f}",
                            'Sonuç': comparison_result['category'],
                            'Path1': file1,
                            'Path2': file2,
                            'Details': comparison_result
                        }

                        self.results.append(result_data)

                        # Yeni bir sonuç bulunduğunda UI'yi güncelle
                        after_id = self.after(0, lambda r=len(self.results):
                                    self.status_var.set(f"Bulunan benzer dosya çifti: {r}"))
                        self.after_ids.append(after_id)

                    processed += 1
                    progress_value = (processed / total_comparisons) * 100 if total_comparisons > 0 else 0

                    # UI güncellemeleri ana thread'de yapılmalı - daha sık güncelleme
                    if time.time() - last_update > 0.05:  # 0.1 yerine 0.05 saniye
                        after_id = self.after(0, self.update_progress, progress_value, processed, total_comparisons)
                        self.after_ids.append(after_id)
                        last_update = time.time()

            # Sonuçları göster
            after_id1 = self.after(0, self.show_results)
            after_id2 = self.after(0, self.update_visual_analysis)
            after_id3 = self.after(0, lambda: self.status_var.set(f"Tamamlandı! {len(self.results)} benzer dosya çifti bulundu."))
            after_id4 = self.after(0, lambda: self.progress.set(1))

            # After ID'lerini kaydet
            self.after_ids.extend([after_id1, after_id2, after_id3, after_id4])

        except Exception as e:
            after_id = self.after(0, lambda: messagebox.showerror("Hata", str(e)))
            self.after_ids.append(after_id)
            logging.error(f"Karşılaştırma hatası: {e}")
        finally:
            self.is_running = False

    def update_progress(self, progress_value, processed, total):
        """İlerleme durumunu günceller."""
        self.progress.set(progress_value / 100)
        self.status_var.set(f"İşlem: {processed}/{total} ({progress_value:.1f}%)")

    def show_results(self):
        """Sonuçları tabloda gösterir."""
        self.tree.delete(*self.tree.get_children())

        for res in self.results:
            total_score = float(res['Toplam'])
            tag = 'none'
            if total_score >= 95:
                tag = 'high'
            elif total_score >= 75:
                tag = 'medium'
            elif total_score >= 25:
                tag = 'low'

            self.tree.insert('', 'end', values=(
                res['Dosya 1'],
                res['Dosya 2'],
                res['Metadata'],
                res['Hash'],
                res['İçerik'],
                res['Yapı'],
                res['Toplam'],
                res['Sonuç']
            ), tags=(tag,))

    def sort_treeview(self, column):
        """Tabloyu belirtilen sütuna göre sıralar."""
        if hasattr(self, 'current_sort_column') and self.current_sort_column == column:
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            self.current_sort_reverse = False
            self.current_sort_column = column

        def get_sort_key(item):
            value = self.tree.set(item, column)
            try:
                if column in ['Metadata', 'Hash', 'İçerik', 'Yapı', 'Toplam']:
                    return float(value)
                return value
            except ValueError:
                return value

        items = sorted(self.tree.get_children(''), key=get_sort_key, reverse=self.current_sort_reverse)

        for i, item in enumerate(items):
            self.tree.move(item, '', i)

        # Sütun başlığına sıralama yönünü ekle
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
        self.tree.heading(column, text=f"{column} {'↓' if self.current_sort_reverse else '↑'}")

    def update_visual_analysis(self):
        """Görsel analiz panelini günceller."""
        if not self.results:
            return

        self.ax.clear()
        scores = [float(r['Toplam']) for r in self.results]
        similarity_ranges = Counter()

        for score in scores:
            if score >= 95: similarity_ranges['95-100'] += 1
            elif score >= 75: similarity_ranges['75-95'] += 1
            elif score >= 50: similarity_ranges['50-75'] += 1
            elif score >= 25: similarity_ranges['25-50'] += 1
            else: similarity_ranges['0-25'] += 1

        labels, sizes = zip(*[(f"{k}% ({v})", v) for k, v in sorted(similarity_ranges.items())])

        if sizes:
            self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
            self.ax.axis('equal')
            self.canvas.draw()

        self.update_statistics()

    def update_statistics(self):
        """İstatistikleri günceller."""
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
        """Seçilen sonucun detaylarını gösterir."""
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
        """Dosya bilgilerini günceller."""
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
        """Dosya boyutunu okunabilir formata çevirir."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"

    def update_comparison_details(self, file_data):
        """Karşılaştırma detaylarını günceller."""
        self.comparison_text.delete("1.0", "end")

        details = file_data['Details']
        file_type = details.get('file_type', 'unknown')

        # Temel bilgiler
        text = f"""
🔍 Detaylı Karşılaştırma 🔍
==========================
Dosya 1: {file_data['Dosya 1']}
Dosya 2: {file_data['Dosya 2']}
Toplam Benzerlik: {details['total']:.2f}%
Sonuç: {details['category']}
Dosya Tipi: {file_type}

📊 Ağırlıklı Skorlar:
- Metadata: {details['metadata']:.2f}%
- Hash: {details['hash']:.2f}%
- İçerik: {details['content']:.2f}%
- Yapı: {details['structure']:.2f}%

🔎 Manipülasyon Analizi:
- Tespit: {'Evet' if details['manipulation']['detected'] else 'Hayır'}
- Skor: {details['manipulation']['score']:.2f}%
- Tür: {details['manipulation']['type']}
        """

        # SolidWorks için özel detaylar
        if file_type == 'solidworks' and 'details' in details:
            sw_details = details['details']
            text += f"""

📊 SolidWorks Detaylı Analiz:
---------------------------
- Feature Tree: {sw_details.get('feature_tree', 0):.2f}%
- Sketch Data: {sw_details.get('sketch_data', 0):.2f}%
- Geometry: {sw_details.get('geometry', 0):.2f}%

Değerlendirme:
{self.get_sw_evaluation(details)}
            """

        self.comparison_text.insert("end", text)

    def get_sw_evaluation(self, details):
        """SolidWorks karşılaştırma sonuçlarını değerlendirir"""
        if not details or 'details' not in details:
            return "Değerlendirme yapılamadı."

        sw_details = details['details']
        feature_tree = sw_details.get('feature_tree', 0)
        sketch_data = sw_details.get('sketch_data', 0)
        geometry = sw_details.get('geometry', 0)
        total = details.get('total', 0)

        if total > 98:
            return "Dosyalar birebir aynı veya çok küçük farklılıklar içeriyor."

        evaluation = []

        # Feature tree analizi
        if feature_tree > 95:
            evaluation.append("Feature ağacı neredeyse aynı.")
        elif feature_tree > 90 and geometry < 80:
            evaluation.append("Feature ağacı benzer ancak geometride değişiklikler var.")
        elif feature_tree < 70 and geometry > 90:
            evaluation.append("Geometri benzer ancak feature ağacında önemli değişiklikler var.")
        elif feature_tree < 50:
            evaluation.append("Feature ağaçları önemli ölçüde farklı.")

        # Sketch analizi
        if sketch_data > 90:
            evaluation.append("Sketch verileri neredeyse aynı.")
        elif sketch_data > 70:
            evaluation.append("Sketch verilerinde küçük değişiklikler var.")
        elif sketch_data < 40:
            evaluation.append("Sketch verileri önemli ölçüde farklı.")

        # Geometri analizi
        if geometry > 95:
            evaluation.append("Geometri neredeyse aynı.")
        elif geometry > 80:
            evaluation.append("Geometride küçük değişiklikler var.")
        elif geometry < 50:
            evaluation.append("Geometri önemli ölçüde farklı.")

        # Genel değerlendirme
        if feature_tree > 85 and sketch_data > 85 and geometry > 85:
            evaluation.append("Dosya muhtemelen 'Save As' ile oluşturulmuş.")
        elif feature_tree > 90 and sketch_data > 70 and geometry < 60:
            evaluation.append("Dosya aynı feature ağacı kullanılarak farklı geometri ile yeniden oluşturulmuş.")
        elif feature_tree < 50 and sketch_data < 50 and geometry > 90:
            evaluation.append("Dosyalar farklı yöntemlerle oluşturulmuş ancak benzer geometriye sahip.")

        if not evaluation:
            if total > 70:
                evaluation.append("Dosyalar benzer ancak çeşitli değişiklikler içeriyor.")
            else:
                evaluation.append("Dosyalar arasında önemli farklılıklar var.")

        return "\n".join(evaluation)

    def clear_results(self):
        """Sonuçları temizler."""
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
        """Karşılaştırma işlemini durdurur."""
        self.is_running = False
        self.status_var.set("İşlem durduruldu!")

    def generate_report(self):
        """HTML rapor oluşturur."""
        if not self.results:
            messagebox.showinfo("Bilgi", "Rapor oluşturmak için sonuç bulunmuyor!")
            return

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML Dosyası", "*.html")],
                title="Rapor Dosyasını Kaydet"
            )

            if not file_path:
                return

            now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            folder_name = os.path.basename(self.folder_path.get()) if self.folder_path.get() else "Bilinmeyen Klasör"

            # SolidWorks dosyalarını say
            sw_count = sum(1 for r in self.results if r.get('Details', {}).get('file_type') == 'solidworks')

            html_content = f"""
            <!DOCTYPE html>
            <html lang="tr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Dosya Karşılaştırma Raporu</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2, h3 {{ color: #2c3e50; }}
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
                    .sw-details {{ background-color: #e8f4f8; padding: 10px; margin: 10px 0; border-radius: 5px; }}
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
                    <p><strong>SolidWorks Dosyaları:</strong> {sw_count}</p>
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
                        <th>Toplam</th>
                        <th>Sonuç</th>
                    </tr>
            """

            for result in self.results:
                total_score = float(result['Toplam'])
                css_class = 'none'
                if total_score >= 95:
                    css_class = 'high'
                elif total_score >= 75:
                    css_class = 'medium'
                elif total_score >= 25:
                    css_class = 'low'

                html_content += f"""
                    <tr class="{css_class}">
                        <td>{result['Dosya 1']}</td>
                        <td>{result['Dosya 2']}</td>
                        <td>{result['Metadata']}</td>
                        <td>{result['Hash']}</td>
                        <td>{result['İçerik']}</td>
                        <td>{result['Yapı']}</td>
                        <td>{result['Toplam']}</td>
                        <td>{result['Sonuç']}</td>
                    </tr>
                """

            # SolidWorks detayları için özel bölüm
            if sw_count > 0:
                html_content += """
                </table>

                <h2>SolidWorks Detaylı Analiz</h2>
                <p>SolidWorks dosyaları için detaylı analiz sonuçları:</p>
                """

                for result in self.results:
                    details = result.get('Details', {})
                    if details.get('file_type') == 'solidworks':
                        sw_details = details.get('details', {})
                        html_content += f"""
                        <div class="sw-details">
                            <h3>{result['Dosya 1']} ↔ {result['Dosya 2']}</h3>
                            <p><strong>Sonuç:</strong> {result['Sonuç']} ({float(result['Toplam']):.1f}%)</p>
                            <ul>
                                <li><strong>Feature Tree:</strong> {sw_details.get('feature_tree', 0):.1f}%</li>
                                <li><strong>Sketch Data:</strong> {sw_details.get('sketch_data', 0):.1f}%</li>
                                <li><strong>Geometry:</strong> {sw_details.get('geometry', 0):.1f}%</li>
                            </ul>
                            <p><strong>Değerlendirme:</strong></p>
                            <div style="background-color: #f5f5f5; padding: 10px; border-left: 4px solid #3498db;">
                                {self.get_sw_evaluation(details).replace('\n', '<br>')}
                            </div>
                        </div>
                        """
            else:
                html_content += """
                </table>
                """

            html_content += """
                <div class="footer">
                    <p>Bu rapor Gelişmiş Dosya Karşılaştırıcı v{__version__} tarafından oluşturulmuştur.</p>
                </div>
            </body>
            </html>
            """

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            webbrowser.open('file://' + os.path.realpath(file_path))
            messagebox.showinfo("Başarılı", f"Rapor başarıyla oluşturuldu:\n{file_path}")

        except Exception as e:
            logging.error(f"Rapor oluşturma hatası: {e}")
            messagebox.showerror("Hata", f"Rapor oluşturma sırasında hata oluştu:\n{str(e)}")

    def export_results(self):
        """Sonuçları CSV olarak dışa aktarır."""
        if not self.results:
            messagebox.showinfo("Bilgi", "Dışa aktarmak için sonuç bulunmuyor!")
            return

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Dosyası", "*.csv")],
                title="CSV Dosyasını Kaydet"
            )

            if not file_path:
                return

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                import csv
                fieldnames = ['Dosya 1', 'Dosya 2', 'Metadata', 'Hash', 'İçerik', 'Yapı', 'Toplam', 'Sonuç']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for result in self.results:
                    row = {k: result[k] for k in fieldnames}
                    writer.writerow(row)

            messagebox.showinfo("Başarılı", f"Sonuçlar başarıyla dışa aktarıldı:\n{file_path}")

        except Exception as e:
            logging.error(f"CSV dışa aktarma hatası: {e}")
            messagebox.showerror("Hata", f"CSV dışa aktarma sırasında hata oluştu:\n{str(e)}")

    def show_help(self):
        """Yardım bilgilerini gösterir."""
        help_text = """
        GELIŞMIŞ DOSYA KARŞILAŞTIRICI YARDIM

        Kullanım:
        1. Bir klasör seçin
        2. Dosya tipini belirleyin (varsayılan: SolidWorks)
        3. Minimum benzerlik eşiğini ayarlayın
        4. "Başlat" butonuna tıklayın

        Özellikler:
        - SolidWorks dosyaları için optimize edilmiş karşılaştırma
        - Çok katmanlı analiz (metadata, hash, içerik, yapı)
        - Manipülasyon tespiti
        - Detaylı raporlar (HTML ve CSV)

        Sonuç Yorumlama:
        - 95-100%: Tam veya neredeyse aynı dosyalar
        - 75-95%: Çok benzer dosyalar
        - 50-75%: Orta benzerlik
        - 25-50%: Zayıf benzerlik
        - 0-25%: Farklı dosyalar
        """

        messagebox.showinfo("Yardım", help_text)

    def on_close(self):
        """Pencere kapatıldığında çağrılır."""
        try:
            # Çalışan işlemleri durdur
            self.is_running = False

            # Matplotlib figürünü kapat (bellek sızıntısını önlemek için)
            if hasattr(self, 'fig') and plt.fignum_exists(self.fig.number):
                plt.close(self.fig)

            # CustomTkinter'in after olaylarını güvenli bir şekilde temizle
            # Önce tüm widget'ları devre dışı bırak
            if hasattr(self, 'title_bar'):
                self.title_bar.pack_forget()

            # Pencereyi yok etmeden önce tüm after olaylarını iptal et
            try:
                # Önce kaydedilen after ID'lerini iptal et
                for after_id in self.after_ids:
                    try:
                        self.after_cancel(after_id)
                    except Exception:
                        pass

                # Sonra tüm bekleyen after olaylarını iptal et
                for after_id in self.tk.call('after', 'info'):
                    try:
                        self.after_cancel(after_id)
                    except Exception:
                        pass
            except Exception:
                pass

            # Pencereyi yok et
            self.quit()
            self.destroy()
        except Exception as e:
            # Hata durumunda sessizce devam et ve pencereyi kapat
            logging.error(f"Kapatma hatası: {e}")
            try:
                self.quit()
                self.destroy()
            except:
                pass

def safe_exit():
    """Uygulamayı güvenli bir şekilde kapatır."""
    try:
        # Tüm matplotlib figürlerini kapat
        plt.close('all')

        # Bekleyen tüm işlemleri temizle
        for thread in threading.enumerate():
            if thread is not threading.current_thread() and thread.daemon:
                try:
                    thread._stop()
                except:
                    pass
    except:
        pass
    finally:
        # Uygulamadan çık
        sys.exit(0)

if __name__ == "__main__":
    try:
        # Tkinter hata yönetimi için
        def report_callback_exception(self, exc, val, tb):
            logging.error(f"Tkinter callback hatası: {val}")

        tk.Tk.report_callback_exception = report_callback_exception

        app = ModernFileComparator()
        app.protocol("WM_DELETE_WINDOW", app.on_close)  # Pencere kapatıldığında on_close metodunu çağır
        app.mainloop()
    except KeyboardInterrupt:
        print("\nUygulama kullanıcı tarafından durduruldu.")
        safe_exit()
    except Exception as e:
        logging.error(f"Uygulama hatası: {e}")
        try:
            messagebox.showerror("Kritik Hata", f"Uygulama hatası: {str(e)}")
        except:
            print(f"Kritik hata: {str(e)}")
        safe_exit()
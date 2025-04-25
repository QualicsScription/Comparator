import os
import logging
import struct
import hashlib
import binascii
from FileMetrics import FileMetrics

class SolidWorksComparator:
    """Gelişmiş SolidWorks dosya karşılaştırıcı"""

    # Kullanıcı dostu metrik isimleri
    METRIC_NAMES = {
        'metadata': 'Dosya Bilgileri',
        'hash': 'Dijital İmza',
        'content': 'Model İçeriği',
        'structure': 'Model Yapısı',
        'feature_tree': 'Özellik Ağacı',
        'sketch_data': 'Çizim Verileri',
        'geometry': 'Geometrik Yapı',
        'dosya_bilgileri': 'Dosya Özellikleri',
        'model_yapısı': 'Model Oluşturma Yöntemi',
        'geometri': '3B Geometri',
        'özellikler': 'Model Özellikleri'
    }

    # Metrik açıklamaları
    HELP_TEXTS = {
        'Dosya Bilgileri': 'Dosyanın oluşturulma tarihi, değiştirilme tarihi, boyutu gibi temel özellikleri',
        'Dijital İmza': 'Dosyanın benzersiz parmak izi, içeriğin değiştirilip değiştirilmediğini kontrol eder',
        'Model İçeriği': 'Modelin içerdiği özellikler, ölçüler, malzeme bilgileri',
        'Model Yapısı': 'Modelin nasıl oluşturulduğu, kullanılan yöntemler ve sıralama',
        'Özellik Ağacı': 'Modeli oluşturan özelliklerin hiyerarşik yapısı',
        'Çizim Verileri': 'Model içindeki 2B çizimler ve ölçülendirmeler',
        'Geometrik Yapı': 'Modelin 3B geometrik özellikleri (hacim, yüzey alanı, vb.)',
        'Dosya Özellikleri': 'Oluşturma tarihi, değiştirme tarihi, boyut gibi temel dosya özellikleri',
        'Model Oluşturma Yöntemi': 'Modelin nasıl oluşturulduğu, kullanılan özellikler ve sıralama',
        '3B Geometri': 'Modelin fiziksel özellikleri (hacim, yüzey alanı, boyutlar)',
        'Model Özellikleri': 'Kullanılan özellikler, ölçüler ve ilişkiler'
    }

    # Detaylı metrik açıklamaları
    METRIC_DESCRIPTIONS = {
        'dosya_bilgileri': {
            'name': 'Dosya Özellikleri',
            'description': 'Oluşturma tarihi, değiştirme tarihi, boyut gibi temel dosya özellikleri',
            'components': ['oluşturma_tarihi', 'değiştirme_tarihi', 'boyut', 'yazar']
        },
        'model_yapısı': {
            'name': 'Model Oluşturma Yöntemi',
            'description': 'Modelin nasıl oluşturulduğu, kullanılan özellikler ve sıralama',
            'components': ['özellik_ağacı', 'parametreler', 'çizimler']
        },
        'geometri': {
            'name': '3B Geometri',
            'description': 'Modelin fiziksel özellikleri (hacim, yüzey alanı, boyutlar)',
            'components': ['hacim', 'yüzey_alanı', 'boyutlar']
        },
        'özellikler': {
            'name': 'Model Özellikleri',
            'description': 'Kullanılan özellikler, ölçüler ve ilişkiler',
            'components': ['özellik_sayısı', 'ölçüler', 'ilişkiler']
        }
    }

    def __init__(self):
        self.comparison_weights = {
            'geometry': 0.4,
            'features': 0.3,
            'content': 0.2,
            'metadata': 0.1
        }

        # Eski ağırlık değerleri (geriye uyumluluk için)
        self.weights = {
            'metadata': 0.15,
            'hash': 0.10,
            'content': 0.40,
            'structure': 0.35
        }

        # SolidWorks detay ağırlıkları (geriye uyumluluk için)
        self.sw_weights = {
            'feature_tree': 0.40,
            'sketch_data': 0.30,
            'geometry': 0.30
        }

    def compare_files(self, file1, file2):
        """İki SolidWorks dosyasını karşılaştırır"""
        try:
            # Metrikleri çıkar
            metrics1 = self._extract_metrics(file1)
            metrics2 = self._extract_metrics(file2)

            # Karşılaştırma sonuçları
            results = {
                'dosya_bilgileri': self._compare_file_info(metrics1, metrics2),
                'geometri': self._compare_geometry(metrics1, metrics2),
                'özellikler': self._compare_features(metrics1, metrics2),
                'içerik': self._compare_content(metrics1, metrics2)
            }

            # Kullanıcı dostu metrik isimleri
            user_friendly_results = {
                self.METRIC_NAMES['metadata']: results['dosya_bilgileri'],
                self.METRIC_NAMES['geometry']: results['geometri'],
                self.METRIC_NAMES['feature_tree']: results['özellikler'],
                self.METRIC_NAMES['content']: results['içerik']
            }

            # Detaylı analiz
            analysis = self._analyze_differences(results)

            # Sonuç hesaplama
            final_result = self._calculate_final_score(results, analysis)

            # Kullanıcı dostu metrik isimlerini ekle
            final_result['metric_names'] = self.METRIC_NAMES
            final_result['user_friendly_results'] = user_friendly_results

            return final_result

        except Exception as e:
            logging.error(f"Karşılaştırma hatası: {e}")
            return None

    def _extract_metrics(self, file_path):
        """Dosyadan metrikleri çıkarır"""
        metrics = FileMetrics()
        metrics.extract_from_file(file_path)
        return metrics

    def _compare_file_info(self, m1, m2):
        """Dosya bilgilerini karşılaştırır"""
        scores = {
            'boyut_benzerliği': self._compare_size(m1.file_info['size'], m2.file_info['size']),
            'zaman_farkı': self._compare_time(m1.file_info['modification_date'], m2.file_info['modification_date']),
            'yazılım_versiyonu': self._compare_version(m1.file_info['software_version'], m2.file_info['software_version'])
        }

        return {
            'scores': scores,
            'total': sum(scores.values()) / len(scores)
        }

    def _compare_geometry(self, m1, m2):
        """Geometri karşılaştırması"""
        scores = {
            'hacim_farkı': self._compare_volume(m1.geometry_metrics['volume'],
                                              m2.geometry_metrics['volume']),
            'yüzey_benzerliği': self._compare_surface(m1.geometry_metrics['surface_area'],
                                                     m2.geometry_metrics['surface_area']),
            'boyut_farkı': self._compare_dimensions(m1.geometry_metrics['bounding_box'],
                                                  m2.geometry_metrics['bounding_box']),
            'yapısal_benzerlik': self._compare_topology(m1.geometry_metrics, m2.geometry_metrics)
        }

        return {
            'scores': scores,
            'total': sum(scores.values()) / len(scores),
            'details': self._analyze_geometry_differences(scores)
        }

    def _compare_features(self, m1, m2):
        """Feature ağacı karşılaştırması"""
        return {
            'yapı_benzerliği': self._compare_tree_structure(m1.feature_tree['structure'],
                                                          m2.feature_tree['structure']),
            'parametre_eşleşmesi': self._compare_parameters(m1.feature_tree['parameters'],
                                                          m2.feature_tree['parameters']),
            'bağımlılık_analizi': self._compare_dependencies(m1.feature_tree['dependencies'],
                                                           m2.feature_tree['dependencies'])
        }

    def _compare_content(self, m1, m2):
        """İçerik karşılaştırması"""
        return {
            'binary_hash': 100 if m1.content_metrics['binary_hash'] == m2.content_metrics['binary_hash'] else 0,
            'feature_sayısı': self._compare_counts(m1.content_metrics['feature_count'],
                                                 m2.content_metrics['feature_count']),
            'sketch_sayısı': self._compare_counts(m1.content_metrics['sketch_count'],
                                                m2.content_metrics['sketch_count']),
            'malzeme': 100 if m1.content_metrics['material'] == m2.content_metrics['material'] else 0
        }

    def _analyze_differences(self, results):
        """Farklılıkların detaylı analizi"""
        analysis = {
            'değişiklik_türü': self._determine_change_type(results),
            'önemli_farklar': self._find_significant_differences(results),
            'benzerlik_nedeni': self._analyze_similarity_reason(results)
        }

        return analysis

    def _determine_change_type(self, results):
        """Değişiklik türünü belirle"""
        if results['geometri']['total'] > 95 and results['özellikler']['yapı_benzerliği'] > 95:
            return "Birebir Kopya"
        elif results['geometri']['total'] > 90 and results['özellikler']['yapı_benzerliği'] < 50:
            return "Yeniden Modellenmiş"
        elif results['özellikler']['yapı_benzerliği'] > 90 and results['geometri']['total'] < 50:
            return "Farklı Parametreler"
        else:
            return "Farklı Model"

    def _find_significant_differences(self, results):
        """Önemli farklılıkları belirle"""
        differences = []

        # Geometri farklılıkları
        if results['geometri']['total'] < 90:
            if results['geometri']['scores']['hacim_farkı'] < 80:
                differences.append("Hacim önemli ölçüde farklı")
            if results['geometri']['scores']['yüzey_benzerliği'] < 80:
                differences.append("Yüzey alanı önemli ölçüde farklı")

        # Feature farklılıkları
        if results['özellikler']['yapı_benzerliği'] < 80:
            differences.append("Feature ağacı yapısı farklı")
        if results['özellikler']['parametre_eşleşmesi'] < 70:
            differences.append("Feature parametreleri farklı")

        return differences

    def _analyze_similarity_reason(self, results):
        """Benzerlik nedenini analiz et"""
        if results['geometri']['total'] > 95 and results['içerik']['binary_hash'] > 90:
            return "Aynı dosyanın kopyası"
        elif results['geometri']['total'] > 90 and results['dosya_bilgileri']['total'] > 80:
            return "SaveAs ile oluşturulmuş"
        elif results['özellikler']['yapı_benzerliği'] > 90:
            return "Aynı feature ağacı kullanılmış"
        else:
            return "Benzerlik tespit edilemedi"

    def _calculate_final_score(self, results, analysis):
        """Final skoru hesapla"""
        # Ağırlıklı toplam
        total_score = (
            results['geometri']['total'] * self.comparison_weights['geometry'] +
            results['özellikler']['yapı_benzerliği'] * self.comparison_weights['features'] +
            self._average_dict_values(results['içerik']) * self.comparison_weights['content'] +
            results['dosya_bilgileri']['total'] * self.comparison_weights['metadata']
        )

        # Bonus: Yüksek geometri benzerliği
        if results['geometri']['total'] > 95:
            total_score *= 1.1  # %10 bonus

        # Kullanıcı dostu metrik isimleri ile sonuçları hazırla
        user_friendly_details = {
            self.METRIC_NAMES['geometry']: results['geometri'],
            self.METRIC_NAMES['feature_tree']: results['özellikler'],
            self.METRIC_NAMES['content']: results['içerik'],
            self.METRIC_NAMES['metadata']: results['dosya_bilgileri']
        }

        # Sonuç
        return {
            'score': min(100, total_score),
            'category': analysis['değişiklik_türü'],
            'details': results,  # Teknik detaylar
            'user_friendly_details': user_friendly_details,  # Kullanıcı dostu detaylar
            'analysis': analysis,
            'help_texts': self.HELP_TEXTS  # Yardım metinleri
        }

    # Yardımcı karşılaştırma metodları
    def _compare_size(self, size1, size2):
        """Boyut karşılaştırması"""
        if size1 is None or size2 is None:
            return 0
        return min(size1, size2) / max(size1, size2) * 100 if max(size1, size2) > 0 else 100

    def _compare_time(self, time1, time2):
        """Zaman karşılaştırması"""
        if time1 is None or time2 is None:
            return 0
        time_diff = abs((time1 - time2).total_seconds())
        return max(0, 100 - (time_diff / 86400 * 100)) if time_diff < 86400 else 0

    def _compare_version(self, ver1, ver2):
        """Versiyon karşılaştırması"""
        return 100 if ver1 == ver2 else 0

    def _compare_volume(self, vol1, vol2):
        """Hacim karşılaştırması"""
        if vol1 is None or vol2 is None:
            return 0
        return min(vol1, vol2) / max(vol1, vol2) * 100 if max(vol1, vol2) > 0 else 100

    def _compare_surface(self, area1, area2):
        """Yüzey alanı karşılaştırması"""
        if area1 is None or area2 is None:
            return 0
        return min(area1, area2) / max(area1, area2) * 100 if max(area1, area2) > 0 else 100

    def _compare_dimensions(self, bbox1, bbox2):
        """Boyut karşılaştırması"""
        if bbox1 is None or bbox2 is None:
            return 0

        # Bounding box boyutları
        size1 = [bbox1[3]-bbox1[0], bbox1[4]-bbox1[1], bbox1[5]-bbox1[2]]
        size2 = [bbox2[3]-bbox2[0], bbox2[4]-bbox2[1], bbox2[5]-bbox2[2]]

        # Boyut oranları
        ratios = [
            min(size1[i], size2[i]) / max(size1[i], size2[i]) * 100
            if max(size1[i], size2[i]) > 0 else 100
            for i in range(3)
        ]

        return sum(ratios) / 3

    def _compare_topology(self, geom1, geom2):
        """Topoloji karşılaştırması"""
        if not geom1 or not geom2:
            return 0

        # Vertex, edge, face sayıları karşılaştırması
        vertex_sim = self._compare_counts(geom1['vertex_count'], geom2['vertex_count'])
        edge_sim = self._compare_counts(geom1['edge_count'], geom2['edge_count'])
        face_sim = self._compare_counts(geom1['face_count'], geom2['face_count'])

        return (vertex_sim + edge_sim + face_sim) / 3

    def _compare_counts(self, count1, count2):
        """Sayı karşılaştırması"""
        if count1 is None or count2 is None:
            return 0
        return min(count1, count2) / max(count1, count2) * 100 if max(count1, count2) > 0 else 100

    def _compare_tree_structure(self, struct1, struct2):
        """Ağaç yapısı karşılaştırması"""
        if not struct1 or not struct2:
            return 0

        # Feature sayısı karşılaştırması
        count_sim = self._compare_counts(len(struct1), len(struct2))

        # Feature isimleri karşılaştırması
        names1 = [f['name'] for f in struct1]
        names2 = [f['name'] for f in struct2]

        name_matches = sum(1 for n1 in names1 if n1 in names2)
        name_sim = name_matches / max(len(names1), len(names2)) * 100 if max(len(names1), len(names2)) > 0 else 0

        # Feature tipleri karşılaştırması
        types1 = [f['type'] for f in struct1]
        types2 = [f['type'] for f in struct2]

        type_matches = sum(1 for t1 in types1 if t1 in types2)
        type_sim = type_matches / max(len(types1), len(types2)) * 100 if max(len(types1), len(types2)) > 0 else 0

        return (count_sim * 0.3 + name_sim * 0.4 + type_sim * 0.3)

    def _compare_parameters(self, params1, params2):
        """Parametre karşılaştırması"""
        if not params1 or not params2:
            return 0

        # Ortak feature ID'leri
        common_ids = set(params1.keys()) & set(params2.keys())

        if not common_ids:
            return 0

        # Parametre değerleri karşılaştırması
        matches = 0
        total = 0

        for id in common_ids:
            p1 = params1[id]
            p2 = params2[id]

            # Ortak parametre anahtarları
            common_keys = set(p1.keys()) & set(p2.keys())

            for key in common_keys:
                total += 1
                if p1[key] == p2[key]:
                    matches += 1

        return matches / total * 100 if total > 0 else 0

    def _compare_dependencies(self, deps1, deps2):
        """Bağımlılık karşılaştırması"""
        if not deps1 or not deps2:
            return 0

        # Ortak feature ID'leri
        common_ids = set(deps1.keys()) & set(deps2.keys())

        if not common_ids:
            return 0

        # Bağımlılık ilişkileri karşılaştırması
        similarity = 0

        for id in common_ids:
            d1 = set(deps1[id])
            d2 = set(deps2[id])

            # Jaccard benzerliği
            if d1 or d2:  # Boş olmayan setler
                intersection = len(d1 & d2)
                union = len(d1 | d2)
                similarity += intersection / union

        return similarity / len(common_ids) * 100 if common_ids else 0

    def _analyze_geometry_differences(self, scores):
        """Geometri farklılıklarını analiz et"""
        details = []

        if scores['hacim_farkı'] < 90:
            details.append("Hacim önemli ölçüde farklı")

        if scores['yüzey_benzerliği'] < 90:
            details.append("Yüzey alanı önemli ölçüde farklı")

        if scores['boyut_farkı'] < 90:
            details.append("Boyutlar önemli ölçüde farklı")

        if scores['yapısal_benzerlik'] < 90:
            details.append("Topoloji önemli ölçüde farklı")

        return details

    def _average_dict_values(self, d):
        """Sözlük değerlerinin ortalamasını hesapla"""
        values = list(d.values())
        return sum(values) / len(values) if values else 0

    def get_friendly_name(self, metric_key):
        """Metrik için kullanıcı dostu isim döndürür"""
        return self.METRIC_NAMES.get(metric_key, metric_key)

    def get_help_text(self, metric_name):
        """Metrik için yardım metni döndürür"""
        return self.HELP_TEXTS.get(metric_name, "Açıklama bulunamadı.")

    # Geriye uyumluluk için eski metodlar
    def compare_files_legacy(self, file1, file2):
        """Gelişmiş SolidWorks dosya karşılaştırması (eski versiyon)"""
        result = {
            'metadata': 0,
            'hash': 0,
            'content': 0,
            'structure': 0,
            'total': 0,
            'details': {
                'feature_tree': 0,
                'sketch_data': 0,
                'geometry': 0
            },
            'manipulation': {
                'detected': False,
                'score': 0,
                'type': 'None'
            },
            'file_type': 'solidworks'
        }

        try:
            # 1. Binary karşılaştırma (hızlı ön kontrol)
            if self._compare_binary(file1, file2):
                return self._create_exact_match_result()

            # 2. Metadata analizi
            result['metadata'] = self._compare_metadata(file1, file2)

            # 3. Feature tree analizi (XML yapısı)
            tree_similarity = self._compare_feature_trees(file1, file2)
            result['details']['feature_tree'] = tree_similarity

            # 4. Geometri analizi
            geometry_similarity = self._compare_geometry(file1, file2)
            result['details']['geometry'] = geometry_similarity

            # 5. Sketch verisi analizi
            sketch_similarity = self._compare_sketches(file1, file2)
            result['details']['sketch_data'] = sketch_similarity

            # 6. Hash karşılaştırması
            result['hash'] = self._compare_hashes(file1, file2)

            # 7. İçerik karşılaştırması
            result['content'] = self._calculate_content_similarity(
                tree_similarity,
                sketch_similarity,
                geometry_similarity
            )

            # 8. Yapı karşılaştırması
            result['structure'] = self._calculate_structure_similarity(
                tree_similarity,
                sketch_similarity
            )

            # 9. Manipülasyon tespiti
            self._detect_manipulation(result)

            # 10. Ağırlıklı toplam hesaplama
            result['total'] = self._calculate_weighted_total(result)

            # 11. Kategori belirleme
            result['category'] = self._determine_category(result['total'])

            return result

        except Exception as e:
            logging.error(f"SolidWorks karşılaştırma hatası: {e}")
            return self._create_error_result()

    def _compare_binary(self, file1, file2):
        """Dosyaların birebir aynı olup olmadığını kontrol eder"""
        try:
            # Dosya boyutları farklıysa hızlıca false döndür
            if os.path.getsize(file1) != os.path.getsize(file2):
                return False

            # Dosya boyutu çok büyükse chunk'lar halinde karşılaştır
            chunk_size = 8192  # 8KB
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                while True:
                    chunk1 = f1.read(chunk_size)
                    chunk2 = f2.read(chunk_size)

                    if chunk1 != chunk2:
                        return False

                    if not chunk1:  # Dosya sonuna gelindi
                        return True
        except Exception as e:
            logging.error(f"Binary karşılaştırma hatası: {e}")
            return False

    def _compare_metadata(self, file1, file2):
        """Dosya metadata'larını karşılaştırır"""
        try:
            # Dosya boyutu, oluşturma tarihi, değiştirme tarihi gibi bilgileri karşılaştır
            stat1 = os.stat(file1)
            stat2 = os.stat(file2)

            # Boyut karşılaştırması
            size_similarity = 100 if stat1.st_size == stat2.st_size else (
                min(stat1.st_size, stat2.st_size) / max(stat1.st_size, stat2.st_size) * 100
            )

            # Değiştirme tarihi karşılaştırması - yakın tarihler için bonus
            time_diff = abs(stat1.st_mtime - stat2.st_mtime)
            time_similarity = 100 if time_diff < 60 else (
                90 if time_diff < 3600 else (
                    70 if time_diff < 86400 else (
                        50 if time_diff < 604800 else 30
                    )
                )
            )

            # Ağırlıklı metadata benzerliği
            return (size_similarity * 0.7 + time_similarity * 0.3)
        except Exception as e:
            logging.error(f"Metadata karşılaştırma hatası: {e}")
            return 0

    def _compare_feature_trees(self, file1, file2):
        """Feature tree karşılaştırması için öneriler:
        1. XML yapısını parse et
        2. Ağaç yapısını karşılaştır
        3. Feature isimlerini ve parametreleri kontrol et
        4. Sıralamayı dikkate al
        5. Feature bağımlılıklarını kontrol et
        """
        try:
            # Örnek implementasyon - gerçek uygulamada SolidWorks API kullanılabilir
            # veya dosya formatı analizi yapılabilir

            # Feature ağacı çıkarma
            tree1 = self._extract_feature_tree(file1)
            tree2 = self._extract_feature_tree(file2)

            if not tree1 or not tree2:
                return 0

            # Feature sayısı karşılaştırması
            count_similarity = min(len(tree1), len(tree2)) / max(len(tree1), len(tree2)) * 100 if max(len(tree1), len(tree2)) > 0 else 0

            # Feature isimleri karşılaştırması
            name_matches = sum(1 for f1 in tree1 if any(f1['name'] == f2['name'] for f2 in tree2))
            name_similarity = name_matches / max(len(tree1), len(tree2)) * 100 if max(len(tree1), len(tree2)) > 0 else 0

            # Feature parametreleri karşılaştırması
            param_similarity = self._compare_feature_parameters(tree1, tree2)

            # Feature sıralaması karşılaştırması
            order_similarity = self._compare_feature_order(tree1, tree2)

            # Ağırlıklı feature tree benzerliği
            return (
                count_similarity * 0.2 +
                name_similarity * 0.3 +
                param_similarity * 0.3 +
                order_similarity * 0.2
            )
        except Exception as e:
            logging.error(f"Feature tree karşılaştırma hatası: {e}")
            return 0

    def _extract_feature_tree(self, file_path):
        """SolidWorks dosyasından feature ağacını çıkarır"""
        # Örnek implementasyon - gerçek uygulamada SolidWorks API kullanılabilir
        features = []
        try:
            # Dosya formatı analizi
            with open(file_path, 'rb') as f:
                # Dosya başlığını oku
                header = f.read(100)

                # Feature ağacı bölümünü bul
                # Bu kısım dosya formatına göre değişir

                # Örnek feature'lar
                features = [
                    {'name': 'Base-Extrude', 'params': {'depth': 10, 'direction': 1}},
                    {'name': 'Fillet', 'params': {'radius': 2}},
                    {'name': 'Cut-Extrude', 'params': {'depth': 5, 'direction': -1}}
                ]

            return features
        except Exception as e:
            logging.error(f"Feature ağacı çıkarma hatası: {e}")
            return []

    def _compare_feature_parameters(self, tree1, tree2):
        """Feature parametrelerini karşılaştırır"""
        # Örnek implementasyon
        param_matches = 0
        total_params = 0

        for f1 in tree1:
            for f2 in tree2:
                if f1['name'] == f2['name']:
                    # Parametre sayısı
                    params1 = f1.get('params', {})
                    params2 = f2.get('params', {})

                    # Ortak parametreler
                    common_params = set(params1.keys()) & set(params2.keys())

                    # Değer karşılaştırması
                    for param in common_params:
                        total_params += 1
                        if params1[param] == params2[param]:
                            param_matches += 1

        return param_matches / total_params * 100 if total_params > 0 else 0

    def _compare_feature_order(self, tree1, tree2):
        """Feature sıralamasını karşılaştırır"""
        # Örnek implementasyon - Longest Common Subsequence algoritması
        names1 = [f['name'] for f in tree1]
        names2 = [f['name'] for f in tree2]

        lcs_length = self._longest_common_subsequence(names1, names2)

        return lcs_length / max(len(names1), len(names2)) * 100 if max(len(names1), len(names2)) > 0 else 0

    def _longest_common_subsequence(self, seq1, seq2):
        """İki dizi arasındaki en uzun ortak alt diziyi bulur"""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return dp[m][n]

    def _compare_geometry(self, file1, file2):
        """Geometri karşılaştırması için öneriler:
        1. BREP (Boundary Representation) verilerini çıkar
        2. Vertex, edge ve face sayılarını karşılaştır
        3. Hacim ve yüzey alanlarını karşılaştır
        4. Bounding box'ları karşılaştır
        5. Mesh yapılarını karşılaştır
        """
        try:
            # Örnek implementasyon - gerçek uygulamada SolidWorks API kullanılabilir

            # Geometri verilerini çıkar
            geo1 = self._extract_geometry(file1)
            geo2 = self._extract_geometry(file2)

            if not geo1 or not geo2:
                return 0

            # Vertex, edge, face sayıları karşılaştırması
            topology_similarity = (
                min(geo1['vertices'], geo2['vertices']) / max(geo1['vertices'], geo2['vertices']) * 100 if max(geo1['vertices'], geo2['vertices']) > 0 else 0 +
                min(geo1['edges'], geo2['edges']) / max(geo1['edges'], geo2['edges']) * 100 if max(geo1['edges'], geo2['edges']) > 0 else 0 +
                min(geo1['faces'], geo2['faces']) / max(geo1['faces'], geo2['faces']) * 100 if max(geo1['faces'], geo2['faces']) > 0 else 0
            ) / 3

            # Hacim ve yüzey alanı karşılaştırması
            volume_similarity = min(geo1['volume'], geo2['volume']) / max(geo1['volume'], geo2['volume']) * 100 if max(geo1['volume'], geo2['volume']) > 0 else 0
            area_similarity = min(geo1['area'], geo2['area']) / max(geo1['area'], geo2['area']) * 100 if max(geo1['area'], geo2['area']) > 0 else 0

            # Bounding box karşılaştırması
            bbox_similarity = self._compare_bounding_boxes(geo1['bbox'], geo2['bbox'])

            # Ağırlıklı geometri benzerliği
            return (
                topology_similarity * 0.4 +
                volume_similarity * 0.2 +
                area_similarity * 0.2 +
                bbox_similarity * 0.2
            )
        except Exception as e:
            logging.error(f"Geometri karşılaştırma hatası: {e}")
            return 0

    def _extract_geometry(self, file_path):
        """SolidWorks dosyasından geometri verilerini çıkarır"""
        # Örnek implementasyon - gerçek uygulamada SolidWorks API kullanılabilir
        try:
            # Örnek geometri verileri
            return {
                'vertices': 100,
                'edges': 150,
                'faces': 50,
                'volume': 1000.0,
                'area': 500.0,
                'bbox': [0, 0, 0, 100, 100, 100]  # [xmin, ymin, zmin, xmax, ymax, zmax]
            }
        except Exception as e:
            logging.error(f"Geometri çıkarma hatası: {e}")
            return None

    def _compare_bounding_boxes(self, bbox1, bbox2):
        """Bounding box'ları karşılaştırır"""
        # Örnek implementasyon
        # Boyut karşılaştırması
        size1 = [(bbox1[3] - bbox1[0]), (bbox1[4] - bbox1[1]), (bbox1[5] - bbox1[2])]
        size2 = [(bbox2[3] - bbox2[0]), (bbox2[4] - bbox2[1]), (bbox2[5] - bbox2[2])]

        size_similarity = (
            min(size1[0], size2[0]) / max(size1[0], size2[0]) * 100 if max(size1[0], size2[0]) > 0 else 0 +
            min(size1[1], size2[1]) / max(size1[1], size2[1]) * 100 if max(size1[1], size2[1]) > 0 else 0 +
            min(size1[2], size2[2]) / max(size1[2], size2[2]) * 100 if max(size1[2], size2[2]) > 0 else 0
        ) / 3

        # Konum karşılaştırması
        center1 = [(bbox1[0] + bbox1[3]) / 2, (bbox1[1] + bbox1[4]) / 2, (bbox1[2] + bbox1[5]) / 2]
        center2 = [(bbox2[0] + bbox2[3]) / 2, (bbox2[1] + bbox2[4]) / 2, (bbox2[2] + bbox2[5]) / 2]

        # Normalize edilmiş mesafe
        max_dist = sum([(size1[i] + size2[i]) / 2 for i in range(3)])
        dist = sum([(center1[i] - center2[i]) ** 2 for i in range(3)]) ** 0.5

        position_similarity = max(0, 100 - (dist / max_dist * 100)) if max_dist > 0 else 0

        return (size_similarity * 0.7 + position_similarity * 0.3)

    def _compare_sketches(self, file1, file2):
        """Sketch verisi karşılaştırması için öneriler:
        1. Sketch sayılarını karşılaştır
        2. Sketch isimlerini karşılaştır
        3. Sketch geometrilerini karşılaştır (çizgi, daire, vb.)
        4. Sketch kısıtlamalarını karşılaştır
        5. Sketch boyutlarını karşılaştır
        """
        try:
            # Örnek implementasyon - gerçek uygulamada SolidWorks API kullanılabilir

            # Sketch verilerini çıkar
            sketches1 = self._extract_sketches(file1)
            sketches2 = self._extract_sketches(file2)

            if not sketches1 or not sketches2:
                return 0

            # Sketch sayısı karşılaştırması
            count_similarity = min(len(sketches1), len(sketches2)) / max(len(sketches1), len(sketches2)) * 100 if max(len(sketches1), len(sketches2)) > 0 else 0

            # Sketch isimleri karşılaştırması
            name_matches = sum(1 for s1 in sketches1 if any(s1['name'] == s2['name'] for s2 in sketches2))
            name_similarity = name_matches / max(len(sketches1), len(sketches2)) * 100 if max(len(sketches1), len(sketches2)) > 0 else 0

            # Sketch geometrileri karşılaştırması
            geometry_similarity = self._compare_sketch_geometries(sketches1, sketches2)

            # Sketch kısıtlamaları karşılaştırması
            constraint_similarity = self._compare_sketch_constraints(sketches1, sketches2)

            # Ağırlıklı sketch benzerliği
            return (
                count_similarity * 0.2 +
                name_similarity * 0.2 +
                geometry_similarity * 0.4 +
                constraint_similarity * 0.2
            )
        except Exception as e:
            logging.error(f"Sketch karşılaştırma hatası: {e}")
            return 0

    def _extract_sketches(self, file_path):
        """SolidWorks dosyasından sketch verilerini çıkarır"""
        # Örnek implementasyon - gerçek uygulamada SolidWorks API kullanılabilir
        try:
            # Örnek sketch verileri
            return [
                {
                    'name': 'Sketch1',
                    'entities': [
                        {'type': 'line', 'points': [(0, 0), (10, 0)]},
                        {'type': 'line', 'points': [(10, 0), (10, 10)]},
                        {'type': 'line', 'points': [(10, 10), (0, 10)]},
                        {'type': 'line', 'points': [(0, 10), (0, 0)]}
                    ],
                    'constraints': ['horizontal', 'vertical', 'perpendicular']
                },
                {
                    'name': 'Sketch2',
                    'entities': [
                        {'type': 'circle', 'center': (5, 5), 'radius': 2}
                    ],
                    'constraints': ['concentric']
                }
            ]
        except Exception as e:
            logging.error(f"Sketch çıkarma hatası: {e}")
            return []

    def _compare_sketch_geometries(self, sketches1, sketches2):
        """Sketch geometrilerini karşılaştırır"""
        # Örnek implementasyon
        entity_matches = 0
        total_entities = 0

        for s1 in sketches1:
            for s2 in sketches2:
                if s1['name'] == s2['name']:
                    entities1 = s1.get('entities', [])
                    entities2 = s2.get('entities', [])

                    total_entities += max(len(entities1), len(entities2))

                    # Basit entity karşılaştırması
                    for e1 in entities1:
                        for e2 in entities2:
                            if e1['type'] == e2['type']:
                                if e1['type'] == 'line' and self._compare_lines(e1, e2):
                                    entity_matches += 1
                                elif e1['type'] == 'circle' and self._compare_circles(e1, e2):
                                    entity_matches += 1

        return entity_matches / total_entities * 100 if total_entities > 0 else 0

    def _compare_lines(self, line1, line2):
        """İki çizgiyi karşılaştırır"""
        # Örnek implementasyon
        # Başlangıç ve bitiş noktaları karşılaştırması
        return (line1['points'][0] == line2['points'][0] and line1['points'][1] == line2['points'][1]) or \
               (line1['points'][0] == line2['points'][1] and line1['points'][1] == line2['points'][0])

    def _compare_circles(self, circle1, circle2):
        """İki daireyi karşılaştırır"""
        # Örnek implementasyon
        # Merkez ve yarıçap karşılaştırması
        return circle1['center'] == circle2['center'] and abs(circle1['radius'] - circle2['radius']) < 0.001

    def _compare_sketch_constraints(self, sketches1, sketches2):
        """Sketch kısıtlamalarını karşılaştırır"""
        # Örnek implementasyon
        constraint_matches = 0
        total_constraints = 0

        for s1 in sketches1:
            for s2 in sketches2:
                if s1['name'] == s2['name']:
                    constraints1 = set(s1.get('constraints', []))
                    constraints2 = set(s2.get('constraints', []))

                    total_constraints += max(len(constraints1), len(constraints2))
                    constraint_matches += len(constraints1 & constraints2)

        return constraint_matches / total_constraints * 100 if total_constraints > 0 else 0

    def _compare_hashes(self, file1, file2):
        """Dosya hash'lerini karşılaştırır"""
        try:
            # MD5 hash'leri hesapla
            hash1 = self._calculate_file_hash(file1)
            hash2 = self._calculate_file_hash(file2)

            # Hash'ler aynıysa 100, değilse 0
            return 100 if hash1 == hash2 else 0
        except Exception as e:
            logging.error(f"Hash karşılaştırma hatası: {e}")
            return 0

    def _calculate_file_hash(self, file_path):
        """Dosya hash'ini hesaplar"""
        try:
            md5_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                # Büyük dosyalar için chunk'lar halinde oku
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            logging.error(f"Hash hesaplama hatası: {e}")
            return ""

    def _calculate_content_similarity(self, tree_similarity, sketch_similarity, geometry_similarity):
        """İçerik benzerliğini hesaplar"""
        # Ağırlıklı içerik benzerliği
        return (
            tree_similarity * self.sw_weights['feature_tree'] +
            sketch_similarity * self.sw_weights['sketch_data'] +
            geometry_similarity * self.sw_weights['geometry']
        )

    def _calculate_structure_similarity(self, tree_similarity, sketch_similarity):
        """Yapı benzerliğini hesaplar"""
        # Ağırlıklı yapı benzerliği
        return (tree_similarity * 0.7 + sketch_similarity * 0.3)

    def _detect_manipulation(self, result):
        """Manipülasyon tespiti yapar"""
        # Örnek manipülasyon tespiti

        # 1. SaveAs tespiti
        if result['metadata'] > 90 and result['content'] > 95:
            result['manipulation']['detected'] = True
            result['manipulation']['type'] = 'SaveAs'
            result['manipulation']['score'] = 95

        # 2. Kopyala-Yapıştır tespiti
        elif result['structure'] > 90 and result['content'] < 70:
            result['manipulation']['detected'] = True
            result['manipulation']['type'] = 'Copy-Paste'
            result['manipulation']['score'] = 80

        # 3. Yeniden modelleme tespiti
        elif result['structure'] < 50 and result['content'] > 80:
            result['manipulation']['detected'] = True
            result['manipulation']['type'] = 'Remodeling'
            result['manipulation']['score'] = 70

        # 4. Parametrik değişiklik tespiti
        elif result['details']['feature_tree'] > 90 and result['details']['geometry'] < 80:
            result['manipulation']['detected'] = True
            result['manipulation']['type'] = 'Parameter-Change'
            result['manipulation']['score'] = 85

    def _calculate_weighted_total(self, result):
        """Ağırlıklı toplam benzerliği hesaplar"""
        total = (
            result['metadata'] * self.weights['metadata'] +
            result['hash'] * self.weights['hash'] +
            result['content'] * self.weights['content'] +
            result['structure'] * self.weights['structure']
        )

        # Bonus: Yüksek geometri benzerliği için
        if result['details']['geometry'] > 95:
            total += 5

        # Bonus: Yüksek feature tree benzerliği için
        if result['details']['feature_tree'] > 95:
            total += 5

        return min(100, total)  # Maksimum 100

    def _determine_category(self, total):
        """Benzerlik kategorisini belirler"""
        if total >= 95:
            return "Birebir Aynı"
        elif total >= 85:
            return "Çok Benzer"
        elif total >= 70:
            return "Benzer"
        elif total >= 50:
            return "Kısmen Benzer"
        elif total >= 30:
            return "Az Benzer"
        else:
            return "Benzer Değil"

    def _create_exact_match_result(self):
        """Birebir aynı dosyalar için sonuç oluşturur"""
        return {
            'metadata': 100,
            'hash': 100,
            'content': 100,
            'structure': 100,
            'total': 100,
            'category': "Birebir Aynı",
            'details': {
                'feature_tree': 100,
                'sketch_data': 100,
                'geometry': 100
            },
            'manipulation': {
                'detected': True,
                'score': 100,
                'type': 'Exact-Copy'
            },
            'file_type': 'solidworks'
        }

    def _create_error_result(self):
        """Hata durumunda sonuç oluşturur"""
        return {
            'metadata': 0,
            'hash': 0,
            'content': 0,
            'structure': 0,
            'total': 0,
            'category': "Hata",
            'details': {
                'feature_tree': 0,
                'sketch_data': 0,
                'geometry': 0
            },
            'manipulation': {
                'detected': False,
                'score': 0,
                'type': 'None'
            },
            'file_type': 'unknown'
        }

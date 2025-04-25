import os
import time
import logging
import hashlib
import binascii
from datetime import datetime

class EnhancedSolidWorksComparator:
    """Gelişmiş SolidWorks karşılaştırma sınıfı"""
    
    def __init__(self):
        """Başlangıç ayarları ve metrik değişkenleri"""
        # Ağırlık değerleri
        self.weights = {
            'feature_tree': 0.4,
            'geometry': 0.3,
            'sketch_data': 0.3
        }
        
        # Metrik değişkenleri
        self.metrics = {
            'feature_tree_success': 0,
            'feature_tree_total': 0,
            'geometry_success': 0,
            'geometry_total': 0,
            'processing_times': []
        }
    
    def compare_files(self, file1, file2):
        """Gelişmiş karşılaştırma algoritması"""
        start_time = time.time()
        result = self._initialize_result()
        
        try:
            # 1. Hızlı ön kontrol
            if self._quick_binary_check(file1, file2):
                return self._create_exact_match_result()
            
            # 2. Feature tree analizi
            tree_result = self._analyze_feature_tree(file1, file2)
            result['details']['feature_tree'] = tree_result['similarity']
            result['error_details'].extend(tree_result['errors'])
            
            # 3. Geometri analizi
            geom_result = self._analyze_geometry(file1, file2)
            result['details']['geometry'] = geom_result['similarity']
            result['error_details'].extend(geom_result['errors'])
            
            # 4. Sketch analizi
            sketch_result = self._analyze_sketches(file1, file2)
            result['details']['sketch_data'] = sketch_result['similarity']
            
            # 5. Sonuçları birleştir
            result['total'] = self._calculate_weighted_total(
                tree_result['similarity'],
                geom_result['similarity'],
                sketch_result['similarity']
            )
            
            # 6. Manipülasyon tespiti
            self._detect_manipulation(result)
            
            # 7. İşlem süresini kaydet
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            self.metrics['processing_times'].append(processing_time)
            
            # 8. Metrikleri güncelle
            self._update_metrics(tree_result, geom_result)
            
            return result
            
        except Exception as e:
            logging.error(f"Comparison error: {e}")
            result['error_details'].append(str(e))
            result['processing_time'] = time.time() - start_time
            return result
    
    def _initialize_result(self):
        """Sonuç şablonu oluşturur"""
        return {
            'details': {
                'feature_tree': 0,
                'geometry': 0,
                'sketch_data': 0
            },
            'error_details': [],
            'total': 0,
            'binary_match': False,
            'manipulation': {
                'detected': False,
                'type': 'None',
                'confidence': 0
            }
        }
    
    def _quick_binary_check(self, file1, file2):
        """Dosyaların birebir aynı olup olmadığını hızlıca kontrol eder"""
        try:
            # Dosya boyutları farklıysa hızlıca false döndür
            if os.path.getsize(file1) != os.path.getsize(file2):
                return False
            
            # Dosya boyutu çok büyükse ilk ve son kısımları kontrol et
            if os.path.getsize(file1) > 10 * 1024 * 1024:  # 10MB'dan büyükse
                with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                    # İlk 1MB'ı kontrol et
                    if f1.read(1024 * 1024) != f2.read(1024 * 1024):
                        return False
                    
                    # Son 1MB'ı kontrol et
                    f1.seek(-1024 * 1024, os.SEEK_END)
                    f2.seek(-1024 * 1024, os.SEEK_END)
                    if f1.read() != f2.read():
                        return False
                    
                    return True
            else:
                # Küçük dosyaları tamamen karşılaştır
                with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                    return f1.read() == f2.read()
        except Exception as e:
            logging.error(f"Binary check error: {e}")
            return False
    
    def _analyze_feature_tree(self, file1, file2):
        """Gelişmiş feature tree analizi"""
        result = {'similarity': 0, 'errors': []}
        
        try:
            # Feature tree analizi başlangıç zamanı
            start_time = time.time()
            
            # XML yapısını çıkar
            tree1 = self._extract_feature_tree(file1)
            tree2 = self._extract_feature_tree(file2)
            
            if not tree1 or not tree2:
                result['errors'].append("Failed to extract feature tree")
                return result
            
            # Ağaç yapısını karşılaştır
            similarity = self._compare_trees(tree1, tree2)
            
            # Feature bağımlılıklarını kontrol et
            dependency_score = self._check_dependencies(tree1, tree2)
            
            # Sonuçları birleştir
            result['similarity'] = (similarity * 0.7 + dependency_score * 0.3)
            
            # Metrik güncelleme
            self.metrics['feature_tree_total'] += 1
            if result['similarity'] > 50:
                self.metrics['feature_tree_success'] += 1
            
            # İşlem süresini kaydet
            result['processing_time'] = (time.time() - start_time) * 1000  # ms cinsinden
            
        except Exception as e:
            result['errors'].append(f"Feature tree analysis failed: {e}")
        
        return result
    
    def _extract_feature_tree(self, file_path):
        """SolidWorks dosyasından feature ağacını çıkarır"""
        # Örnek implementasyon - gerçek uygulamada SolidWorks API kullanılabilir
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
            logging.error(f"Feature tree extraction error: {e}")
            return []
    
    def _compare_trees(self, tree1, tree2):
        """İki feature ağacını karşılaştırır"""
        # Örnek implementasyon
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
    
    def _check_dependencies(self, tree1, tree2):
        """Feature bağımlılıklarını kontrol eder"""
        # Örnek implementasyon
        # Gerçek uygulamada feature'lar arasındaki parent-child ilişkileri kontrol edilir
        return 80  # Örnek değer
    
    def _analyze_geometry(self, file1, file2):
        """Gelişmiş geometri analizi"""
        result = {'similarity': 0, 'errors': []}
        
        try:
            # Geometri analizi başlangıç zamanı
            start_time = time.time()
            
            # Geometri verilerini çıkar
            geo1 = self._extract_geometry(file1)
            geo2 = self._extract_geometry(file2)
            
            if not geo1 or not geo2:
                result['errors'].append("Failed to extract geometry data")
                return result
            
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
            result['similarity'] = (
                topology_similarity * 0.4 +
                volume_similarity * 0.2 +
                area_similarity * 0.2 +
                bbox_similarity * 0.2
            )
            
            # Metrik güncelleme
            self.metrics['geometry_total'] += 1
            if result['similarity'] > 50:
                self.metrics['geometry_success'] += 1
            
            # İşlem süresini kaydet
            result['processing_time'] = (time.time() - start_time) * 1000  # ms cinsinden
            
        except Exception as e:
            result['errors'].append(f"Geometry analysis failed: {e}")
        
        return result
    
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
            logging.error(f"Geometry extraction error: {e}")
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
    
    def _analyze_sketches(self, file1, file2):
        """Sketch verisi karşılaştırması"""
        result = {'similarity': 0, 'errors': []}
        
        try:
            # Sketch verilerini çıkar
            sketches1 = self._extract_sketches(file1)
            sketches2 = self._extract_sketches(file2)
            
            if not sketches1 or not sketches2:
                result['errors'].append("Failed to extract sketch data")
                return result
            
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
            result['similarity'] = (
                count_similarity * 0.2 +
                name_similarity * 0.2 +
                geometry_similarity * 0.4 +
                constraint_similarity * 0.2
            )
            
        except Exception as e:
            result['errors'].append(f"Sketch analysis failed: {e}")
        
        return result
    
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
            logging.error(f"Sketch extraction error: {e}")
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
    
    def _calculate_weighted_total(self, tree_similarity, geometry_similarity, sketch_similarity):
        """Ağırlıklı toplam benzerliği hesaplar"""
        total = (
            tree_similarity * self.weights['feature_tree'] +
            geometry_similarity * self.weights['geometry'] +
            sketch_similarity * self.weights['sketch_data']
        )
        
        # Bonus: Yüksek geometri benzerliği için
        if geometry_similarity > 95:
            total += 5
        
        # Bonus: Yüksek feature tree benzerliği için
        if tree_similarity > 95:
            total += 5
        
        return min(100, total)  # Maksimum 100
    
    def _detect_manipulation(self, result):
        """Manipülasyon tespiti yapar"""
        # Örnek manipülasyon tespiti
        details = result['details']
        
        # 1. SaveAs tespiti
        if details['feature_tree'] > 90 and details['geometry'] > 90:
            result['manipulation']['detected'] = True
            result['manipulation']['type'] = 'SaveAs'
            result['manipulation']['confidence'] = 95
        
        # 2. Kopyala-Yapıştır tespiti
        elif details['feature_tree'] > 90 and details['geometry'] < 70:
            result['manipulation']['detected'] = True
            result['manipulation']['type'] = 'Copy-Paste'
            result['manipulation']['confidence'] = 80
        
        # 3. Yeniden modelleme tespiti
        elif details['feature_tree'] < 50 and details['geometry'] > 80:
            result['manipulation']['detected'] = True
            result['manipulation']['type'] = 'Remodeling'
            result['manipulation']['confidence'] = 70
    
    def _create_exact_match_result(self):
        """Birebir aynı dosyalar için sonuç oluşturur"""
        return {
            'details': {
                'feature_tree': 100,
                'geometry': 100,
                'sketch_data': 100
            },
            'error_details': [],
            'total': 100,
            'binary_match': True,
            'manipulation': {
                'detected': True,
                'type': 'Exact-Copy',
                'confidence': 100
            },
            'processing_time': 0
        }
    
    def _update_metrics(self, tree_result, geom_result):
        """Metrik değişkenlerini günceller"""
        # Feature tree metrikleri zaten _analyze_feature_tree içinde güncelleniyor
        # Geometry metrikleri zaten _analyze_geometry içinde güncelleniyor
        pass
    
    def get_metrics(self):
        """Mevcut metrikleri döndürür"""
        metrics = self.metrics.copy()
        
        # Başarı oranlarını hesapla
        metrics['feature_tree_success_rate'] = (
            metrics['feature_tree_success'] / metrics['feature_tree_total'] * 100
            if metrics['feature_tree_total'] > 0 else 0
        )
        
        metrics['geometry_success_rate'] = (
            metrics['geometry_success'] / metrics['geometry_total'] * 100
            if metrics['geometry_total'] > 0 else 0
        )
        
        # Ortalama işlem sürelerini hesapla
        metrics['avg_processing_time'] = (
            sum(metrics['processing_times']) / len(metrics['processing_times'])
            if metrics['processing_times'] else 0
        )
        
        return metrics

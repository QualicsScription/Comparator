import logging
from SolidWorksInterface import SolidWorksInterface
from FileMetrics import FileMetrics

class EnhancedComparator:
    # Metrik açıklamaları
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
        self.sw_interface = SolidWorksInterface()
        self.metrics = FileMetrics()
        
    def compare_files(self, file1, file2):
        """Gelişmiş dosya karşılaştırması"""
        try:
            # SolidWorks'e bağlan
            if not self.sw_interface.connect():
                raise Exception("SolidWorks bağlantısı kurulamadı")
            
            # Dosyaları analiz et
            metrics1 = self._analyze_file(file1)
            metrics2 = self._analyze_file(file2)
            
            # Karşılaştırma sonuçları
            comparison = {
                'dosya_bilgileri': self._compare_file_info(metrics1, metrics2),
                'model_yapısı': self._compare_model_structure(metrics1, metrics2),
                'geometri': self._compare_geometry(metrics1, metrics2),
                'özellikler': self._compare_features(metrics1, metrics2)
            }
            
            # Sonuçları ağırlıklandır ve analiz et
            weighted_result = self._calculate_weighted_result(comparison)
            analysis = self._analyze_differences(comparison)
            
            return {
                'comparison': comparison,
                'weighted_result': weighted_result,
                'analysis': analysis,
                'metric_descriptions': self.METRIC_DESCRIPTIONS
            }
            
        except Exception as e:
            logging.error(f"Karşılaştırma hatası: {e}")
            return None
        finally:
            self.sw_interface.close()
    
    def _analyze_file(self, file_path):
        """Dosyayı analiz et ve metrikleri çıkar"""
        try:
            # Dosya metriklerini çıkar
            file_metrics = FileMetrics()
            file_metrics.extract_from_file(file_path)
            
            # SolidWorks ile dosyayı aç
            if not self.sw_interface.open_document(file_path):
                raise Exception(f"Dosya açılamadı: {file_path}")
            
            # Feature ağacını al
            feature_tree = self.sw_interface.get_feature_tree()
            
            # Geometri verilerini al
            geometry_data = self.sw_interface.get_geometry_data()
            
            # Çizimleri al
            sketches = self.sw_interface.get_sketches()
            
            # Tüm metrikleri birleştir
            return {
                'file_metrics': file_metrics,
                'feature_tree': feature_tree,
                'geometry': geometry_data,
                'sketches': sketches,
                'parameters': self._extract_parameters(feature_tree)
            }
        except Exception as e:
            logging.error(f"Dosya analiz hatası: {e}")
            return None
    
    def _extract_parameters(self, feature_tree):
        """Feature ağacından parametreleri çıkar"""
        parameters = {}
        if not feature_tree:
            return parameters
            
        for feature in feature_tree:
            if 'parameters' in feature and feature['parameters']:
                parameters[feature['id']] = feature['parameters']
                
            if 'children' in feature and feature['children']:
                child_params = self._extract_parameters(feature['children'])
                parameters.update(child_params)
                
        return parameters
    
    def _compare_file_info(self, m1, m2):
        """Dosya bilgilerini karşılaştır"""
        if not m1 or not m2:
            return {'similarity': 0}
            
        file_info1 = m1['file_metrics'].file_info
        file_info2 = m2['file_metrics'].file_info
        
        # Boyut karşılaştırması
        size_ratio = min(file_info1['size'], file_info2['size']) / max(file_info1['size'], file_info2['size']) if max(file_info1['size'], file_info2['size']) > 0 else 1
        
        # Tarih karşılaştırması
        time_diff = abs((file_info1['modification_date'] - file_info2['modification_date']).total_seconds())
        time_similarity = max(0, 1 - (time_diff / 86400)) # 1 gün içinde
        
        # Yazılım versiyonu karşılaştırması
        version_match = 1 if file_info1['software_version'] == file_info2['software_version'] else 0
        
        # Ağırlıklı benzerlik
        similarity = (size_ratio * 0.4 + time_similarity * 0.4 + version_match * 0.2) * 100
        
        return {
            'similarity': similarity,
            'size_ratio': size_ratio * 100,
            'time_similarity': time_similarity * 100,
            'version_match': version_match * 100
        }
    
    def _compare_model_structure(self, m1, m2):
        """Model yapısını karşılaştır"""
        if not m1 or not m2:
            return {'similarity': 0}
            
        feature_tree_similarity = self._compare_trees(m1['feature_tree'], m2['feature_tree'])
        parameter_match = self._compare_parameters(m1['parameters'], m2['parameters'])
        sketch_similarity = self._compare_sketches(m1['sketches'], m2['sketches'])
        
        # Ağırlıklı benzerlik
        similarity = feature_tree_similarity * 0.5 + parameter_match * 0.3 + sketch_similarity * 0.2
        
        return {
            'similarity': similarity,
            'feature_tree_similarity': feature_tree_similarity,
            'parameter_match': parameter_match,
            'sketch_similarity': sketch_similarity
        }
    
    def _compare_trees(self, tree1, tree2):
        """Feature ağaçlarını karşılaştır"""
        if not tree1 or not tree2:
            return 0
            
        # Feature sayısı karşılaştırması
        count_ratio = min(len(tree1), len(tree2)) / max(len(tree1), len(tree2)) if max(len(tree1), len(tree2)) > 0 else 1
        
        # Feature tipleri karşılaştırması
        types1 = [f['type'] for f in tree1]
        types2 = [f['type'] for f in tree2]
        
        common_types = set(types1) & set(types2)
        type_similarity = len(common_types) / max(len(types1), len(types2)) if max(len(types1), len(types2)) > 0 else 1
        
        # Feature isimleri karşılaştırması
        names1 = [f['name'] for f in tree1]
        names2 = [f['name'] for f in tree2]
        
        common_names = set(names1) & set(names2)
        name_similarity = len(common_names) / max(len(names1), len(names2)) if max(len(names1), len(names2)) > 0 else 1
        
        # Ağırlıklı benzerlik
        return (count_ratio * 0.3 + type_similarity * 0.4 + name_similarity * 0.3) * 100
    
    def _compare_parameters(self, params1, params2):
        """Parametreleri karşılaştır"""
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
        
        return (matches / total * 100) if total > 0 else 0
    
    def _compare_sketches(self, sketches1, sketches2):
        """Çizimleri karşılaştır"""
        if not sketches1 or not sketches2:
            return 0
            
        # Çizim sayısı karşılaştırması
        count_ratio = min(len(sketches1), len(sketches2)) / max(len(sketches1), len(sketches2)) if max(len(sketches1), len(sketches2)) > 0 else 1
        
        # Çizim isimleri karşılaştırması
        names1 = [s['name'] for s in sketches1]
        names2 = [s['name'] for s in sketches2]
        
        common_names = set(names1) & set(names2)
        name_similarity = len(common_names) / max(len(names1), len(names2)) if max(len(names1), len(names2)) > 0 else 1
        
        # Çizim elemanları karşılaştırması
        entity_similarity = 0
        
        for s1 in sketches1:
            for s2 in sketches2:
                if s1['name'] == s2['name']:
                    entity_similarity += self._compare_sketch_entities(s1['entities'], s2['entities'])
        
        entity_similarity = entity_similarity / len(common_names) if common_names else 0
        
        # Ağırlıklı benzerlik
        return (count_ratio * 0.3 + name_similarity * 0.3 + entity_similarity * 0.4) * 100
    
    def _compare_sketch_entities(self, entities1, entities2):
        """Çizim elemanlarını karşılaştır"""
        if not entities1 or not entities2:
            return 0
            
        # Eleman sayısı karşılaştırması
        count_ratio = min(len(entities1), len(entities2)) / max(len(entities1), len(entities2)) if max(len(entities1), len(entities2)) > 0 else 1
        
        # Eleman tipleri karşılaştırması
        types1 = [e['type'] for e in entities1]
        types2 = [e['type'] for e in entities2]
        
        type_counts1 = {}
        type_counts2 = {}
        
        for t in types1:
            type_counts1[t] = type_counts1.get(t, 0) + 1
            
        for t in types2:
            type_counts2[t] = type_counts2.get(t, 0) + 1
            
        # Tip dağılımı benzerliği
        type_similarity = 0
        all_types = set(type_counts1.keys()) | set(type_counts2.keys())
        
        for t in all_types:
            count1 = type_counts1.get(t, 0)
            count2 = type_counts2.get(t, 0)
            type_similarity += min(count1, count2) / max(count1, count2) if max(count1, count2) > 0 else 1
            
        type_similarity = type_similarity / len(all_types) if all_types else 1
        
        return (count_ratio * 0.5 + type_similarity * 0.5)
    
    def _compare_geometry(self, m1, m2):
        """Geometri karşılaştırması"""
        if not m1 or not m2 or not m1['geometry'] or not m2['geometry']:
            return {'similarity': 0}
            
        geom1 = m1['geometry']
        geom2 = m2['geometry']
        
        # Hacim karşılaştırması
        volume_ratio = min(geom1['volume'], geom2['volume']) / max(geom1['volume'], geom2['volume']) if max(geom1['volume'], geom2['volume']) > 0 else 1
        
        # Yüzey alanı karşılaştırması
        area_ratio = min(geom1['surface_area'], geom2['surface_area']) / max(geom1['surface_area'], geom2['surface_area']) if max(geom1['surface_area'], geom2['surface_area']) > 0 else 1
        
        # Topoloji karşılaştırması
        vertex_ratio = min(len(geom1['vertices']), len(geom2['vertices'])) / max(len(geom1['vertices']), len(geom2['vertices'])) if max(len(geom1['vertices']), len(geom2['vertices'])) > 0 else 1
        edge_ratio = min(len(geom1['edges']), len(geom2['edges'])) / max(len(geom1['edges']), len(geom2['edges'])) if max(len(geom1['edges']), len(geom2['edges'])) > 0 else 1
        face_ratio = min(len(geom1['faces']), len(geom2['faces'])) / max(len(geom1['faces']), len(geom2['faces'])) if max(len(geom1['faces']), len(geom2['faces'])) > 0 else 1
        
        topology_similarity = (vertex_ratio + edge_ratio + face_ratio) / 3
        
        # Ağırlıklı benzerlik
        similarity = (volume_ratio * 0.4 + area_ratio * 0.3 + topology_similarity * 0.3) * 100
        
        return {
            'similarity': similarity,
            'volume_similarity': volume_ratio * 100,
            'surface_similarity': area_ratio * 100,
            'topology_similarity': topology_similarity * 100
        }
    
    def _compare_features(self, m1, m2):
        """Özellikleri karşılaştır"""
        if not m1 or not m2:
            return {'similarity': 0}
            
        # Feature sayısı karşılaştırması
        feature_count1 = len(m1['feature_tree']) if m1['feature_tree'] else 0
        feature_count2 = len(m2['feature_tree']) if m2['feature_tree'] else 0
        
        count_ratio = min(feature_count1, feature_count2) / max(feature_count1, feature_count2) if max(feature_count1, feature_count2) > 0 else 1
        
        # Parametre sayısı karşılaştırması
        param_count1 = sum(len(params) for params in m1['parameters'].values()) if m1['parameters'] else 0
        param_count2 = sum(len(params) for params in m2['parameters'].values()) if m2['parameters'] else 0
        
        param_ratio = min(param_count1, param_count2) / max(param_count1, param_count2) if max(param_count1, param_count2) > 0 else 1
        
        # Çizim sayısı karşılaştırması
        sketch_count1 = len(m1['sketches']) if m1['sketches'] else 0
        sketch_count2 = len(m2['sketches']) if m2['sketches'] else 0
        
        sketch_ratio = min(sketch_count1, sketch_count2) / max(sketch_count1, sketch_count2) if max(sketch_count1, sketch_count2) > 0 else 1
        
        # Ağırlıklı benzerlik
        similarity = (count_ratio * 0.4 + param_ratio * 0.3 + sketch_ratio * 0.3) * 100
        
        return {
            'similarity': similarity,
            'feature_count_similarity': count_ratio * 100,
            'parameter_count_similarity': param_ratio * 100,
            'sketch_count_similarity': sketch_ratio * 100
        }
    
    def _calculate_weighted_result(self, comparison):
        """Ağırlıklı sonucu hesapla"""
        weights = {
            'dosya_bilgileri': 0.1,
            'model_yapısı': 0.3,
            'geometri': 0.4,
            'özellikler': 0.2
        }
        
        weighted_sum = 0
        for key, weight in weights.items():
            if key in comparison and 'similarity' in comparison[key]:
                weighted_sum += comparison[key]['similarity'] * weight
        
        # Bonus: Yüksek geometri benzerliği
        if 'geometri' in comparison and comparison['geometri']['similarity'] > 95:
            weighted_sum *= 1.1  # %10 bonus
        
        # Bonus: Yüksek model yapısı benzerliği
        if 'model_yapısı' in comparison and comparison['model_yapısı']['similarity'] > 90:
            weighted_sum *= 1.05  # %5 bonus
        
        return min(100, weighted_sum)
    
    def _analyze_differences(self, comparison):
        """Farklılıkları analiz et"""
        analysis = {
            'değişiklik_türü': self._determine_change_type(comparison),
            'önemli_farklar': self._find_significant_differences(comparison),
            'benzerlik_nedeni': self._analyze_similarity_reason(comparison)
        }
        
        return analysis
    
    def _determine_change_type(self, comparison):
        """Değişiklik türünü belirle"""
        if comparison['geometri']['similarity'] > 95 and comparison['model_yapısı']['similarity'] > 95:
            return "Birebir Kopya"
        elif comparison['geometri']['similarity'] > 90 and comparison['model_yapısı']['similarity'] < 50:
            return "Yeniden Modellenmiş"
        elif comparison['model_yapısı']['similarity'] > 90 and comparison['geometri']['similarity'] < 50:
            return "Farklı Parametreler"
        else:
            return "Farklı Model"
    
    def _find_significant_differences(self, comparison):
        """Önemli farklılıkları belirle"""
        differences = []
        
        # Geometri farklılıkları
        if comparison['geometri']['similarity'] < 90:
            if comparison['geometri']['volume_similarity'] < 80:
                differences.append("Hacim önemli ölçüde farklı")
            if comparison['geometri']['surface_similarity'] < 80:
                differences.append("Yüzey alanı önemli ölçüde farklı")
            if comparison['geometri']['topology_similarity'] < 80:
                differences.append("Topoloji önemli ölçüde farklı")
        
        # Model yapısı farklılıkları
        if comparison['model_yapısı']['similarity'] < 80:
            if comparison['model_yapısı']['feature_tree_similarity'] < 70:
                differences.append("Feature ağacı yapısı farklı")
            if comparison['model_yapısı']['parameter_match'] < 70:
                differences.append("Parametreler farklı")
            if comparison['model_yapısı']['sketch_similarity'] < 70:
                differences.append("Çizimler farklı")
        
        # Özellik farklılıkları
        if comparison['özellikler']['similarity'] < 80:
            if comparison['özellikler']['feature_count_similarity'] < 70:
                differences.append("Feature sayısı farklı")
            if comparison['özellikler']['parameter_count_similarity'] < 70:
                differences.append("Parametre sayısı farklı")
        
        return differences
    
    def _analyze_similarity_reason(self, comparison):
        """Benzerlik nedenini analiz et"""
        if comparison['geometri']['similarity'] > 95 and comparison['dosya_bilgileri']['similarity'] > 90:
            return "Aynı dosyanın kopyası"
        elif comparison['geometri']['similarity'] > 90 and comparison['dosya_bilgileri']['similarity'] > 80:
            return "SaveAs ile oluşturulmuş"
        elif comparison['model_yapısı']['similarity'] > 90:
            return "Aynı feature ağacı kullanılmış"
        elif comparison['geometri']['similarity'] > 80 and comparison['model_yapısı']['similarity'] < 50:
            return "Benzer geometri, farklı modelleme yöntemi"
        else:
            return "Benzerlik tespit edilemedi"

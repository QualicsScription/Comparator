import os
import hashlib
import difflib
import logging

class SolidWorksAnalyzer:
    def __init__(self):
        self.markers = {
            'feature_start': b'\x00\x00\x00\x14\x00\x00\x00\x01\x00\x00\x00\x02',
            'feature_end': b'\x00\x00\x00\x14\x00\x00\x00\x02\x00\x00\x00\x01',
            'sketch_start': b'\x00\x00\x00\x12\x00\x00\x00\x01',
            'sketch_end': b'\x00\x00\x00\x12\x00\x00\x00\x02',
            'geom_start': b'\x00\x00\x00\x10\x00\x00\x00\x01',
            'geom_end': b'\x00\x00\x00\x10\x00\x00\x00\x02'
        }
        
    def extract_sections(self, file_path):
        """SolidWorks dosyasından bölümleri çıkar"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                
                sections = {
                    'feature_tree': [],
                    'sketches': [],
                    'geometry': []
                }
                
                # Feature Tree bölümlerini bul
                pos = 0
                while True:
                    start = data.find(self.markers['feature_start'], pos)
                    if start == -1:
                        break
                    
                    end = data.find(self.markers['feature_end'], start)
                    if end == -1:
                        break
                        
                    sections['feature_tree'].append(data[start:end])
                    pos = end + len(self.markers['feature_end'])
                
                # Sketch bölümlerini bul
                pos = 0
                while True:
                    start = data.find(self.markers['sketch_start'], pos)
                    if start == -1:
                        break
                        
                    end = data.find(self.markers['sketch_end'], start)
                    if end == -1:
                        break
                        
                    sections['sketches'].append(data[start:end])
                    pos = end + len(self.markers['sketch_end'])
                
                # Geometri bölümlerini bul
                pos = 0
                while True:
                    start = data.find(self.markers['geom_start'], pos)
                    if start == -1:
                        break
                        
                    end = data.find(self.markers['geom_end'], start)
                    if end == -1:
                        break
                        
                    sections['geometry'].append(data[start:end])
                    pos = end + len(self.markers['geom_end'])
                
                return sections
                
        except Exception as e:
            logging.error(f"Bölüm çıkarma hatası: {e}")
            return None

    def compare_sections(self, sections1, sections2):
        """Bölümleri karşılaştır"""
        if not sections1 or not sections2:
            return {
                'feature_tree': 0,
                'sketches': 0,
                'geometry': 0
            }
        
        results = {}
        
        # Feature Tree karşılaştırması
        feature_sim = self._compare_section_lists(
            sections1['feature_tree'],
            sections2['feature_tree']
        )
        results['feature_tree'] = feature_sim
        
        # Sketch karşılaştırması
        sketch_sim = self._compare_section_lists(
            sections1['sketches'],
            sections2['sketches']
        )
        results['sketches'] = sketch_sim
        
        # Geometri karşılaştırması
        geom_sim = self._compare_section_lists(
            sections1['geometry'],
            sections2['geometry']
        )
        results['geometry'] = geom_sim
        
        return results

    def _compare_section_lists(self, list1, list2):
        """İki bölüm listesini karşılaştır"""
        if not list1 or not list2:
            return 0.0
            
        # En iyi eşleşmeleri bul
        similarities = []
        for section1 in list1:
            best_match = 0
            for section2 in list2:
                sim = difflib.SequenceMatcher(None, section1, section2).ratio()
                best_match = max(best_match, sim)
            similarities.append(best_match)
            
        return sum(similarities) / len(similarities) * 100

    def compare(self, file1, file2):
        """İki SolidWorks dosyasını karşılaştır"""
        try:
            # Hash kontrolü
            if self._compare_hash(file1, file2):
                return self._create_exact_match()

            # Bölümleri çıkar
            sections1 = self.extract_sections(file1)
            sections2 = self.extract_sections(file2)
            
            # Bölümleri karşılaştır
            section_results = self.compare_sections(sections1, sections2)
            
            # Metadata karşılaştırması
            metadata_sim = self._compare_metadata(file1, file2)
            
            # SaveAs kontrolü
            if self._is_save_as(section_results, metadata_sim):
                return self._create_save_as_match()
            
            # Final skor hesaplama
            total_score = self._calculate_final_score(section_results, metadata_sim)
            
            # Kategori ve değerlendirme
            category = self._get_category(total_score)
            evaluation = self._get_evaluation(total_score, section_results)
            
            return {
                'score': total_score,
                'details': {
                    'metadata': metadata_sim,
                    'feature_tree': section_results['feature_tree'],
                    'sketches': section_results['sketches'],
                    'geometry': section_results['geometry']
                },
                'match': total_score > 95,
                'similarity_category': category,
                'evaluation': evaluation
            }
            
        except Exception as e:
            logging.error(f"Karşılaştırma hatası: {e}")
            return self._create_error_result()
            
    def _compare_hash(self, file1, file2):
        """Hash karşılaştırması"""
        try:
            hash1 = hashlib.md5(open(file1, 'rb').read()).hexdigest()
            hash2 = hashlib.md5(open(file2, 'rb').read()).hexdigest()
            return hash1 == hash2
        except Exception as e:
            logging.error(f"Hash karşılaştırma hatası: {e}")
            return False
            
    def _compare_metadata(self, file1, file2):
        """Metadata karşılaştırması"""
        try:
            stat1 = os.stat(file1)
            stat2 = os.stat(file2)

            # Boyut karşılaştırması
            size_ratio = min(stat1.st_size, stat2.st_size) / max(stat1.st_size, stat2.st_size)

            # Zaman damgası karşılaştırması (24 saat içinde: 1.0, bir hafta içinde: 0.5)
            time_diff = abs(stat1.st_mtime - stat2.st_mtime)
            time_sim = 1.0 if time_diff < 86400 else (0.5 if time_diff < 604800 else 0.0)

            return (size_ratio * 0.7 + time_sim * 0.3) * 100
        except Exception as e:
            logging.error(f"Metadata karşılaştırma hatası: {e}")
            return 0.0
            
    def _is_save_as(self, section_results, metadata_sim):
        """SaveAs kontrolü"""
        return (
            metadata_sim > 60 and
            section_results['geometry'] > 90 and
            section_results['feature_tree'] > 80
        )
            
    def _calculate_final_score(self, section_results, metadata_sim):
        """Final skor hesaplama"""
        weights = {
            'feature_tree': 0.30,  # Feature tree önemli
            'sketches': 0.25,      # Sketch'ler önemli
            'geometry': 0.35,      # Geometri en önemli
            'metadata': 0.10       # Metadata en az önemli
        }
        
        score = (
            section_results['feature_tree'] * weights['feature_tree'] +
            section_results['sketches'] * weights['sketches'] +
            section_results['geometry'] * weights['geometry'] +
            metadata_sim * weights['metadata']
        )
        
        # Tüm bölümler yüksek benzerlik gösteriyorsa bonus
        if (section_results['feature_tree'] > 90 and
            section_results['sketches'] > 90 and
            section_results['geometry'] > 90):
            score *= 1.1  # %10 bonus
        
        return min(100, score)
        
    def _get_category(self, score):
        """Benzerlik kategorisini belirle"""
        if score >= 95: 
            return "Tam Eşleşme"
        elif score >= 85: 
            return "SaveAs Kopyası"
        elif score >= 70: 
            return "Küçük Değişiklikler"
        elif score >= 50: 
            return "Büyük Değişiklikler"
        elif score >= 30: 
            return "Az Benzer"
        else: 
            return "Farklı Dosyalar"
            
    def _get_evaluation(self, score, section_results):
        """Detaylı değerlendirme metni oluştur"""
        if score >= 95:
            return "Dosyalar birebir aynı veya çok küçük farklılıklar içeriyor."
        elif score >= 85:
            return "Dosya muhtemelen 'Save As' ile oluşturulmuş."
        elif score >= 70:
            if section_results['geometry'] > 90:
                return "Dosyalar benzer geometriye sahip, ancak feature tree'de değişiklikler var."
            else:
                return "Dosyalar benzer, küçük değişiklikler var."
        elif score >= 50:
            return "Dosyalar arasında önemli değişiklikler var."
        elif score >= 30:
            return "Dosyalar az benzerlik gösteriyor."
        else:
            return "Dosyalar önemli ölçüde farklı."
            
    def _create_exact_match(self):
        """Tam eşleşme sonucu"""
        return {
            'score': 100.0,
            'details': {
                'metadata': 100.0,
                'feature_tree': 100.0,
                'sketches': 100.0,
                'geometry': 100.0
            },
            'match': True,
            'similarity_category': "Tam Eşleşme",
            'evaluation': "Dosyalar birebir aynı."
        }

    def _create_save_as_match(self):
        """SaveAs eşleşme sonucu"""
        return {
            'score': 95.0,
            'details': {
                'metadata': 95.0,
                'feature_tree': 95.0,
                'sketches': 95.0,
                'geometry': 95.0
            },
            'match': True,
            'similarity_category': "SaveAs Kopyası",
            'evaluation': "Dosya muhtemelen 'Save As' ile oluşturulmuş."
        }

    def _create_error_result(self):
        """Hata sonucu"""
        return {
            'score': 0.0,
            'details': {
                'metadata': 0.0,
                'feature_tree': 0.0,
                'sketches': 0.0,
                'geometry': 0.0
            },
            'match': False,
            'similarity_category': "Hata",
            'evaluation': "Karşılaştırma sırasında hata oluştu."
        }

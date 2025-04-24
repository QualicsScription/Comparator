import os
import hashlib
import difflib
import logging

class SolidWorksAnalyzer:
    def __init__(self):
        self.signatures = {
            'feature_tree': b'FeatureData',
            'sketch': b'SketchData',
            'geometry': b'GeomData',
            'metadata': b'MetaData'
        }
        
    def analyze_file(self, file_path):
        """SolidWorks dosyasını analiz et"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                
                # Bölümleri bul
                sections = {}
                for key, signature in self.signatures.items():
                    start = content.find(signature)
                    if start != -1:
                        end = content.find(b'\x00' * 8, start)  # 8 null byte ile bölüm sonu
                        if end != -1:
                            sections[key] = content[start:end]
                
                return {
                    'sections': sections,
                    'size': len(content),
                    'header': content[:1024],  # İlk 1KB
                    'footer': content[-1024:]  # Son 1KB
                }
        except Exception as e:
            logging.error(f"Dosya analiz hatası: {e}")
            return None

    def compare(self, file1, file2):
        """İki SolidWorks dosyasını karşılaştır"""
        try:
            # Dosyaları analiz et
            data1 = self.analyze_file(file1)
            data2 = self.analyze_file(file2)
            
            if not data1 or not data2:
                return self._create_error_result()

            # Hash kontrolü
            if self._compare_hash(file1, file2):
                return self._create_exact_match()

            # Bölüm karşılaştırmaları
            comparisons = {
                'feature_tree': self._compare_section('feature_tree', data1, data2),
                'sketch': self._compare_section('sketch', data1, data2),
                'geometry': self._compare_section('geometry', data1, data2),
                'metadata': self._compare_section('metadata', data1, data2)
            }

            # Yapısal analiz
            structure_sim = self._compare_structure(data1, data2)
            
            # SaveAs kontrolü
            if self._is_save_as(comparisons, structure_sim):
                return self._create_save_as_match()

            # Final skor hesaplama
            total_score = self._calculate_final_score(comparisons, structure_sim)
            
            # Kategori ve değerlendirme
            category = self._get_category(total_score)
            
            result = {
                'score': total_score,
                'details': {
                    'metadata': comparisons['metadata'],
                    'content': (comparisons['geometry'] + comparisons['sketch']) / 2,
                    'structure': structure_sim
                },
                'match': total_score > 95,
                'similarity_category': category,
                'evaluation': self._get_evaluation(total_score, comparisons)
            }
            
            return result

        except Exception as e:
            logging.error(f"Karşılaştırma hatası: {e}")
            return self._create_error_result()

    def _compare_section(self, section_name, data1, data2):
        """Belirli bir bölümü karşılaştır"""
        try:
            section1 = data1['sections'].get(section_name)
            section2 = data2['sections'].get(section_name)
            
            if not section1 or not section2:
                return 0.0

            # Bölüm boyutu karşılaştırması
            size_ratio = min(len(section1), len(section2)) / max(len(section1), len(section2))
            
            # İçerik benzerliği
            content_sim = difflib.SequenceMatcher(None, section1, section2).ratio()
            
            return (size_ratio * 0.3 + content_sim * 0.7) * 100

        except Exception as e:
            logging.error(f"Bölüm karşılaştırma hatası: {e}")
            return 0.0

    def _compare_structure(self, data1, data2):
        """Yapısal karşılaştırma"""
        try:
            # Header karşılaştırması
            header_sim = difflib.SequenceMatcher(None, data1['header'], data2['header']).ratio()
            
            # Footer karşılaştırması
            footer_sim = difflib.SequenceMatcher(None, data1['footer'], data2['footer']).ratio()
            
            # Boyut karşılaştırması
            size_ratio = min(data1['size'], data2['size']) / max(data1['size'], data2['size'])
            
            return (header_sim * 0.4 + footer_sim * 0.3 + size_ratio * 0.3) * 100
            
        except Exception as e:
            logging.error(f"Yapısal karşılaştırma hatası: {e}")
            return 0.0

    def _compare_hash(self, file1, file2):
        """Hash karşılaştırması"""
        try:
            hash1 = hashlib.md5(open(file1, 'rb').read()).hexdigest()
            hash2 = hashlib.md5(open(file2, 'rb').read()).hexdigest()
            return hash1 == hash2
        except Exception as e:
            logging.error(f"Hash karşılaştırma hatası: {e}")
            return False

    def _is_save_as(self, comparisons, structure_sim):
        """SaveAs kontrolü"""
        return (
            comparisons['metadata'] > 60 and
            comparisons['geometry'] > 90 and
            structure_sim > 80
        )

    def _calculate_final_score(self, comparisons, structure_sim):
        """Final skor hesaplama"""
        weights = {
            'feature_tree': 0.25,
            'sketch': 0.20,
            'geometry': 0.30,
            'metadata': 0.15,
            'structure': 0.10
        }

        score = (
            comparisons['feature_tree'] * weights['feature_tree'] +
            comparisons['sketch'] * weights['sketch'] +
            comparisons['geometry'] * weights['geometry'] +
            comparisons['metadata'] * weights['metadata'] +
            structure_sim * weights['structure']
        )

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
            
    def _get_evaluation(self, score, comparisons):
        """Detaylı değerlendirme metni oluştur"""
        if score >= 95:
            return "Dosyalar birebir aynı veya çok küçük farklılıklar içeriyor."
        elif score >= 85:
            return "Dosya muhtemelen 'Save As' ile oluşturulmuş."
        elif score >= 70:
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
                'content': 100.0,
                'structure': 100.0
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
                'content': 95.0,
                'structure': 95.0
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
                'content': 0.0,
                'structure': 0.0
            },
            'match': False,
            'similarity_category': "Hata",
            'evaluation': "Karşılaştırma sırasında hata oluştu."
        }

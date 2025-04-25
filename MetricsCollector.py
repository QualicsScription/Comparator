import time
import logging
import numpy as np
from collections import defaultdict
from datetime import datetime

class MetricsCollector:
    """Karşılaştırma metriklerini toplar ve analiz eder"""
    
    def __init__(self):
        """Başlangıç ayarları"""
        self.metrics = defaultdict(list)
        self.start_time = time.time()
        self.categories = {
            'high_similarity': [],
            'medium_similarity': [],
            'low_similarity': [],
            'errors': []
        }
        self.processing_times = []
    
    def add_comparison_result(self, result):
        """Her karşılaştırma sonucunu kaydeder"""
        self.metrics['total_comparisons'].append(result)
        
        # İşlem süresini kaydet
        processing_time = result.get('processing_time', 0)
        self.processing_times.append(processing_time)
        
        # Hata durumlarını kaydet
        if result.get('error_details'):
            self.categories['errors'].append(result)
        
        # Benzerlik kategorilerine göre sınıflandır
        similarity = result.get('total', 0)
        if similarity > 95:
            self.categories['high_similarity'].append(result)
        elif similarity > 75:
            self.categories['medium_similarity'].append(result)
        elif similarity > 50:
            self.categories['low_similarity'].append(result)
        
        # Manipülasyon tespitlerini kaydet
        if result.get('manipulation', {}).get('detected', False):
            manipulation_type = result.get('manipulation', {}).get('type', 'Unknown')
            if 'manipulations' not in self.metrics:
                self.metrics['manipulations'] = defaultdict(list)
            self.metrics['manipulations'][manipulation_type].append(result)
    
    def generate_analysis(self):
        """Toplanan metrikleri analiz eder"""
        total_comparisons = len(self.metrics['total_comparisons'])
        
        if total_comparisons == 0:
            return {
                'error': 'No comparison data available'
            }
        
        analysis = {
            'runtime': time.time() - self.start_time,
            'total_comparisons': total_comparisons,
            'error_rate': len(self.categories['errors']) / total_comparisons if total_comparisons > 0 else 0,
            'avg_processing_time': np.mean(self.processing_times) if self.processing_times else 0,
            'similarity_distribution': {
                'high': len(self.categories['high_similarity']),
                'medium': len(self.categories['medium_similarity']),
                'low': len(self.categories['low_similarity'])
            },
            'performance': {
                'min_time': min(self.processing_times) if self.processing_times else 0,
                'max_time': max(self.processing_times) if self.processing_times else 0,
                'std_dev': np.std(self.processing_times) if self.processing_times else 0
            }
        }
        
        # Manipülasyon istatistikleri
        if 'manipulations' in self.metrics:
            analysis['manipulations'] = {
                'total_detected': sum(len(v) for v in self.metrics['manipulations'].values()),
                'by_type': {k: len(v) for k, v in self.metrics['manipulations'].items()}
            }
        
        return analysis
    
    def generate_report(self, file_path=None):
        """Analiz raporunu dosyaya yazar"""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"metrics_report_{timestamp}.txt"
        
        analysis = self.generate_analysis()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=== METRICS ANALYSIS REPORT ===\n\n")
                
                # 1. Genel Bilgiler
                f.write("GENERAL INFORMATION\n")
                f.write("-------------------\n")
                f.write(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total runtime: {analysis['runtime']:.2f} seconds\n")
                f.write(f"Total comparisons: {analysis['total_comparisons']}\n\n")
                
                # 2. Performans Metrikleri
                f.write("PERFORMANCE METRICS\n")
                f.write("-------------------\n")
                f.write(f"Average processing time: {analysis['avg_processing_time']:.2f} seconds\n")
                f.write(f"Minimum processing time: {analysis['performance']['min_time']:.2f} seconds\n")
                f.write(f"Maximum processing time: {analysis['performance']['max_time']:.2f} seconds\n")
                f.write(f"Standard deviation: {analysis['performance']['std_dev']:.2f} seconds\n\n")
                
                # 3. Benzerlik Dağılımı
                f.write("SIMILARITY DISTRIBUTION\n")
                f.write("----------------------\n")
                f.write(f"High similarity (>95%): {analysis['similarity_distribution']['high']} files\n")
                f.write(f"Medium similarity (75-95%): {analysis['similarity_distribution']['medium']} files\n")
                f.write(f"Low similarity (50-75%): {analysis['similarity_distribution']['low']} files\n\n")
                
                # 4. Hata Oranı
                f.write("ERROR ANALYSIS\n")
                f.write("-------------\n")
                f.write(f"Error rate: {analysis['error_rate']:.2f}%\n")
                f.write(f"Total errors: {len(self.categories['errors'])}\n\n")
                
                # 5. Manipülasyon Tespiti
                if 'manipulations' in analysis:
                    f.write("MANIPULATION DETECTION\n")
                    f.write("---------------------\n")
                    f.write(f"Total manipulations detected: {analysis['manipulations']['total_detected']}\n")
                    f.write("By type:\n")
                    for m_type, count in analysis['manipulations']['by_type'].items():
                        f.write(f"- {m_type}: {count}\n")
                
                # 6. Öneriler
                f.write("\nRECOMMENDATIONS\n")
                f.write("---------------\n")
                self._generate_recommendations(f, analysis)
                
            logging.info(f"Metrics report generated: {file_path}")
            return file_path
            
        except Exception as e:
            logging.error(f"Metrics report generation failed: {e}")
            return None
    
    def _generate_recommendations(self, f, analysis):
        """Analiz sonuçlarına göre öneriler oluşturur"""
        # Performans önerileri
        if analysis['avg_processing_time'] > 2.0:
            f.write("1. Performance Optimization:\n")
            f.write("   - Consider implementing parallel processing\n")
            f.write("   - Optimize the most time-consuming analysis steps\n")
        
        # Hata oranı önerileri
        if analysis['error_rate'] > 0.05:  # %5'ten fazla hata varsa
            f.write("\n2. Error Handling:\n")
            f.write("   - Improve error recovery mechanisms\n")
            f.write("   - Add more detailed error logging\n")
        
        # Benzerlik dağılımı önerileri
        high_ratio = analysis['similarity_distribution']['high'] / analysis['total_comparisons'] if analysis['total_comparisons'] > 0 else 0
        if high_ratio > 0.8:  # %80'den fazla yüksek benzerlik varsa
            f.write("\n3. Similarity Threshold Adjustment:\n")
            f.write("   - Consider increasing the similarity threshold\n")
            f.write("   - Add more granular similarity categories\n")
        
        # Manipülasyon tespiti önerileri
        if 'manipulations' in analysis and analysis['manipulations']['total_detected'] > 0:
            f.write("\n4. Manipulation Detection:\n")
            f.write("   - Fine-tune manipulation detection algorithms\n")
            f.write("   - Add more detailed reporting for detected manipulations\n")

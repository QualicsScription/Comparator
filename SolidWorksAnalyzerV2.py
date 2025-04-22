import os
import hashlib
import difflib
import logging

class SolidWorksAnalyzer:
    def __init__(self):
        self.chunk_size = 8192  # 8KB chunks

    def compare(self, file1, file2):
        """İki SolidWorks dosyasını karşılaştırır"""
        try:
            # Hash kontrolü
            if self._compare_hash(file1, file2):
                return self._create_exact_match()
                
            # Binary karşılaştırma sonuçları
            binary_results = self._compare_binary(file1, file2)
            
            # Metadata karşılaştırması
            metadata_sim = self._compare_metadata(file1, file2)

            # SaveAs kontrolü
            if self._is_save_as(metadata_sim, binary_results['content_similarity'], binary_results['structure_similarity']):
                return self._create_save_as_match()

            # Final skor hesaplama
            total_score = self._calculate_final_score(binary_results, metadata_sim)

            # Benzerlik kategorisi
            similarity_category = self._get_category(total_score)

            result = {
                'score': total_score,
                'details': {
                    'metadata': metadata_sim,
                    'content': binary_results['content_similarity'],
                    'structure': binary_results['structure_similarity']
                },
                'match': total_score > 95,
                'type': 'solidworks',
                'similarity_category': similarity_category
            }

            return result

        except Exception as e:
            logging.error(f"Karşılaştırma hatası: {e}")
            return self._create_error_result()

    def _compare_binary(self, file1, file2):
        """Binary karşılaştırma"""
        try:
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                # Dosya boyutları
                f1.seek(0, 2)
                f2.seek(0, 2)
                size1 = f1.tell()
                size2 = f2.tell()
                
                # Başa dön
                f1.seek(0)
                f2.seek(0)

                # Header analizi (ilk 1KB)
                header_sim = self._compare_chunks(f1.read(1024), f2.read(1024))

                # Content analizi
                content_chunks = []
                f1.seek(0)
                f2.seek(0)
                
                while True:
                    chunk1 = f1.read(self.chunk_size)
                    chunk2 = f2.read(self.chunk_size)
                    
                    if not chunk1 or not chunk2:
                        break
                        
                    sim = self._compare_chunks(chunk1, chunk2)
                    content_chunks.append(sim)

                # Footer analizi (son 1KB)
                f1.seek(-1024, 2)
                f2.seek(-1024, 2)
                footer_sim = self._compare_chunks(f1.read(), f2.read())

                # Sonuçları hesapla
                content_similarity = sum(content_chunks) / len(content_chunks) if content_chunks else 0
                structure_similarity = (header_sim + footer_sim) / 2

                return {
                    'content_similarity': content_similarity * 100,
                    'structure_similarity': structure_similarity * 100,
                    'size_ratio': min(size1, size2) / max(size1, size2) * 100
                }

        except Exception as e:
            logging.error(f"Binary karşılaştırma hatası: {e}")
            return {
                'content_similarity': 0,
                'structure_similarity': 0,
                'size_ratio': 0
            }

    def _compare_chunks(self, chunk1, chunk2):
        """İki binary chunk'ı karşılaştır"""
        if not chunk1 or not chunk2:
            return 0.0
            
        return difflib.SequenceMatcher(None, chunk1, chunk2).ratio()

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

    def _calculate_final_score(self, binary_results, metadata_sim):
        """Final skor hesaplama"""
        weights = {
            'content': 0.5,      # İçerik en önemli
            'structure': 0.3,    # Yapı ikinci önemli
            'metadata': 0.2      # Metadata en az önemli
        }

        # Temel skor
        score = (
            binary_results['content_similarity'] * weights['content'] +
            binary_results['structure_similarity'] * weights['structure'] +
            metadata_sim * weights['metadata']
        )

        # Boyut oranı çok yüksekse bonus
        if binary_results['size_ratio'] > 95:
            score *= 1.1  # %10 bonus

        return min(100, score)

    def _compare_hash(self, file1, file2):
        """Hash karşılaştırması"""
        try:
            hash1 = hashlib.md5(open(file1, 'rb').read()).hexdigest()
            hash2 = hashlib.md5(open(file2, 'rb').read()).hexdigest()
            return hash1 == hash2
        except Exception as e:
            logging.error(f"Hash karşılaştırma hatası: {e}")
            return False

    def _is_save_as(self, metadata_sim, content_sim, structure_sim):
        """SaveAs kontrolü"""
        return (
            metadata_sim > 60 and    # Metadata benzer
            content_sim > 80 and     # İçerik çok benzer
            structure_sim > 70       # Yapı benzer
        )

    def _get_category(self, score):
        """Benzerlik kategorisini belirle"""
        if score >= 95:
            return "Tam Eşleşme"
        elif score >= 85:
            return "SaveAs Kopyası"
        elif score >= 70:
            return "Benzer Dosya"
        elif score >= 50:
            return "Kısmen Benzer"
        elif score >= 30:
            return "Az Benzer"
        else:
            return "Farklı Dosyalar"

    def _format_results(self, results):
        """Sonuçları formatla"""
        return {
            'total_score': round(results['score'], 1),
            'details': {
                'metadata': round(results['details']['metadata'], 1),
                'content': round(results['details']['content'], 1),
                'structure': round(results['details']['structure'], 1)
            },
            'category': self._get_category(results['score']),
            'evaluation': self._get_evaluation(results)
        }

    def _get_evaluation(self, results):
        """Sonuçları değerlendir"""
        score = results['score']
        
        if score >= 95:
            return "Dosyalar birebir aynı veya çok küçük farklılıklar içeriyor."
        elif score >= 85:
            return "Dosyalardan biri diğerinin SaveAs ile oluşturulmuş kopyası olabilir."
        elif score >= 70:
            return "Dosyalar benzer içeriğe sahip, ancak bazı değişiklikler yapılmış."
        elif score >= 50:
            return "Dosyalar kısmen benzer, önemli farklılıklar var."
        elif score >= 30:
            return "Dosyalar az benzerlik gösteriyor, çoğunlukla farklılar."
        else:
            return "Dosyalar tamamen farklı."

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
            'type': 'solidworks',
            'similarity_category': "Tam Eşleşme"
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
            'type': 'solidworks',
            'similarity_category': "SaveAs Kopyası"
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
            'type': 'solidworks',
            'similarity_category': "Hata"
        }

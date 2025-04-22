import os
import hashlib
import difflib
import logging

class SolidWorksAnalyzer:
    def __init__(self):
        self.binary_cache = {}
        self.chunk_size = 4096  # 4KB chunks

    def compare(self, file1, file2):
        """İki SolidWorks dosyasını karşılaştırır"""
        try:
            # Hash kontrolü
            if self._compare_hash(file1, file2):
                return self._create_exact_match()

            # Metadata analizi
            metadata_sim = self._compare_metadata(file1, file2)

            # Binary analiz
            binary_sim = self._compare_binary_content(file1, file2)

            # Yapısal analiz
            structure_sim = self._compare_file_structure(file1, file2)

            # SaveAs kontrolü
            if self._is_save_as(metadata_sim, binary_sim, structure_sim):
                return self._create_save_as_match()

            # Final skor hesaplama
            total_score = self._calculate_final_score(
                metadata_sim,
                binary_sim,
                structure_sim
            )

            # Benzerlik kategorisi
            similarity_category = self._categorize_similarity(total_score)

            return {
                'score': total_score,
                'details': {
                    'metadata': metadata_sim,
                    'content': binary_sim,
                    'structure': structure_sim
                },
                'match': total_score > 95,
                'type': 'solidworks',
                'similarity_category': similarity_category
            }

        except Exception as e:
            logging.error(f"Karşılaştırma hatası: {e}")
            return self._create_error_result()

    def _compare_metadata(self, file1, file2):
        """Metadata karşılaştırması"""
        try:
            stat1 = os.stat(file1)
            stat2 = os.stat(file2)

            # Boyut karşılaştırması
            size_ratio = min(stat1.st_size, stat2.st_size) / max(stat1.st_size, stat2.st_size)

            # Zaman damgası karşılaştırması
            time_diff = abs(stat1.st_mtime - stat2.st_mtime)
            time_sim = max(0, 1 - (time_diff / 86400))  # 24 saat içinde

            return (size_ratio * 0.7 + time_sim * 0.3) * 100
        except Exception as e:
            logging.error(f"Metadata karşılaştırma hatası: {e}")
            return 0.0

    def _compare_binary_content(self, file1, file2):
        """Binary içerik karşılaştırması"""
        try:
            # Önbellek anahtarı
            cache_key = f"{file1}:{file2}:binary"
            if cache_key in self.binary_cache:
                return self.binary_cache[cache_key]
                
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                matches = 0
                total_chunks = 0

                while True:
                    chunk1 = f1.read(self.chunk_size)
                    chunk2 = f2.read(self.chunk_size)

                    if not chunk1 and not chunk2:
                        break

                    if not chunk1 or not chunk2:
                        # Dosya boyutları farklı, kalan kısmı penalize et
                        total_chunks += 1
                        continue

                    similarity = difflib.SequenceMatcher(None, chunk1, chunk2).ratio()
                    matches += similarity
                    total_chunks += 1

                result = (matches / total_chunks * 100) if total_chunks > 0 else 0
                self.binary_cache[cache_key] = result
                return result
        except Exception as e:
            logging.error(f"Binary içerik karşılaştırma hatası: {e}")
            return 0.0

    def _compare_file_structure(self, file1, file2):
        """Dosya yapısı karşılaştırması"""
        try:
            # Önbellek anahtarı
            cache_key = f"{file1}:{file2}:structure"
            if cache_key in self.binary_cache:
                return self.binary_cache[cache_key]
                
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                # Header analizi (ilk 1024 byte)
                header1 = f1.read(1024)
                header2 = f2.read(1024)
                header_sim = difflib.SequenceMatcher(None, header1, header2).ratio()

                # Footer analizi (son 1024 byte)
                f1.seek(-1024, 2)
                f2.seek(-1024, 2)
                footer1 = f1.read()
                footer2 = f2.read()
                footer_sim = difflib.SequenceMatcher(None, footer1, footer2).ratio()
                
                # Orta kısım analizi (dosyanın ortasından 1024 byte)
                f1_size = os.path.getsize(file1)
                f2_size = os.path.getsize(file2)
                
                if f1_size > 4096 and f2_size > 4096:
                    f1.seek(f1_size // 2 - 512)
                    f2.seek(f2_size // 2 - 512)
                    middle1 = f1.read(1024)
                    middle2 = f2.read(1024)
                    middle_sim = difflib.SequenceMatcher(None, middle1, middle2).ratio()
                else:
                    middle_sim = (header_sim + footer_sim) / 2

                result = (header_sim * 0.4 + middle_sim * 0.2 + footer_sim * 0.4) * 100
                self.binary_cache[cache_key] = result
                return result
        except Exception as e:
            logging.error(f"Dosya yapısı karşılaştırma hatası: {e}")
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

    def _is_save_as(self, metadata_sim, binary_sim, structure_sim):
        """SaveAs kontrolü"""
        return (
            metadata_sim > 60 and    # Metadata benzer
            binary_sim > 80 and      # İçerik çok benzer
            structure_sim > 90       # Yapı neredeyse aynı
        )

    def _calculate_final_score(self, metadata_sim, binary_sim, structure_sim):
        """Final skor hesaplama"""
        weights = {
            'metadata': 0.20,
            'binary': 0.50,
            'structure': 0.30
        }

        base_score = (
            metadata_sim * weights['metadata'] +
            binary_sim * weights['binary'] +
            structure_sim * weights['structure']
        )

        # Binary benzerliği yüksekse bonus
        if binary_sim > 95:
            base_score *= 1.1

        return min(100, base_score)
        
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

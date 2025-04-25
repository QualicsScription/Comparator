from src.utils.helpers import get_file_info, calculate_similarity

class FileComparator:
    def __init__(self):
        self.file1_path = None
        self.file2_path = None
        self.comparison_results = {}
    
    def set_files(self, file1_path, file2_path):
        self.file1_path = file1_path
        self.file2_path = file2_path
    
    def compare(self):
        if not self.file1_path or not self.file2_path:
            raise ValueError("Dosya yolları ayarlanmamış!")
        
        # Dosya bilgilerini al
        file1_info = get_file_info(self.file1_path)
        file2_info = get_file_info(self.file2_path)
        
        # Karşılaştırma sonuçlarını hesapla
        self.comparison_results = {
            'similarity': calculate_similarity(file1_info, file2_info),
            'file1_info': file1_info,
            'file2_info': file2_info
        }
        
        return self.comparison_results
import os
from datetime import datetime

def get_file_info(filepath):
    """Dosya hakkında temel bilgileri döndürür."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dosya bulunamadı: {filepath}")
        
    stats = os.stat(filepath)
    return {
        'size': stats.st_size,
        'created': datetime.fromtimestamp(stats.st_ctime),
        'modified': datetime.fromtimestamp(stats.st_mtime),
        'name': os.path.basename(filepath),
        'extension': os.path.splitext(filepath)[1]
    }

def calculate_similarity(file1_info, file2_info):
    """İki dosya arasındaki benzerlik oranını hesaplar."""
    # Basit bir benzerlik hesaplaması
    similar_points = 0
    total_points = 0
    
    # Boyut karşılaştırması
    if abs(file1_info['size'] - file2_info['size']) < 100:
        similar_points += 1
    total_points += 1
    
    # Uzantı karşılaştırması
    if file1_info['extension'] == file2_info['extension']:
        similar_points += 1
    total_points += 1
    
    return (similar_points / total_points) * 100 if total_points > 0 else 0
import os
import shutil

def fix_project_structure():
    # Ana dizini temizle
    if os.path.exists('main'):
        # main klasörünün içindeki src klasörünü ana dizine taşı
        shutil.move('main/src', '.')
        # main klasörünü sil
        shutil.rmtree('main')

    # main.py'yi güncelle
    main_content = """from src.ui.main_window import MainWindow

def main():
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()"""

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(main_content)

    # main_window.py'deki import yollarını güncelle
    main_window_path = 'src/ui/main_window.py'
    with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('from ..core.comparator', 'from src.core.comparator')
    
    with open(main_window_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # comparator.py'deki import yollarını güncelle
    comparator_path = 'src/core/comparator.py'
    with open(comparator_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('from ..utils.helpers', 'from src.utils.helpers')
    
    with open(comparator_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Proje yapısı güncellendi!")

if __name__ == "__main__":
    fix_project_structure()

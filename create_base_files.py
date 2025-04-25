import os

def create_base_files():
    # README.md içeriği
    readme_content = """# File Comparator

SolidWorks dosyalarını karşılaştırmak için geliştirilmiş bir Python uygulaması.

## Özellikler
- SolidWorks dosyalarını karşılaştırma
- Farklılıkları görsel olarak gösterme
- Detaylı rapor oluşturma

## Kurulum
pip install -r requirements.txt

## Kullanım
python main.py"""

    # requirements.txt içeriği
    requirements_content = """customtkinter==5.2.0
Pillow==10.0.0
numpy==1.24.3
matplotlib==3.7.1"""

    # .gitignore içeriği
    gitignore_content = """# Python
__pycache__/
*.pyc
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
comperator_env/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Logs
*.log
setup_log_*.txt

# Project specific
dev/reports/performance/*.txt
dev/reports/analysis/*.txt"""

    # Dosyaları oluştur
    files = {
        'README.md': readme_content,
        'requirements.txt': requirements_content,
        '.gitignore': gitignore_content
    }

    for filename, content in files.items():
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"{filename} oluşturuldu")

    # __init__.py dosyalarını oluştur
    init_directories = [
        'main/src/ui',
        'main/src/core',
        'main/src/utils',
        'main/src/config'
    ]

    for directory in init_directories:
        init_path = os.path.join(directory, '__init__.py')
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(f"# {os.path.basename(directory)} package\n")
        print(f"{init_path} oluşturuldu")

if __name__ == "__main__":
    create_base_files()

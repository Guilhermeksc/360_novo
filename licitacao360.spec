# licitacao360.spec
from PyInstaller.utils.hooks import collect_data_files
import os
from pathlib import Path

# Nome do executável e especificações gerais
app_name = "licitacao360"
main_file = "src/main.py" 

# Usando o diretório atual como base
base_dir = Path(os.path.abspath('.'))
src_dir = base_dir / "src"
database_dir = src_dir / "database"
resources_dir = src_dir / "resources"


datas = [
    (str(src_dir / "style.css"), "src/"),  # Inclui o style.css diretamente na pasta `src`
    (str(resources_dir / "icons"), "src/resources/icons"),
    ]

# Incluindo arquivos de recursos, ícones e bancos de dados
datas += collect_data_files('src', includes=['**/*'])

a = Analysis(
    [main_file],
    pathex=[str(base_dir), str(src_dir)], 
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
)


# Configurando o executável com ícone e ocultando o console
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name=app_name,
    debug=True,  # Terminal aberto para exibir saídas
    strip=False,
    upx=True,
    console=True,  
    icon=str(resources_dir / "icone_brasil.ico"),
)

# Gerando o executável final
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name=app_name,
)
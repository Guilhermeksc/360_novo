import sys
from pathlib import Path
import json

if getattr(sys, 'frozen', False):  # Executável compilado
    BASE_DIR = Path(sys._MEIPASS) / "src"  # Diretório temporário + 'src'
else:  # Ambiente de desenvolvimento
    BASE_DIR = Path(__file__).resolve().parent.parent

# Diretórios
DATABASE_DIR = BASE_DIR / "database"
DATA_ATAS_PATH = DATABASE_DIR / "controle_atas.db"
DATA_LICITACAO_PATH = DATABASE_DIR / "controle_licitacao.db"
DATA_DISPENSA_ELETRONICA_PATH = DATABASE_DIR / "controle_contratacao_direta.db"
DATA_CONTRATOS_PATH = DATABASE_DIR / "controle_contrato.db"
CONTROLE_ASS_CONTRATOS_DADOS = DATABASE_DIR / "controle_assinatura.db"
CONTROLE_DADOS = DATABASE_DIR / "controle_dados.db"

CONFIG_FILE = BASE_DIR / "config.json"
PRE_DEFINICOES_JSON = BASE_DIR / "pre_definicioes.json"
AGENTES_RESPONSAVEIS_FILE = BASE_DIR / "agentes_responsaveis.json"
ORGANIZACOES_FILE = BASE_DIR / "organizacoes.json"

# Resources
RESOURCES_DIR = BASE_DIR / "resources"
TEMPLATE_DIR = RESOURCES_DIR / "templates"
STYLE_PATH = RESOURCES_DIR / "style.css" 
ICONS_DIR = RESOURCES_DIR / "icons"
IMAGES_DIR = RESOURCES_DIR / "images"
TEMPLATE_DIR = RESOURCES_DIR / "template"
TEMPLATE_PATH = TEMPLATE_DIR / 'template_ata.docx'

# Modules
MODULES_DIR = BASE_DIR / "modules"
DISPENSA_ELETRONICA_DIR = MODULES_DIR / "dispensa_eletronica"

LICITACAO_DIR = MODULES_DIR / "planejamento"

ATAS_DIR = MODULES_DIR / "atas_novo"

PDF_DIR = ATAS_DIR / "termo_homologacao"

CONTRATOS_DIR = MODULES_DIR / "contratos"
JSON_CONTRATOS_DIR = CONTRATOS_DIR / "json"

HOME_PATH = BASE_DIR / "main.py"
CONTROLE_ATAS_DIR = DATABASE_DIR / "Atas"

TEMPLATE_DISPENSA_DIR = DISPENSA_ELETRONICA_DIR / "template"

CONFIG_FILE = BASE_DIR / 'config.json'

# Funções de Configuração
def load_config_path_id():
    if not Path(CONFIG_FILE).exists():
        return {}
    with open(CONFIG_FILE, 'r') as file:
        return json.load(file)

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)

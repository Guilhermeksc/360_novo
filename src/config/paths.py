from PyQt6.QtCore import *
import sys
from pathlib import Path
import json

if getattr(sys, 'frozen', False):  # Executável compilado
    BASE_DIR = Path(sys._MEIPASS) / "src"  # Diretório temporário + 'src'
else:  # Ambiente de desenvolvimento
    BASE_DIR = Path(__file__).resolve().parent.parent

# Diretórios
DATABASE_DIR = BASE_DIR / "database"
TREEVIEW_DATA_PATH =  DATABASE_DIR / "treeview_data.csv"
DATA_ATAS_PATH = DATABASE_DIR / "controle_atas.db"
DATA_LICITACAO_PATH = DATABASE_DIR / "controle_licitacao.db"
DATA_DISPENSA_ELETRONICA_PATH = DATABASE_DIR / "controle_contratacao_direta.db"
DATA_CONTRATOS_PATH = DATABASE_DIR / "controle_contrato.db"
CONTROLE_ASS_CONTRATOS_DADOS = DATABASE_DIR / "controle_assinatura.db"
CONTROLE_DADOS = DATABASE_DIR / "controle_dados.db"

MSG_LICITACAO_JSON = BASE_DIR / "msg_licitacao.json"
LICITACAO_CONTROLE_JSON = BASE_DIR / "licitacao.json"
CONTROLE_PRAZOS = BASE_DIR / "controle_status.json"
CONFIG_FILE = BASE_DIR / "config.json"
PRE_DEFINICOES_JSON = BASE_DIR / "pre_definicioes.json"
AGENTES_RESPONSAVEIS_FILE = BASE_DIR / "agentes_responsaveis.json"
ORGANIZACOES_FILE = BASE_DIR / "organizacoes.json"
CONFIG_API_FILE = BASE_DIR / "config_api.json"

# Resources
RESOURCES_DIR = BASE_DIR / "resources"
TEMPLATE_DIR = RESOURCES_DIR / "templates"
STYLE_PATH = RESOURCES_DIR / "style.css" 
ICONS_DIR = RESOURCES_DIR / "icons"
IMAGES_DIR = RESOURCES_DIR / "images"
TEMPLATE_DIR = RESOURCES_DIR / "template"
TEMPLATE_PATH = TEMPLATE_DIR / 'template_ata.docx'

TEMPLATE_AUTUACAO = TEMPLATE_DIR / "template_autuacao.docx"
TEMPLATE_CHECKLIST = TEMPLATE_DIR / "checklist.docx"

ACANTO = ICONS_DIR / "brasil.png"

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

class ConfigManager(QObject):
    config_updated = pyqtSignal(str, Path)  # sinal emitido quando uma configuração é atualizada

    def __init__(self, config_file):
        super().__init__()
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_config(self, key, value):
        self.config[key] = value
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
        self.config_updated.emit(key, Path(value))
        
    def update_config(self, key, value):
        # Aqui garantimos que ambos os parâmetros sejam passados corretamente para save_config
        self.save_config(key, value)
        self.config_updated.emit(key, Path(value))

    def get_config(self, key, default_value):
        return self.config.get(key, default_value)
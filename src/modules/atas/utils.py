
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATABASE_DIR = ASSETS_DIR / "database"
CONFIG_FILE = BASE_DIR / "config.json"
CONTROLE_DADOS = DATABASE_DIR / "controle_atas.db"
CONTROLE_ASS_CONTRATOS_DADOS = DATABASE_DIR / "controle_assinatura.db"
PDF_DIR = BASE_DIR / "pasta_pdf"
RESOURCES_DIR = ASSETS_DIR / "resources"
PRE_DEFINICOES_JSON = BASE_DIR / "pre_definicioes.json"
ICONS_DIR = RESOURCES_DIR / "icons"

def load_config(key, default_value):
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get(key, default_value)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_value

def extract_text_from_pdf(self, pdf_file):
    # Extrai o texto de um arquivo PDF usando PyMuPDF
    print(f"Extraindo texto do PDF: {pdf_file}.")
    text = ""
    try:
        # Abre o arquivo PDF
        with fitz.open(pdf_file) as pdf:
            for page_number in range(len(pdf)):
                # Carrega a página
                page = pdf.load_page(page_number)
                # Extrai o texto da página
                page_text = page.get_text()
                if page_text:
                    text += page_text
                else:
                    self.update_context(f"Aviso: Página {page_number + 1} de {pdf_file} não contém texto extraível.")
                    print(f"Aviso: Página {page_number + 1} de {pdf_file} não contém texto extraível.")
    except Exception as e:
        self.update_context(f"Erro ao extrair texto de {pdf_file}: {e}")
        print(f"Erro ao extrair texto de {pdf_file}: {e}")
    return text

def create_button(text, icon, callback, tooltip_text, icon_size=QSize(30, 30), button_size=QSize(120, 30)):
    """Cria um botão personalizado com texto, ícone, callback e tooltip."""
    btn = QPushButton(text)
    if icon:
        btn.setIcon(icon)
        btn.setIconSize(icon_size)
    btn.clicked.connect(callback)
    btn.setToolTip(tooltip_text)
    
    # Define o tamanho fixo do botão
    btn.setFixedSize(button_size.width(), button_size.height())

    btn.setStyleSheet("""
    QPushButton {
        font-size: 12pt;
        padding: 5px;
    }
    """)

    return btn
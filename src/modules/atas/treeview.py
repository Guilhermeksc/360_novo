from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from utils import *
from datetime import datetime
from pathlib import Path    
import pandas as pd
from num2words import num2words
from docxtpl import DocxTemplate
from docx import Document
from docx.shared import Pt
from openpyxl import Workbook, load_workbook
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from openpyxl.styles import Font, PatternFill
import re
from typing import Optional, Dict
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import time
import pandas as pd
from pathlib import Path
from utils import *

COLETA_DADOS_RESPONSAVEL = (
    r"Dados do Responsável Legal CPF: (?P<cpf>\d{3}\.\d{3}\.\d{3}-\d{2}) Nome:"    
    r"(?P<nome>.*?)(?: Dados do Responsável pelo Cadastro| Emitido em:|CPF:)"
)

def extrair_dados_responsavel(texto: str) -> Optional[Dict[str, str]]:
    match = re.search(COLETA_DADOS_RESPONSAVEL, texto, re.S)
    if not match:
        return None

    return {
        'cpf': match.group('cpf').strip(),
        'responsavel_legal': match.group('nome').strip()
    }

import pandas as pd

def replace_invalid_chars(filename: str, invalid_chars: list, replacement: str = '_') -> str:
    """Substitui caracteres inválidos em um nome de arquivo."""
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, replacement)
    return filename

def clean_company_names_in_csv(csv_path: str, invalid_chars: list, replacement: str = '_') -> None:
    """Limpa os nomes das empresas na coluna 'empresa' de um arquivo CSV."""
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    # Carregar o CSV em um DataFrame
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    
    # Verificar se a coluna 'empresa' existe
    if 'empresa' in df.columns:
        # Aplicar a função de limpeza na coluna 'empresa'
        df['empresa'] = df['empresa'].apply(lambda x: replace_invalid_chars(str(x), invalid_chars, replacement))
        
        # Salvar as alterações de volta ao CSV
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
def extrair_dados_sicaf(texto: str) -> pd.DataFrame:
    dados_sicaf = (
        r"CNPJ:\s*(?P<cnpj>[\d./-]+)\s*"
        r"(?:DUNS®:\s*(?P<duns>[\d]+)\s*)?"
        r"Razão Social:\s*(?P<empresa>.*?)\s*"
        r"Nome Fantasia:\s*(?P<nome_fantasia>.*?)\s*"
        r"Situação do Fornecedor:\s*(?P<situacao_cadastro>.*?)\s*"
        r"Data de Vencimento do Cadastro:\s*(?P<data_vencimento>\d{2}/\d{2}/\d{4})\s*"
        r"Dados do Nível.*?Dados para Contato\s*"
        r"CEP:\s*(?P<cep>[\d.-]+)\s*"
        r"Endereço:\s*(?P<endereco>.*?)\s*"
        r"Município\s*/\s*UF:\s*(?P<municipio>.*?)\s*/\s*(?P<uf>.*?)\s*"
        r"Telefone:\s*(?P<telefone>.*?)\s*"
        r"E-mail:\s*(?P<email>.*?)\s*"
        r"Dados do Responsável Legal"
    )

    match = re.search(dados_sicaf, texto, re.S)
    if not match:
        return pd.DataFrame()  # Retorna um DataFrame vazio

    data = {key: [value.strip()] if value else [None] for key, value in match.groupdict().items()}

    df = pd.DataFrame(data)
    return df

def extrair_dados_responsavel(texto: str) -> Optional[Dict[str, str]]:
    match = re.search(COLETA_DADOS_RESPONSAVEL, texto, re.S)
    if not match:
        return None

    return {
        'cpf': match.group('cpf').strip(),
        'responsavel_legal': match.group('nome').strip()
    }


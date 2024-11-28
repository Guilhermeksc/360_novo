from functools import partial
import requests
import json
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.config.paths import CONTRATOS_JSON
from src.modules.utils.add_button import add_button_func
from pathlib import Path
from datetime import datetime

class ItensManagerContratos(QWidget):
    def __init__(self, icons, dados):
        super().__init__()
        self.icons = icons
        self.dados = dados
        self.init_ui()

    def init_ui(self):
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        
        # Adicionar conteúdo relacionado aos itens
        titulo_label = QLabel("Itens")
        titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        # Adiciona uma tabela para listar itens
        self.tabela_itens = QTableWidget(0, 4)
        self.tabela_itens.setHorizontalHeaderLabels(["ID", "Nome", "Quantidade", "Preço"])
        self.tabela_itens.horizontalHeader().setStretchLastSection(True)
        
        # Botão para consultar itens
        self.botao_consultar = QPushButton("Consultar Itens")
        self.botao_consultar.setStyleSheet("font-size: 14px; padding: 6px;")
        self.botao_consultar.clicked.connect(self.load_itens_data)  # Conecta o botão à função de consulta
        
        # Adiciona widgets ao layout
        self.main_layout.addWidget(titulo_label)
        self.main_layout.addWidget(self.tabela_itens)
        self.main_layout.addWidget(self.botao_consultar)

    def load_itens_data(self):
        """Carrega os itens da API e preenche a tabela."""
        try:
            # Obtém o ID do contrato
            contrato_id = self.dados.get('id')
            if not contrato_id:
                raise ValueError("ID do contrato não encontrado em self.dados")
            
            # Faz a requisição à API
            url = f"https://contratos.comprasnet.gov.br/api/contrato/{contrato_id}/itens"
            print(f"Realizando consulta na URL: {url}")  # Exibe a URL no console
            
            response = requests.get(url)
            response.raise_for_status()
            itens = response.json()
            
            # Exibe a resposta da API no console
            print("Resposta da API (JSON):")
            print(json.dumps(itens, indent=4, ensure_ascii=False))
            
            # Preenche a tabela com os dados obtidos
            self.populate_table(itens)
        
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar itens: {str(e)}")

    def populate_table(self, itens):
        """Popula a tabela com os itens."""
        self.tabela_itens.setRowCount(len(itens))
        
        for row, item in enumerate(itens):
            # Preenche as colunas
            self.tabela_itens.setItem(row, 0, QTableWidgetItem(str(item.get('id', ''))))
            self.tabela_itens.setItem(row, 1, QTableWidgetItem(item.get('nome', '')))
            self.tabela_itens.setItem(row, 2, QTableWidgetItem(str(item.get('quantidade', ''))))
            self.tabela_itens.setItem(row, 3, QTableWidgetItem(f"R$ {item.get('preco', 0):,.2f}"))
        
        self.tabela_itens.resizeColumnsToContents()

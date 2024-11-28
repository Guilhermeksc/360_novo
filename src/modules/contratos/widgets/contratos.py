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
import os

class DownloadManagerContratos(QWidget):
    def __init__(self, icons, dados):
        super().__init__()
        self.icons = icons
        self.dados = dados
        self.init_ui()

    def init_ui(self):
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        
        # Adicionar conteúdo relacionado ao download do contrato
        titulo_label = QLabel("Download do Contrato")
        titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        # Botão para iniciar consulta
        self.botao_consultar = QPushButton("Consultar Contrato")
        self.botao_consultar.setStyleSheet("font-size: 14px; padding: 6px;")
        self.botao_consultar.clicked.connect(self.load_itens_data)  # Conecta o botão ao método de consulta
        
        # Adiciona widgets ao layout
        self.main_layout.addWidget(titulo_label)
        self.main_layout.addWidget(self.botao_consultar)

    def load_itens_data(self):
        """Consulta a API e processa o resultado."""
        try:
            # Obtém o ID do contrato
            contrato_id = self.dados.get('id')
            if not contrato_id:
                raise ValueError("ID do contrato não encontrado em self.dados")
            
            # Faz a requisição à API
            url = f"https://contratos.comprasnet.gov.br/api/contrato/{contrato_id}/arquivos"
            print(f"Realizando consulta na URL: {url}")  # Exibe a URL no console
            
            response = requests.get(url)
            response.raise_for_status()
            arquivos = response.json()
            
            # Exibe o resultado da API no console
            print("Resultado da consulta (JSON):")
            print(json.dumps(arquivos, indent=4, ensure_ascii=False))
            
            if not arquivos:
                QMessageBox.information(self, "Sem resultados", "Nenhum arquivo foi encontrado para o contrato informado.")
                return
            
            # Obtém o primeiro arquivo e faz o download
            arquivo = arquivos[0]
            path_arquivo = arquivo.get('path_arquivo')
            if not path_arquivo:
                QMessageBox.warning(self, "Erro", "O caminho do arquivo não está disponível no resultado.")
                return
            
            # Realiza o download do arquivo
            self.download_and_open_file(path_arquivo)
        
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {str(e)}")

    def download_and_open_file(self, url):
        """Faz o download do arquivo e o abre."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Define o nome do arquivo local
            local_filename = os.path.join(os.getcwd(), url.split("/")[-1])
            with open(local_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            QMessageBox.information(self, "Download Concluído", f"Arquivo baixado com sucesso em: {local_filename}")
            
            # Abre o arquivo baixado
            QDesktopServices.openUrl(QUrl.fromLocalFile(local_filename))
        
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao baixar ou abrir o arquivo: {str(e)}")
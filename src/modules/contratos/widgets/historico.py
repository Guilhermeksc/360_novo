from functools import partial
import json
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.config.paths import CONTRATOS_JSON
from src.modules.utils.add_button import add_button_func
from pathlib import Path
from datetime import datetime
import requests


class HistoricoManagerContratos(QWidget):
    def __init__(self, icons, dados):
        super().__init__()
        self.icons = icons
        self.dados = dados
        self.id = self.dados.get("id", None)  # Obtém o ID do dicionário self.dados
        self.init_ui()
        
    def init_ui(self):
        # Layout principal
        self.main_layout = QVBoxLayout(self)

        # Título
        titulo_label = QLabel("Histórico")
        titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        # Botão para consultar a API
        self.consulta_button = QPushButton("Histórico do Contrato")
        self.consulta_button.setStyleSheet("font-size: 14px; padding: 5px;")
        self.consulta_button.clicked.connect(self.consultar_empenhos)

        # Área de rolagem para exibir os detalhes do empenho
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_content = QWidget()
        self.scroll_area.setWidget(self.scroll_area_content)
        self.details_layout = QVBoxLayout(self.scroll_area_content)
        
        # Adiciona widgets ao layout
        self.main_layout.addWidget(titulo_label)
        self.main_layout.addWidget(self.consulta_button)
        self.main_layout.addWidget(self.scroll_area)
    
    def consultar_empenhos(self):
        """
        Faz a consulta à API e exibe o resultado no console.
        """
        if not self.id:
            print("Erro: ID não definido.")
            return
        
        url = f"https://contratos.comprasnet.gov.br/api/contrato/{self.id}/historico"
        print(f"Consultando API: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            historico = response.json()  # Supõe que o retorno é um JSON
            print(historico)  # Print no console
            # self.popular_detalhes(historico)
        except requests.exceptions.RequestException as e:
            print(f"Erro ao consultar a API: {e}")
    
    # def popular_detalhes(self, empenhos):
    #     """
    #     Popula os detalhes do empenho no layout.
    #     """
    #     # Limpa o layout atual
    #     for i in reversed(range(self.details_layout.count())):
    #         widget = self.details_layout.itemAt(i).widget()
    #         if widget:
    #             widget.deleteLater()

    #     # Adiciona os dados formatados
    #     for empenho in empenhos:
    #         detalhes = f"""
    #         <b>Nº do empenho:</b> {empenho.get('numero', 'N/A')} - 
    #         <b>Data da emissão:</b> {empenho.get('data_emissao', 'N/A')} -
    #         <b>Fonte de recurso:</b> {empenho.get('fonte_recurso', 'N/A')} -
    #         <b>Programa de Trabalho:</b> {empenho.get('programa_trabalho', 'N/A')}<br>
    #         <b>Plano interno:</b> {empenho.get('planointerno', 'N/A')} -
    #         <b>Natureza Despesa:</b> {empenho.get('naturezadespesa', 'N/A')}<br>
    #         <b>Empenhado:</b> {empenho.get('empenhado', 'N/A')} -
    #         <b>Liquidado:</b> {empenho.get('liquidado', 'N/A')} -
    #         <b>Pago:</b> {empenho.get('pago', 'N/A')}<br>
    #         <b>RP Inscrito:</b> {empenho.get('rpinscrito', 'N/A')} -
    #         <b>RP a Liquidar:</b> {empenho.get('rpaliquidar', 'N/A')} -
    #         <b>RP Liquidado:</b> {empenho.get('rpliquidado', 'N/A')} -
    #         <b>RP Pago:</b> {empenho.get('rppago', 'N/A')}<br>
    #         """

    #         label = QLabel(detalhes)
    #         label.setWordWrap(True)
    #         label.setStyleSheet("font-size: 14px; padding: 10px; border: 1px solid #ccc; margin: 5px;")
    #         self.details_layout.addWidget(label)

    #     self.details_layout.addStretch()  # Adiciona espaço flexível no final

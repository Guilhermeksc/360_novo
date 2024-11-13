import pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.modules.utils.add_button import add_button

class TermoReferenciaWidget(QWidget):
    abrirTabelaNova = pyqtSignal()
    carregarTabela = pyqtSignal()  
    configurarSqlModelSignal = pyqtSignal() 

    def __init__(self, parent=None, icons=None):
        super().__init__(parent)
        self.setWindowTitle("Termo de Referência")
        self.resize(800, 600)
        self.parent = parent
        self.icons = icons

        # Configuração do layout principal
        self.layout = QVBoxLayout(self)

        # Configurar o QTableView para exibir os dados
        self.table_view = QTableView(self)
        self.layout.addWidget(self.table_view)

        # Criar layout horizontal para os botões
        button_layout = QHBoxLayout()

        # Usando add_button para criar e adicionar botões
        add_button("Abrir Tabela Nova", "excel_down", self.abrirTabelaNova, button_layout, icons=None, tooltip="Cria e abre uma nova tabela em Excel")
        add_button("Carregar Tabela", "excel_up", self.carregarTabela, button_layout, icons=None, tooltip="Carrega uma tabela existente para o banco de dados")

        # Adicionar layout de botões ao layout principal
        self.layout.addLayout(button_layout)

        # Configurar o modelo SQL para visualização
        self.configurarSqlModelSignal.emit()

    def inserir_dados_no_banco(self, tabela: pd.DataFrame):
        # Inserir os dados do DataFrame na tabela usando DatabaseATASManager
        try:
            self.database_manager.save_dataframe(tabela, "controle_atas")
            print("Dados inseridos no banco com sucesso.")
        except Exception as e:
            print(f"Erro ao inserir dados no banco: {e}")
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.modules.utils.add_button import add_button
class TermoReferenciaWidget(QWidget): 
    abrirTabelaNova = pyqtSignal()
    carregarTabela = pyqtSignal()  
    configurarSqlModelSignal = pyqtSignal() 

    def __init__(self, parent, icons):
        super().__init__(parent)
        self.setWindowTitle("Termo de Referência")
        self.resize(800, 600)
        self.parent = parent
        self.icons = icons
        # Configuração do layout principal
        self.layout = QVBoxLayout(self)

        # Configurar o QTableView para exibir os dados
        self.table_view = QTableView(self)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)  # Seleciona a linha inteira
        self.table_view.verticalHeader().setVisible(False)  # Oculta a coluna de índice
        self.layout.addWidget(self.table_view)

        # Aplicar estilo CSS para personalização adicional
        self.table_view.setStyleSheet("""
            QTableView {
                background-color: #181928;
                color: #FFFFFF;
                gridline-color: #3C3C5A;
                alternate-background-color: #2C2F3F;
                selection-background-color: #2C2F3F;
                selection-color: #D4F8F2;
                border: none;
                                      font-size: 14px;
            }
            QTableView::item:selected {
                background-color: #2C2F3F;
                color: #D4F8F2;
            }
            QTableView::item {
                border: 1px solid transparent;
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #2C9E97;
                color: black;
                                      font-weight: bold;
                                      font-size: 14px;
                padding: 4px;
                border: 1px solid #3C3C5A;
            }
        """)

        # Criar layout horizontal para os botões
        button_layout = QHBoxLayout()

        # Usando add_button para criar e adicionar botões
        add_button("Abrir Tabela Nova", "excel_down", self.abrirTabelaNova, button_layout, self.icons, tooltip="Cria e abre uma nova tabela em Excel")
        add_button("Carregar Tabela", "excel_up", self.carregarTabela, button_layout, self.icons, tooltip="Carrega uma tabela existente para o banco de dados")

        # Adicionar layout de botões ao layout principal
        self.layout.addLayout(button_layout)

        # Configurar o modelo SQL para visualização
        self.configurarSqlModelSignal.emit()

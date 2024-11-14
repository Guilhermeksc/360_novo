from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.modules.utils.add_button import add_button
from src.modules.atas_novo.widgets.importar_tr import TermoReferenciaWidget
from src.modules.atas_novo.widgets.progresso_homolog import ProcessamentoWidget
from src.modules.atas_novo.widgets.atas import GerarAtaWidget
from pathlib import Path
from src.config.paths import PDF_DIR
from src.modules.atas_novo.database_manager.db_manager import DatabaseATASManager

class GerarAtasView(QMainWindow):
    instrucoesSignal = pyqtSignal()
    trSignal = pyqtSignal()
    homologSignal = pyqtSignal() 
    apiSignal = pyqtSignal()
    atasSignal = pyqtSignal()
    indicadoresSignal = pyqtSignal()
    pdf_dir_changed = pyqtSignal(Path) 

    def __init__(self, icons, model, database_path, parent=None):
        super().__init__(parent)
        self.icons = icons
        self.model = model
        self.database_ata_manager = DatabaseATASManager(database_path)
        self.pdf_dir = PDF_DIR
        self.setup_ui()

        self.pdf_dir_changed.connect(self.on_pdf_dir_changed)

    def setup_ui(self):
        # Configuração inicial do layout principal
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        
        # Título da interface
        label_dispensa = QLabel("Atas de Registro de Preços", self)
        label_dispensa.setStyleSheet("font-size: 20px; font-weight: bold; color: #4E648B")
        self.main_layout.addWidget(label_dispensa)
        
        # Adiciona menu e conteúdo
        menu_widget = self.create_menu_layout()
        
        # Área de conteúdo com QStackedWidget
        self.content_area = QStackedWidget()
        self.main_layout.addWidget(menu_widget)
        self.main_layout.addWidget(self.content_area)
        
        # Inicializa os widgets de conteúdo para cada seção
        self.init_content_widgets()

    def init_content_widgets(self):
        # Criação dos widgets de conteúdo e adição ao QStackedWidget
        self.instrucoes_widget = QLabel("Conteúdo das Instruções")
        self.content_area.addWidget(self.instrucoes_widget)

        self.tr_widget = TermoReferenciaWidget(self, self.icons)
        self.content_area.addWidget(self.tr_widget)

        self.homolog_widget = ProcessamentoWidget(
            pdf_dir=self.pdf_dir,
            icons=self.icons,
            model=self.model,
            database_ata_manager=self.database_ata_manager,  # Passa a instância do DatabaseATASManager
            main_window=self
        )
        self.content_area.addWidget(self.homolog_widget)

        self.api_widget = QLabel("Conteúdo de Consulta API")
        self.content_area.addWidget(self.api_widget)

        self.atas_widget = GerarAtaWidget(
            icons=self.icons, 
            database_ata_manager=self.database_ata_manager, 
            main_window=self)
        self.content_area.addWidget(self.atas_widget)

        self.indicadores_widget = QLabel("Conteúdo dos Indicadores")
        self.content_area.addWidget(self.indicadores_widget)

    def create_menu_layout(self):
        menu_widget = QWidget()
        menu_layout = QHBoxLayout(menu_widget)

        # Garante que um layout válido seja adicionado
        button_layout = self.create_button_layout()
        if button_layout is not None:
            menu_layout.addLayout(button_layout)

        return menu_widget

    def create_button_layout(self):
        button_layout = QHBoxLayout()

        # Cria cada botão individualmente chamando a função `add_button`
        add_button("Instruções", "arquivo", self.instrucoesSignal, button_layout, self.icons, "Clique para ver instruções")
        add_button("Termo de Referência", "stats", self.trSignal, button_layout, self.icons, "Acessar Termo de Referência")
        add_button("Termo de Homologação", "page", self.homologSignal, button_layout, self.icons, "Acessar Termo de Homologação")
        add_button("Consultar API", "api", self.apiSignal, button_layout, self.icons, "Consultar informações da API")
        add_button("Gerar Ata", "template", self.atasSignal, button_layout, self.icons, "Gerar nova ata")
        add_button("Indicadores", "performance", self.indicadoresSignal, button_layout, self.icons, "Visualizar indicadores")

        # Adiciona um espaçamento no final para ajustar o layout
        button_layout.addStretch()
        return button_layout

    def configurar_visualizacao_tabela_tr(self, table_view):
        # Verifica se o modelo foi configurado antes de prosseguir
        if table_view.model() is None:
            print("O modelo de dados não foi configurado para table_view.")
            return  # Sai da função se o modelo não estiver configurado

        # Define colunas visíveis
        visible_columns = [1, 2, 3, 4]
        for col in range(table_view.model().columnCount()):
            if col not in visible_columns:
                table_view.hideColumn(col)
            else:
                header = table_view.model().headerData(col, Qt.Orientation.Horizontal)
                table_view.model().setHeaderData(col, Qt.Orientation.Horizontal, header)

        # Configuração de redimensionamento das colunas
        table_view.setColumnWidth(0, 50)
        table_view.setColumnWidth(1, 100)
        table_view.setColumnWidth(2, 150)
        table_view.horizontalHeader().setStretchLastSection(True)
        table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table_view.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

    def on_pdf_dir_changed(self, new_pdf_dir):
        # Lida com a mudança do diretório PDF, se necessário
        print(f"Novo diretório PDF definido: {new_pdf_dir}")
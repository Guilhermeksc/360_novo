from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.config.data.contratos.contratos_data import GerenciarInclusaoExclusaoContratos
from pathlib import Path
from src.config.paths import DATA_CONTRATOS_PATH

class ConfigManager(QWidget):
    def __init__(self, icons, parent=None):
        super().__init__(parent)
        self.icons = icons
        self.setup_ui()
        self.database_path = Path(DATA_CONTRATOS_PATH)

    def setup_ui(self):
        """Configura o layout de configuração com um menu lateral."""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Cria o menu lateral com as opções de configuração
        menu_layout = QVBoxLayout()
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(0)

        # Define estilo padrão, hover e selecionado para os botões
        button_style = """
            QPushButton {
                border: none;
                color: white;
                font-size: 16px; 
                text-align: center;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #3A3B47; 
            }
            QPushButton:checked {
                background-color: #202124; 
                font-weight: bold;
            }
        """

        # Cria os botões para o menu lateral com texto e ações correspondentes
        buttons = [
            ("Agentes Responsáveis", self.show_agentes_responsaveis_dialog),
            ("Organizações Militares", self.show_organizacoes_dialog),
            ("Setores Requisitantes", self.show_setores_requisitantes_dialog),
            ("Modelos de Documentos", self.show_templates_dialog),
            ("Database", self.show_gerenciar_inclusao_exclusao_contratos_dialog),
        ]
        
        # Armazena os botões para gerenciar o estado selecionado
        self.config_menu_buttons = []

        for text, callback in buttons:
            button = QPushButton(text)
            button.setCheckable(True)
            button.setStyleSheet(button_style)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(callback)
            button.clicked.connect(lambda _, b=button: self.set_selected_button(b))
            menu_layout.addWidget(button)
            self.config_menu_buttons.append(button)

        # Adiciona um espaçador ao final para empurrar os botões para baixo
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        menu_layout.addItem(spacer)

        # Cria um widget para o menu lateral e aplica o layout
        menu_widget = QWidget()
        menu_widget.setLayout(menu_layout)
        menu_widget.setStyleSheet("background-color: #181928;")  # Cor de fundo do menu lateral

        # Adiciona o menu lateral ao layout principal
        main_layout.addWidget(menu_widget, stretch=1)
        
        # Área de conteúdo onde as configurações serão exibidas
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #13141F;")  # Cor de fundo da área de conteúdo
        main_layout.addWidget(self.content_widget, stretch=3)

    def set_selected_button(self, selected_button):
        """Define o botão selecionado no menu lateral."""
        # Desmarca todos os botões
        for button in self.config_menu_buttons:
            button.setChecked(False)
        
        # Marca o botão atualmente selecionado
        selected_button.setChecked(True)

    # Métodos de exibição das configurações individuais
    def show_agentes_responsaveis_dialog(self):
        # Código para exibir a janela de Agentes Responsáveis
        pass

    def show_organizacoes_dialog(self):
        # Código para exibir a janela de Organizações Militares
        pass

    def show_setores_requisitantes_dialog(self):
        # Código para exibir a janela de Setores Requisitantes
        pass

    def show_templates_dialog(self):
        # Código para exibir a janela de Modelos de Documentos
        pass

    def show_gerenciar_inclusao_exclusao_contratos_dialog(self):
        """Abre o diálogo de Gerenciar Inclusão e Exclusão de Contratos."""
        synchronize_icon = self.icons.get("synchronize")  # Carrega o ícone específico
        if not synchronize_icon:
            QMessageBox.critical(self, "Erro", "Ícone 'synchronize' não encontrado.")
            return
        dialog = GerenciarInclusaoExclusaoContratos(synchronize_icon, self.database_path, self)
        dialog.exec()
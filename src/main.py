from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.config.paths import DATA_CONTRATOS_PATH, ICONS_DIR, IMAGES_DIR, DATA_DISPENSA_ELETRONICA_PATH, DATA_LICITACAO_PATH, DATA_ATAS_PATH
from src.config.styles.styless import get_menu_button_style, get_menu_button_activated_style
from src.config.config_widget import ConfigManager
from src.modules.widgets import *
from src.config.dialogs import * 

# class MainWindow(QMainWindow):
#     def __init__(self, application):
#         super().__init__()
#         self.app = application
#         self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # Remove a barra de título nativa
#         self.setFixedSize(800, 600)  # Define o tamanho fixo da janela
#         self.init_ui()

#     def init_ui(self):
#         # Cria a barra de título personalizada
#         self.title_bar = QWidget(self)
#         self.title_bar.setFixedHeight(40)
#         self.title_bar.setStyleSheet("background-color: black;")

#         # Botão de fechar
#         self.close_button = QPushButton("X", self.title_bar)
#         self.close_button.setStyleSheet("""
#             QPushButton {
#                 background-color: red;
#                 color: white;
#                 border: none;
#                 font-weight: bold;
#             }
#             QPushButton:hover {
#                 background-color: darkred;
#             }
#         """)
#         self.close_button.setFixedSize(40, 40)
#         self.close_button.move(self.width() - 40, 0)
#         self.close_button.clicked.connect(self.close)

#         # Rótulo para o título
#         self.title_label = QLabel("Licitação 360", self.title_bar)
#         self.title_label.setStyleSheet("color: white; font-size: 16px;")
#         self.title_label.move(10, 10)

#         # Layout principal
#         self.central_widget = QWidget(self)
#         self.setCentralWidget(self.central_widget)
#         layout = QVBoxLayout(self.central_widget)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.addWidget(self.title_bar)
#         layout.addStretch()

#     def mousePressEvent(self, event):
#         if event.button() == Qt.MouseButton.LeftButton and self.title_bar.underMouse():
#             self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
#             event.accept()

#     def mouseMoveEvent(self, event):
#         if event.buttons() == Qt.MouseButton.LeftButton and self.title_bar.underMouse():
#             self.move(event.globalPosition().toPoint() - self.drag_position)
#             event.accept()
class MainWindow(QMainWindow):
    def __init__(self, application):
        super().__init__()
        self.app = application
        self.icons = load_icons()
        self.buttons = {}
        self.active_button = None
        self.setup_ui()
        self.open_initial_page()

    # ====== SETUP DA INTERFACE ======

    def setup_ui(self):
        """Configura a interface principal da aplicação."""
        self.configure_window()
        self.setup_central_widget()
        self.setup_menu()
        self.setup_content_area()

    def configure_window(self):
        """Configurações básicas da janela principal."""
        self.setWindowTitle("Licitação 360")
        self.setWindowIcon(self.icons["brasil"])
        
        # Posiciona a janela no canto superior esquerdo
        screen_geometry = self.screen().geometry()
        self.move(screen_geometry.left(), screen_geometry.top())

    # ====== CENTRAL WIDGET E MENU ======

    def setup_central_widget(self):
        """Define o widget central e layout principal."""
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_layout = QHBoxLayout(self.central_widget)
        self.central_layout.setSpacing(0)
        self.central_layout.setContentsMargins(0, 0, 0, 0)

    def setup_menu(self):
        """Configura o menu lateral com botões de ícone que mudam de cor ao hover e adiciona tooltips personalizados."""
        self.menu_layout = QVBoxLayout()
        self.menu_layout.setSpacing(0)
        self.menu_layout.setContentsMargins(0, 0, 0, 0)
        self.menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Tooltip personalizado
        self.tooltip_label = QLabel("", self)
        self.tooltip_label.setStyleSheet("""
            background-color: #13141F;
            color: white;
            border: 1px solid #8AB4F7;
            padding: 4px;
            border-radius: 4px;
        """)
        self.tooltip_label.setFont(QFont("Arial", 12))
        self.tooltip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tooltip_label.setVisible(False)  # Inicialmente oculto

        # Definindo os botões do menu e seus contextos
        self.menu_buttons = [
            ("init", "init_hover", "Início", self.show_inicio),
            ("dispensa", "dispensa_hover", "Dispensa Eletrônica", self.show_dispensa),
            ("ata", "ata_hover", "Atas", self.show_atas),
            ("contract", "contract_hover", "Contratos", self.show_contratos),
            ("plan", "plan_hover", "Planejamento", self.show_planejamento),
            ("dash", "dash_hover", "Dashboard", self.show_dashboard),
            ("config", "config_hover", "Configurações", self.show_config),
        ]

        # Criando os botões e adicionando-os ao layout do menu
        for icon_key, hover_icon_key, tooltip_text, callback in self.menu_buttons:
            button = self.create_icon_button(icon_key, hover_icon_key)
            button.clicked.connect(callback)
            button.installEventFilter(self)  # Instala um filtro de evento para gerenciar o tooltip
            button.setProperty("tooltipText", tooltip_text)  # Define o texto do tooltip como propriedade
            self.menu_layout.addWidget(button)
            self.buttons[icon_key] = button  # Armazena o botão para referência futura
    
        # Cria um widget para o menu e adiciona o layout
        self.menu_widget = QWidget()
        self.menu_widget.setLayout(self.menu_layout)
        self.menu_widget.setStyleSheet("background-color: #13141F;")
        self.central_layout.addWidget(self.menu_widget)

    def show_tooltip_with_arrow(self, text, button):
        self.tooltip_label.setText(text)
        self.tooltip_label.move(button.x() + button.width(), button.y())
        self.tooltip_label.setVisible(True)

        # Posiciona a seta
        self.tooltip_arrow.move(self.tooltip_label.x() - 10, self.tooltip_label.y() + (self.tooltip_label.height() // 2) - 10)
        self.tooltip_arrow.setVisible(True)

    # Oculta ambos quando o tooltip desaparece
    def hide_tooltip(self):
        self.tooltip_label.setVisible(False)
        self.tooltip_arrow.setVisible(False)
        
    def eventFilter(self, obj, event):
        """Filtra eventos para exibir tooltips personalizados alinhados à direita dos botões do menu."""
        if event.type() == QEvent.Type.Enter and obj in self.buttons.values():
            tooltip_text = obj.property("tooltipText")
            if tooltip_text:
                self.tooltip_label.setText(tooltip_text)
                self.tooltip_label.adjustSize()

                # Posição do tooltip alinhada à direita do botão, considerando a posição global da janela
                button_pos = obj.mapToGlobal(QPoint(obj.width(), 0))
                window_pos = self.mapFromGlobal(button_pos)  # Converte para coordenadas relativas à janela principal
                tooltip_x = window_pos.x() + 5  # Ajuste para a direita do botão
                tooltip_y = window_pos.y() + (obj.height() - self.tooltip_label.height()) // 2  # Centraliza verticalmente
                self.tooltip_label.move(tooltip_x, tooltip_y)
                self.tooltip_label.setVisible(True)
        elif event.type() == QEvent.Type.Leave and obj in self.buttons.values():
            self.tooltip_label.setVisible(False)

        return super().eventFilter(obj, event)
    def create_icon_button(self, icon_key, hover_icon_key):
        button = QPushButton()
        button.setIcon(self.icons[icon_key])  # Ícone padrão
        button.setIconSize(QSize(40, 40))
        button.setStyleSheet(get_menu_button_style())
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedSize(50, 50)

        # Armazena o ícone padrão e o ícone de hover
        button.default_icon = self.icons[icon_key]
        button.hover_icon = self.icons[hover_icon_key]
        button.icon_key = icon_key  # Armazena a chave do ícone

        # Instala o event filter para capturar eventos de hover
        button.installEventFilter(self)

        return button

    def set_active_button(self, button):
        """Define o botão ativo e altera o ícone para o estado hover permanente."""
        # Reseta o estilo do botão anteriormente ativo
        if self.active_button and self.active_button != button:
            self.active_button.setIcon(self.active_button.default_icon)
            self.active_button.setStyleSheet(get_menu_button_style())

        # Aplica o estilo de botão ativo
        button.setIcon(button.hover_icon)
        button.setStyleSheet(get_menu_button_activated_style())
        self.active_button = button 

    # ====== EVENTOS DE MENU ======

    def show_inicio(self):
        self.clear_content_area(keep_image_label=True)
        self.content_layout.addWidget(self.inicio_widget)
        # Define o botão "init" como o ativo (correspondente ao botão inicial)
        self.set_active_button(self.buttons["init"])

    def show_dispensa(self):
        self.clear_content_area()
        
        # Instancia o modelo de Dispensa Eletrônica com o caminho do banco de dados
        self.dispensa_eletronica_model = DispensaEletronicaModel(DATA_DISPENSA_ELETRONICA_PATH)
        
        # Configura o modelo SQL
        sql_model = self.dispensa_eletronica_model.setup_model("controle_dispensas", editable=True)
        
        # Cria o widget de Dispensa Eletrônica e passa o modelo SQL e o caminho do banco de dados
        self.dispensa_eletronica_widget = DispensaEletronicaWidget(self.icons, sql_model, self.dispensa_eletronica_model.database_manager.db_path)

        # Cria o controlador e passa o widget e o modelo
        self.controller = DispensaEletronicaController(self.icons, self.dispensa_eletronica_widget, self.dispensa_eletronica_model)

        # Adiciona o widget de Dispensa Eletrônica na área de conteúdo
        self.content_layout.addWidget(self.dispensa_eletronica_widget)
        self.set_active_button(self.buttons["dispensa"])

    def show_atas(self):
        self.clear_content_area()
        
        # Instancia o modelo de Dispensa Eletrônica com o caminho do banco de dados
        self.gerar_atas_model = GerarAtasModel(DATA_ATAS_PATH)
        
        # Configura o modelo SQL
        sql_model = self.gerar_atas_model.setup_model("controle_atas", editable=True)
        
        # Cria o widget de Dispensa Eletrônica e passa o modelo SQL e o caminho do banco de dados
        self.gerar_atas_widget = GerarAtasView(self.icons, sql_model, self.gerar_atas_model.database_ata_manager.db_path)

        # Cria o controlador e passa o widget e o modelo
        self.gerar_atas_controller = GerarAtasController(self.icons, self.gerar_atas_widget, self.gerar_atas_model)

        # Adiciona o widget de Dispensa Eletrônica na área de conteúdo
        self.content_layout.addWidget(self.gerar_atas_widget)
        self.set_active_button(self.buttons["ata"])

    def show_contratos(self):
        self.clear_content_area()
        
        # Instancia o modelo de Dispensa Eletrônica com o caminho do banco de dados
        self.contratos_model = ContratosModel(DATA_CONTRATOS_PATH)
        
        # Configura o modelo SQL
        sql_model = self.contratos_model.setup_model("controle_licitacao", editable=True)
        
        # Cria o widget de Dispensa Eletrônica e passa o modelo SQL e o caminho do banco de dados
        self.contratos_widget = ContratosView(self.icons, sql_model, self.contratos_model.database_contratos_manager.db_path)

        # Cria o controlador e passa o widget e o modelo
        self.contratos_controller = ContratosController(self.icons, self.contratos_widget, self.contratos_model)

        # Adiciona o widget de Dispensa Eletrônica na área de conteúdo
        self.content_layout.addWidget(self.contratos_widget)
        self.set_active_button(self.buttons["contract"])

    def show_planejamento(self):
        self.clear_content_area()
        
        # Instancia o modelo de Dispensa Eletrônica com o caminho do banco de dados
        self.licitacao_model = LicitacaoModel(DATA_LICITACAO_PATH)
        
        # Configura o modelo SQL
        sql_model = self.licitacao_model.setup_model("controle_licitacao", editable=True)
        
        # Cria o widget de Dispensa Eletrônica e passa o modelo SQL e o caminho do banco de dados
        self.licitacao_widget = LicitacaoWidget(self.icons, sql_model, self.licitacao_model.database_licitacao_manager.db_path)

        # Cria o controlador e passa o widget e o modelo
        self.licitacao_controller = LicitacaoController(self.icons, self.licitacao_widget, self.licitacao_model)

        # Adiciona o widget de Dispensa Eletrônica na área de conteúdo
        self.content_layout.addWidget(self.licitacao_widget)
        self.set_active_button(self.buttons["plan"])

    def show_dashboard(self):
        # Limpa a área de conteúdo antes de adicionar novos widgets
        self.clear_content_area()

        # Instancia o widget de dashboard e adiciona à área de conteúdo
        dashboard_widget = DashboardWidget(self.icons)
        self.content_layout.addWidget(dashboard_widget)

        # Define o botão do dashboard como ativo
        self.set_active_button(self.buttons["dash"])

    def show_config(self):
        """Exibe a área de configurações usando o ConfigManager."""
        self.clear_content_area()
        self.config_widget = ConfigManager(self.icons, self)
        self.content_layout.addWidget(self.config_widget)
        self.set_active_button(self.buttons["config"])


    def set_selected_button(self, selected_button):
        """Define o botão selecionado no menu lateral."""
        # Desmarca todos os botões
        for button in self.config_menu_buttons:
            button.setChecked(False)
        
        # Marca o botão atualmente selecionado
        selected_button.setChecked(True)

    def open_initial_page(self):
        """Abre a página inicial da aplicação."""
        self.clear_content_area(keep_image_label=True)
        self.content_layout.addWidget(self.inicio_widget)
        # Define o botão "init" como o ativo (correspondente ao botão inicial)
        self.set_active_button(self.buttons["init"])

        
    # ====== CONFIGURAÇÕES ======

    def create_config_button(self):
        config_layout = QHBoxLayout()
        self.config_button = QPushButton()  # Define como atributo da classe
        self.config_button.setIcon(self.icons["setting_1"])
        self.config_button.setIconSize(QSize(40, 40))
        self.config_button.setStyleSheet("border: none;")
        self.config_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.config_button.setFixedSize(40, 40)
        
        # Instala o event filter para capturar o efeito de hover
        self.config_button.installEventFilter(self)
        self.config_button.clicked.connect(lambda: self.show_settings_menu(self.config_button))
        
        config_layout.addWidget(self.config_button)
        config_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return config_layout

    def show_settings_menu(self, button):
        menu = self.create_settings_menu()
        menu.setStyleSheet("""
            QMenu { background-color: #181928; }
            QMenu::item { background-color: transparent; padding: 8px 20px; color: white; border-radius: 5px; }
            QMenu::item:selected { background-color: #5A5B6A; }
        """)
        pos = button.mapToGlobal(QPoint(button.width(), 0))
        menu.exec(pos - QPoint(0, menu.sizeHint().height() - button.height()))

    def create_settings_menu(self):
        menu = QMenu()
        settings_options = {
            "Configurar Banco de Dados": self.show_configurar_database_dialog,
            "Agentes Responsáveis": self.show_agentes_responsaveis_dialog,
            "Templates": self.show_templates_dialog,
            "Organizações": self.show_organizacoes_dialog
        }
        for title, handler in settings_options.items():
            action = QAction(title, self)
            action.triggered.connect(handler)
            menu.addAction(action)
        return menu
    
    # ====== ÁREA DE CONTEÚDO ======

    def setup_content_area(self):
        """Configura a área principal para exibição do conteúdo."""
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(0)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_image_label = QLabel(self.central_widget)
        self.content_image_label.hide()
        self.content_layout.addWidget(self.content_image_label)

        self.content_widget = QWidget()
        self.content_widget.setLayout(self.content_layout)
        self.content_widget.setMinimumSize(1050, 700)
        self.central_layout.addWidget(self.content_widget)
        
        self.inicio_widget = InicioWidget(self.icons, self)

    def clear_content_area(self, keep_image_label=False):
        """Remove todos os widgets da área de conteúdo, exceto a imagem opcional."""
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget and (widget is not self.content_image_label or not keep_image_label):
                widget.setParent(None)

    # ====== AÇÕES DOS DIÁLOGOS ======

    def show_configurar_database_dialog(self):
        ConfigurarDatabaseDialog(self).exec()

    def show_organizacoes_dialog(self):
        OrganizacoesDialog(self).exec()

    def show_templates_dialog(self):
        TemplatesDialog(self).exec()

    def show_setores_requisitantes_dialog(self):
        pass
        # SetoresRequisitantesDialog(self).exec()
        
    # ====== AÇÕES DO MENU ======

    def setup_content_widget(self, widget_class, *args):
        """Auxiliar para limpar a área de conteúdo e adicionar um novo widget."""
        self.clear_content_area()
        widget_instance = widget_class(*args)
        self.content_layout.addWidget(widget_instance)
        return widget_instance

    # ====== EVENTO DE FECHAMENTO DA JANELA ======

    def closeEvent(self, event):
        """Solicita confirmação ao usuário antes de fechar a janela."""
        reply = QMessageBox.question(
            self, 'Confirmar Saída', "Você realmente deseja fechar o aplicativo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        event.accept() if reply == QMessageBox.StandardButton.Yes else event.ignore()


    # def setup_planejamento(self):
    #     self.application_ui = self.setup_content_widget(PlanejamentoWidget, self, str(ICONS_DIR))

    # def setup_pca(self):
    #     self.pca_widget = self.setup_content_widget(PCAWidget, self)

    # def setup_pncp(self):
    #     self.clear_content_area()
    #     self.pca_widget = PNCPWidget(self)
    #     self.content_layout.addWidget(self.pca_widget)

    # def setup_atas(self):
    #     self.clear_content_area()
    #     self.atas_widget = AtasWidget(str(ICONS_DIR), self)
    #     self.content_layout.addWidget(self.atas_widget)
    #     print("Contratos widget added to layout")

    # def setup_contratos(self):
    #     print("Setting up contratos...")
    #     self.clear_content_area()
    #     self.atas_contratos_widget = ContratosWidget(str(ICONS_DIR), self)
    #     self.content_layout.addWidget(self.atas_contratos_widget)
    #     print("Contratos widget added to layout")
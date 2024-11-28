from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.modules.utils.brl import formatar_para_brl, CustomQLineEdit
from src.modules.utils.add_button import add_button, add_button_func
from src.modules.dispensa_eletronica.dialogs.edit_data.apoio_data import COLUNAS_LEGIVEIS, COLUNAS_LEGIVEIS_INVERSO, CORRECAO_VALORES, STYLE_GROUP_BOX
from src.modules.contratos.widgets.msg import MensagensManagerContratos
from src.modules.contratos.widgets.historico import HistoricoManagerContratos
from src.modules.contratos.widgets.empenho import EmpenhoManagerContratos
from src.modules.contratos.widgets.itens import ItensManagerContratos
from src.modules.contratos.widgets.comentarios import ComentariosManagerContratos
from src.modules.contratos.widgets.contratos import DownloadManagerContratos
from src.modules.utils.linha_layout import linha_divisoria_layout, linha_divisoria_sem_spacer_layout
from src.config.paths import CONTROLE_DADOS, CONTRATOS_JSON, verificar_criar_json

class EditarDadosContratos(QMainWindow):
    save_data_signal = pyqtSignal(dict)  # Sinal para salvar dados
    window_closed = pyqtSignal()  # Sinal para notificar fechamento

    def __init__(self, dados, icons, parent=None):
        super().__init__(parent)
        self.dados = dados
        self.icons = icons

        # Configurações gerais da janela
        self.setWindowTitle("Edição de Dados")
        self.setWindowIcon(self.icons.get("edit", None))
        self.setFixedSize(1150, 600)
        self.move(0, 0)  # Posicionar no canto superior esquerdo da tela

        # Configuração adicional
        self.carregar_referencias()
        verificar_criar_json(CONTRATOS_JSON)
        # Inicializa o gerenciador de mensagens
        self.mensagens_manager = MensagensManagerContratos(self.icons, self.dados)
        self.comentarios_manager = ComentariosManagerContratos(self.icons, self.dados)
        self.historico_manager = HistoricoManagerContratos(self.icons, self.dados)
        self.empenho_manager = EmpenhoManagerContratos(self.icons, self.dados)
        self.itens_manager = ItensManagerContratos(self.icons, self.dados)
        self.contrato_manager = DownloadManagerContratos(self.icons, self.dados)

        self.setup_ui()

    def closeEvent(self, event):
        """
        Sobrescreve o evento de fechamento para emitir o sinal customizado.
        """
        super().closeEvent(event)
        self.window_closed.emit()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def setup_ui(self):
        # Configura o widget principal e define o fundo preto e borda
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        # Configuração do layout principal com margens e espaçamento zero
        self.central_layout = QHBoxLayout(main_widget)

        # Layout esquerdo
        Left_layout = QVBoxLayout()
        layout_titulo = self.setup_layout_titulo()
        Left_layout.addLayout(layout_titulo)
        nav_frame = self.create_navigation_layout()
        Left_layout.addWidget(nav_frame)
        Left_layout.addWidget(self.stacked_widget)
        self.central_layout.addLayout(Left_layout)

        # Configuração dos widgets no QStackedWidget
        self.setup_stacked_widgets()

    def setup_layout_titulo(self):
        """Configura o layout do título com o ID do processo e a seção de consulta API."""
        layout_titulo = QHBoxLayout()

        spacer_left = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout_titulo.addSpacerItem(spacer_left)

        # Cria um layout vertical para o título e um layout horizontal para ícones e texto
        vlayout_titulo = QVBoxLayout()

        # Layout horizontal para ícone esquerdo, título e ícone direito
        hlayout_titulo = QHBoxLayout()

        hlayout_titulo.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        # Ícone à esquerda
        brasil_icon = QIcon(self.icons.get("brasil_2", None))
        image_label_esquerda = QLabel()
        image_label_esquerda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label_esquerda.setPixmap(brasil_icon.pixmap(30, 30))
        hlayout_titulo.addWidget(image_label_esquerda)

        # Texto do título centralizado
        tipo = self.dados.get("tipo", "N/A")
        numero = self.dados.get("contrato_numero", "N/A")
        title_label = QLabel(f"{tipo} nº {numero}", self)

        # Define o tamanho da fonte para 18 e em negrito
        font_title = QFont()
        font_title.setPointSize(18)
        font_title.setBold(True)
        title_label.setFont(font_title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hlayout_titulo.addWidget(title_label)

        # Ícone à direita
        acanto_icon = QIcon(self.icons.get("acanto", None))
        image_label_direita = QLabel()
        image_label_direita.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label_direita.setPixmap(acanto_icon.pixmap(40, 40))
        hlayout_titulo.addWidget(image_label_direita)

        # Adiciona outro espaçador para empurrar o ícone da direita
        hlayout_titulo.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Adiciona o layout horizontal ao layout vertical do título
        vlayout_titulo.addLayout(hlayout_titulo)

        # Criação do om_label com fonte 14
        sigla_om = self.dados.get("sigla_om", "N/A")
        orgao_responsavel = self.dados.get("nome_om", "N/A")
        self.uasg = self.dados.get("codigo_uasg", "N/A")
        self.om_label = QLabel(f"{sigla_om} - {orgao_responsavel} ({ self.uasg})", self)

        font_objeto = QFont()
        font_objeto.setPointSize(12)
        self.om_label.setFont(font_objeto)
        self.om_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Adiciona objeto_label ao layout de labels abaixo de title_label
        vlayout_titulo.addWidget(self.om_label)

                # Cria a linha divisória com espaçamento e adiciona ao layout
        linha_divisoria, spacer_baixo_linha = linha_divisoria_layout()
        vlayout_titulo.addWidget(linha_divisoria)
        vlayout_titulo.addSpacerItem(spacer_baixo_linha)

        # Adiciona o layout vertical com título e situação ao layout principal
        layout_titulo.addLayout(vlayout_titulo)

        # Espaçador para empurrar o título e o botão "Salvar" para a direita
        spacer_right = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout_titulo.addSpacerItem(spacer_right)

        # Botão "Salvar" à direita
        add_button_func("Salvar", "confirm", self.save_data, layout_titulo, self.icons, tooltip="Salvar os Dados")

        return layout_titulo

    def create_navigation_layout(self):
        # Criação do frame que conterá o nav_layout e aplicará a borda inferior
        nav_frame = QFrame()
        nav_frame.setStyleSheet("QFrame {border-bottom: 1px solid #2C2F3F;}")

        # Layout horizontal para os botões de navegação
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setSpacing(0)
        nav_layout.setContentsMargins(0, 0, 0, 0)

        buttons = [
            ("Informações", "Informações"),
            ("Mensagens", "Mensagens"),
            ("Histórico", "Histórico"),
            ("Empenhos", "Empenhos"),
            ("Itens", "Itens"),
            ("Contrato", "Contrato"),
        ]
        
        nav_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        for index, (text, name) in enumerate(buttons):
            button = QPushButton(text, self)
            button.setObjectName(name)
            button.setProperty("class", "nav-button")
            button.clicked.connect(lambda _, n=name, b=button: self.on_navigation_button_clicked(n, b))
            
            button.setCursor(Qt.CursorShape.PointingHandCursor)

            nav_layout.addWidget(button)

            # Define o botão "Informações" como selecionado
            if name == "Informações":
                button.setProperty("class", "nav-button selected")
                button.setStyleSheet("")  # Aplica o estilo imediatamente
                self.selected_button = button  # Mantém o botão "Informações" como o selecionado inicial

        nav_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Define o estilo para os botões dentro do nav_layout
        self.setStyleSheet("""
            QPushButton[class="nav-button"] {
                background-color: #181928;
                color: #8AB4F7;
                border: none;
                font-size: 14px;
                padding: 8px 15px;
                border-top: 10px solid #181928;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px; 
            }
            QPushButton[class="nav-button"]:hover {
                background-color: #3A3E5B; 
                color: #FFFFFF;
                border-left: 2px solid #3A3E5B; 
                border-right: 2px solid #3A3E5B; 
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;                           
                border-top: 2px solid #3A3E5B;
                padding: 2px 4px; 
            }
            QPushButton[class="nav-button selected"] {
                background-color: #181928;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
                border-left: 2px solid #2C2F3F; 
                border-right: 2px solid #2C2F3F; 
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;                           
                border-top: 2px solid #2C2F3F;
                border-bottom: 5px solid #181928;
            }
        """)

        return nav_frame

    def on_navigation_button_clicked(self, name, button):
        if self.selected_button:
            self.selected_button.setProperty("class", "nav-button")
            self.selected_button.setStyleSheet("")

        button.setProperty("class", "nav-button selected")
        button.setStyleSheet("")

        self.selected_button = button
        self.show_widget(name)

    def show_widget(self, name):
        widget = self.widgets_map.get(name)
        if widget:
            self.stacked_widget.setCurrentWidget(widget)
    
    def setup_stacked_widgets(self):       
        # Cria widgets para cada seção
        self.widgets_map = {
            "Informações": self.stacked_widget_info(self.dados),
            "Mensagens": self.stacked_widget_mensagens(self.dados),
            "Histórico": self.stacked_widget_historico(self.dados),
            "Empenhos": self.stacked_widget_empenho(self.dados),
            "Itens": self.stacked_widget_itens(self.dados),
            "Contrato": self.stacked_widget_contrato(self.dados),
        }

        # Adiciona cada widget ao QStackedWidget
        for name, widget in self.widgets_map.items():
            self.stacked_widget.addWidget(widget)

    def stacked_widget_info(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        hbox_top_layout = QHBoxLayout()

        info_contratacao_layout = QVBoxLayout()
        self.contratacao_layout = self.create_contratacao_group()
        info_contratacao_layout.addWidget(self.contratacao_layout)

        hbox_top_layout.addLayout(info_contratacao_layout)

        layout.addLayout(hbox_top_layout)
        frame.setLayout(layout)

        return frame

    def create_comentarios_layout(self):
        """
        Cria o layout de comentários utilizando ComentariosManagerContratos.
        """
        return self.comentarios_manager.get_comentarios_layout()

    def create_contratacao_group(self):
        contratacao_group_box = QGroupBox("Informações da Contratação")
        contratacao_group_box.setStyleSheet(STYLE_GROUP_BOX)

        contratacao_layout = QVBoxLayout()

        spacer_item = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        contratacao_layout.addItem(spacer_item)

        # Campo de Objeto
        objeto_layout = QHBoxLayout()

        # NUP, Material e Serviço com seleção exclusiva
        nup_label = QLabel("NUP:")
        self.nup_edit = QLineEdit(self.dados.get('processo', ''))
        self.nup_edit.setFixedWidth(170)  # Define largura fixa
        objeto_layout.addWidget(nup_label)
        objeto_layout.addWidget(self.nup_edit)

        valor_total_label = QLabel("Valor da Contratação:")
        valor_inicial = self.dados.get('valor_global', 0.0)  # Obtém o valor inicial
        self.valor_total_edit = CustomQLineEdit(valor_inicial)
        self.valor_total_edit.setFixedWidth(130)  # Define largura fixa
        objeto_layout.addWidget(valor_total_label)
        objeto_layout.addWidget(self.valor_total_edit)

        contratacao_layout.addLayout(objeto_layout)    
        # Campo de Objeto
        objeto_completo_layout = QVBoxLayout()
        objeto_completo_label = QLabel("Objeto:")
        self.objeto_completo_edit = QTextEdit(self.dados.get('objeto', ''))
        self.objeto_completo_edit.setFixedHeight(100)  # Define altura fixa
        objeto_completo_layout.addWidget(objeto_completo_label)
        objeto_completo_layout.addWidget(self.objeto_completo_edit)
        contratacao_layout.addLayout(objeto_completo_layout)
        
        spacer_item = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        contratacao_layout.addItem(spacer_item)

        linha_divisoria, spacer_baixo_linha = linha_divisoria_layout()
        contratacao_layout.addWidget(linha_divisoria)
        contratacao_layout.addSpacerItem(spacer_baixo_linha)

        comentarios_layout = self.comentarios_manager.get_comentarios_layout()
        contratacao_layout.addLayout(comentarios_layout)

        # Configura layout do GroupBox
        contratacao_group_box.setLayout(contratacao_layout)

        return contratacao_group_box

    def copyToClipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QToolTip.showText(QCursor.pos(), "Texto copiado para a área de transferência.", msecShowTime=1500)

    def carregar_referencias(self):       
        # Referências aos RadioButtons para material_servico, com_disputa e pesquisa_preco
        self.radio_material = None
        self.radio_servico = None
        self.selected_button = None
        self.valor_total_edit = None
        # Inicialização do stacked_widget com estilo aplicado
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setStyleSheet("""
            QLabel { font-size: 16px; }
            QCheckBox { font-size: 16px; }
            QLineEdit { font-size: 14px; }
        """)
        # Label de status para mostrar atualizações de consolidação
        self.status_label = QLabel(self)

    def stacked_widget_mensagens(self, data):
        return self.mensagens_manager

    def stacked_widget_historico(self, data):
        return self.historico_manager

    def stacked_widget_empenho(self, data):
        return self.empenho_manager

    def stacked_widget_itens(self, data):
        return self.itens_manager

    def stacked_widget_contrato(self, data):
        return self.contrato_manager
        
    def atualizar_texto_padronizado(self):
        """Atualiza o campo de texto padronizado sempre que o texto editável for alterado."""
        texto_editado = self.edit_text_field.toPlainText()
        self.standard_text_field.setText(texto_editado)

    def save_data(self):
        # Coleta os dados dos widgets de contratação
        data_to_save = {
            'id_processo': self.dados.get('id_processo'),
            'tipo': self.dados.get('tipo'),
            'numero': self.dados.get('numero'),
            'ano': self.dados.get('ano'),
            'situacao': self.dados.get('situacao'),
            'sigla_om': self.dados.get('sigla_om'),
            'uasg': self.dados.get('uasg'),
            'orgao_responsavel': self.dados.get('orgao_responsavel'),
            'setor_responsavel': self.dados.get('setor_responsavel'),
            'objeto': self.objeto_edit.text(),
            'nup': self.nup_edit.text(),
            'material_servico': "Serviço" if self.radio_servico.isChecked() else "Material",
        }
        
        # Coleta os dados dos widgets de classificação orçamentária
        data_to_save.update({
            'valor_total': self.valor_total_edit.text(),
        })

        # Emissão do sinal para salvar os dados
        self.save_data_signal.emit(data_to_save)

        self.show_confirmation_message()

    def show_confirmation_message(self, message="Dados salvos com sucesso!"):
        """Exibe uma mensagem de confirmação temporária."""
        confirmation_label = QLabel(message, self)
        confirmation_label.setStyleSheet("""
            QLabel {
                background-color: #009B3A;
                color: white;
                font-size: 16px;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        confirmation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confirmation_label.setFixedSize(300, 50)
        confirmation_label.move(
            self.width() // 2 - confirmation_label.width() // 2,
            self.height() // 2 - confirmation_label.height() // 2
        )
        confirmation_label.show()

        # Fecha a mensagem automaticamente após 1 segundo
        QTimer.singleShot(700, confirmation_label.close)
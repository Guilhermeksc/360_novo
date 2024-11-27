from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.modules.utils.brl import formatar_para_brl, CustomQLineEdit
from src.modules.utils.add_button import add_button, add_button_func, create_button
from src.modules.dispensa_eletronica.dados_api.api_consulta import ConsultaAPIDialog
from src.modules.dispensa_eletronica.dialogs.edit_data.apoio_data import COLUNAS_LEGIVEIS, COLUNAS_LEGIVEIS_INVERSO, CORRECAO_VALORES, STYLE_GROUP_BOX
from src.modules.dispensa_eletronica.dialogs.edit_data.widgets.formulario import TableCreationWorker
from src.modules.planejamento.dialogs.checklist import ChecklistWidget
from src.modules.planejamento.dialogs.edit_data.widgets.msg import MensagensManager
from src.modules.planejamento.dialogs.edit_data.widgets.etapa import EtapasManager
from src.modules.utils.linha_layout import linha_divisoria_layout, linha_divisoria_sem_spacer_layout
from pathlib import Path
from src.config.paths import CONTROLE_DADOS, CONTRATOS_JSON
import json
import pandas as pd
import os
import subprocess
from datetime import datetime

def verificar_criar_json(arquivo_json):
    if not arquivo_json.exists():
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

class EditarDadosWindow(QMainWindow):
    save_data_signal = pyqtSignal(dict)  # Sinal para salvar dados
    window_closed = pyqtSignal()  # Sinal para notificar fechamento

    def __init__(self, dados, icons, parent=None):
        super().__init__(parent)
        self.dados = dados
        self.icons = icons

        # Configurações gerais da janela
        self.setWindowTitle("Edição de Dados")
        self.setWindowIcon(self.icons.get("edit", None))
        self.setFixedSize(1150, 780)
        self.move(0, 0)  # Posicionar no canto superior esquerdo da tela

        # Configuração adicional
        self.carregar_referencias()
        verificar_criar_json(CONTRATOS_JSON)
        # Inicializa o gerenciador de mensagens
        self.mensagens_manager = MensagensManager(self.icons, self.dados)

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
        numero = self.dados.get("numero", "N/A")
        ano = self.dados.get("ano", "N/A")
        title_label = QLabel(f"{tipo} nº {numero}/{ano}", self)

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
        orgao_responsavel = self.dados.get("orgao_responsavel", "N/A")
        self.uasg = self.dados.get("uasg", "N/A")
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
        comentarios_layout = QHBoxLayout()

        # Layout para adicionar novos comentários
        comentario_novo = QVBoxLayout()

        comentario_label_layout = QHBoxLayout()
        brasil_icon = QIcon(self.icons.get("comments", None))
        image_label_esquerda = QLabel()
        image_label_esquerda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label_esquerda.setPixmap(brasil_icon.pixmap(40, 40))
        comentario_label_layout.addWidget(image_label_esquerda)

        comentario_label = QLabel("Novo Comentário:")
        comentario_label_layout.addWidget(comentario_label)

        # Adiciona o combobox
        self.comentarios_padronizados_combo = QComboBox()
        self.comentarios_padronizados_combo.addItems([
            "Selecione um comentário padronizado",
            "Devolvido para correções",
            "Divulgação de IRP",
            "Atendimento de Nota Técnica",
            "Envio para CJACM",
            "Atendimento das Recomendações",
            "Data da Sessão Pública"
        ])
        # Ajusta o tamanho da fonte do combobox
        self.comentarios_padronizados_combo.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                color: #FFFFFF;
                background-color: #2C2F3F;
                border: 1px solid #434364;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.comentarios_padronizados_combo.currentIndexChanged.connect(self.atualizar_comentario_padronizado)
        comentario_label_layout.addWidget(self.comentarios_padronizados_combo)

        comentario_label_layout.addStretch()
        comentario_novo.addLayout(comentario_label_layout)

        self.comentario_edit = QTextEdit()
        comentario_novo.addWidget(self.comentario_edit)

        button_layout = QHBoxLayout()
        # Botão para adicionar comentário
        add_button_func(
            "Adicionar Comentário",
            "add_comment",
            self.adicionar_comentario,
            button_layout,
            self.icons,
            "Clique para adicionar um novo comentário."
        )

        # Botão para excluir comentário
        add_button_func(
            "Excluir Comentário",
            "delete_comment",
            self.excluir_comentario,
            button_layout,
            self.icons,
            "Clique para excluir o comentário selecionado."
        )
        comentario_novo.addLayout(button_layout)

        # Layout para listar comentários existentes
        comentarios_registrados = QVBoxLayout()
        self.lista_comentarios = QListWidget()
        self.lista_comentarios.setFixedWidth(630)
        self.lista_comentarios.setStyleSheet("""
            QListWidget {
                color: #FFFFFF;
                font-size: 14px;
                background-color: #2C2F3F;
                border: 1px solid #434364; /* Borda branca */
                border-radius: 10px; /* Bordas arredondadas */
                padding: 5px;
            }
        """)
        self.lista_comentarios.itemDoubleClicked.connect(self.editar_comentario)  # Conecta o duplo clique ao método
        self.carregar_comentarios()

        comentarios_registrados.addWidget(QLabel("Comentários Registrados:"))
        comentarios_registrados.addWidget(self.lista_comentarios)

        comentarios_layout.addLayout(comentario_novo)
        comentarios_layout.addLayout(comentarios_registrados)

        return comentarios_layout

    def atualizar_comentario_padronizado(self):
        """Atualiza o QTextEdit com o comentário padronizado selecionado."""
        # Obtém a data e hora atual
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        comentarios_texto = {
            "Devolvido para correções": f"O processo foi devolvido em {data_atual} para correções necessárias no documento.",
            "Divulgação de IRP": f"A IRP foi divulgada em {data_atual}.",
            "Atendimento de Nota Técnica": f"Nota Técnica atendida em {data_atual} conforme as recomendações solicitadas.",
            "Envio para CJACM": f"O processo foi enviado em {data_atual} para análise do CJACM.",
            "Atendimento das Recomendações": f"As recomendações foram atendidas em {data_atual}.",
            "Data da Sessão Pública": f"A sessão pública foi agendada para o dia {data_atual}."
        }

        texto = comentarios_texto.get(self.comentarios_padronizados_combo.currentText(), "")
        self.comentario_edit.setText(texto)

    def editar_comentario(self, item):
        """Permite editar o comentário selecionado e salva no JSON."""
        id_processo = self.dados.get("id_processo", "Desconhecido")
        if not id_processo:
            QMessageBox.warning(self, "Erro", "ID do processo não encontrado.")
            return

        # Armazena o texto original antes de editar
        texto_anterior = item.text()

        # Abre um diálogo para o usuário editar o texto
        novo_texto, ok = QInputDialog.getText(
            self, 
            "Editar Comentário", 
            "Altere o comentário:", 
            QLineEdit.EchoMode.Normal, 
            texto_anterior
        )
        if ok and novo_texto.strip():
            item.setText(novo_texto.strip())  # Atualiza o texto no QListWidget

            # Atualiza o JSON com o novo texto
            with open(CONTRATOS_JSON, 'r+', encoding='utf-8') as f:
                comentarios_data = json.load(f)

                if id_processo in comentarios_data:
                    for comentario in comentarios_data[id_processo]:
                        if comentario["comentario"] == texto_anterior:
                            comentario["comentario"] = novo_texto.strip()
                            break

                    # Salva as alterações no JSON
                    f.seek(0)
                    json.dump(comentarios_data, f, ensure_ascii=False, indent=4)
                    f.truncate()

            QMessageBox.information(self, "Sucesso", "Comentário atualizado com sucesso.")
        else:
            QMessageBox.information(self, "Cancelado", "A edição foi cancelada.")
                    
    def carregar_comentarios(self):
        """Carrega os comentários do arquivo JSON."""
        with open(CONTRATOS_JSON, 'r', encoding='utf-8') as f:
            comentarios_data = json.load(f)
        
        id_processo = self.dados.get("id_processo", "Desconhecido")
        if id_processo in comentarios_data:
            self.lista_comentarios.clear()
            for comentario in comentarios_data[id_processo]:
                self.lista_comentarios.addItem(comentario["comentario"])

    def adicionar_comentario(self):
        """Adiciona um novo comentário ao JSON."""
        novo_comentario = self.comentario_edit.toPlainText().strip()
        if not novo_comentario:
            QMessageBox.warning(self, "Aviso", "O comentário não pode estar vazio.")
            return

        id_processo = self.dados.get("id_processo", "Desconhecido")
        with open(CONTRATOS_JSON, 'r+', encoding='utf-8') as f:
            comentarios_data = json.load(f)

            if id_processo not in comentarios_data:
                comentarios_data[id_processo] = []

            comentarios_data[id_processo].append({"comentario": novo_comentario})

            # Salva no JSON
            f.seek(0)
            json.dump(comentarios_data, f, ensure_ascii=False, indent=4)
            f.truncate()

        self.comentario_edit.clear()
        self.carregar_comentarios()

    def excluir_comentario(self):
        """Exclui apenas o comentário selecionado."""
        selected_row = self.lista_comentarios.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Aviso", "Nenhum comentário selecionado para exclusão.")
            return

        id_processo = self.dados.get("id_processo", "Desconhecido")

        with open(CONTRATOS_JSON, 'r+', encoding='utf-8') as f:
            comentarios_data = json.load(f)

            if id_processo in comentarios_data:
                # Remove o comentário pela posição
                comentarios_data[id_processo].pop(selected_row)

                # Salva no JSON
                f.seek(0)
                json.dump(comentarios_data, f, ensure_ascii=False, indent=4)
                f.truncate()

        self.carregar_comentarios()

    def create_contratacao_group(self):
        contratacao_group_box = QGroupBox("Informações da Contratação")
        contratacao_group_box.setStyleSheet(STYLE_GROUP_BOX)

        contratacao_layout = QVBoxLayout()

        spacer_item = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        contratacao_layout.addItem(spacer_item)

        # Campo de Objeto
        objeto_layout = QHBoxLayout()
        objeto_label = QLabel("Objeto:")
        self.objeto_edit = QLineEdit(self.dados.get('objeto', ''))
        objeto_layout.addWidget(objeto_label)
        objeto_layout.addWidget(self.objeto_edit)

        # NUP, Material e Serviço com seleção exclusiva
        nup_label = QLabel("NUP:")
        self.nup_edit = QLineEdit(self.dados.get('nup', ''))
        self.nup_edit.setFixedWidth(170)  # Define largura fixa
        objeto_layout.addWidget(nup_label)
        objeto_layout.addWidget(self.nup_edit)

        valor_total_label = QLabel("Valor Estimado:")
        valor_inicial = self.dados.get('valor_total', 0.0)  # Obtém o valor inicial
        self.valor_total_edit = CustomQLineEdit(valor_inicial)
        self.valor_total_edit.setFixedWidth(130)  # Define largura fixa
        objeto_layout.addWidget(valor_total_label)
        objeto_layout.addWidget(self.valor_total_edit)

        contratacao_layout.addLayout(objeto_layout)    
        # Campo de Objeto
        objeto_completo_layout = QVBoxLayout()
        objeto_completo_label = QLabel("Objeto Completo:")
        self.objeto_completo_edit = QTextEdit(self.dados.get('objeto_completo', ''))
        self.objeto_completo_edit.setFixedHeight(100)  # Define altura fixa
        objeto_completo_layout.addWidget(objeto_completo_label)
        objeto_completo_layout.addWidget(self.objeto_completo_edit)
        contratacao_layout.addLayout(objeto_completo_layout)
        
        spacer_item = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        contratacao_layout.addItem(spacer_item)

        linha_divisoria, spacer_baixo_linha = linha_divisoria_layout()
        contratacao_layout.addWidget(linha_divisoria)
        contratacao_layout.addSpacerItem(spacer_baixo_linha)

        comentarios_layout = self.create_comentarios_layout()
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
        self.radio_disputa_sim = None
        self.radio_disputa_nao = None
        self.radio_pesquisa_sim = None
        self.radio_pesquisa_nao = None
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
        # Retorna o gerenciador de mensagens
        return self.mensagens_manager

    def teste(self):
        print("Teste de função")

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
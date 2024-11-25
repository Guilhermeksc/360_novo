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
from src.modules.utils.linha_layout import linha_divisoria_layout, linha_divisoria_sem_spacer_layout
from pathlib import Path
from src.config.paths import CONTROLE_DADOS, CONTROLE_PRAZOS, LICITACAO_CONTROLE_JSON
import json
import pandas as pd
import os
import subprocess
from datetime import datetime

def verificar_criar_json(arquivo_json):
    if not arquivo_json.exists():
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

def create_icon_checkbox(label_text, icon_unchecked, icon_checked, is_checked=False):
    """Cria um layout horizontal contendo um QCheckBox com QIcon para estados personalizado."""
    layout = QHBoxLayout()

    # Checkbox
    checkbox = QCheckBox()
    checkbox.setChecked(is_checked)
    checkbox.setFixedSize(40, 40)  # Tamanho fixo do componente
    checkbox.setCursor(Qt.CursorShape.PointingHandCursor)  # Cursor de mãozinha

    # Definindo os ícones para estados marcados e desmarcados
    checkbox.setIcon(icon_unchecked if not is_checked else icon_checked)
    checkbox.setIconSize(checkbox.size())  # Ajusta o tamanho do ícone ao tamanho do checkbox

    # Atualiza o ícone ao alternar o estado
    def update_icon(state):
        if state == 2:  # Marcado
            checkbox.setIcon(icon_checked)
        else:  # Desmarcado
            checkbox.setIcon(icon_unchecked)

    checkbox.stateChanged.connect(update_icon)

    # Texto do checkbox
    label = QLabel(label_text)
    label.setStyleSheet("font-size: 14px; font-weight: bold")
    layout.addWidget(checkbox)
    layout.addWidget(label)

    return layout, checkbox

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
        verificar_criar_json(LICITACAO_CONTROLE_JSON)
        # Inicializa o gerenciador de mensagens
        self.mensagens_manager = MensagensManager(self.icons, self.dados)     
        self.setup_ui()

    def closeEvent(self, event):
        """
        Sobrescreve o evento de fechamento para emitir o sinal customizado.
        """
        super().closeEvent(event)
        self.window_closed.emit()

    def atualizar_om_label(self, uasg, orgao_responsavel):
        """Atualiza o texto do om_label com os valores atualizados de OM."""
        sigla_om = self.om_combo.currentText()  # Obtém a sigla OM atual do ComboBox
        self.om_label.setText(f"{sigla_om} - {orgao_responsavel} ({uasg})")

    def atualizar_objeto_label(self):
        """Atualiza o texto do objeto_label com o valor atual de objeto_edit e a seleção de material/serviço."""
        objeto_text = self.objeto_edit.text() or "N/A"
        material_servico = "Serviço" if self.radio_servico.isChecked() else "Material"
        self.objeto_label.setText(f"{objeto_text} ({material_servico})")

    def atualizar_status_layout(self, status_text, icon):
        """Atualiza o status_label e icon_label com o texto e ícone fornecidos."""
        self.status_label.setText(status_text)
        if icon and isinstance(icon, QIcon):
            icon_pixmap = icon.pixmap(30, 30)
            self.icon_label.setPixmap(icon_pixmap)
        else:
            self.icon_label.clear()  # Limpa o ícone se não houver um válido
        
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

        # Criação do objeto_label com fonte 14
        objeto = self.dados.get("objeto", "N/A")
        material_servico = self.dados.get("material_servico", "N/A")
        self.objeto_label = QLabel(f"{objeto} ({material_servico})", self)

        font_objeto = QFont()
        font_objeto.setPointSize(12)
        self.objeto_label.setFont(font_objeto)
        self.objeto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Adiciona objeto_label ao layout de labels abaixo de title_label
        vlayout_titulo.addWidget(self.objeto_label)

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

        # Cria um layout horizontal para o campo "Situação"
        situacao_om_setor_layout = QHBoxLayout()
        spacer_situacao = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        situacao_om_setor_layout.addSpacerItem(spacer_situacao)

        divisao_layout = QHBoxLayout()
        divisao_label = QLabel("  Divisão: ")
        divisao_label.setStyleSheet("font-size: 16px; font-weight: bold")
        divisao_layout.addWidget(divisao_label)

        # Criando o QComboBox editável
        self.setor_responsavel_combo = QComboBox()
        self.setor_responsavel_combo .setStyleSheet("font-size: 14px")
        # Adicionando as opções ao ComboBox
        divisoes = [
            "Divisão de Abastecimento",
            "Divisão de Finanças",
            "Divisão de Obtenção",
            "Divisão de Pagamento",
            "Divisão de Administração",
            "Divisão de Subsistência"
        ]
        self.setor_responsavel_combo .addItems(divisoes)

        # Definindo o texto atual com base nos dados fornecidos
        self.setor_responsavel_combo .setCurrentText(self.dados.get('setor_responsavel', 'Selecione a Divisão'))
        divisao_layout.addWidget(self.setor_responsavel_combo )

        situacao_om_setor_layout.addLayout(divisao_layout)
            # Espaçador abaixo da linha divisória
        spacer_baixo_linha = QSpacerItem(5, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
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
            ("Documentos", "Documentos"),
            ("Controle de Etapas", "Controle de Etapas"),
            ("Mensagens", "Mensagens"),
            ("Envio AGU", "Envio AGU"),
            ("Resultados", "Resultados"),
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

    def stacked_widget_envio_agu(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        label = QLabel("AGU")        
        checklist_widget = ChecklistWidget(parent=self, icons_path=self.icons, df_registro_selecionado=self.dados)
        layout.addWidget(label)
        layout.addWidget(checklist_widget)
        frame.setLayout(layout)
        return frame
    
    def stacked_widget_documentos(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        label = QLabel("Documentos")
        layout.addWidget(label)
        frame.setLayout(layout)
        return frame
    
    def setup_stacked_widgets(self):       
        # Cria widgets para cada seção
        self.widgets_map = {
            "Informações": self.stacked_widget_info(self.dados),
            "Controle de Etapas": self.stacked_widget_etapas(self.dados),
            "Documentos": self.stacked_widget_documentos(self.dados),
            "Mensagens": self.stacked_widget_mensagens(self.dados),
            "Envio AGU": self.stacked_widget_envio_agu(self.dados),
            "Resultados": self.stacked_widget_pncp(self.dados),
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
            with open(LICITACAO_CONTROLE_JSON, 'r+', encoding='utf-8') as f:
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
        with open(LICITACAO_CONTROLE_JSON, 'r', encoding='utf-8') as f:
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
        with open(LICITACAO_CONTROLE_JSON, 'r+', encoding='utf-8') as f:
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

        with open(LICITACAO_CONTROLE_JSON, 'r+', encoding='utf-8') as f:
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

        # Material e Serviço com seleção exclusiva usando RadioButtons
        material_servico_label = QLabel("Material/Serviço:")
        self.radio_material = QRadioButton("Material")
        self.radio_servico = QRadioButton("Serviço")

        # Grupo de botões exclusivo para Material e Serviço
        self.material_servico_group = QButtonGroup()
        self.material_servico_group.addButton(self.radio_material)
        self.material_servico_group.addButton(self.radio_servico)

        # Define o estado inicial
        material_servico = self.dados.get('material_servico', 'Material')
        self.radio_servico.setChecked(material_servico == "Serviço")
        self.radio_material.setChecked(material_servico == "Material")

        objeto_layout.addWidget(material_servico_label)
        objeto_layout.addWidget(self.radio_material)
        objeto_layout.addWidget(self.radio_servico)
        contratacao_layout.addLayout(objeto_layout)

        # Conecta o sinal para atualizar o objeto_label quando "Material" ou "Serviço" é selecionado
        self.material_servico_group.buttonClicked.connect(self.atualizar_objeto_label)        
    
        # Conecta o sinal editingFinished para atualizar o objeto_label automaticamente
        self.objeto_edit.editingFinished.connect(self.atualizar_objeto_label)

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

    def create_GrupoSIGDEM(self):       
        grupoSIGDEM = QGroupBox("SIGDEM")
        grupoSIGDEM.setStyleSheet(STYLE_GROUP_BOX)

        layout = QVBoxLayout(grupoSIGDEM)

        icon_copy = QIcon(self.icons["copy_1"])

        self.id_processo = self.dados.get('id_processo', 'desconhecido')
        self.objeto = self.dados.get('objeto', 'objeto_desconhecido')
        self.tipo = self.dados.get('tipo', 'desconhecido')
        self.numero = self.dados.get('numero', 'desconhecido')
        self.ano = self.dados.get('ano', 'desconhecido')
        self.nup = self.dados.get('nup', 'desconhecido')

        labelAssunto = QLabel("No campo “Assunto”:")
        layout.addWidget(labelAssunto)
        self.textEditAssunto = QTextEdit(f"{self.id_processo} - Abertura de Processo ({self.objeto})")
        self.textEditAssunto.setMaximumHeight(40)
        layoutHAssunto = QHBoxLayout()
        layoutHAssunto.addWidget(self.textEditAssunto)
        btnCopyAssunto = self.create_button(
            text="", icon=icon_copy, 
            callback=lambda: self.copyToClipboard(self.textEditAssunto.toPlainText()), 
            tooltip_text="Copiar texto para a área de transferência", 
            button_size=QSize(40, 40), 
            icon_size=QSize(25, 25)
            )
        layoutHAssunto.addWidget(btnCopyAssunto)
        layout.addLayout(layoutHAssunto)

        labelSinopse = QLabel("No campo “Sinopse”:")
        layout.addWidget(labelSinopse)
        self.textEditSinopse = QTextEdit(
            f"Termo de Abertura referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel_combo.currentText()}"
        )
        self.textEditSinopse.setMaximumHeight(150) 
        layoutHSinopse = QHBoxLayout()
        layoutHSinopse.addWidget(self.textEditSinopse)
        btnCopySinopse = self.create_button(text="", icon=icon_copy, callback=lambda: self.copyToClipboard(self.textEditSinopse.toPlainText()), tooltip_text="Copiar texto para a área de transferência", button_size=QSize(40, 40), icon_size=QSize(25, 25))
        layoutHSinopse.addWidget(btnCopySinopse)
        layout.addLayout(layoutHSinopse)

        grupoSIGDEM.setLayout(layout)
        # self.carregarAgentesResponsaveis()
        
        return grupoSIGDEM

    def get_descricao_servico(self):
        material_servico = "Material" if self.radio_material.isChecked() else "Serviço"
        return "aquisição de" if material_servico == "Material" else "contratação de empresa especializada em"

    def copyToClipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QToolTip.showText(QCursor.pos(), "Texto copiado para a área de transferência.", msecShowTime=1500)

    def criar_e_abrir_pasta(self):
        # Cria a estrutura de pastas
        self.consolidador.verificar_e_criar_pastas(self.pasta_base / self.nome_pasta)
        icon = self.icons.get("folder_v", None)
        
        # Após criar, tenta abrir a pasta
        self.abrir_pasta(self.pasta_base / self.nome_pasta)
        
        # Emite o sinal para atualizar o layout de status
        self.pastas_existentes.emit("Pastas encontradas", icon)

    def abrir_pasta(self, pasta_path):
        if pasta_path.exists() and pasta_path.is_dir():
            # Abre a pasta no explorador de arquivos usando QDesktopServices
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(pasta_path)))
        else:
            QMessageBox.warning(self, "Erro", "A pasta selecionada não existe ou não é um diretório.")

    def create_utilidades_group(self):
        utilidades_layout = QHBoxLayout()
        utilidades_layout.setSpacing(0)
        utilidades_layout.setContentsMargins(0, 0, 0, 0)

        icon_criar_pasta = QIcon(self.icons["create-folder"])
        icon_salvar_pasta = QIcon(self.icons["zip-folder"])
        icon_template = QIcon(self.icons["template"])

        # Verifique se pasta_base está corretamente inicializada
        if not hasattr(self, 'pasta_base') or not isinstance(self.pasta_base, Path):
            self.pasta_base = Path(self.config.get('pasta_base', str(Path.home() / 'Documentos')))  # Exemplo de inicialização

        # Define um nome padrão para a pasta (ou modifique conforme necessário)
        self.nome_pasta = f'{self.id_processo.replace("/", "-")} - {self.objeto.replace("/", "-")}'

        # Botão para criar a estrutura de pastas e abrir a pasta
        criar_pasta_button = self.create_button(
            "Criar e Abrir Pasta", 
            icon=icon_criar_pasta, 
            callback=self.criar_e_abrir_pasta,  # Chama a função que cria e abre a pasta
            tooltip_text="Clique para criar a estrutura de pastas e abrir", 
            button_size=QSize(210, 40), 
            icon_size=QSize(40, 40)
        )
        utilidades_layout.addWidget(criar_pasta_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Botão para abrir o arquivo de registro
        editar_registro_button = self.create_button(
            "Local de Salvamento", 
            icon=icon_salvar_pasta, 
            callback=self.consolidador.alterar_diretorio_base, 
            tooltip_text="Clique para alterar o local de salvamento dos arquivos", 
            button_size=QSize(210, 40), icon_size=QSize(40, 40)
            )
        utilidades_layout.addWidget(editar_registro_button, alignment=Qt.AlignmentFlag.AlignCenter)
        # Botão para abrir o arquivo de registro
        visualizar_pdf_button = self.create_button(
            "Editar Modelos", 
            icon=icon_template, 
            callback=self.consolidador.editar_modelo, 
            tooltip_text="Clique para editar os modelos dos documentos", 
            button_size=QSize(210, 40), icon_size=QSize(40, 40)
            )
        
        utilidades_layout.addWidget(visualizar_pdf_button, alignment=Qt.AlignmentFlag.AlignCenter)

        return utilidades_layout

    def create_button(self, text="", icon=None, callback=None, tooltip_text="", button_size=None, icon_size=None, font_size=None):
        btn = QPushButton(text)
        
        # Configura o ícone, se fornecido
        if icon:
            btn.setIcon(icon)
            btn.setIconSize(icon_size if icon_size else QSize(40, 40))
        
        # Define o tamanho do botão, se fornecido
        if button_size:
            btn.setFixedSize(button_size)
        
        # Aplica a dica de ferramenta
        btn.setToolTip(tooltip_text)
        
        # Conecta o callback ao evento de clique
        if callback:
            btn.clicked.connect(callback)
        
        # Ajusta o tamanho da fonte, se fornecido
        style = ""
        if font_size:
            style += f"font-size: {font_size}px;"
        
        btn.setStyleSheet(style)
        
        # Define o cursor como uma mãozinha
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        return btn

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
    
    def atualizar_status_label(self, status_message, icon_path):
        # Atualiza o texto do status_label com a mensagem passada
        self.status_label.setText(status_message)

        # Atualiza o ícone
        icon_folder = QIcon(icon_path)
        icon_pixmap = icon_folder.pixmap(30, 30)  # Define o tamanho do ícone
        self.icon_label.setPixmap(icon_pixmap)

        # Opcional: Mude a cor do texto de status (se necessário)
        self.status_label.setStyleSheet("font-size: 14px;")

    def stacked_widget_anexos(self, data):
        frame = QFrame()
        layout = QVBoxLayout()

        # Cria e adiciona o QGroupBox "Dados do Setor Responsável pela Contratação"
        anexos_group = self.create_anexos_group()
        layout.addWidget(anexos_group)

        # Define o layout para o frame
        frame.setLayout(layout)        
        return frame

    def stacked_widget_etapas(self, data):
        frame = QFrame()
        layout = QVBoxLayout()

        label = QLabel("Etapas")
        layout.addWidget(label)

        # Carregar o arquivo CONTROLE_PRAZOS
        try:
            with open(CONTROLE_PRAZOS, 'r', encoding='utf-8') as f:
                controle_prazos = json.load(f)
        except Exception as e:
            layout.addWidget(QLabel(f"Erro ao carregar CONTROLE_PRAZOS: {str(e)}"))
            frame.setLayout(layout)
            return frame

        # Procurar o id_processo em controle_prazos
        id_processo = data.get('id_processo', None)
        if id_processo and id_processo in controle_prazos:
            etapas = controle_prazos[id_processo]

            # Exibir as etapas no layout
            for etapa in etapas:
                situacao = etapa.get("situacao", "N/A")
                data_inicial = etapa.get("data_inicial", "N/A")
                data_final = etapa.get("data_final", "N/A")
                dias_na_etapa = etapa.get("dias_na_etapa", 0)
                comentario = etapa.get("comentario", "")

                etapa_label = QLabel(
                    f"Situação: {situacao}\n"
                    f"Data Inicial: {data_inicial}\n"
                    f"Data Final: {data_final}\n"
                    f"Dias na Etapa: {dias_na_etapa}\n"
                    f"Comentário: {comentario}"
                )
                etapa_label.setWordWrap(True)
                layout.addWidget(etapa_label)
        else:
            layout.addWidget(QLabel("Nenhuma etapa encontrada para o processo."))

        frame.setLayout(layout)
        return frame
    
    def stacked_widget_pncp(self, data):
        frame = QFrame()
        layout = QVBoxLayout()
        label = QLabel("Conteúdo do PNCP")
        layout.addWidget(label)
        frame.setLayout(layout)
        return frame

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

    def create_sessao_publica_group(self):
        # Criação do QGroupBox para a seção Sessão Pública
        self.sessao_groupbox = QGroupBox("Sessão Pública:")
        self.sessao_groupbox.setMaximumWidth(300)
        self.sessao_groupbox.setStyleSheet(STYLE_GROUP_BOX)

        group_layout = QHBoxLayout(self.sessao_groupbox)
        
        # Ícone de calendário ao lado do label "Defina a data:"
        calendar_icon = QIcon(self.icons.get("calendar", None))
        icon_label = QLabel()
        icon_label.setPixmap(calendar_icon.pixmap(40, 40))  # Tamanho do ícone ajustado
        
        # Label "Defina a data:"
        date_label = QLabel("Defina a data:")
        date_label.setStyleSheet("font-size: 16px")
        # Layout horizontal para o ícone e o label "Defina a data:"
        top_layout = QHBoxLayout()
        top_layout.addWidget(icon_label)
        top_layout.addWidget(date_label)
        top_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        group_layout.addLayout(top_layout)
        
        # Configuração do DateEdit com a data inicial
        self.data_edit = QDateEdit()
        self.data_edit.setStyleSheet("font-size: 14px")
        self.data_edit.setCalendarPopup(True)
        data_sessao_str = self.dados.get('data_sessao', '')
        if data_sessao_str:
            self.data_edit.setDate(QDate.fromString(data_sessao_str, "yyyy-MM-dd"))
        else:
            self.data_edit.setDate(QDate.currentDate())

        group_layout.addWidget(self.data_edit)
        
        return self.sessao_groupbox

    def setup_layout_conteudo(self):
        """Configura o layout de conteúdo com StackedWidget e agentes responsáveis."""
        layout_conteudo = QHBoxLayout()
        
        # Layout StackedWidget e ao lado layout agentes responsáveis
        stacked_widget = QStackedWidget(self)
        layout_conteudo.addWidget(stacked_widget)

        # Layout para agentes responsáveis ao lado do StackedWidget
        agentes_responsaveis_layout = QVBoxLayout()
        layout_conteudo.addLayout(agentes_responsaveis_layout)
        
        return layout_conteudo

    def setup_formularios(self):
        """Configura o layout para consulta à API com campos de CNPJ e Sequencial PNCP."""
        group_box = QGroupBox("Formulário")
        layout = QVBoxLayout(group_box)

        # Aplicando o estilo CSS específico ao GroupBox
        group_box.setStyleSheet(STYLE_GROUP_BOX)

        # Layout vertical para os botões
        vlayout_botoes = QVBoxLayout()
        
        # Conectar o botão `Novo Formulário` à função `criar_formulario` usando uma função lambda
        add_button_func("   Novo Formulário   ", "excel_down", lambda: self.criar_formulario(), vlayout_botoes, self.icons, tooltip="Gerar o Formulário")
        add_button_func("Importar Formulário", "excel_up", self.on_import_formulario_clicked, vlayout_botoes, self.icons, tooltip="Carregar o Formulário")

        # Adicionar o layout de botões ao layout principal
        layout.addLayout(vlayout_botoes)
        return group_box
    
    def criar_formulario(self):
        # Inicia o worker para criação do formulário em segundo plano
        self.worker = TableCreationWorker(self.dados, self.colunas_legiveis, self.pasta_base)
        self.worker.file_saved.connect(self.abrir_arquivo)  # Conecta o sinal de conclusão
        self.worker.start()  # Inicia a execução em segundo plano

    def abrir_arquivo(self, file_path):
        """Abre o arquivo salvo com o caminho fornecido."""
        if os.name == 'nt':
            os.startfile(file_path)
        elif os.name == 'posix':
            subprocess.call(['open', file_path])
        else:
            subprocess.call(['xdg-open', file_path])

    def on_import_formulario_clicked(self):
        """Ação disparada ao clicar no botão 'Importar Formulário'."""
        self.carregar_formulario()
            
    def carregar_formulario(self):
        """Permite ao usuário selecionar um arquivo XLSX ou ODS e carrega os dados"""
        # Abre a caixa de diálogo para selecionar o arquivo
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Formulário", "", "Arquivos Excel (*.xlsx *.ods)")

        if not file_path:
            return  # Se o usuário cancelar, encerra a função

        try:
            # Verifica a extensão do arquivo para escolher o método de leitura adequado e pula a primeira linha
            if file_path.endswith('.xlsx'):
                data = pd.read_excel(file_path, engine='openpyxl', header=1)
            elif file_path.endswith('.ods'):
                data = pd.read_excel(file_path, engine='odf', header=1)
            else:
                QMessageBox.warning(self, "Formato Inválido", "Por favor, selecione um arquivo .xlsx ou .ods.")
                return

            # Exibe os dados no console para verificar o conteúdo
            print("Dados do formulário carregados:")
            print(data)

            # Armazena o DataFrame para ser usado na função de preenchimento
            self.df_registro_selecionado = data

            # Preenche os campos específicos com os valores carregados
            self.preencher_dados(data)

        except Exception as e:
            QMessageBox.critical(self, "Erro ao Carregar Formulário", f"Erro ao carregar o formulário: {e}")

    def preencher_dados(self, dados_novos):
        """Preenche os campos da interface com os dados carregados"""
        try:
            def obter_valor(indice):
                """Função auxiliar para obter um valor de 'Valor' com base no 'Índice'"""
                resultado = dados_novos.loc[dados_novos['Índice'] == indice, 'Valor']
                return str(resultado.values[0]) if not resultado.empty else ""

            # Atualizar campos específicos com base nos valores da coluna 'Valor' do DataFrame
            self.valor_total_edit.setText(obter_valor('Valor Total'))
            self.acao_interna_edit.setText(obter_valor('Ação Interna'))
            self.fonte_recursos_edit.setText(obter_valor('Fonte de Recursos'))
            self.natureza_despesa_edit.setText(obter_valor('Natureza da Despesa'))
            self.unidade_orcamentaria_edit.setText(obter_valor('Unidade Orçamentária'))
            self.ptres_edit.setText(obter_valor('PTRES'))
            
            # Configurar o estado do botão de rádio com base no valor encontrado
            atividade_custeio_valor = obter_valor('Atividade de Custeio')
            self.radio_custeio_sim.setChecked(atividade_custeio_valor == 'Sim')
            self.radio_custeio_nao.setChecked(atividade_custeio_valor == 'Não')

        except Exception as e:
            print(f"Erro ao preencher os dados: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Falha ao preencher os dados: {str(e)}")

    def handle_gerar_autorizacao(self):
        self.assunto_text = f"{self.id_processo} - Abertura de Processo ({self.objeto})"
        self.sinopse_text = (
            f"Termo de Abertura referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel_combo.currentText()}"
        )
        self.update_text_fields()
        self.consolidador.gerar_autorizacao()

        icon = self.icons.get("folder_v", None)        
        # Emite o sinal para atualizar o layout de status
        self.pastas_existentes.emit("Pastas encontradas", icon)


    def handle_gerar_autorizacao_sidgem(self):
        self.assunto_text = f"{self.id_processo} - Abertura de Processo ({self.objeto})"
        self.sinopse_text = (
            f"Termo de Abertura referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel_combo.currentText()}"
        )
        self.update_text_fields()

    def handle_gerar_comunicacao_padronizada(self):
        self.assunto_text = f"{self.id_processo} - Documentos de Planejamento ({self.objeto})"
        self.sinopse_text = (
            f"Documentos de Planejamento (DFD, TR e Declaração de Adequação Orçamentária) referente à {self.tipo} nº {self.numero}/{self.ano}, "
            f"para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel_combo.currentText()}\n"
        )

        # Chama a função para verificar PDFs existentes
        documentos = self.consolidador.verificar_pdfs_existentes()
        self.sinopse_text += "\n".join(documentos)  # Adiciona os documentos verificados à sinopse
        
        # Imprime a lista de documentos para verificar o conteúdo
        print("Documentos verificados para inclusão:")
        for documento in documentos:
            print(documento)

        self.update_text_fields()  # Atualiza os campos de texto
        self.consolidador.gerar_comunicacao_padronizada()  # Chama a função de geração de comunicação

    def handle_gerar_comunicacao_padronizada_sidgem(self):
        self.assunto_text = f"{self.id_processo} - Documentos de Planejamento ({self.objeto})"
        self.sinopse_text = (
            f"Documentos de Planejamento (DFD, TR e Declaração de Adequação Orçamentária) referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel_combo.currentText()}"
        )
        self.update_text_fields()

    def handle_gerar_aviso_dispensa(self):
        self.assunto_text = f"{self.id_processo} - Aviso ({self.objeto})"
        self.sinopse_text = (
            f"Aviso referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel_combo.currentText()}"
        )
        self.update_text_fields()
        self.consolidador.gerar_aviso_dispensa()

    def handle_gerar_aviso_dispensa_sidgem(self):
        self.assunto_text = f"{self.id_processo} - Aviso ({self.objeto})"
        self.sinopse_text = (
            f"Aviso referente à {self.tipo} nº {self.numero}/{self.ano}, para {self.get_descricao_servico()} {self.objeto}\n"
            f"Processo Administrativo NUP: {self.nup}\n"
            f"Setor Demandante: {self.setor_responsavel_combo.currentText()}"
        )
        self.update_text_fields()

    def update_text_fields(self):
        self.textEditAssunto.setPlainText(self.assunto_text)
        self.textEditSinopse.setPlainText(self.sinopse_text)

    def create_anexos_group(self):
        # LineEdit para o ID de Dispensa Eletrônica
        self.id_dispensa_eletronica = self.dados.get('id_processo', '')
        id_display = self.id_dispensa_eletronica if self.id_dispensa_eletronica else 'ID não disponível'

        # GroupBox para Anexos
        anexos_group_box = QGroupBox(f"Anexos da {id_display}")
        anexos_group_box.setStyleSheet(STYLE_GROUP_BOX)

        # Layout principal do GroupBox
        anexo_layout = QVBoxLayout()
        
        self.anexos_dict = {}

        # Função auxiliar para adicionar seções de anexos
        def add_anexo_section(section_title, *anexos):
            section_label = QLabel(section_title)
            anexo_layout.addWidget(section_label)
            self.anexos_dict[section_title] = []

            for anexo in anexos:
                layout = QHBoxLayout()

                # Caminho e tooltip
                pasta_anexo = self.define_pasta_anexo(section_title, anexo)
                tooltip_text = self.define_tooltip_text(section_title, anexo)

                # Verificação de arquivo PDF
                icon_label = QLabel()
                icon = self.get_icon_for_anexo(pasta_anexo)
                icon_label.setPixmap(icon.pixmap(QSize(25, 25)))
                layout.addWidget(icon_label)
                layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

                # Botão para abrir a pasta
                btnabrirpasta = self.create_open_folder_button(pasta_anexo, tooltip_text)
                layout.addWidget(btnabrirpasta)

                # Label do anexo
                anexo_label = QLabel(anexo)
                layout.addWidget(anexo_label)
                layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
                layout.addStretch()

                self.anexos_dict[section_title].append((anexo, icon_label))
                anexo_layout.addLayout(layout)

        # Adiciona seções de anexos
        add_anexo_section("Documento de Formalização de Demanda (DFD)", "Anexo A - Relatório do Safin", "Anexo B - Especificações")
        add_anexo_section("Termo de Referência (TR)", "Anexo - Pesquisa de Preços")
        add_anexo_section("Declaração de Adequação Orçamentária", "Anexo - Relatório do PDM/CATSER")
        add_anexo_section("Demais Documentos", "Estudo Técnico Preliminar", "Matriz de Riscos")
        justificativa_label = QLabel("Justificativas relevantes")
        anexo_layout.addWidget(justificativa_label)

        # Botões de Ação
        self.add_buttons_to_layout(anexo_layout)

        # Definição do layout final e do GroupBox
        anexos_group_box.setLayout(anexo_layout)

        return anexos_group_box

    def define_pasta_anexo(self, section_title, anexo):
        """Define o caminho da pasta de anexo baseado no título da seção e nome do anexo."""
        id_processo_modificado = self.id_processo.replace("/", "-")
        objeto_modificado = self.objeto.replace("/", "-")

        if section_title == "Documento de Formalização de Demanda (DFD)":
            if "Anexo A" in anexo:
                return self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'DFD' / 'Anexo A - Relatorio Safin'
            elif "Anexo B" in anexo:
                return self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'DFD' / 'Anexo B - Especificações e Quantidade'
        elif section_title == "Termo de Referência (TR)":
            return self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'TR' / 'Pesquisa de Preços'
        elif section_title == "Declaração de Adequação Orçamentária":
            return self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária' / 'Relatório do PDM-Catser'
        elif section_title == "Demais Documentos":
            if "Estudo" in anexo:
                return self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'ETP'
            elif "Matriz" in anexo:
                return self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'MR'
        return None

    def define_tooltip_text(self, section_title, anexo):
        """Retorna o texto da tooltip para um anexo."""
        if section_title == "Documento de Formalização de Demanda (DFD)":
            if "Anexo A" in anexo:
                return "Abrir pasta Anexo A - Relatório do Safin"
            elif "Anexo B" in anexo:
                return "Abrir pasta Anexo B - Especificações e Quantidade"
        elif section_title == "Termo de Referência (TR)":
            return "Abrir pasta Pesquisa de Preços"
        elif section_title == "Declaração de Adequação Orçamentária":
            return "Abrir pasta Relatório do PDM-Catser"
        return "Abrir pasta"

    def get_icon_for_anexo(self, pasta_anexo):
        icon_confirm = QIcon(self.icons["concluido"])
        icon_cancel = QIcon(self.icons["cancel"])
        if pasta_anexo and self.verificar_arquivo_pdf(pasta_anexo):
            return icon_confirm
        return icon_cancel

    def verificar_arquivo_pdf(self, pasta):
        arquivos_pdf = []
        if not pasta.exists():
            print(f"Pasta não encontrada: {pasta}")
            return None
        for arquivo in pasta.iterdir():
            if arquivo.suffix.lower() == ".pdf":
                arquivos_pdf.append(arquivo)
                # print(f"Arquivo PDF encontrado: {arquivo.name}")
        if arquivos_pdf:
            return max(arquivos_pdf, key=lambda p: p.stat().st_mtime)  # Retorna o PDF mais recente
        return None
    
    def create_open_folder_button(self, pasta_anexo, tooltip_text):
        icon_abrir_pasta = QIcon(self.icons["open-folder"])
        btnabrirpasta = self.create_button(
            "", icon=icon_abrir_pasta, callback=lambda _, p=pasta_anexo: self.abrir_pasta(p),
            tooltip_text=tooltip_text, button_size=QSize(25, 25), icon_size=QSize(25, 25)
        )
        btnabrirpasta.setToolTipDuration(0)
        return btnabrirpasta

    def add_buttons_to_layout(self, layout):
        icon_browser = QIcon(self.icons["browser"])
        icon_refresh = QIcon(self.icons["refresh"])       

        atualizar_button = self.create_button(
            "   Atualizar Pastas  ",
            icon_refresh,
            self.atualizar_action,
            "Atualizar os dados",
            QSize(220, 40), QSize(30, 30)
        )

        button_layout_atualizar = QHBoxLayout()
        button_layout_atualizar.addStretch()
        button_layout_atualizar.addWidget(atualizar_button)
        button_layout_atualizar.addStretch()

        layout.addLayout(button_layout_atualizar)

    def atualizar_action(self):
        icon_confirm = QIcon(self.icons["concluido"])
        icon_x = QIcon(self.icons["cancel"])

        def atualizar_anexo(section_title, anexo, label):
            pasta_anexo = None
            id_processo_modificado = self.id_processo.replace("/", "-")
            objeto_modificado = self.objeto.replace("/", "-")

            if section_title == "Documento de Formalização de Demanda (DFD)":
                if "Anexo A" in anexo:
                    pasta_anexo = self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'DFD' / 'Anexo A - Relatorio Safin'
                elif "Anexo B" in anexo:
                    pasta_anexo = self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'DFD' / 'Anexo B - Especificações e Quantidade'
            elif section_title == "Termo de Referência (TR)":
                pasta_anexo = self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'TR' / 'Pesquisa de Preços'
            elif section_title == "Declaração de Adequação Orçamentária":
                pasta_anexo = self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'Declaracao de Adequação Orçamentária' / 'Relatório do PDM-Catser'
            elif section_title == "Demais Documentos":
                if "Estudo" in anexo:
                    pasta_anexo = self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'ETP'
                elif "Matriz" in anexo:
                    pasta_anexo = self.pasta_base / f'{id_processo_modificado} - {objeto_modificado}' / '2. CP e anexos' / 'MR'
            
            if pasta_anexo:
                print(f"Verificando pasta: {pasta_anexo}")
                arquivos_pdf = self.verificar_arquivo_pdf(pasta_anexo)
                icon = icon_confirm if arquivos_pdf else icon_x
                label.setPixmap(icon.pixmap(QSize(25, 25)))
            else:
                print(f"Anexo não identificado: {anexo}")
                label.setPixmap(icon_x.pixmap(QSize(25, 25)))

        for section_title, anexos in self.anexos_dict.items():
            for anexo, icon_label in anexos:
                atualizar_anexo(section_title, anexo, icon_label)

    def setup_consulta_api(self):
        """Configura o layout para consulta à API com campos de CNPJ e Sequencial PNCP."""
        group_box = QGroupBox("Consulta API", self)
        layout = QVBoxLayout(group_box)
        group_box.setStyleSheet(STYLE_GROUP_BOX)

        # Layout para CNPJ
        cnpj_layout = QHBoxLayout() 
        label_cnpj = QLabel("CNPJ Matriz:", self)
        label_cnpj.setStyleSheet("color: #8AB4F7; font-size: 16px")
        cnpj_layout.addWidget(label_cnpj)
        self.cnpj_edit = QLineEdit(str(self.dados.get('cnpj_matriz', '00394502000144')))
        cnpj_layout.addWidget(self.cnpj_edit)
        layout.addLayout(cnpj_layout)

        # Layout para Sequencial PNCP
        sequencial_layout = QHBoxLayout()
        label_sequencial = QLabel("Sequencial PNCP:", self)
        label_sequencial.setStyleSheet("color: #8AB4F7; font-size: 16px")
        sequencial_layout.addWidget(label_sequencial)
        self.sequencial_edit = QLineEdit(str(self.dados.get('sequencial_pncp', '')))
        self.sequencial_edit.setPlaceholderText("Digite o Sequencial PNCP")
        sequencial_layout.addWidget(self.sequencial_edit)
        layout.addLayout(sequencial_layout)

        # Botão de consulta
        btn_consultar = create_button(
            text="Consultar",
            icon=self.icons.get("api", None),
            callback=self.emit_request_consulta_api,  # Conectar ao método para emitir o sinal
            tooltip_text="Clique para consultar dados usando o CNPJ e Sequencial PNCP",
        )
        layout.addWidget(btn_consultar)

        return group_box

    def emit_request_consulta_api(self):
        """Emite o sinal request_consulta_api com os parâmetros necessários para a consulta."""
        cnpj = self.cnpj_edit.text()
        ano = self.dados.get('ano', None)
        sequencial = self.sequencial_edit.text()
        uasg = self.dados.get('uasg', None)
        numero = self.dados.get('numero', None)
        self.request_consulta_api.emit(cnpj, ano, sequencial, uasg, numero)

    # def on_link_pncp_clicked(self, link_pncp, cnpj, ano):
    #     # Montando a URL
    #     url = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{link_pncp}"

    #     # Abrindo o link no navegador padrão
    #     QDesktopServices.openUrl(QUrl(url))
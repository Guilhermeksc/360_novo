from functools import partial
from pathlib import Path
import json
import functools
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.config.paths import MSG_LICITACAO_JSON
from src.modules.utils.add_button import add_button_func

class EditableTextField(QTextEdit):
    text_changed_signal = pyqtSignal(str)  # Sinal personalizado para enviar texto atualizado

    def __init__(self, parent=None):
        super().__init__(parent)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        # Emite o sinal com o texto atualizado
        self.text_changed_signal.emit(self.toPlainText())

class MensagensManager(QWidget):
    def __init__(self, icons, dados):
        super().__init__()
        self.icons = icons
        self.dados = dados
        self.current_button_name = None  # Nome do botão selecionado
        self.init_ui()
        self.load_buttons_from_json()
    
    def init_ui(self):
        # Layout principal
        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        self.adicionar_button_layout = QVBoxLayout()
        self.main_layout.addLayout(self.adicionar_button_layout)

        add_button_func("Adicionar Nova Mensagem", "plus", self.add_new_message, self.adicionar_button_layout, self.icons, tooltip="Adicionar uma nova mensagem")

        # Layout para botões à esquerda
        self.msg_button_layout = QVBoxLayout()
        self.adicionar_button_layout.addLayout(self.msg_button_layout)

        # Adiciona um espaço flexível para manter os botões alinhados
        self.msg_button_layout.addStretch()

        # Layout para o conteúdo à direita
        self.msg_content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.msg_content_layout)

        msg_label = QLabel("Conteúdo da Mensagem")
        self.msg_content_layout.addWidget(msg_label)

        # Sub-layout para os dois campos de texto
        self.text_fields_layout = QHBoxLayout()

        # Campo de edição do texto
        self.edit_text_field = EditableTextField()
        self.edit_text_field.setPlaceholderText("Edite o texto da mensagem aqui...")
        self.edit_text_field.text_changed_signal.connect(self.save_message_to_json)
        self.text_fields_layout.addWidget(self.edit_text_field)

        # Campo para texto padronizado
        self.standard_text_field = QTextEdit()
        self.standard_text_field.setReadOnly(True)
        self.standard_text_field.setPlaceholderText("Texto padronizado da mensagem...")
        self.text_fields_layout.addWidget(self.standard_text_field)

        # Adiciona o sub-layout ao layout de conteúdo
        self.msg_content_layout.addLayout(self.text_fields_layout)

        self.main_layout.addLayout(self.adicionar_button_layout)
    
    def save_message_to_json(self, updated_text):
        """Salva o texto atualizado no JSON."""
        if not self.current_button_name:
            print("Nenhum botão está selecionado.")
            return

        try:
            with open(MSG_LICITACAO_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if self.current_button_name in data:
                data[self.current_button_name][0]["texto_msg"] = updated_text

            with open(MSG_LICITACAO_JSON, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            print(f"Mensagem para o botão '{self.current_button_name}' salva com sucesso.")

            # Recarrega os botões na interface
            self.load_buttons_from_json()

        except Exception as e:
            print(f"Erro ao salvar mensagem no JSON: {e}")

    def update_buttons(self):
        """Atualiza os botões recarregando o JSON."""
        self.load_buttons_from_json()

    def load_message(self, msg, button_name):
        """Carrega a mensagem no campo de edição e renderiza os placeholders."""
        self.current_button_name = button_name  # Define o botão atual
        self.edit_text_field.setText(msg)  # Define o texto com placeholders
        self.render_standard_text(msg)  # Renderiza o texto com os valores de dados

    def render_standard_text(self, msg):
        """Renderiza os placeholders no texto usando os valores de self.dados."""
        try:
            # Substitui os placeholders no texto com os valores de self.dados
            formatted_text = msg.format(**self.dados)
        except KeyError as e:
            print(f"Erro: Placeholder não encontrado em self.dados: {e}")
            formatted_text = msg  # Mantém o texto original se houver erro

        self.standard_text_field.setText(formatted_text)  # Atualiza o campo renderizado

    def load_buttons_from_json(self):
        """Carrega os botões a partir do JSON atualizado."""
        # Remove todos os widgets, exceto o botão "Adicionar Nova Mensagem"
        while self.msg_button_layout.count() > 1:  # Mantém o último widget (botão "Adicionar Nova Mensagem")
            widget = self.msg_button_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        # Verifica se o arquivo JSON existe, caso contrário cria-o com valores padrão
        if not MSG_LICITACAO_JSON.exists():
            default_data = {
                "IRP": [{"texto_msg": "texto1"}],
                "Homologação": [{"texto_msg": "texto1"}],
                "Atendimento de Nota Técnica": [{"texto_msg": "texto1"}],
                "Recomendações AGU": [{"texto_msg": "texto1"}]
            }
            with open(MSG_LICITACAO_JSON, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)

        # Lê o arquivo JSON
        try:
            with open(MSG_LICITACAO_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Erro ao ler o arquivo {MSG_LICITACAO_JSON}: {e}")
            return

        # Recarrega os botões no layout
        for nome_botao in data:
            texto_msg = data[nome_botao][0]['texto_msg']
            button = self.create_button(
                text=nome_botao,
                icon_name='mensagem',
                slot=partial(self.load_message, texto_msg, nome_botao),
                tooltip="Clique para carregar a mensagem"
            )
            # Adiciona o botão ao layout
            self.msg_button_layout.insertWidget(self.msg_button_layout.count() - 1, button)

        # Certifica-se de que o botão "Adicionar Nova Mensagem" está sempre no final
        self.msg_button_layout.addStretch()


    def create_button(self, text, icon_name, slot, tooltip=None):
        button = QPushButton()
        # Configurar ícone no botão
        icon = self.icons.get(icon_name)
        if icon:
            button.setIcon(icon)
        button.setIconSize(QSize(30, 30))
        
        # Define o texto do botão
        if text:
            button.setText(text)
        
        # Aplicando o estilo CSS ao botão
        button.setStyleSheet("""
            QPushButton {
                background-color: #181928;
                color: #8AB4F7;
                font-size: 14px;
                font-weight: bold;
                border: none;
                padding: 8px;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #2C2F3F;
                color: #FFFFFF;
            }
        """)

        if tooltip:
            button.setToolTip(tooltip)

        button.clicked.connect(slot)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def atualizar_texto_padronizado(self):
        """Atualiza o campo padrão com base no texto editado."""
        texto = self.edit_text_field.toPlainText()  # Obtém o texto do campo de edição
        self.render_standard_text(texto)  # Renderiza o texto formatado

    def add_new_message(self):
        """Adiciona uma nova mensagem ao JSON e atualiza os botões."""
        nome_botao, ok1 = QInputDialog.getText(self, 'Novo Botão', 'Nome do Botão:')
        if not ok1 or not nome_botao.strip():
            return
        texto_msg, ok2 = QInputDialog.getMultiLineText(self, 'Novo Botão', 'Texto da Mensagem:')
        if not ok2:
            return

        try:
            # Atualiza o arquivo JSON com o novo botão
            with open(MSG_LICITACAO_JSON, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                data[nome_botao] = [{'texto_msg': texto_msg}]
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=4)
                f.truncate()

            print(f"Botão '{nome_botao}' adicionado com sucesso.")

            # Recarrega os botões para refletir as alterações
            self.load_buttons_from_json()

        except Exception as e:
            print(f"Erro ao adicionar nova mensagem: {e}")


		
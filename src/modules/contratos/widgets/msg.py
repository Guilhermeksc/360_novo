from functools import partial
import json
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.config.paths import MSG_LICITACAO_JSON
from src.modules.utils.add_button import add_button_func
import re

class EditableTextField(QTextEdit):
    text_changed_signal = pyqtSignal(str)  # Sinal personalizado para enviar texto atualizado

    def __init__(self, parent=None):
        super().__init__(parent)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        # Emite o sinal com o texto atualizado
        self.text_changed_signal.emit(self.toPlainText())

class MensagensManagerContratos(QWidget):
    def __init__(self, icons, dados):
        super().__init__()
        self.icons = icons
        self.dados = dados
        self.current_button_name = None  # Nome do botão selecionado
        self.init_ui()
        self.load_buttons_from_json()
        
    def init_ui(self):
        # Layout principal
        self.main_layout = QHBoxLayout(self)  # Define diretamente como o layout do widget

        # Layout para os botões à esquerda
        self.msg_layout = QVBoxLayout()
        self.main_layout.addLayout(self.msg_layout)

        # Adiciona um espaço flexível para alinhar os botões
        self.msg_layout.addStretch()

        # Layout para o conteúdo à direita
        self.msg_content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.msg_content_layout)

        # Layout para título e botões de ações
        self.titulo_layout = QHBoxLayout()
        self.msg_label = QLabel("Conteúdo da Mensagem")
        self.titulo_layout.addWidget(self.msg_label)

        add_button_func(
            "Inserir Variável", 
            "brace", 
            self.open_variables_dialog, 
            self.titulo_layout, 
            self.icons, 
            tooltip="Inserir uma variável no campo de edição"
        )

        # Botão de copiar para área de transferência
        add_button_func("Copiar Conteúdo", "copy", self.copy_to_clipboard, self.titulo_layout, self.icons, tooltip="Copiar o texto padronizado para a área de transferência")

        self.msg_content_layout.addLayout(self.titulo_layout)

        # Layout para campos de texto
        self.text_fields_layout = QHBoxLayout()
        
        # Campo de edição de texto
        self.edit_text_field = EditableTextField()
        self.edit_text_field.setPlaceholderText("Edite o texto da mensagem aqui...")
        self.edit_text_field.text_changed_signal.connect(self.save_message_to_json)
        self.text_fields_layout.addWidget(self.edit_text_field)

        # Campo de texto padronizado
        self.standard_text_field = QTextEdit()
        self.standard_text_field.setReadOnly(True)
        self.standard_text_field.setPlaceholderText("Texto padronizado da mensagem...")
        self.text_fields_layout.addWidget(self.standard_text_field)

        self.msg_content_layout.addLayout(self.text_fields_layout)
        
    def open_variables_dialog(self):
        """Abre um diálogo com as variáveis de self.dados e insere a escolhida no campo de edição."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Inserir Variável")
        dialog.setLayout(QVBoxLayout())

        # Configura o diálogo como modeless
        dialog.setWindowModality(Qt.WindowModality.NonModal)
        dialog.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)

        # Adiciona as variáveis e seus valores ao diálogo
        for var, value in self.dados.items():
            # Botão para inserir a variável no campo de edição
            variable_layout = QHBoxLayout()
            insert_button = QPushButton("Inserir")
            insert_button.clicked.connect(lambda _, v=var: self.insert_variable_in_editor(v))
            variable_layout.addWidget(insert_button)

            label = QLabel(f"{var} - {value}")
            variable_layout.addWidget(label)

            dialog.layout().addLayout(variable_layout)

        # Botão de fechar
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(dialog.close)
        dialog.layout().addWidget(close_button)

        dialog.show()  # Exibe o diálogo de forma modeless


    def insert_variable_in_editor(self, variable):
        """Insere a variável no campo de edição na posição atual do cursor e mantém o diálogo aberto."""
        cursor = self.edit_text_field.textCursor()
        cursor.insertText(f"{{{variable}}}")

    def highlight_variables_in_edit_field(self):
        """
        Aplica um destaque laranja às variáveis no texto do `self.edit_text_field`.
        Considera variáveis como strings no formato `{variavel}`.
        """
        # Obtém o texto atual do campo de edição
        text = self.edit_text_field.toPlainText()

        # Regex para identificar as variáveis no formato {variavel}
        variable_pattern = r"\{(.*?)\}"

        # Cria o formato para as variáveis
        format_ = QTextCharFormat()
        format_.setForeground(QColor("orange"))  # Define a cor laranja

        # Usa um QTextCursor para aplicar o formato
        cursor = QTextCursor(self.edit_text_field.document())
        cursor.setPosition(0)  # Inicia no começo do texto

        # Itera sobre as correspondências no texto
        for match in re.finditer(variable_pattern, text):
            start, end = match.span()  # Pega a posição inicial e final da variável
            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, end - start)
            cursor.setCharFormat(format_)  # Aplica o formato    
    
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
        self.msg_label.setText(f"Conteúdo da Mensagem - {button_name}")  # Atualiza o label
        self.edit_text_field.setText(msg)  # Define o texto com placeholders
        self.render_standard_text(msg)  # Renderiza o texto com os valores de dados

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

    def delete_message(self):
        """Permite ao usuário selecionar e excluir uma mensagem do JSON."""
        try:
            # Carrega as mensagens do arquivo JSON
            with open(MSG_LICITACAO_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                QMessageBox.information(self, "Excluir Mensagem", "Não há mensagens para excluir.")
                return

            # Exibe uma lista para o usuário selecionar a mensagem a ser excluída
            nome_botao, ok = QInputDialog.getItem(
                self, 
                "Excluir Mensagem", 
                "Selecione a mensagem para excluir:", 
                list(data.keys()), 
                editable=False
            )
            if not ok or not nome_botao:
                return

            # Remove a mensagem selecionada
            data.pop(nome_botao, None)

            # Salva as alterações no arquivo JSON
            with open(MSG_LICITACAO_JSON, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            print(f"Mensagem '{nome_botao}' excluída com sucesso.")

            # Atualiza os botões na interface
            self.load_buttons_from_json()

        except Exception as e:
            print(f"Erro ao excluir mensagem: {e}")

    def load_buttons_from_json(self):
        """Carrega os botões a partir do JSON atualizado."""
        # Remove todos os widgets, exceto o layout final de botões
        while self.msg_layout.count() > 0:
            widget = self.msg_layout.takeAt(0).widget()
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

        # Recarrega os botões de mensagens no layout
        for nome_botao in data:
            texto_msg = data[nome_botao][0]['texto_msg']
            button = self.create_button(
                text=nome_botao,
                icon_name='mensagem',
                slot=partial(self.load_message, texto_msg, nome_botao),
                tooltip="Clique para carregar a mensagem"
            )
            self.msg_layout.addWidget(button)
        self.msg_layout.addStretch()
        # Adiciona o QHBoxLayout para os botões de adicionar e excluir mensagens
        action_buttons_layout = QHBoxLayout()
        self.msg_layout.addLayout(action_buttons_layout)
        
        # Botão "Adicionar Nova Mensagem"
        add_button_func(
            "Adicionar", 
            "plus", 
            self.add_new_message, 
            action_buttons_layout, 
            self.icons, 
            tooltip="Adicionar uma nova mensagem"
        )

        # Botão "Excluir Mensagem"
        add_button_func(
            "Excluir", 
            "delete", 
            self.delete_message, 
            action_buttons_layout, 
            self.icons, 
            tooltip="Excluir uma mensagem existente"
        )   

    def copy_to_clipboard(self):
        """Copia o texto padronizado para a área de transferência."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.standard_text_field.toPlainText())
        self.show_confirmation_message()

    def show_confirmation_message(self, message="Conteúdo copiado para a área de transferência."):
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
        confirmation_label.setFixedSize(400, 50)
        confirmation_label.move(
            self.width() // 2 - confirmation_label.width() // 2,
            self.height() // 2 - confirmation_label.height() // 2
        )
        confirmation_label.show()

        # Fecha a mensagem automaticamente após 1 segundo
        QTimer.singleShot(700, confirmation_label.close)

    def render_standard_text(self, msg):
        """Renderiza os placeholders no texto usando os valores de self.dados e destaca os valores renderizados."""
        try:
            # Substitui os placeholders no texto com os valores de self.dados
            formatted_text = msg.format(**self.dados)
        except KeyError as e:
            print(f"Erro: Placeholder não encontrado em self.dados: {e}")
            formatted_text = msg  # Mantém o texto original se houver erro

        self.standard_text_field.setText(formatted_text)  # Atualiza o campo renderizado
        self.highlight_rendered_values(formatted_text)  # Aplica o destaque aos valores renderizados
        self.highlight_variables_in_edit_field()

    def highlight_rendered_values(self, text):
        """
        Aplica destaque aos valores renderizados no texto.
        Considera os valores de `self.dados` usados para renderizar o texto.
        """
        # Cria o formato para destacar os valores renderizados
        format_ = QTextCharFormat()
        format_.setForeground(QColor("orange"))  # Define a cor laranja

        # Usa um QTextCursor para aplicar o formato
        cursor = QTextCursor(self.standard_text_field.document())
        cursor.setPosition(0)  # Inicia no começo do texto

        # Itera sobre os valores renderizados de self.dados
        for value in self.dados.values():
            if not isinstance(value, str):
                continue  # Garante que apenas valores de texto serão destacados

            start_pos = 0
            while True:
                # Encontra a posição do valor renderizado no texto
                start_pos = text.find(value, start_pos)
                if start_pos == -1:
                    break

                # Seleciona o texto e aplica o formato
                cursor.setPosition(start_pos)
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(value))
                cursor.setCharFormat(format_)

                start_pos += len(value) 

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

		
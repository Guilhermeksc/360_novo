from functools import partial
import json
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.config.paths import CONTRATOS_JSON
from src.modules.utils.add_button import add_button_func
from pathlib import Path
from datetime import datetime

class ComentariosManagerContratos:
    def __init__(self, icons, dados):
        self.icons = icons
        self.dados = dados
        self.comentarios_json = Path(CONTRATOS_JSON)
        
        # Inicialize a lista de comentários no construtor
        self.lista_comentarios = QListWidget()
        self.comentarios_padronizados_combo = QComboBox()
        self.comentario_edit = QTextEdit()

        # Carrega comentários do JSON
        self.carregar_comentarios()

    def get_comentarios_layout(self):
        """
        Retorna o layout de comentários configurado.
        """
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

        self.comentarios_padronizados_combo.addItems([
            "Selecione um comentário padronizado",
            "Devolvido para correções",
            "Divulgação de IRP",
            "Atendimento de Nota Técnica",
            "Envio para CJACM",
            "Atendimento das Recomendações",
            "Data da Sessão Pública"
        ])
        self.comentarios_padronizados_combo.currentIndexChanged.connect(self.atualizar_comentario_padronizado)
        comentario_label_layout.addWidget(self.comentarios_padronizados_combo)

        comentario_label_layout.addStretch()
        comentario_novo.addLayout(comentario_label_layout)

        comentario_novo.addWidget(self.comentario_edit)

        button_layout = QHBoxLayout()
        add_button_func(
            "Adicionar Comentário",
            "add_comment",
            self.adicionar_comentario,
            button_layout,
            self.icons,
            "Clique para adicionar um novo comentário."
        )
        add_button_func(
            "Excluir Comentário",
            "delete_comment",
            self.excluir_comentario,
            button_layout,
            self.icons,
            "Clique para excluir o comentário selecionado."
        )
        comentario_novo.addLayout(button_layout)

        comentarios_registrados = QVBoxLayout()
        self.lista_comentarios.setFixedWidth(630)
        self.lista_comentarios.itemDoubleClicked.connect(self.editar_comentario)
        comentarios_registrados.addWidget(QLabel("Comentários Registrados:"))
        comentarios_registrados.addWidget(self.lista_comentarios)

        comentarios_layout.addLayout(comentario_novo)
        comentarios_layout.addLayout(comentarios_registrados)

        return comentarios_layout

    def carregar_comentarios(self):
        """Carrega os comentários do JSON."""
        if not self.comentarios_json.exists():
            with open(self.comentarios_json, 'w', encoding='utf-8') as f:
                json.dump({}, f)

        with open(self.comentarios_json, 'r', encoding='utf-8') as f:
            comentarios_data = json.load(f)

        id_processo = self.dados.get("id_processo", "Desconhecido")
        self.lista_comentarios.clear()
        if id_processo in comentarios_data:
            for comentario in comentarios_data[id_processo]:
                self.lista_comentarios.addItem(comentario["comentario"])

    def adicionar_comentario(self):
        """Adiciona um novo comentário."""
        novo_comentario = self.comentario_edit.toPlainText().strip()
        if not novo_comentario:
            QMessageBox.warning(None, "Aviso", "O comentário não pode estar vazio.")
            return

        id_processo = self.dados.get("id_processo", "Desconhecido")
        with open(self.comentarios_json, 'r+', encoding='utf-8') as f:
            comentarios_data = json.load(f)
            if id_processo not in comentarios_data:
                comentarios_data[id_processo] = []
            comentarios_data[id_processo].append({"comentario": novo_comentario})
            f.seek(0)
            json.dump(comentarios_data, f, ensure_ascii=False, indent=4)

        self.comentario_edit.clear()
        self.carregar_comentarios()

    def excluir_comentario(self):
        """Exclui o comentário selecionado."""
        selected_row = self.lista_comentarios.currentRow()
        if selected_row == -1:
            QMessageBox.warning(None, "Aviso", "Nenhum comentário selecionado para exclusão.")
            return

        id_processo = self.dados.get("id_processo", "Desconhecido")
        with open(self.comentarios_json, 'r+', encoding='utf-8') as f:
            comentarios_data = json.load(f)
            if id_processo in comentarios_data:
                comentarios_data[id_processo].pop(selected_row)
                f.seek(0)
                json.dump(comentarios_data, f, ensure_ascii=False, indent=4)

        self.carregar_comentarios()

    def editar_comentario(self, item):
        """Edita o comentário selecionado."""
        texto_anterior = item.text()
        novo_texto, ok = QInputDialog.getText(
            None, "Editar Comentário", "Altere o comentário:",
            QLineEdit.EchoMode.Normal, texto_anterior
        )
        if ok and novo_texto.strip():
            item.setText(novo_texto.strip())
            id_processo = self.dados.get("id_processo", "Desconhecido")
            with open(self.comentarios_json, 'r+', encoding='utf-8') as f:
                comentarios_data = json.load(f)
                for comentario in comentarios_data[id_processo]:
                    if comentario["comentario"] == texto_anterior:
                        comentario["comentario"] = novo_texto.strip()
                        break
                f.seek(0)
                json.dump(comentarios_data, f, ensure_ascii=False, indent=4)
            QMessageBox.information(None, "Sucesso", "Comentário atualizado com sucesso.")

    def atualizar_comentario_padronizado(self):
        """Atualiza o QTextEdit com o comentário padronizado."""
        texto = {
            "Devolvido para correções": "O processo foi devolvido para correções.",
            "Divulgação de IRP": "A IRP foi divulgada.",
            "Atendimento de Nota Técnica": "Nota Técnica atendida.",
            "Envio para CJACM": "O processo foi enviado ao CJACM.",
            "Atendimento das Recomendações": "As recomendações foram atendidas.",
            "Data da Sessão Pública": "A sessão pública foi agendada."
        }.get(self.comentarios_padronizados_combo.currentText(), "")
        self.comentario_edit.setText(texto)
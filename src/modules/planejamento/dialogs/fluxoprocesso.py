#fluoprocesso.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
import json
import re
from src.config.paths import CONTROLE_PRAZOS

class ControlePrazosDialog(QDialog):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("Controle do Planejamento de Licitações")
        self.setup_ui()

    def check_and_create_json(self):
        if not CONTROLE_PRAZOS.exists():
            data = {}
            for row in range(self.model.rowCount()):
                id_processo = self.model.index(row, 1).data()  # Supondo que a coluna 0 seja `id_processo`
                data[id_processo] = []

            # Salva a estrutura inicial no JSON
            with open(CONTROLE_PRAZOS, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

    def populate_widgets_from_json(self):
        # Carrega o JSON
        with open(CONTROLE_PRAZOS, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Popula cada etapa com base no JSON
        for etapa, list_widget in self.etapas.items():
            for id_processo, contadores in data.items():
                for contador in contadores:
                    if contador["situacao"] == etapa:
                        formatted_text = (
                            f"<b>{id_processo}</b><br>"
                            f"Data Inicial: {contador['data_inicial']}<br>"
                            f"Data Final: {contador['data_final']}<br>"
                            f"Dias: {contador['dias_na_etapa']}<br>"
                            f"Comentário: {contador['comentario']}"
                        )
                        list_widget.addFormattedTextItem(id_processo, formatted_text)

    def setup_ui(self):
        self.check_and_create_json()  # Verifica e cria o JSON, se necessário

        layout = QVBoxLayout(self)

        # Label de Título
        title_label = QLabel("Controle do Planejamento de Licitações", self)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        self.etapas = {etapa: CustomListWidget(self) for etapa in CustomListWidget.etapas.keys()}

        self._add_process_stages_to_layout(layout)
        self.populate_widgets_from_json()  # Popula os widgets com dados do JSON

    def update_selected_item(self, current_list_widget, current_item):
        # Remove o efeito do último item selecionado, se existir
        if self.last_selected_item and self.last_selected_list_widget:
            last_widget = self.last_selected_list_widget.itemWidget(self.last_selected_item)
            if last_widget:
                last_widget.setStyleSheet("background-color: white; color: black;")

        # Aplica o efeito ao item atual
        widget = current_list_widget.itemWidget(current_item)
        if widget:
            widget.setStyleSheet("background-color: #8AB4F7; color: black; border: 1px solid #000080;")

        # Atualiza as referências ao item e QListWidget atuais
        self.last_selected_item = current_item
        self.last_selected_list_widget = current_list_widget

    def closeEvent(self, event):
        # Emitir sinal quando o diálogo for fechado
        super().closeEvent(event)

    def _add_process_stages_to_layout(self, layout):
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()
        metade_etapas = len(self.etapas) // 2
        for index, etapa in enumerate(self.etapas.keys()):
            group_box = self._create_group_box(etapa)
            if index < metade_etapas:
                top_layout.addWidget(group_box)
            else:
                bottom_layout.addWidget(group_box)
        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)

    def _create_group_box(self, etapa):
        group_box = QGroupBox(etapa)
        group_box.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        group_box.setStyleSheet("QGroupBox {background-color: #050f41; color: #8AB4F7; border-radius: 10px; } QGroupBox::title { font-weight: bold; font-size: 14px}")
        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(1, 25, 1, 4)
        list_widget = CustomListWidget(parent=self, database_path=self.database_path)
        list_widget.setObjectName(etapa)
        self._populate_list_widget(list_widget)
        list_widget.updateRequired.connect(self.updateRequired.emit)  # Conecta o sinal ao método que emite o sinal do diálogo
        layout.addWidget(list_widget)
        return group_box
    
class CustomListWidget(QListWidget):
    updateRequired = pyqtSignal()
    etapas = {
        'Planejamento': None,
        'Consolidação de Demanda': None,
        'Montagem do Processo': None,
        'Nota Técnica': None,
        'AGU': None,
        'Recomendações AGU': None,
        'Pré-Publicação': None,
        'Sessão Pública': None,
        'Assinatura Contrato': None,
        'Concluído': None
    }

    def __init__(self, parent=None, database_path=None):
        super().__init__(parent)
        self.parent_dialog = self.parent()
        self.database_path = database_path
        self.last_selected_item = None  # Referência ao último item selecionado
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setMinimumSize(QSize(190, 250))
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setStyleSheet("""
            QListWidget {
                background-color: white;
                color: black;  
                border: 2px solid transparent;
                border-radius: 4px;
                           
            }
            QListWidget::item {
                background-color: white;
                color: black;  
            }
            QListWidget::item:selected {
                background-color: white;
                color: black;
            }
        """)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.effect_timer = QTimer(self)
        self.effect_timer.setInterval(100)  # 1 milisegundo
        self.effect_timer.setSingleShot(True)
        self.effect_timer.timeout.connect(self.clearClickEffect)

    def on_config_updated(self, key, path):
        if key == "CONTROLE_PRAZOS":
            self.database_path = path
            print(f"Database path atualizado para: {self.database_path}")

    def showContextMenu(self, position):
        contextMenu = QMenu(self)
        alterar_datas_action = contextMenu.addAction("Alterar Datas")
        gerar_relatorio_action = contextMenu.addAction("Gerar Relatório")
        action = contextMenu.exec(self.mapToGlobal(position))
        
        if action == alterar_datas_action:
            self.alterarDatas()
        elif action == gerar_relatorio_action:
            self.gerarRelatorio()

    def parseDatabaseIdFromItem(self, item):
        # Implemente esta função conforme a necessidade de extrair o ID
        text = item.text()
        try:
            database_id = int(text.split(' ')[0])  # Exemplo de extração do ID
        except ValueError:
            database_id = None
        return database_id

    def addFormattedTextItem(self, id_processo, objeto):
        formattedText = f"<html><head/><body><p style='text-align: center;'><span style='font-weight:600; font-size:14pt;'>{id_processo}</span><br/><span style='font-size:10pt;'>{objeto}</span></p></body></html>"
        item = QListWidgetItem()
        item.setText(formattedText)
        item.setSizeHint(QSize(0, 45))  # Ajuste a altura conforme necessário
        label = QLabel(formattedText)
        label.setStyleSheet("""
            background-color: white;
            color: black;
        """)
        # label.setStyleSheet("background-color: #F8F9FA;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.addItem(item)
        self.setItemWidget(item, label)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        item = self.itemAt(event.position().toPoint())

        if event.button() == Qt.MouseButton.LeftButton:
            if item:
                # Utilize o método do diálogo pai para gerenciar a seleção
                if self.parent_dialog:
                    self.parent_dialog.update_selected_item(self, item)
                self.startDrag(Qt.DropAction.MoveAction)

        elif event.button() == Qt.MouseButton.RightButton:
            if item:
                self.setCurrentItem(item)
                self.effect_timer.start()

    def applyRightClickEffect(self, item):
        widget = self.itemWidget(item)
        if widget:
            widget.setStyleSheet("background-color: yellow, color: navy;")

    def clearClickEffect(self):
        item = self.currentItem()
        if item:
            widget = self.itemWidget(item)
            if widget:
                widget.setStyleSheet("background-color: white; color: black;")

    def applyClickEffect(self, item):
        # Remova o efeito do último item selecionado, se houver
        if self.last_selected_item:
            last_widget = self.itemWidget(self.last_selected_item)
            if last_widget:
                last_widget.setStyleSheet("background-color: white;")  # Estilo original

        # Aplique o efeito ao item atual
        widget = self.itemWidget(item)
        if widget:
            widget.setStyleSheet("background-color: #8AB4F7; border: 1px solid #000080;")

        # Atualize a referência ao último item selecionado
        self.last_selected_item = item

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            currentWidget = self.itemWidget(item)
            if currentWidget:
                mimeData = QMimeData()
                itemData = {
                    "formattedText": item.text(),  # ou outra propriedade que deseje transmitir
                    "objeto": currentWidget.text(),
                    "origin": self.objectName()
                }
                mimeData.setText(json.dumps(itemData))

                drag = QDrag(self)
                pixmap = QPixmap(currentWidget.size())
                currentWidget.render(pixmap)
                drag.setMimeData(mimeData)
                drag.setPixmap(pixmap)
                drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
                drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            itemData = json.loads(event.mimeData().text())
            formattedText = itemData["formattedText"]  # O texto HTML completo
            id_processo = extrair_id_processo(formattedText)  # Extrai id_processo do HTML
            objeto = extrair_objeto(formattedText)  # Extrair objeto do HTML, implementar esta função similarmente

            origin = itemData["origin"]
            nova_etapa = self.objectName()

            if origin != nova_etapa:
                self.addFormattedTextItem(id_processo, objeto)  # Usa id_processo e objeto extraídos
                event.source().takeItem(event.source().currentRow())  # Remove o item da lista original
                etapa_manager = EtapaManager(str(CONTROLE_PRAZOS))
                etapa_manager.registrar_etapa(id_processo, nova_etapa, "Comentário opcional")
                self.updateRequired.emit()
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

class EtapaManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def registrar_etapa(self, id_processo, nova_etapa, comentario):
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Arquivo {self.db_path} não encontrado.")

        with open(self.db_path, "r+", encoding="utf-8") as file:
            data = json.load(file)

            if id_processo not in data:
                data[id_processo] = []

            # Adiciona uma nova entrada para a etapa
            data[id_processo].append({
                "situacao": nova_etapa,
                "data_inicial": "2024-01-01",  # Ajustar para datas reais
                "data_final": "2024-01-10",    # Ajustar para datas reais
                "dias_na_etapa": 10,
                "comentario": comentario
            })

            # Salva de volta no arquivo
            file.seek(0)
            json.dump(data, file, indent=4, ensure_ascii=False)
            file.truncate()


def extrair_id_processo(texto_html):
    # Usa expressão regular para extrair o texto dentro do primeiro <span> após <p>
    match = re.search(r"<p[^>]*><span[^>]*>(.*?)</span>", texto_html)
    if match:
        return match.group(1)
    return None

def extrair_objeto(texto_html):
    # Extrai o texto do objeto, que aparece após a id_processo no HTML
    match = re.search(r"<br/><span[^>]*>(.*?)</span></p>", texto_html)
    if match:
        return match.group(1)
    return None

def parse_id_processo(id_processo):
    """
    Espera uma string no formato '{mod} {num_pregao}/{ano_pregao}' e retorna uma tupla (ano_pregao, num_pregao)
    para ordenação.
    """
    try:
        parts = id_processo.split(' ')[-1]  # Pega a parte '{num_pregao}/{ano_pregao}'
        num_pregao, ano_pregao = parts.split('/')
        return (int(ano_pregao), int(num_pregao))  # Retorna uma tupla para ordenação
    except (IndexError, ValueError):
        return (0, 0)  # Em caso de falha na parse, retorna uma tupla que coloca este item no início

class CustomCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setStyleSheet("""
            QCalendarWidget QAbstractItemView {
                selection-background-color: yellow;
                selection-color: black;
            }
        """)

def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
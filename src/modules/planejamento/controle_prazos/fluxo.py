#fluoprocesso.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
import json
import re
from src.config.paths import CONTROLE_PRAZOS
from datetime import datetime
class ControlePrazosDialog(QDialog):
    def __init__(self, model, icons, select_year, parent=None):
        super().__init__(parent)
        self.model = model
        self.icons = icons
        self.select_year = select_year
        self.last_selected_item = None
        self.last_selected_list_widget = None
        self.setWindowTitle("Controle do Planejamento de Licitações")

        self.setup_ui()  # Garante que o arquivo JSON é criado

        self.sync_json_with_model() 
        # Inicializa EtapaManager após garantir que o JSON existe
        self.etapa_manager = EtapaManager(CONTROLE_PRAZOS)
        self.etapa_manager.atualizar_dados()

    def sync_json_with_model(self):
        """Sincroniza o arquivo JSON com o modelo:
        - Remove id_processo do JSON que não estão no modelo.
        - Adiciona novos id_processo do modelo ao JSON.
        """
        # Carrega os dados existentes do JSON
        with open(CONTROLE_PRAZOS, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Obter conjunto de id_processo do modelo
        id_processo_in_model = set()
        for row in range(self.model.rowCount()):
            id_processo = self.model.index(row, 1).data()
            id_processo_in_model.add(id_processo)

        # Obter conjunto de id_processo do JSON
        id_processo_in_json = set(data.keys())

        # Identificar id_processo a serem adicionados ao JSON
        new_id_processo = id_processo_in_model - id_processo_in_json
        for id_processo in new_id_processo:
            print(f"Adicionando novo id_processo '{id_processo}' ao arquivo JSON")  # Depuração
            data[id_processo] = [
                {
                    "situacao": "Planejamento",
                    "data_inicial": datetime.now().strftime("%Y-%m-%d"),
                    "data_final": "",
                    "dias_na_etapa": 0,
                    "comentario": ""
                }
            ]

        # Salva os dados atualizados de volta no arquivo JSON
        with open(CONTROLE_PRAZOS, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def check_and_create_json(self):
        """Cria o JSON inicial se não existir."""
        if not CONTROLE_PRAZOS.exists():
            print(f"Criando arquivo JSON em {CONTROLE_PRAZOS}")  # Depuração
            data = {}
            for row in range(self.model.rowCount()):
                id_processo = self.model.index(row, 1).data()
                data[id_processo] = [
                    {
                        "situacao": "Planejamento",
                        "data_inicial": datetime.now().strftime("%Y-%m-%d"),
                        "data_final": "",
                        "dias_na_etapa": 0,
                        "comentario": ""
                    }
                ]

            # Certifica-se de que o diretório existe
            CONTROLE_PRAZOS.parent.mkdir(parents=True, exist_ok=True)

            with open(CONTROLE_PRAZOS, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        else:
            print(f"Arquivo JSON já existe em {CONTROLE_PRAZOS}")  # Depuração

    def populate_widgets_from_json(self, selected_year):
        """
        Popula os widgets com os dados do JSON filtrados pelo ano selecionado.
        """
        print(f"Populando widgets para o ano {selected_year}...")

        with open(CONTROLE_PRAZOS, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Limpa os widgets antes de preencher novamente
        for etapa, list_widget in self.etapas.items():
            list_widget.clear()

        for id_processo, contadores in data.items():
            if contadores:  # Verifica se há etapas registradas
                ultima_etapa = contadores[-1]
                situacao = ultima_etapa["situacao"]

                # Obtém o objeto e verifica se pertence ao ano selecionado
                objeto = self._get_objeto_by_id_processo(id_processo)
                ano = self._get_ano_by_id_processo(id_processo)

                if ano == selected_year:  # Filtra pelo ano selecionado
                    # Adiciona o item apenas no widget correspondente à última etapa
                    if situacao in self.etapas:
                        print(f"Adicionando '{id_processo}' na etapa '{situacao}'")
                        self.etapas[situacao].addFormattedTextItem(id_processo, objeto)
                    else:
                        print(f"Erro: Etapa '{situacao}' não encontrada para '{id_processo}'")

    def _get_ano_by_id_processo(self, id_processo):
        """
        Obtém o valor do ano no modelo baseado no id_processo.
        """
        for row in range(self.model.rowCount()):
            if self.model.index(row, 1).data() == id_processo:  # Considera que a coluna 1 é 'id_processo'
                return self.model.index(row, self.model.fieldIndex("ano")).data()
        return None

    def _get_objeto_by_id_processo(self, id_processo):
        """Busca o valor de `objeto` no modelo baseado no `id_processo`."""
        for row in range(self.model.rowCount()):
            if self.model.index(row, 1).data() == id_processo:
                return self.model.index(row, 7).data()
        return "Objeto não encontrado"

    def _add_process_stages_to_layout(self, layout):
        row_layout = QHBoxLayout()  # Cria um layout horizontal para cada linha
        count = 0  # Contador para rastrear o número de widgets adicionados na linha atual

        for etapa in self.etapas.keys():
            group_box = self._create_group_box(etapa)
            row_layout.addWidget(group_box)
            count += 1

            # Quando atingir 6 widgets na linha, adiciona o layout atual ao layout principal e cria uma nova linha
            if count == 6:
                layout.addLayout(row_layout)
                row_layout = QHBoxLayout()
                count = 0

        # Adiciona a última linha se houver widgets restantes
        if count > 0:
            layout.addLayout(row_layout)

    def setup_ui(self):
        """Configura a interface do diálogo."""
        self.check_and_create_json()
        layout = QVBoxLayout(self)
        # Garante que self.etapas seja um dicionário limpo
        self.etapas = {}
        
        # Cria os widgets de etapas
        etapas_keys = list(CustomListWidget.etapas.keys())
        for etapa in etapas_keys:
            self.etapas[etapa] = CustomListWidget(self)

        self._add_process_stages_to_layout(layout)
        self.populate_widgets_from_json(self.select_year)

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
        
    def _create_group_box(self, etapa):
        group_box = QGroupBox(etapa)
        group_box.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        group_box.setStyleSheet("""
            QGroupBox {
                background-color: #181928;
                color: #8AB4F7;
                border: 1px solid #8AB4F7;
                border-radius: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                font-weight: bold;
                font-size: 14px;
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
            }
        """)

        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(5, 10, 5, 5)

        # Mapeia a etapa ao ícone correspondente
        icon_key = {
            'Planejamento': 'priority',
            'Consolidação de Demanda': 'jigsaw',
            'Montagem do Processo': 'montagem',
            'Nota Técnica': 'deal',
            'Atendimento da NT': 'alert',
            'AGU': 'agu',
            'Assinatura Contrato': 'sign',
            'Recomendações AGU': 'report',
            'Pré-Publicação': 'loading_table',
            'Sessão Pública': 'session',
            'Concluído': 'aproved',
            'Arquivado': 'archive',
        }.get(etapa)

        # Adiciona o ícone ao layout se existir
        if icon_key and icon_key in self.icons:
            icon = self.icons[icon_key]
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(40, 40))  # Tamanho do ícone ajustável
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)

        list_widget = CustomListWidget(parent=self)
        list_widget.setStyleSheet("""
            QListWidget {
                background-color: white;
            }
        """)
        list_widget.setObjectName(etapa)  # Configura o nome do widget como a etapa
        layout.addWidget(list_widget)

        self.etapas[etapa] = list_widget
        return group_box
    
class CustomListWidget(QListWidget):
    updateRequired = pyqtSignal()
    etapas = {
        'Planejamento': None,
        'Consolidação de Demanda': None,
        'Montagem do Processo': None,
        'Nota Técnica': None,
        'Atendimento da NT': None,
        'AGU': None,
        'Recomendações AGU': None,
        'Pré-Publicação': None,
        'Sessão Pública': None,
        'Assinatura Contrato': None,
        'Concluído': None,
        'Arquivado': None
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_dialog = self.parent()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setMinimumSize(QSize(170, 250))
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.effect_timer = QTimer(self)
        self.effect_timer.setInterval(10)  # 1 milisegundo
        self.effect_timer.setSingleShot(True)
        self.effect_timer.timeout.connect(self.clearClickEffect)
        
    def addFormattedTextItem(self, id_processo, objeto):
        print(f"Formatando item: id_processo = {id_processo}, objeto = {objeto}")
        formattedText = (
            f"<html><head/><body>"
            f"<p style='text-align: center;'>"
            f"<span style='font-weight:600; font-size:14pt;'>{id_processo}</span><br/>"
            f"<span style='font-size:10pt;'>{objeto}</span>"
            f"</p></body></html>"
        )
        item = QListWidgetItem()
        item.setText(formattedText)
        item.setSizeHint(QSize(0, 45))  # Ajuste a altura conforme necessário
        label = QLabel(formattedText)
        label.setStyleSheet("""
            background-color: white;
            color: black;
        """)
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
                # Extrai id_processo e objeto do texto formatado
                id_processo = extrair_id_processo(item.text())
                objeto = extrair_objeto(item.text())

                mimeData = QMimeData()
                itemData = {
                    "id_processo": id_processo,
                    "objeto": objeto,  # Inclui o objeto
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
            id_processo = itemData["id_processo"]
            objeto = itemData["objeto"]
            nova_etapa = self.objectName()

            print(f"Tentando transferir item '{id_processo}' para a etapa: '{nova_etapa}'")  # Depuração

            # Verifica se a etapa atual é a mesma
            etapa_manager = EtapaManager(str(CONTROLE_PRAZOS))
            etapa_atual = etapa_manager.get_ultima_etapa(id_processo)

            if etapa_atual == nova_etapa:
                print(f"Item '{id_processo}' já está na etapa '{nova_etapa}'. Nenhuma alteração necessária.")
                event.ignore()  # Ignora o evento
                return

            print(f"Transferindo item '{id_processo}' para a nova etapa '{nova_etapa}'")  # Depuração
            etapa_manager.registrar_transicao(id_processo, nova_etapa)

            self.addFormattedTextItem(id_processo, objeto)
            event.source().takeItem(event.source().currentRow())
            self.updateRequired.emit()
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            print("Drop ignorado - nenhum texto no evento.")
            event.ignore()



class EtapaManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_ultima_etapa(self, id_processo):
        """Obtém a última etapa registrada para o processo."""
        if not Path(self.db_path).exists():
            print(f"Arquivo JSON '{self.db_path}' não encontrado.")
            return None

        with open(self.db_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if id_processo in data and data[id_processo]:
            ultima_etapa = data[id_processo][-1]["situacao"]
            print(f"Última etapa de '{id_processo}' é '{ultima_etapa}'")  # Depuração
            return ultima_etapa

        print(f"Processo '{id_processo}' não encontrado no JSON ou sem etapas.")
        return None
    
    def registrar_transicao(self, id_processo, nova_etapa):
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Arquivo {self.db_path} não encontrado.")

        print(f"Registrando transição para o processo '{id_processo}' na etapa '{nova_etapa}'.")  # Depuração

        with open(self.db_path, "r+", encoding="utf-8") as file:
            data = json.load(file)

            if id_processo not in data:
                print(f"Erro: Processo '{id_processo}' não encontrado no JSON.")
                return

            etapas = data[id_processo]

            # Atualiza a última etapa
            if etapas:
                ultima_etapa = etapas[-1]
                ultima_etapa["data_final"] = QDate.currentDate().toString("yyyy-MM-dd")
                ultima_etapa["dias_na_etapa"] = (
                    QDate.fromString(ultima_etapa["data_final"], "yyyy-MM-dd")
                    .daysTo(QDate.fromString(ultima_etapa["data_inicial"], "yyyy-MM-dd"))
                )

            nova_data_inicial = (
                etapas[-1]["data_final"] if etapas else QDate.currentDate().toString("yyyy-MM-dd")
            )
            nova_etapa_data = {
                "situacao": nova_etapa,
                "data_inicial": nova_data_inicial,
                "data_final": "",
                "dias_na_etapa": 0,
                "comentario": "",
            }
            etapas.append(nova_etapa_data)
            data[id_processo] = etapas

            print(f"Nova etapa registrada: {nova_etapa_data}")  # Depuração

            file.seek(0)
            json.dump(data, file, indent=4, ensure_ascii=False)
            file.truncate()


    def atualizar_dados(self):
        """Atualiza datas e contagem de dias no JSON."""
        if not Path(self.db_path).exists():
            print(f"Arquivo {self.db_path} não encontrado. Criando um novo arquivo.")
            with open(self.db_path, "w", encoding="utf-8") as file:
                json.dump({}, file, indent=4, ensure_ascii=False)
            return  # Retorna, pois não há dados para atualizar

        with open(self.db_path, "r+", encoding="utf-8") as file:
            data = json.load(file)

            for id_processo, etapas in data.items():
                for i, etapa in enumerate(etapas):
                    # Atualiza `dias_na_etapa`
                    if etapa["data_inicial"] and etapa["data_final"]:
                        data_inicial = datetime.strptime(etapa["data_inicial"], "%Y-%m-%d")
                        data_final = datetime.strptime(etapa["data_final"], "%Y-%m-%d")
                        etapa["dias_na_etapa"] = (data_final - data_inicial).days
                    else:
                        etapa["dias_na_etapa"] = 0

                    # Atualiza a última etapa para a data atual
                    if i == len(etapas) - 1:
                        etapa["data_final"] = datetime.now().strftime("%Y-%m-%d")

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
    # Usa expressão regular para extrair o texto dentro do segundo <span>
    match = re.search(r"<br/><span[^>]*>(.*?)</span></p>", texto_html)
    if match:
        return match.group(1)
    return "Objeto não encontrado"
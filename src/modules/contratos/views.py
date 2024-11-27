from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from src.modules.utils.search_bar import setup_search_bar, MultiColumnFilterProxyModel
from src.modules.utils.add_button import add_button, add_button_func
import pandas as pd

class ContratosView(QMainWindow):
    # Sinais para comunicação com o controlador
    dataManager = pyqtSignal()
    pauloVitor = pyqtSignal()
    loadData = pyqtSignal(str)
    rowDoubleClicked = pyqtSignal(dict)
    request_consulta_api = pyqtSignal(str, str, str, str, str)
    
    def __init__(self, icons, model, database_path, parent=None):
        super().__init__(parent)
        self.icons = icons
        self.model = model
        self.database_path = database_path
        self.selected_row_data = None
        
        # Inicializa o proxy_model e configura o filtro
        self.proxy_model = MultiColumnFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # Configura a interface de usuário
        self.setup_ui()

    def setup_ui(self):
        # Cria o widget principal e layout principal
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        label_dispensa = QLabel("Controle de Vigência dos Contratos", self)
        label_dispensa.setStyleSheet("font-size: 20px; font-weight: bold; color: #4E648B")
        self.main_layout.addWidget(label_dispensa)
        
        # Layout para a barra de ferramentas
        top_layout = QHBoxLayout()
        self.search_bar = setup_search_bar(self.icons, top_layout, self.proxy_model)
        self.setup_buttons(top_layout)
        self.main_layout.addLayout(top_layout)
        
        self.setup_table_view()
        self.configure_table_model()
        self.adjust_columns()

    def connect_editar_dados_window(self, editar_dados_window):
        # Conecta o sinal do EditarDadosWindow ao próprio widget
        editar_dados_window.request_consulta_api.connect(self.request_consulta_api.emit)
        
    def on_table_double_click(self, index):
        row = self.proxy_model.mapToSource(index).row()
        id_processo = self.model.index(row, self.model.fieldIndex("id_processo")).data()

        # Carrega os dados e redefine `selected_row_data` a cada clique duplo
        self.selected_row_data = self.carregar_dados_por_id(id_processo)
        print (self.selected_row_data)
        print (id_processo)
        if self.selected_row_data:
            self.rowDoubleClicked.emit(self.selected_row_data)
        else:
            QMessageBox.warning(self, "Erro", "Falha ao carregar dados para o ID do processo selecionado.")

    def carregar_dados_por_id(self, id_processo):
        """Carrega os dados da linha selecionada a partir do banco de dados usando `id_processo`."""
        query = f"SELECT * FROM controle_contratos WHERE id_processo = '{id_processo}'"
        try:
            # Obtenha os dados do banco de dados
            dados = self.model.database_licitacao_manager.fetch_all(query)
            
            # Converte para DataFrame caso dados seja uma lista
            if isinstance(dados, list):
                dados = pd.DataFrame(dados, columns=self.model.column_names)  # Substitua `self.model.column_names` pela lista de nomes de colunas correta
            
            # Verifica se o DataFrame não está vazio
            return dados.iloc[0].to_dict() if not dados.empty else None
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return None
        
    def setup_buttons(self, layout):
        add_button("Mensagem", "mensagem", self.pauloVitor, layout, self.icons, tooltip="Teste paulo vitor" )
        add_button("Comunicação Padronizada", "mensagem", self.pauloVitor, layout, self.icons, tooltip="Teste paulo vitor" )
        add_button("Abrir Tabela", "excel", self.pauloVitor, layout, self.icons, tooltip="Adicionar um novo item")
        add_button("Controle Vigência", "time", self.pauloVitor, layout, self.icons, tooltip="Adicionar um novo item")
        # add_button("Excluir", "delete", self.deleteItem, layout, self.icons, tooltip="Excluir o item selecionado")
        # add_button("Database", "data-server", self.dataManager, layout, self.icons, tooltip="Salva o dataframe em um arquivo Excel")

    def refresh_model(self):
        """Atualiza a tabela com os dados mais recentes do banco de dados."""
        self.model.select()

    def setup_table_view(self):
        self.table_view = QTableView(self)
        self.table_view.setModel(self.proxy_model)  # Usa o proxy_model corretamente
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.doubleClicked.connect(self.on_table_double_click)
        
        # Configuração do comportamento de seleção
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        # Aplica o ColorDelegate na coluna 'prorrogável' (índice 2)
        self.table_view.setItemDelegateForColumn(2, ColorDelegate(self.table_view))
        self.table_view.setItemDelegateForColumn(1, ColorDelegate(self.table_view))

        self.table_view.setStyleSheet("""
            QTableView {
                font-size: 14px;
                padding: 4px;
                border: 1px solid #8AB4F7;
                border-radius: 6px;
                gridline-color: #3C3C5A;
            }
        """)

        # Define CenterAlignDelegate para centralizar o conteúdo em todas as colunas
        center_delegate = CenterAlignDelegate(self.table_view)
        for column in range(self.model.columnCount()):
            self.table_view.setItemDelegateForColumn(column, center_delegate)

        # Aplica CustomItemDelegate à coluna "situação" para exibir ícones
        situacao_index = self.model.fieldIndex('Status')
        self.table_view.setItemDelegateForColumn(situacao_index, CustomItemDelegate(self.icons, self.table_view, self.model))

        self.main_layout.addWidget(self.table_view)

    def configure_table_model(self):
        self.proxy_model.setSortRole(Qt.ItemDataRole.UserRole)
        self.update_column_headers()
        self.hide_unwanted_columns()

    def update_column_headers(self):
        titles = {0: "Status", 1: "Dias", 2: "Renova?", 3: "Sigla", 4: "Contrato/Ata", 5: "Tipo", 6: "Processo", 7: "Fornecedor", 9: "Valor"}
        for column, title in titles.items():
            self.model.setHeaderData(column, Qt.Orientation.Horizontal, title)

    def hide_unwanted_columns(self):
        visible_columns = {0, 1, 2, 3, 4, 5, 7, 9}
        for column in range(self.model.columnCount()):
            if column not in visible_columns:
                self.table_view.hideColumn(column)

    def adjust_columns(self):
        # Ajustar automaticamente as larguras das colunas ao conteúdo
        self.table_view.resizeColumnsToContents()
        QTimer.singleShot(1, self.apply_custom_column_sizes) 

    def apply_custom_column_sizes(self):
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed) # Status
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed) # Dias
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed) # Renova?
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed) # Sigla
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed) # Contrato/Ata
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed) # Tipo
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed) # Processo
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch) # Fornecedor
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed) # Valor

        header.resizeSection(0, 140)        
        header.resizeSection(1, 65)
        header.resizeSection(2, 60)
        header.resizeSection(3, 80)
        header.resizeSection(4, 100)
        header.resizeSection(5, 100)
        header.resizeSection(6, 80)
        header.resizeSection(9, 120)

class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

class ColorDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        value = index.data(Qt.ItemDataRole.DisplayRole)

        # Configura o estilo para as colunas específicas
        painter.save()
        if index.column() == 2:  # Coluna 'prorrogável'
            if value == "Sim":
                painter.fillRect(option.rect, QColor("lightgreen"))
                painter.setPen(QColor("lightgreen"))
            elif value == "Não":
                painter.fillRect(option.rect, QColor("lightcoral"))
                painter.setPen(QColor("lightcoral"))
            else:
                painter.setPen(option.palette.color(QPalette.ColorRole.Text))

        elif index.column() == 1:  # Coluna 'dias'
            if value is not None and isinstance(value, int):
                # Define a cor com base no valor de dias
                if value < 30:
                    color = QColor(255, 0, 0)  # Vermelho
                elif 30 <= value <= 90:
                    color = QColor(255, 165, 0)  # Laranja
                elif 91 <= value <= 159:
                    color = QColor(255, 255, 0)  # Amarelo
                else:
                    color = QColor(0, 255, 0)  # Verde
                
                # Cria um degradê com tons suaves
                gradient = QLinearGradient(option.rect.topLeft(), option.rect.bottomRight())
                gradient.setColorAt(0, QColor(255, 255, 255))  # Branco
                gradient.setColorAt(1, color)
                painter.fillRect(option.rect, gradient)

                painter.setPen(option.palette.color(QPalette.ColorRole.Text))

        # Desenha o texto
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, str(value) if value is not None else "")
        painter.restore()


class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, icons, parent=None, model=None):
        super().__init__(parent)
        self.icons = icons
        self.model = model

    def paint(self, painter, option, index):
        # Verifica se estamos na coluna de status
        if index.column() == self.model.fieldIndex('status'):
            status = index.data(Qt.ItemDataRole.DisplayRole)
            
            # Define o mapeamento de ícones
            icon_key = {
                'Seção de Contratos': 'business',
                'Aprovado': 'check-circle',
                'Pendente': 'alert-circle',
                'Concluído': 'check',
            }.get(status)

            # Configura cor do texto com base no status
            color_map = {
                'Seção de Contratos': QColor("green"),
                'Pendente': QColor("orange"),
                'Concluído': QColor("blue"),
                'Rejeitado': QColor("red"),
            }
            text_color = color_map.get(status, option.palette.color(QPalette.ColorRole.Text))

            # Desenha o ícone, se disponível
            if icon_key and icon_key in self.icons:
                icon = self.icons[icon_key]
                icon_size = 24
                icon_rect = QRect(option.rect.left() + 5,
                                  option.rect.top() + (option.rect.height() - icon_size) // 2,
                                  icon_size, icon_size)
                painter.drawPixmap(icon_rect, icon.pixmap(icon_size, icon_size))

                # Ajusta o retângulo de texto para não sobrepor o ícone
                text_rect = QRect(icon_rect.right() + 5, option.rect.top(),
                                  option.rect.width() - icon_size - 10, option.rect.height())
            else:
                # Usa o espaço completo se não houver ícone
                text_rect = option.rect

            # Configura o pincel para o texto
            painter.setPen(text_color)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, status)

        else:
            # Desenha normalmente nas outras colunas
            super().paint(painter, option, index)

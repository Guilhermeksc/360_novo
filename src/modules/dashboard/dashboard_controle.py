# dashboard_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea
from PyQt6.QtGui import QFont, QPainter, QIcon, QBrush, QColor
from PyQt6.QtCore import Qt, QSize, QRectF, QMargins
import sqlite3
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice

from src.config.paths import DATA_LICITACAO_PATH, DATA_DISPENSA_ELETRONICA_PATH
from src.modules.utils.linha_layout import linha_divisoria_layout

class DashboardWidget(QWidget):
    def __init__(self, icons):
        super().__init__()
        self.icons = icons  # Recebe o dicionário de ícones
        self.setup_ui()

class DashboardWidget(QWidget):
    def __init__(self, icons):
        super().__init__()
        self.icons = icons  # Recebe o dicionário de ícones
        self.setup_ui()

    def setup_ui(self):
        # Widget principal que conterá todo o layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Configura o ícone e o título do dashboard
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dash_icon_button = QPushButton()
        dash_icon_button.setIcon(self.icons["dash_titulo"])
        dash_icon_button.setIconSize(QSize(40, 40))
        dash_icon_button.setFlat(True)
        title_layout.addWidget(dash_icon_button)

        title_label = QLabel("Dashboard de Contratações em construção")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_layout.addWidget(title_label)

        main_layout.addLayout(title_layout)

        # # Cria o layout vertical para a seção de licitações
        # licitacao_layout = QVBoxLayout()

        # licitacao_label = QLabel("Licitação")
        # licitacao_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        # licitacao_layout.addWidget(licitacao_label)

        # # Cria o layout horizontal para os gráficos
        # charts_layout = QHBoxLayout()
        # charts_layout.setSpacing(10)
        # charts_layout.setContentsMargins(0, 0, 0, 0)

        # # Gráfico com o tamanho máximo padrão de 400x300
        # material_servico_widget = self.create_pie_chart(
        #     DATA_LICITACAO_PATH,
        #     'material_servico',
        #     'controle_licitacao',
        #     'Distribuição de Material/Serviço'
        # )

        # # Gráfico com tamanho máximo personalizado de 500x400
        # situacao_widget = self.create_pie_chart(
        #     DATA_LICITACAO_PATH,
        #     'situacao',
        #     'controle_licitacao',
        #     'Distribuição de Situação',
        #     max_width=600,
        #     max_height=300
        # )
        # # Adiciona os gráficos ao layout horizontal
        # charts_layout.addWidget(material_servico_widget)
        # charts_layout.addWidget(situacao_widget)
        # licitacao_layout.addLayout(charts_layout)

        # # Adiciona o layout de licitação ao layout principal
        # main_layout.addLayout(licitacao_layout)

        # linha_divisoria, spacer_baixo_linha = linha_divisoria_layout()
        # main_layout.addWidget(linha_divisoria)
        # main_layout.addSpacerItem(spacer_baixo_linha)

        # dispensa_layout = QVBoxLayout()
        # dispensa_label = QLabel("Dispensa Eletrônica")
        # dispensa_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        # dispensa_layout.addWidget(dispensa_label)

        # # Cria o layout horizontal para os gráficos
        # charts_dispensa_layout = QHBoxLayout()
        # charts_dispensa_layout.setSpacing(10)
        # charts_dispensa_layout.setContentsMargins(0, 0, 0, 0)

        # # Gráfico com o tamanho máximo padrão de 400x300
        # material_servico_dispensa_widget = self.create_pie_chart(
        #     DATA_DISPENSA_ELETRONICA_PATH,
        #     'material_servico',
        #     'controle_dispensas',
        #     'Distribuição de Material/Serviço'
        # )

        # # Gráfico com tamanho máximo personalizado de 600x300
        # situacao_dispensa_widget = self.create_pie_chart(
        #     DATA_DISPENSA_ELETRONICA_PATH,
        #     'situacao',
        #     'controle_dispensas',
        #     'Distribuição de Situação',
        #     max_width=600,
        #     max_height=300
        # )
        # # Adiciona os gráficos ao layout horizontal
        # charts_dispensa_layout.addWidget(material_servico_dispensa_widget)
        # charts_dispensa_layout.addWidget(situacao_dispensa_widget)
        # dispensa_layout.addLayout(charts_dispensa_layout)

        # # Adiciona o layout de dispensa ao layout principal
        # main_layout.addLayout(dispensa_layout)

        # linha_divisoria, spacer_baixo_linha = linha_divisoria_layout()
        # main_layout.addWidget(linha_divisoria)
        # main_layout.addSpacerItem(spacer_baixo_linha)

        # contratos_layout = QVBoxLayout()
        # contratos_label = QLabel("Contratos")
        # contratos_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        # contratos_layout.addWidget(contratos_label)

        # # Cria o layout horizontal para os gráficos
        # charts_contratos_layout = QHBoxLayout()
        # charts_contratos_layout.setSpacing(10)
        # charts_contratos_layout.setContentsMargins(0, 0, 0, 0)

        # # Gráfico com o tamanho máximo padrão de 400x300
        # material_servico_contratos_widget = self.create_pie_chart(
        #     DATA_DISPENSA_ELETRONICA_PATH,
        #     'material_servico',
        #     'controle_dispensas',
        #     'Distribuição de Material/Serviço'
        # )

        # # Gráfico com tamanho máximo personalizado de 600x300
        # situacao_contratos_widget = self.create_pie_chart(
        #     DATA_DISPENSA_ELETRONICA_PATH,
        #     'situacao',
        #     'controle_dispensas',
        #     'Distribuição de Situação',
        #     max_width=600,
        #     max_height=300
        # )
        # # Adiciona os gráficos ao layout horizontal
        # charts_contratos_layout.addWidget(material_servico_contratos_widget)
        # charts_contratos_layout.addWidget(situacao_contratos_widget)
        # contratos_layout.addLayout(charts_contratos_layout)

        # # Adiciona o layout de dispensa ao layout principal
        # main_layout.addLayout(contratos_layout)

        # # Adiciona um QScrollArea para rolagem
        # scroll_area = QScrollArea(self)
        # scroll_area.setWidget(central_widget)
        # scroll_area.setWidgetResizable(True)
        # scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Somente barra vertical
        # scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # # Define o layout do widget principal para incluir a barra de rolagem
        # layout_with_scroll = QVBoxLayout(self)
        # layout_with_scroll.addWidget(scroll_area)
        # self.setLayout(layout_with_scroll)

    def create_pie_chart(self, db_path, column_name, table_name, chart_title, max_width=400, max_height=300):
        # Conecta ao banco de dados SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Executa a consulta para obter os dados
        query = f"SELECT {column_name}, COUNT(*) FROM {table_name} GROUP BY {column_name}"
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()

        # Cria a série de dados para o gráfico de pizza
        series = QPieSeries()
        for value, count in data:
            label = str(value) if value is not None else 'N/A'
            slice_label = f"{count} {label}"
            pie_slice = series.append(slice_label, count)

            # Ajusta a posição e visibilidade do rótulo
            pie_slice.setLabelVisible(True)
            pie_slice.setLabelPosition(QPieSlice.LabelPosition.LabelOutside)
            pie_slice.setLabelArmLengthFactor(0.1)

            # Define a cor da fonte do rótulo para branco
            pie_slice.setLabelBrush(QBrush(Qt.GlobalColor.white))

            # Opcional: Destaca a fatia ao passar o mouse
            pie_slice.setExploded(False)
            pie_slice.hovered.connect(lambda hovered, s=pie_slice: s.setExploded(hovered))

        # Cria o gráfico e adiciona a série de dados
        chart = QChart()
        chart.addSeries(series)
        chart.legend().setVisible(False)

        # Personaliza o título do gráfico
        title_font = QFont("Arial", 14)

        # Torna o fundo do gráfico transparente
        chart.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        chart.setBackgroundVisible(False)
        chart.setPlotAreaBackgroundVisible(False)

        # Remove as margens do gráfico
        chart.setMargins(QMargins(0, 0, 0, 0))

        # Ajusta o tamanho da área de plotagem para ocupar mais espaço
        chart_layout = chart.layout()
        chart_layout.setContentsMargins(0, 0, 0, 0)
        # chart_layout.setSpacing(0)

        # Cria o QChartView para exibir o gráfico
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setStyleSheet("background: transparent")
        chart_view.setContentsMargins(0, 0, 0, 0)

        # Cria um widget para conter o título e o gráfico
        chart_widget = QWidget()
        widget_layout = QVBoxLayout(chart_widget)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(0)

        # Cria um QLabel para o título
        title_label = QLabel(chart_title)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: lightgray;")

        # Define tamanhos mínimos e máximos para o gráfico
        chart_widget.setMaximumSize(max_width, max_height) 
        chart_widget.setMinimumHeight(300)
        # Adiciona o título e o gráfico ao layout do widget
        widget_layout.addWidget(title_label)
        widget_layout.addWidget(chart_view)

        return chart_widget
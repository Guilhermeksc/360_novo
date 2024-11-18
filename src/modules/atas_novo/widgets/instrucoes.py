from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from src.modules.utils.linha_layout import linha_divisoria_layout, linha_divisoria_sem_spacer_layout
class InstructionWidget(QWidget):
    def __init__(self, icons, parent=None):
        super().__init__(parent)

        self.icons = icons

        # Configuração do layout principal
        layout = QVBoxLayout(self)

        # Adicionar parágrafos
        layout.addLayout(self.create_paragraph(
            "Primeiro passo (Importar os dados do Termo de Referência)",
            [
                ("Importe do Termo de Referência no botão", None),
                ("TR", self.icons.get("layers")),
                ("as colunas ('catalogo', 'descricao' e 'descricao_detalhada').", None),
            ],
            additional_text="Este passo é essencial, pois as especificações não constam no termo de homologação e no comprasnet."
        ))
        
        self.add_divider(layout)

        layout.addLayout(self.create_paragraph(
            "Segundo passo (Extrair os dados dos Termos de Homologação)",
            [
                ("No módulo", None),
                ("Termo de Homologação", self.icons.get("layers")),
                ("coloque os arquivos PDF dos termos de homologação na pasta", None),
                ("Abrir Pasta", self.icons.get("add-folder")),
                (".", None)
            ],
            additional_text="O local de salvamento do PDF pode ser redefinido nas configurações."
        ))

        self.add_divider(layout)

        layout.addLayout(self.create_paragraph(
            "Terceiro passo (Extrais os dados do SICAF)",
            [
                ("Obtenha o nível de credenciamento 1 do SICAF em", None),
                ("SICAF", self.icons.get("features")),
                ("para que os dados da empresa sejam automaticamente incluídos na ata.", None)
            ]
        ))

        self.add_divider(layout)

        layout.addLayout(self.create_paragraph(
            "Quarto passo (Gerar Atas)",
            [
                ("O botão", None),
                ("Gerar Ata", self.icons.get("features")),
                ("permite criar as atas automaticamente com base nos dados carregados nos passos anteriores.", None)
            ]
        ))

        self.setLayout(layout)

        self.add_divider(layout)

        layout.addLayout(self.create_paragraph(
            "Gerar Atas por meio de consulta à API do PNCP (Opcional)",
            [
                ("O botão", None),
                ("Consulta", self.icons.get("api")),
                ("permite criar as atas automaticamente com base no número sequencial da contratação no PNCP.", None)
            ]
        ))

        # Configurar o layout para ocupar o espaço no widget
        self.setLayout(layout)

    def create_paragraph(self, title, components, additional_text=None):
        """Cria um parágrafo com título e componentes."""
        paragraph_layout = QVBoxLayout()

        # Adiciona título
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; color: #4E648B; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centraliza o título
        paragraph_layout.addWidget(title_label)

        # Adiciona linha principal de componentes
        line_layout = QHBoxLayout()
        for text, icon in components:
            label = QLabel(text)
            label.setStyleSheet("font-size: 16px; color: #E6E6E6;" if not icon else "font-size: 16px; color: #8AB4F7; font-weight: bold;")
            if icon:
                icon_label = QLabel()
                icon_label.setPixmap(icon.pixmap(24, 24))
                line_layout.addWidget(icon_label)
            line_layout.addWidget(label)

        line_layout.addStretch()
        paragraph_layout.addLayout(line_layout)

        # Adiciona texto adicional, se houver
        if additional_text:
            additional_label = QLabel(additional_text)
            additional_label.setStyleSheet("font-size: 16px; color: #FFF;")
            paragraph_layout.addWidget(additional_label)

        return paragraph_layout


    def add_divider(self, layout):
        """Adiciona uma linha divisória com espaçamento."""
        linha_divisoria, spacer_baixo_linha = linha_divisoria_layout()
        layout.addWidget(linha_divisoria)
        layout.addSpacerItem(spacer_baixo_linha)

import json
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

class EditPredefinicoesDialog(QDialog):
    def __init__(self, categoria, config_data, parent=None):
        super().__init__(parent)
        self.categoria = categoria
        self.config_data = config_data
        self.setWindowTitle(f"Editar {categoria.replace('_', ' ').capitalize()}")

        layout = QVBoxLayout(self)

        # Título
        title = QLabel(f"Edição de {categoria.replace('_', ' ').capitalize()}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Lista de itens
        self.list_widget = QListWidget()
        if categoria in config_data:
            for item in config_data[categoria]:
                item_text = f"{item['Nome']} - {item['Posto']} - {item['Abreviacao']} - {item['Funcao']}"
                self.list_widget.addItem(item_text)
        layout.addWidget(self.list_widget)

        # Nome
        layout.addWidget(QLabel("Nome:"))
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Digite o nome")
        self.nome_input.textChanged.connect(self.forcar_caixa_alta)
        layout.addWidget(self.nome_input)

        # Posto
        layout.addWidget(QLabel("Posto:"))
        self.posto_input = QComboBox()
        self.posto_input.setEditable(True)
        self.posto_input.currentTextChanged.connect(self.atualizar_abreviacao)
        layout.addWidget(self.posto_input)

        # Abreviação do Posto
        layout.addWidget(QLabel("Abreviação do Posto:"))
        self.abrev_posto_input = QComboBox()  # Inicializando o atributo antes da chamada
        self.abrev_posto_input.setEditable(True)
        layout.addWidget(self.abrev_posto_input)

        # Preencher o ComboBox de posto dinamicamente
        self.atualizar_posto()

        # Conectar a função de inicialização da abreviação
        self.atualizar_abreviacao(self.posto_input.currentText())

        # Função
        layout.addWidget(QLabel("Função:"))
        self.funcao_input = QComboBox()
        self.funcao_input.setEditable(True)
        layout.addWidget(self.funcao_input)

        # Inicializa os valores da função com base na categoria
        self.inicializar_funcoes()

        # Botões para adicionar e remover itens
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Adicionar")
        add_btn.clicked.connect(self.adicionar_item)
        button_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remover")
        remove_btn.clicked.connect(self.remover_item)
        button_layout.addWidget(remove_btn)

        layout.addLayout(button_layout)

        # Botão de salvar
        save_btn = QPushButton("Salvar")
        save_btn.clicked.connect(self.salvar_e_fechar)
        layout.addWidget(save_btn)

        # Conecta a seleção na lista para preencher os campos
        self.list_widget.itemClicked.connect(self.preencher_campos)

    def forcar_caixa_alta(self):
        """Garante que o nome seja sempre em caixa alta."""
        self.nome_input.setText(self.nome_input.text().upper())

    def atualizar_posto(self):
        """Atualiza as opções de posto com base na categoria."""
        # Mapas de postos por categoria
        postos_ordenador_agente_fiscal = [
            "Capitão de Mar e Guerra (IM)",
            "Capitão de Fragata (IM)",
            "Capitão de Corveta (IM)",
            "Capitão Tenente (IM)",
            "Outro"
        ]

        postos_geral = [
            "Primeiro-Tenente",
            "Segundo-Tenente",
            "Suboficial",
            "Primeiro-Sargento",
            "Segundo-Sargento",
            "Terceiro-Sargento",
            "Cabo",
            "Outro"
        ]

        # Seleciona o mapa apropriado com base na categoria
        if self.categoria in ["ordenador_de_despesa", "agente_fiscal"]:
            postos = postos_ordenador_agente_fiscal
        else:
            postos = postos_geral

        # Atualiza as opções no ComboBox de posto
        self.posto_input.clear()
        self.posto_input.addItems(postos)


    def atualizar_abreviacao(self, posto):
        """Atualiza as opções de abreviação de posto com base no posto selecionado e categoria."""
        # Mapas de abreviações por categoria
        abrev_map_ordenador_agente_fiscal = {
            "Capitão de Mar e Guerra (IM)": ["CMG (IM)", "Outro"],
            "Capitão de Fragata (IM)": ["CF (IM)", "Outro"],
            "Capitão de Corveta (IM)": ["CC (IM)", "Outro"],
            "Capitão Tenente (IM)": ["CT (IM)", "Outro"],
            "Outro": ["Outro"]
        }

        abrev_map_geral = {
            "Primeiro-Tenente": ["1ºTEN", "Outro"],
            "Segundo-Tenente": ["2ºTEN", "Outro"],
            "Suboficial": ["SO", "Outro"],
            "Primeiro-Sargento": ["1º SG", "Outro"],
            "Segundo-Sargento": ["2º SG", "Outro"],
            "Terceiro-Sargento": ["3º SG", "Outro"],
            "Cabo": ["CB", "Outro"],
            "Outro": ["Outro"]
        }

        # Seleciona o mapa apropriado com base na categoria
        if self.categoria in ["ordenador_de_despesa", "agente_fiscal"]:
            abrev_map = abrev_map_ordenador_agente_fiscal
        else:
            abrev_map = abrev_map_geral

        # Atualiza as opções no combobox de abreviação
        self.abrev_posto_input.clear()
        self.abrev_posto_input.addItems(abrev_map.get(posto, ["Outro"]))

    def inicializar_funcoes(self):
        """Define as funções disponíveis com base na categoria."""
        self.funcao_input.clear()
        if self.categoria == "ordenador_de_despesa":
            self.funcao_input.addItems(["Ordenador de Despesa", "Ordenador de Despesa Substituto"])
        elif self.categoria == "agente_fiscal":
            self.funcao_input.addItems(["Agente Fiscal", "Agente Fiscal Substituto"])
        else:
            funcoes_padrao = [
                "Gerente de Crédito",
                "Responsável pela Demanda",
                "Operador da Contratação",
                "Pregoeiro"
            ]
            self.funcao_input.addItems(funcoes_padrao)

    def preencher_campos(self, item):
        """Preenche os campos de edição com os valores do item selecionado."""
        partes = item.text().split(" - ")
        if len(partes) == 4:
            self.nome_input.setText(partes[0].strip())
            self.posto_input.setCurrentText(partes[1].strip())
            self.abrev_posto_input.setCurrentText(partes[2].strip())
            self.funcao_input.setCurrentText(partes[3].strip())

    def adicionar_item(self):
        """Adiciona um novo item à lista."""
        nome = self.nome_input.text().strip()
        posto = self.posto_input.currentText().strip()
        abreviacao = self.abrev_posto_input.currentText().strip()
        funcao = self.funcao_input.currentText().strip()

        if not nome or not posto or not abreviacao or not funcao:
            QMessageBox.warning(self, "Aviso", "Todos os campos devem ser preenchidos.")
            return

        item_text = f"{nome} - {posto} - {abreviacao} - {funcao}"
        self.list_widget.addItem(item_text)

        # Limpa os campos após adicionar
        self.nome_input.clear()
        self.posto_input.setCurrentIndex(-1)
        self.abrev_posto_input.clear()
        self.funcao_input.setCurrentIndex(-1)

    def remover_item(self):
        """Remove o item selecionado da lista."""
        selected_item = self.list_widget.currentItem()
        if selected_item:
            self.list_widget.takeItem(self.list_widget.row(selected_item))

    def salvar_e_fechar(self):
        """Salva as alterações na configuração e fecha o diálogo."""
        items = []
        for i in range(self.list_widget.count()):
            partes = self.list_widget.item(i).text().split(" - ")
            if len(partes) == 4:
                items.append({
                    "Nome": partes[0].strip(),
                    "Posto": partes[1].strip(),
                    "Abreviacao": partes[2].strip(),
                    "Funcao": partes[3].strip()
                })
        self.config_data[self.categoria] = items
        self.accept()

import json
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

class EditOMDialog(QDialog):
    def __init__(self, categoria, config_data, parent=None):
        super().__init__(parent)
        self.categoria = categoria
        self.config_data = config_data
        self.setWindowTitle(f"Editar {categoria.replace('_', ' ').capitalize()}")

        self.setFixedSize(600, 600)
        
        layout = QVBoxLayout(self)

        # Título
        title = QLabel(f"Edição de {categoria.replace('_', ' ').capitalize()}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Lista de itens
        self.list_widget = QListWidget()
        if categoria in config_data:
            for item in config_data[categoria]:
                item_text = f"UASG: {item['UASG']} - {item['Nome']} - {item['Sigla']} - {item['Indicativo']} - {item['Cidade']}"
                self.list_widget.addItem(item_text)
        layout.addWidget(self.list_widget)

        # Nome
        layout.addWidget(QLabel("Nome:"))
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Digite o nome, Exemplo: Centro de Intendência da Marinha em Brasília")
        self.nome_input.textChanged.connect(self.forcar_caixa_alta)
        layout.addWidget(self.nome_input)

        # Posto
        layout.addWidget(QLabel("Sigla:"))
        self.sigla_input = QLineEdit()
        self.sigla_input.setPlaceholderText("Digite a Sigla, Exemplo: CeIMBra")
        self.sigla_input.textChanged.connect(self.forcar_caixa_alta)        
        layout.addWidget(self.sigla_input)

        # Abreviação do Posto
        layout.addWidget(QLabel("UASG:"))
        self.uasg_input = QLineEdit()
        self.uasg_input.setPlaceholderText("Digite a UASG, Exemplo: 787010")
        layout.addWidget(self.uasg_input)
        
        # Função
        layout.addWidget(QLabel("Indicativo:"))
        self.indicativo_input = QLineEdit()
        self.indicativo_input.setPlaceholderText("Digite o Indicativo, Exemplo: CITBRA")

        layout.addWidget(self.indicativo_input)

        # Função
        layout.addWidget(QLabel("Cidade:"))
        self.cidade_input = QLineEdit()
        self.cidade_input.setPlaceholderText("Digite a Cidade, Exemplo: Brasília-DF")

        layout.addWidget(self.cidade_input)

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

    def preencher_campos(self, item):
        """Preenche os campos de edição com os valores do item selecionado."""
        partes = item.text().split(" - ")
        if len(partes) == 5:
            self.nome_input.setText(partes[0].strip())
            self.sigla_input.setText(partes[1].strip())
            self.uasg_input.setText(partes[2].strip())
            self.indicativo_input.setText(partes[3].strip())
            self.cidade_input.setText(partes[4].strip())

    def adicionar_item(self):
        """Adiciona um novo item à lista."""
        nome = self.nome_input.text().strip()
        sigla = self.sigla_input.text().strip()
        uasg = self.uasg_input.text().strip()
        indicativo = self.indicativo_input.text().strip()
        cidade = self.cidade_input.text().strip()

        if not nome or not sigla or not uasg or not indicativo or not cidade:
            QMessageBox.warning(self, "Aviso", "Todos os campos devem ser preenchidos.")
            return

        item_text = f"{sigla} - {sigla} - {uasg} - {indicativo} - {cidade}"
        self.list_widget.addItem(item_text)

        # Limpa os campos após adicionar
        self.nome_input.clear()
        self.sigla_input.clear()
        self.uasg_input.clear()
        self.indicativo_input.clear()
        self.cidade_input.clear()

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
            if len(partes) == 5:
                items.append({
                    "Nome": partes[0].strip(),
                    "Sigla": partes[1].strip(),
                    "UASG": partes[2].strip(),
                    "Indicativo": partes[3].strip(),
                    "Cidade": partes[4].strip()
                })
        self.config_data[self.categoria] = items
        self.accept()

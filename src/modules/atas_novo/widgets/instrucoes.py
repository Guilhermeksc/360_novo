from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class InstructionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Configuração do layout principal
        layout = QVBoxLayout(self)

        # Primeira instrução
        instrucao1 = QLabel("1. O primeiro passo é importar o Termo de Referência com as colunas necessárias. "
                            "Este termo é essencial, pois as especificações não constam no termo de homologação.")
        instrucao1.setWordWrap(True)  # Permite a quebra de linha
        layout.addWidget(instrucao1)

        # Segunda instrução
        instrucao2 = QLabel("2. Coloque os termos de homologação na pasta definida para processá-los. "
                            "O local de salvamento do PDF pode ser redefinido nas configurações.")
        instrucao2.setWordWrap(True)
        layout.addWidget(instrucao2)

        # Instrução adicional sobre o SICAF
        instrucao3 = QLabel("3. Opcionalmente, insira os dados do SICAF para que sejam automaticamente incluídos na ata.")
        instrucao3.setWordWrap(True)
        layout.addWidget(instrucao3)

        # Instrução final sobre geração de atas
        instrucao4 = QLabel("4. O botão 'Gerar Atas' permite criar as atas automaticamente com base nos dados carregados.")
        instrucao4.setWordWrap(True)
        layout.addWidget(instrucao4)

        # Configurar o layout para ocupar o espaço no widget
        self.setLayout(layout)
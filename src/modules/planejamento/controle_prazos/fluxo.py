from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

class ControlePrazosDialog(QDialog):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("Controle do Planejamento de Licitações")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Label de Título
        title_label = QLabel("Controle do Planejamento de Licitações", self)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)


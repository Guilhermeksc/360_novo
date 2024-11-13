from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QIcon, QCursor
from PyQt6.QtCore import QSize, Qt
from pathlib import Path

def add_button_func(text, icon_name, slot, layout, icons, tooltip=None):
    button = QPushButton(text)
    icon = icons.get(icon_name)
    if icon:
        button.setIcon(icon)

    button.setIconSize(QSize(30, 30))
    
    # Aplicando o CSS para o estilo do botão
    button.setStyleSheet("""
        QPushButton {
            background-color: #181928;
            color: #8AB4F7;
            font-size: 14px;
            font-weight: bold;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
        }
        QPushButton:hover {
            background-color: #2C2F3F;
            color: #FFFFFF;
        }
    """)


    if tooltip:
        button.setToolTip(tooltip)

    button.clicked.connect(slot)

    layout.addWidget(button)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


def add_button(label, icon_name, signal, layout, icons=None, tooltip=None):
    button = QPushButton(label)
    
    # Verifica se icons não é None antes de tentar obter o ícone
    if icons and icon_name in icons:
        button.setIcon(icons.get(icon_name))
    else:
        print(f"Aviso: Ícone '{icon_name}' não encontrado ou 'icons' não foi passado.")
    
    button.setIconSize(QSize(30, 30))
    button.clicked.connect(signal.emit)

    # Estilo do botão
    button.setStyleSheet("""
        QPushButton {
            background-color: #181928;
            color: #8AB4F7;
            font-size: 14px;
            font-weight: bold;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
        }
        QPushButton:hover {
            background-color: #2C2F3F;
            color: #FFFFFF;
        }
    """)
    
    button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    if tooltip:
        button.setToolTip(tooltip)

    layout.addWidget(button)
    return button


def create_button(text, icon, callback, tooltip_text, icon_size=QSize(30, 30)):
    btn = QPushButton(text)
    
    # Define o ícone e tamanho do ícone, se fornecido
    if icon:
        btn.setIcon(QIcon(icon))
        btn.setIconSize(icon_size)
    
    # Conecta o callback ao clique, se fornecido
    if callback:
        btn.clicked.connect(callback)
    
    
    # Define o estilo de hover para o botão
    btn.setStyleSheet("""
        QPushButton {
            background-color: transparent;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #222236; 
        }
    """)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn

import sys
from PyQt6.QtWidgets import QApplication
from src.main import MainWindow
from src.config.paths import STYLE_PATH

# def load_stylesheet(app):
#     with open(STYLE_PATH, "r") as f:
#         app.setStyleSheet(f.read())

# def run():
#     app = QApplication(sys.argv)
#     load_stylesheet(app)
#     window = MainWindow(app)
#     window.show()
#     sys.exit(app.exec())

# if __name__ == "__main__":
#     run()

import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from src.main import MainWindow
from src.config.paths import STYLE_PATH, ACANTO

def load_stylesheet(app):
    with open(STYLE_PATH, "r") as f:
        app.setStyleSheet(f.read())

def run():
    app = QApplication(sys.argv)

    # Configuração da tela de splash
    splash_pix = QPixmap(str(ACANTO))  # Caminho para a imagem de splash
    splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()

    # Barra de progresso no splash
    progress_bar = QProgressBar(splash)
    progress_bar.setGeometry(0, splash_pix.height() - 30, splash_pix.width(), 20)
    progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
    progress_bar.setStyleSheet("QProgressBar { text-align: center; }")
    progress_bar.setRange(0, 100)
    progress_bar.setValue(0)

    # Simulação de carregamento
    for i in range(1, 101):
        QTimer.singleShot(i * 10, lambda value=i: progress_bar.setValue(value))
        app.processEvents()  # Garante que o splash atualize corretamente

    # Carregamento de estilos e janela principal
    load_stylesheet(app)
    window = MainWindow(app)
    QTimer.singleShot(1000, splash.close)  # Fecha o splash após 1 segundo
    QTimer.singleShot(1000, window.show)  # Exibe a janela principal após 1 segundo

    sys.exit(app.exec())

if __name__ == "__main__":
    run()

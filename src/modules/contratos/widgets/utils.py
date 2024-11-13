## módulo incluido em modules/contratos/utils.py ##

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import pandas as pd
import sqlite3

class IconDelegate(QStyledItemDelegate):
    def __init__(self, image_cache, parent=None):
        super().__init__(parent)
        self.image_cache = image_cache

    def paint(self, painter, option, index):
        value = index.data()
        if value is not None:
            try:
                days = int(value)
                icon = None

                if 60 <= days <= 180:
                    icon = QPixmap(self.image_cache.get("head_skull.png"))
                elif 30 <= days < 60:
                    icon = QPixmap(self.image_cache.get("message_alert.png"))

                if icon:
                    # Draw the icon on the right side of the cell
                    icon_rect = option.rect
                    icon_rect.setLeft(icon_rect.right() - icon.width())
                    icon_rect.setTop(icon_rect.top() + (icon_rect.height() - icon.height()) // 2)
                    painter.drawPixmap(icon_rect, icon)

                # Adjust the text area to avoid overlapping with the icon
                option.rect.setRight(option.rect.right() - icon.width() - 5)
            except ValueError:
                pass

        # Centraliza o texto
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        super().paint(painter, option, index)

class ColorDelegate(QStyledItemDelegate):
    def __init__(self, icons_dir, parent=None):
        super().__init__(parent)
        self.image_cache = self.load_images(icons_dir, ["head_skull.png", "message_alert.png"])

    def load_images(self, icons_dir, image_names):
        image_cache = {}
        for name in image_names:
            path = icons_dir / name
            image_cache[name] = str(path)
        return image_cache

    def paint(self, painter, option, index):
        value = index.data()
        if value is not None:
            try:
                days = int(value)
                icon = None
                color = None

                # Definir ícone com base no valor dos dias
                if 60 <= days <= 180:
                    icon = QPixmap(self.image_cache.get("head_skull.png"))
                elif 30 <= days < 60:
                    icon = QPixmap(self.image_cache.get("message_alert.png"))

                # Definir cor com base no valor dos dias
                if days < 30:
                    color = QColor(255, 0, 0)  # Vermelho
                elif 30 <= days <= 90:
                    color = QColor(255, 165, 0)  # Laranja
                elif 91 <= days <= 159:
                    color = QColor(255, 255, 0)  # Amarelo
                else:
                    color = QColor(0, 255, 0)  # Verde

                # Aplicar a cor ao texto
                if color:
                    option.palette.setColor(QPalette.ColorRole.Text, color)

                # Desenhar o ícone
                if icon:
                    # Desenhar o ícone no lado direito da célula
                    icon_rect = option.rect
                    icon_rect.setLeft(icon_rect.right() - icon.width())
                    icon_rect.setTop(icon_rect.top() + (icon_rect.height() - icon.height()) // 2)
                    painter.drawPixmap(icon_rect, icon)

                    # Ajustar a área do texto para evitar sobreposição com o ícone
                    option.rect.setRight(option.rect.right() - icon.width() - 5)
                
            except ValueError:
                pass

        # Centraliza o texto
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        super().paint(painter, option, index)

        
class ExportThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, model, filepath):
        super().__init__()
        self.model = model
        self.filepath = filepath

    def run(self):
        try:
            df = self.model_to_dataframe(self.model)
            df.to_excel(self.filepath, index=False)
            self.finished.emit('Completed successfully!')
        except Exception as e:
            self.finished.emit(f"Failed: {str(e)}")

    def model_to_dataframe(self, model):
        headers = [model.headerData(i, Qt.Orientation.Horizontal) for i in range(model.columnCount())]
        data = [
            [model.data(model.index(row, col)) for col in range(model.columnCount())]
            for row in range(model.rowCount())
        ]
        return pd.DataFrame(data, columns=headers)
    
def carregar_dados_contratos(index, caminho_banco_dados):
    """
    Carrega os dados de contrato do banco de dados SQLite especificado pelo caminho_banco_dados.

    Parâmetros:
    - index: O índice da linha selecionada na QTableView.
    - caminho_banco_dados: O caminho para o arquivo do banco de dados SQLite.
    
    Retorna:
    - Um dicionário contendo os dados do registro selecionado.
    """
    try:
        connection = sqlite3.connect(caminho_banco_dados)
        
        # Recupere o número do contrato com base no índice da linha
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM controle_contratos LIMIT 1 OFFSET ?", (index,))
        resultado = cursor.fetchone()
        
        if resultado is None:
            raise Exception("Nenhum contrato encontrado para o índice fornecido.")
        
        id = resultado[0]
        
        # Carrega os dados do contrato específico
        query = f"SELECT * FROM controle_contratos WHERE id='{id}'"
        df_registro_selecionado = pd.read_sql_query(query, connection)
        connection.close()

        if not df_registro_selecionado.empty:
            return df_registro_selecionado.iloc[0].to_dict()  # Retorna o primeiro registro como dicionário
        else:
            return {}
    except Exception as e:
        print(f"Erro ao carregar dados do banco de dados: {e}")
        return {}  # Retorna um dicionário vazio em caso de erro


class Dialogs:
    @staticmethod
    def info(parent, title, message):
        QMessageBox.information(parent, title, message)

    @staticmethod
    def warning(parent, title, message):
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def error(parent, title, message):
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def confirm(parent, title, message):
        reply = QMessageBox.question(parent, title, message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, icons, status_column_index, parent=None):
        super().__init__(parent)
        self.icons = icons
        self.status_column_index = status_column_index

    def paint(self, painter, option, index):
        if index.column() == self.status_column_index:
            situacao = index.model().data(index, Qt.ItemDataRole.DisplayRole)
            icon = self.icons.get(situacao, None)

            if icon:
                icon_size = 24
                icon_x = option.rect.left() + 5
                icon_y = option.rect.top() + (option.rect.height() - icon_size) // 2
                icon_rect = QRect(int(icon_x), int(icon_y), icon_size, icon_size)
                
                # Obtém o pixmap no tamanho desejado
                pixmap = icon.pixmap(icon_size, icon_size)
                painter.drawPixmap(icon_rect, pixmap)

                # Ajusta o retângulo para o texto para ficar ao lado do ícone
                text_rect = QRect(
                    icon_rect.right() + 5,
                    option.rect.top(),
                    option.rect.width() - icon_size - 10,
                    option.rect.height()
                )
                option.rect = text_rect
            else:
                print(f"Ícone não encontrado para a situação: {situacao}")

        # Chama o método padrão para desenhar o texto ajustado
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if index.column() == self.status_column_index:
            size.setWidth(size.width() + 30)
        return size


class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter


etapas = {
    'Planejamento': None,
    'Consolidar Demandas': None,
    'Montagem do Processo': None,
    'Nota Técnica': None,
    'AGU': None,
    'Recomendações AGU': None,
    'Pré-Publicação': None,
    'Sessão Pública': None,
    'Assinatura Contrato': None,
    'Concluído': None
}

def load_and_map_icons(icons_dir, image_cache):
    icons = {}
    icon_mapping = {
        'Seção de Contratos': 'business.png',
        'Consolidar Demandas': 'loading_table.png',
        'Assinado': 'aproved.png',
        'AGU': 'deal.png',
        'Pré-Publicação': 'loading_table.png',
        'Empresa': 'enterprise.png',
        'Nota Técnica': 'law_menu.png',
        'Ata Gerada': 'contrato.png',
        'Recomendações AGU': 'loading_table.png',
        'SIGDEM': 'session.png',
        'Mensagem': 'message_alert.png',
        'API': 'api.png',
        'Abrir Tabela': 'excel.png',
    }

    for status, filename in icon_mapping.items():
        if filename in image_cache:
            pixmap = image_cache[filename]
        else:
            icon_path = icons_dir / filename
            if icon_path.exists():
                pixmap = QPixmap(str(icon_path))
                image_cache[filename] = pixmap
            else:
                print(f"Warning: Icon file {filename} not found in {icons_dir}")
                continue
        icon = QIcon(pixmap)
        icons[status] = icon

    return icons



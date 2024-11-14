from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtSql import *
from PyQt6.QtCore import *
import sys
from pathlib import Path
from database_manager import DatabaseManager
from importar_tr import TermoReferenciaDialog
import os
import sqlite3
import pandas as pd
from modules.atas_novo.widgets.progresso_homolog import ProcessamentoDialog
from gerar_ata import GerarAtaWidget
from indicadores import IndicadoresWidget
from consultar_api import ConsultarAPI
from utils import *

class GerarAtasWindow(QMainWindow):
    pdf_dir_changed = pyqtSignal(Path)
    def __init__(self, icons, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Licitação 360")
        self.pdf_dir = Path(PDF_DIR)
        self.icons_dir = icons
        self.message_widgets = {}
        self.tr_variavel_df_carregado = None 
        self.icon_cache = self.load_icons()

        # Cria o widget central e define um atributo para ele
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Configura o layout do widget central
        self.content_layout = QVBoxLayout()
        self.central_widget.setLayout(self.content_layout)
        self.current_dataframe = None
        
        # Inicializar o UIManager
        self.ui_manager = UIManager(self)
        self.db_manager = DatabaseManager(CONTROLE_DADOS)
        self.db_path = os.path.join(os.getcwd(), "termo_referencia.db")

        # Adiciona um container para os widgets dinâmicos
        self.dynamic_content_container = QWidget()
        self.dynamic_content_container.setContentsMargins(0, 0, 0, 0)  # Define margens zero para o container dinâmico
        self.dynamic_content_layout = QVBoxLayout(self.dynamic_content_container)
        self.dynamic_content_layout.setContentsMargins(0, 0, 0, 0)  # Define margens zero para o layout dinâmico
        self.dynamic_content_container.setFixedHeight(580)  # Define a altura fixa para 500 pixels
        self.content_layout.addWidget(self.dynamic_content_container)

        # Lista para manter referências aos widgets adicionados
        self.active_widgets = []
        # Conecta o sinal de mudança de diretório PDF
        self.pdf_dir_changed.connect(self.on_pdf_dir_changed)

    def load_tr_dataframe(self):
        """Carrega o DataFrame do banco de dados termo_referencia.db."""
        try:
            # Verifica se o arquivo de banco de dados existe
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"O banco de dados {self.db_path} não foi encontrado.")
            
            # Conecta ao banco de dados e carrega a tabela controle_atas
            self.tr_variavel_df_carregado = pd.read_sql("SELECT * FROM controle_atas", sqlite3.connect(self.db_path))
            
            # Verifica se o DataFrame foi carregado com sucesso
            if not self.tr_variavel_df_carregado.empty:
                print("DataFrame carregado com sucesso:")
                print(self.tr_variavel_df_carregado.head())  # Mostra os primeiros registros para verificação
            else:
                print("O DataFrame está vazio.")
                QMessageBox.warning(self, "Aviso", "O DataFrame carregado está vazio.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar o DataFrame: {e}")
            print(f"Erro ao carregar o DataFrame: {e}")

    def open_termo_referencia_widget(self):
        # Limpa apenas a área de conteúdo dinâmico
        self.clear_content_area()

        # Cria a instância do TermoReferenciaWidget e armazena a referência com self
        self.termo_referencia_widget = TermoReferenciaDialog(self)

        # Adiciona o widget ao layout dinâmico
        self.dynamic_content_layout.addWidget(self.termo_referencia_widget)

        # Mantém a referência ao widget ativo
        self.active_widgets.append(self.termo_referencia_widget)

    def clear_content_area(self):
        while self.dynamic_content_layout.count():
            item = self.dynamic_content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                self.dynamic_content_layout.removeWidget(widget)
                if isinstance(widget, ProcessamentoDialog):
                    widget.setParent(None)  # Remove do layout, mas não destrói
                else:
                    widget.deleteLater()
        self.active_widgets.clear()

    def addWidget(self, widget):
        # Adiciona o widget ao layout ou à área principal de exibição
        if hasattr(self, 'content_layout'):
            self.content_layout.addWidget(widget)

    def open_instrucoes_widget(self):
        # Limpa apenas a área de conteúdo dinâmico
        self.clear_content_area()

        # Cria um widget temporário para exibir instruções e armazena a referência com self
        self.instrucoes_widget = QWidget(self)
        instrucoes_layout = QVBoxLayout(self.instrucoes_widget)
        instrucoes_label = QLabel("Instruções de Uso", self.instrucoes_widget)
        instrucoes_label.setWordWrap(True)
        instrucoes_layout.addWidget(instrucoes_label)

        # Adiciona o widget ao layout dinâmico
        self.dynamic_content_layout.addWidget(self.instrucoes_widget)

        # Mantém a referência ao widget ativo
        self.active_widgets.append(self.instrucoes_widget)
                    
    def on_pdf_dir_changed(self, new_pdf_dir):
        """Atualiza o diretório PDF em ProcessamentoDialog."""
        # Atualiza o pdf_dir no diálogo de processamento se estiver aberto
        if hasattr(self, 'termo_homologacao_widget'):
            self.termo_homologacao_widget.pdf_dir = new_pdf_dir

    def open_processamento_widget(self):
        # Carrega o DataFrame e limpa o layout de conteúdo dinâmico
        self.load_tr_dataframe()
        self.clear_content_area()

        # Verifica se o widget já foi criado para evitar duplicidade
        if not hasattr(self, 'termo_homologacao_widget') or self.termo_homologacao_widget is None:
            self.termo_homologacao_widget = ProcessamentoDialog(
                pdf_dir=self.pdf_dir,
                icons=self.icon_cache,
                db_manager=self.db_manager,
                tr_variavel_df_carregado=self.tr_variavel_df_carregado,
                current_dataframe=self.current_dataframe,
                main_window=self,  # Corrigido: passagem de self como main_window
                parent=self
            )
            
        # Adiciona o widget ao layout dinâmico
        self.dynamic_content_layout.addWidget(self.termo_homologacao_widget)

        # Adiciona o widget à lista de widgets ativos
        if not hasattr(self, 'active_widgets'):
            self.active_widgets = []
        self.active_widgets.append(self.termo_homologacao_widget)


    def show_gerar_ata(self):
        # Limpa apenas a área de conteúdo dinâmico
        self.clear_content_area()
        
        # Verifica se homologacao_dataframe está disponível
        if not hasattr(self, 'homologacao_dataframe') or self.homologacao_dataframe is None:
            # Exibe uma mensagem com a opção de carregar um DataFrame ou cancelar
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle('Aviso')
            msg_box.setText('Dados de homologação não disponíveis.\nDeseja carregar um DataFrame existente?')
            carregar_button = msg_box.addButton('Carregar DataFrame', QMessageBox.ButtonRole.YesRole)
            cancel_button = msg_box.addButton('Cancelar', QMessageBox.ButtonRole.RejectRole)
            msg_box.exec()
            
            if msg_box.clickedButton() == cancel_button:
                return
            elif msg_box.clickedButton() == carregar_button:
                # Obter tabelas com 'Homolog' no nome
                tables = self.db_manager.get_tables_with_keyword('Homolog')
                if not tables:
                    QMessageBox.warning(self, 'Aviso', 'Não há tabelas disponíveis com dados de homologação.')
                    return
                # Apresentar um diálogo para seleção da tabela
                table_name, ok = QInputDialog.getItem(
                    self,
                    'Selecionar Tabela',
                    'Selecione uma tabela de homologação:',
                    tables,
                    0,
                    False
                )
                if ok and table_name:
                    # Carregar a tabela selecionada em homologacao_dataframe
                    self.homologacao_dataframe = self.db_manager.load_table_to_dataframe(table_name)
                    if self.homologacao_dataframe is None or self.homologacao_dataframe.empty:
                        QMessageBox.warning(self, 'Aviso', 'Falha ao carregar a tabela selecionada.')
                        return
                else:
                    # Usuário cancelou a seleção
                    return
        # Cria uma instância de GerarAtaWidget
        self.gerar_ata_widget = GerarAtaWidget(self.homologacao_dataframe, self.icons, self.db_manager, self)        
        # Adiciona o widget ao layout dinâmico
        self.dynamic_content_layout.addWidget(self.gerar_ata_widget)
        self.active_widgets.append(self.gerar_ata_widget)

    def show_indicadores_info(self):
        # Limpa apenas a área de conteúdo dinâmico
        self.clear_content_area()
        
        # Verifica se homologacao_dataframe está disponível
        if not hasattr(self, 'homologacao_dataframe') or self.homologacao_dataframe is None:
            # Exibe uma mensagem com a opção de carregar um DataFrame ou cancelar
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle('Aviso')
            msg_box.setText('Dados de homologação não disponíveis.\nDeseja carregar um DataFrame existente?')
            carregar_button = msg_box.addButton('Carregar DataFrame', QMessageBox.ButtonRole.YesRole)
            cancel_button = msg_box.addButton('Cancelar', QMessageBox.ButtonRole.RejectRole)
            msg_box.exec()
            
            if msg_box.clickedButton() == cancel_button:
                return
            elif msg_box.clickedButton() == carregar_button:
                # Obter tabelas com 'Homolog' no nome
                tables = self.db_manager.get_tables_with_keyword('Homolog')
                if not tables:
                    QMessageBox.warning(self, 'Aviso', 'Não há tabelas disponíveis com dados de homologação.')
                    return
                # Apresentar um diálogo para seleção da tabela
                table_name, ok = QInputDialog.getItem(
                    self,
                    'Selecionar Tabela',
                    'Selecione uma tabela de homologação:',
                    tables,
                    0,
                    False
                )
                if ok and table_name:
                    # Carregar a tabela selecionada em homologacao_dataframe
                    self.homologacao_dataframe = self.db_manager.load_table_to_dataframe(table_name)
                    if self.homologacao_dataframe is None or self.homologacao_dataframe.empty:
                        QMessageBox.warning(self, 'Aviso', 'Falha ao carregar a tabela selecionada.')
                        return
                else:
                    # Usuário cancelou a seleção
                    return
        # Cria uma instância de GerarAtaWidget
        self.indicadores_widget = IndicadoresWidget(self.homologacao_dataframe, self.icons_dir, self.db_manager, self)        
        # Adiciona o widget ao layout dinâmico
        self.dynamic_content_layout.addWidget(self.indicadores_widget)
        self.active_widgets.append(self.indicadores_widget)

    def show_consulta_api(self):
        # Limpa apenas a área de conteúdo dinâmico
        self.clear_content_area()                # Cria uma instância de GerarAtaWidget
        self.consulta_api_widget = ConsultarAPI(self.icons, self.db_manager, self)        
        # Adiciona o widget ao layout dinâmico
        self.dynamic_content_layout.addWidget(self.consulta_api_widget)
        self.active_widgets.append(self.consulta_api_widget)

class UIManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        # Use o central_widget e content_layout já definidos na GerarAtasWindow
        central_widget = self.main_window.central_widget
        content_layout = self.main_window.content_layout

        title = self.create_title_label("Licitação 360 - Módulo de Atas de Registro de Preços")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")

        menu_widget = self.create_menu_layout()

        # Define o tamanho fixo do menu_widget para 150 pixels de altura
        menu_widget.setFixedHeight(50)

        # Adiciona os widgets ao layout existente
        content_layout.addWidget(title)
        content_layout.addWidget(menu_widget)

        # Adiciona um widget expansível para preencher o espaço restante
        content_layout.addStretch()

    def create_title_label(self, text):
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        label.setFont(font)
        return label

    def create_menu_layout(self):
        menu_widget = QWidget()
        menu_layout = QHBoxLayout(menu_widget)
        menu_layout.setContentsMargins(0, 0, 0, 0)  # Define margens zero para o layout do menu

        button_widget = QWidget()
        button_layout = self.create_button_layout()
        button_layout.setContentsMargins(0, 0, 0, 0)  # Define margens zero para o layout dos botões
        button_widget.setLayout(button_layout)

        menu_layout.addWidget(button_widget)

        return menu_widget

    def create_button_layout(self):
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)

        buttons = {
            "Instruções": self.main_window.open_instrucoes_widget,
            "Termo de Referência": self.main_window.open_termo_referencia_widget,
            "Termo de Homologação": self.main_window.open_processamento_widget,
            "Consultar API": self.main_window.show_consulta_api,
            "Gerar Ata": self.main_window.show_gerar_ata,
            "Indicadores": self.main_window.show_indicadores_info
        }

        for button_name, action in buttons.items():
            button = QPushButton(button_name)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(action)
            button_layout.addWidget(button)

        button_layout.addStretch()
        return button_layout

def main():
    # Cria a aplicação Qt
    app = QApplication(sys.argv)
    
    # Cria a janela principal
    main_window = GerarAtasWindow()
    
    # Exibe a janela principal
    main_window.show()
    
    # Executa o loop da aplicação
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
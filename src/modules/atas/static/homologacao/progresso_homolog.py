from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from utils import *
import re
import time
import pandas as pd
from pathlib import Path
from utils import *
from static.homologacao.worker_homologacao import Worker, TreeViewWindow, WorkerSICAF, extrair_dados_sicaf

class ConclusaoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processamento Concluído")
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        message_label = QLabel("O processamento foi concluído com sucesso!")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = message_label.font()
        font.setPointSize(14)
        message_label.setFont(font)
        main_layout.addWidget(message_label)

        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

class ProcessamentoDialog(QDialog):
    def __init__(self, pdf_dir, icons, db_manager, tr_variavel_df_carregado, current_dataframe, main_window, parent=None):
        super().__init__(parent)
        self.pdf_dir = pdf_dir
        self.icon_cache = icons
        self.db_manager = db_manager
        self.tr_variavel_df_carregado = tr_variavel_df_carregado
        self.current_dataframe = current_dataframe
        self.main_window = main_window
        self.homologacao_dataframe = None  # Inicializa o dataframe como None
        self.setWindowTitle("Processamento")
        self.setup_ui()
        self.timer = QTimer(self)
        self.start_time = 0

    def on_pdf_dir_changed(self, new_pdf_dir):
        """Atualiza o diretório PDF em ProcessamentoDialog."""
        # Atualiza o pdf_dir no diálogo de processamento se estiver aberto
        if hasattr(self, 'termo_homologacao_widget'):
            self.termo_homologacao_widget.pdf_dir = new_pdf_dir
            
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        title = QLabel("Processamento de Documentos")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(14)
        title.setFont(font)
        main_layout.addWidget(title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.context_area = QTextEdit()
        self.context_area.setReadOnly(True)
        main_layout.addWidget(self.context_area)

        self.time_label = QLabel("Tempo decorrido: 0s")
        main_layout.addWidget(self.time_label)

        self.setup_button_layout(main_layout)
        self.setLayout(main_layout)

        self.update_pdf_count()

    def setup_button_layout(self, main_layout):
        button_layout = QHBoxLayout()
        
        start_button = QPushButton("Iniciar Processamento")
        start_button.clicked.connect(self.start_processing)
        button_layout.addWidget(start_button)

        update_button = QPushButton("Atualizar")
        update_button.clicked.connect(self.update_pdf_count)
        button_layout.addWidget(update_button)

        abrir_pasta_button = QPushButton("Abrir Pasta PDF")
        abrir_pasta_button.clicked.connect(self.abrir_pasta_pdf)
        button_layout.addWidget(abrir_pasta_button)

        definir_pasta_button = QPushButton("Definir Pasta PDF Padrão")
        definir_pasta_button.clicked.connect(self.definir_pasta_pdf_padrao)
        button_layout.addWidget(definir_pasta_button)

        # Define registro_sicaf_button como um atributo de instância
        self.registro_sicaf_button = QPushButton("Registro SICAF")
        self.registro_sicaf_button.clicked.connect(self.abrir_registro_sicaf)
        button_layout.addWidget(self.registro_sicaf_button)

        # Botão "Abrir Resultados"
        self.open_results_button = QPushButton("Abrir Resultados")
        self.open_results_button.clicked.connect(self.open_results_treeview)
        self.open_results_button.setEnabled(False)
        button_layout.addWidget(self.open_results_button)

        main_layout.addLayout(button_layout)

    def abrir_pasta_pdf(self):
        if self.pdf_dir.exists() and self.pdf_dir.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.pdf_dir)))
        else:
            QMessageBox.warning(self, "Erro", "O diretório PDF atual não existe.")

    def definir_pasta_pdf_padrao(self):
        folder = QFileDialog.getExistingDirectory(self, "Defina a Pasta PDF Padrão")
        if folder:
            self.main_window.pdf_dir = Path(folder)
            # Save the new configuration here
            self.main_window.pdf_dir_changed.emit(self.main_window.pdf_dir)
            QMessageBox.information(self, "Pasta Padrão Definida", f"A pasta padrão foi definida como: {folder}")

    def update_context(self, text):
        self.context_area.append(text)

    def update_pdf_count(self):
        if self.pdf_dir.exists() and self.pdf_dir.is_dir():
            pdf_count = len(list(self.pdf_dir.glob("*.pdf")))
            self.update_context(f"Quantidade de arquivos PDF: {pdf_count}")
        else:
            self.update_context("Diretório PDF não encontrado.")

    def start_processing(self):
        self.current_dataframe = None

        if not self.verify_directories():
            return

        self.start_time = time.time()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        self.worker_thread = Worker(self.pdf_dir)
        self.worker_thread.processing_complete.connect(self.finalizar_processamento_homologacao)
        self.worker_thread.update_context_signal.connect(self.update_context)
        self.worker_thread.progress_signal.connect(self.progress_bar.setValue)

        self.worker_thread.start()

    def finalizar_processamento_homologacao(self, extracted_data):
        self.update_context("Processamento concluído.")
        self.timer.stop()  # Para o temporizador
        elapsed_time = int(time.time() - self.start_time)
        self.time_label.setText(f"Tempo total: {elapsed_time}s")

        # Processar dados e atualizar o treeView
        self.homologacao_dataframe = save_to_dataframe(extracted_data, self.tr_variavel_df_carregado, self.current_dataframe)

        # Lógica de salvar dados após a atribuição do dataframe
        if self.homologacao_dataframe is not None and not self.homologacao_dataframe.empty:
            self.current_dataframe = self.homologacao_dataframe  # Atualiza o DataFrame corrente
            
            # Verifica se as colunas necessárias existem para salvar os dados
            if {'num_pregao', 'ano_pregao', 'uasg'}.issubset(self.current_dataframe.columns):
                # Filtra linhas onde qualquer uma das colunas chave contém NaN e cria uma cópia para evitar o aviso
                filtered_df = self.current_dataframe.dropna(subset=['num_pregao', 'ano_pregao', 'uasg']).copy()

                # Gera o nome da tabela apenas para linhas sem NaN
                def create_table_name(row):
                    return f"{row['num_pregao']}-{row['ano_pregao']}-{row['uasg']}-Homolog"

                # Use o .loc para atribuir os valores ao DataFrame filtrado
                filtered_df.loc[:, 'table_name'] = filtered_df.apply(create_table_name, axis=1)

                # Debugging output
                print("Valores de 'num_pregao':", filtered_df['num_pregao'].unique())
                print("Valores de 'ano_pregao':", filtered_df['ano_pregao'].unique())
                print("Valores de 'uasg':", filtered_df['uasg'].unique())
                print("Nomes de tabelas gerados:", filtered_df['table_name'].unique())

                if filtered_df['table_name'].nunique() == 1:
                    table_name = filtered_df['table_name'].iloc[0]
                    self.save_data(table_name)  # Chama a função de salvar com o nome da tabela
                else:
                    QMessageBox.critical(self, "Erro", "A combinação de 'num_pregão', 'ano_pregão', e 'uasg' não é única. Por favor, verifique os dados.")
            else:
                QMessageBox.critical(self, "Erro", "Dados necessários para criar o nome da tabela não estão presentes.")

            # Habilita o botão de abrir resultados
            self.open_results_button.setEnabled(True)
        else:
            QMessageBox.warning(self, "Erro", "Falha ao salvar os dados.")
        
        # Habilita o botão Registro SICAF se homologacao_dataframe estiver disponível
        self.update_registro_sicaf_button()


    def save_data(self, table_name):
        if isinstance(self.current_dataframe, pd.DataFrame) and not self.current_dataframe.empty:
            # print("Salvando DataFrame com as colunas:", self.current_dataframe.columns)
            try:
                with self.db_manager as conn:
                    self.current_dataframe.to_sql(table_name, conn, if_exists='replace', index=False)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar os dados no banco de dados: {e}")
        else:
            QMessageBox.critical(self, "Erro", "Nenhum DataFrame válido disponível para salvar ou o objeto não é um DataFrame.")
            
    def update_time(self):
        elapsed_time = int(time.time() - self.start_time)
        self.time_label.setText(f"Tempo decorrido: {elapsed_time}s")

    def verify_directories(self):
        if not self.pdf_dir.exists() or not self.pdf_dir.is_dir():
            self.update_context("Diretório PDF não encontrado.")
            return False
        return True
    
    def setup_treeview_styles(self):
        header = self.treeView.header()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def open_results_treeview(self):
        if self.homologacao_dataframe is not None and not self.homologacao_dataframe.empty:
            # Certifique-se de passar os argumentos na ordem correta
            tree_view_window = TreeViewWindow(
                dataframe=self.homologacao_dataframe,
                icons_dir=self.icon_cache,       # Diretório de ícones
                parent=self
            )
            tree_view_window.exec()  # Abre a janela como modal
        else:
            QMessageBox.warning(self, "Erro", "Não há dados disponíveis para mostrar no TreeView.")
  
    def update_current_dataframe(self, new_data):
        # Mesclar new_data com self.current_dataframe
        if self.current_dataframe is not None:
            # Verificar se 'cnpj' está presente em ambos os DataFrames
            if 'cnpj' in self.current_dataframe.columns and 'cnpj' in new_data.columns:
                self.current_dataframe = pd.merge(self.current_dataframe, new_data, on='cnpj', how='left')
                print("DataFrame atualizado após merge:")
                print(self.current_dataframe)
            else:
                QMessageBox.warning(self, "Erro", "Não é possível mesclar os dados. A coluna 'cnpj' não está presente em ambos os DataFrames.")
        else:
            self.current_dataframe = new_data
            print("DataFrame atualizado com novos dados:")
            print(self.current_dataframe)

    def abrir_registro_sicaf(self):
        if self.homologacao_dataframe is None:
            QMessageBox.warning(self, "Erro", "Dados não disponíveis.")
            return

        # Instancia e exibe o diálogo de Registro SICAF com pdf_dir correto
        dialog = RegistroSICAFDialog(
            homologacao_dataframe=self.homologacao_dataframe,
            pdf_dir=self.pdf_dir,
            db_manager=self.db_manager,
            icons=self.icon_cache,
            parent=self
        )
        dialog.exec()

    def update_registro_sicaf_button(self):
        # Verifica a existência do DataFrame para habilitar o botão
        self.registro_sicaf_button.setEnabled(self.homologacao_dataframe is not None)

class RegistroSICAFDialog(QDialog):
    def __init__(self, homologacao_dataframe, pdf_dir, db_manager, icons, parent=None, update_context_callback=None):
        super().__init__(parent)
        self.homologacao_dataframe = homologacao_dataframe
        self.sicaf_dir = pdf_dir / 'pasta_sicaf'
        self.db_manager = db_manager
        self.icon_cache = icons
        self.update_context = update_context_callback  # Recebe o método de atualização de contexto
        self.setWindowTitle("Registro SICAF")
        self.setFixedSize(1000, 600)
        self.setup_ui()

    def setup_ui(self):
        """Configura a interface do diálogo."""
        main_layout = QHBoxLayout(self)

        # Cria e adiciona o layout esquerdo
        left_layout = self.criar_layout_esquerdo()
        main_layout.addLayout(left_layout)

        # Cria e adiciona o layout direito
        right_widget = self.criar_layout_direito()
        main_layout.addWidget(right_widget)

        self.setLayout(main_layout)

        # Chama atualizar_lista após todos os elementos serem inicializados
        self.atualizar_lista()

    def criar_layout_esquerdo(self):
        left_layout = QVBoxLayout()

        # Adiciona o layout da legenda
        legenda_layout = self.criar_legenda_layout()
        left_layout.addLayout(legenda_layout)

        # Define o QListWidget para a lista de empresas e CNPJs
        self.left_list_widget = QListWidget()
        self.left_list_widget.setStyleSheet("QListWidget::item { text-align: left; }")

        # Adiciona o QListWidget ao layout esquerdo
        left_layout.addWidget(self.left_list_widget)

        # Botão "Processamento de SICAF" com ícone 'processing'
        processing_button = self.create_button(
            text="Processamento de SICAF",
            icon=self.icon_cache["processing"],
            callback=self.iniciar_processamento_sicaf,  # Método de callback ao clicar no botão
            tooltip_text="Iniciar processamento do SICAF"
        )

        # Adiciona o botão ao layout e alinha ao centro
        left_layout.addWidget(processing_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        return left_layout

    def iniciar_processamento_sicaf(self):
        """Inicializa o processamento SICAF com atualizações de contexto para cada arquivo PDF analisado."""
        if not self.sicaf_dir.exists():
            QMessageBox.warning(self, "Erro", "A pasta SICAF não existe.")
            return

        self.update_context("Iniciando o processamento dos arquivos SICAF...")
        
        # Cria uma instância de WorkerSICAF e conecta os sinais
        self.worker = WorkerSICAF(self.sicaf_dir)
        self.worker.processing_complete.connect(self.on_processing_complete)
        
        self.worker.update_context_signal.connect(self.update_context)  # Conecta o sinal ao método de atualização de contexto
        self.worker.progress_signal.connect(self.progress_bar.setValue)

        # Inicia o Worker
        self.worker.start()

    def on_processing_complete(self, dataframes):
        if dataframes:
            self.current_dataframe = pd.concat(dataframes, ignore_index=True)
            print("Dados extraídos de todos os arquivos:")
            print(self.current_dataframe)

            # Salvar o DataFrame na tabela 'sicaf_table_teste'
            self.save_data('sicaf_table_teste')

            # Emitir o sinal com os novos dados, se necessário
            self.data_extracted.emit(self.current_dataframe)
        else:
            print("Nenhum dado foi extraído de nenhum dos arquivos.")

    def save_data(self, table_name):
        if isinstance(self.current_dataframe, pd.DataFrame) and not self.current_dataframe.empty:
            try:
                with self.db_manager as conn:
                    self.current_dataframe.to_sql(table_name, conn, if_exists='replace', index=False)
                print(f"Dados salvos na tabela {table_name} com sucesso.")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar os dados no banco de dados: {e}")
        else:
            QMessageBox.critical(self, "Erro", "Nenhum DataFrame válido disponível para salvar ou o objeto não é um DataFrame.")



    def create_button(self, text, icon, callback, tooltip_text, icon_size=QSize(30, 30), button_size=QSize(120, 30)):
        """Cria um botão personalizado com texto, ícone, callback e tooltip."""
        btn = QPushButton(text)
        if icon:
            btn.setIcon(icon)
            btn.setIconSize(icon_size)
        btn.clicked.connect(callback)
        btn.setToolTip(tooltip_text)
        
        # Define o tamanho fixo do botão
        btn.setFixedSize(button_size.width(), button_size.height())

        btn.setStyleSheet("""
        QPushButton {
            font-size: 12pt;
            padding: 5px;
        }
        """)

        return btn

    def criar_legenda_layout(self):
        """Cria o layout da legenda com os ícones de confirmação e cancelamento."""
        legenda_layout = QHBoxLayout()
        legenda_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Texto da legenda
        legenda_text = QLabel("Legenda: ")

        # Ícone de confirmação
        confirm_icon = QLabel()
        confirm_icon.setPixmap(self.icon_cache["check"].pixmap(24, 24))
        confirm_text = QLabel("SICAF encontrado")

        # Ícone de cancelamento
        cancel_icon = QLabel()
        cancel_icon.setPixmap(self.icon_cache["cancel"].pixmap(24, 24))
        cancel_text = QLabel("SICAF não encontrado")

        # Adiciona elementos ao layout da legenda
        legenda_layout.addWidget(legenda_text)
        legenda_layout.addWidget(confirm_icon)
        legenda_layout.addWidget(confirm_text)
        legenda_layout.addWidget(cancel_icon)
        legenda_layout.addWidget(cancel_text)

        return legenda_layout

    def criar_layout_direito(self):
        """Cria o layout direito com a lista de arquivos PDF e os botões."""
        right_widget = QWidget()
        right_widget.setFixedWidth(350)
        right_layout = QVBoxLayout(right_widget)

        # Adiciona os botões "Abrir Pasta" e "Atualizar" ao layout
        top_right_layout = self.criar_botoes_direitos()
        right_layout.addLayout(top_right_layout)

        # Conta e exibe a quantidade de arquivos PDF
        self.right_label = QLabel(self.obter_texto_arquivos_pdf())
        right_layout.addWidget(self.right_label)

        # Define o QListWidget para a lista de arquivos PDF
        self.pdf_list_widget = QListWidget()
        self.load_pdf_files()
        right_layout.addWidget(self.pdf_list_widget)

        return right_widget


    def load_pdf_files(self):
        """Carrega arquivos .pdf da pasta sicaf_dir e os exibe na lista."""
        if self.sicaf_dir.exists() and self.sicaf_dir.is_dir():
            pdf_files = list(self.sicaf_dir.glob("*.pdf"))
            for pdf_file in pdf_files:
                self.pdf_list_widget.addItem(pdf_file.name)
        else:
            self.pdf_list_widget.addItem("Nenhum arquivo PDF encontrado.")


    def criar_botoes_direitos(self):
        """Cria o layout horizontal com os botões 'Abrir Pasta' e 'Atualizar'."""
        top_right_layout = QHBoxLayout()

        # Botão "Abrir Pasta"
        abrir_pasta_button = QPushButton("Abrir Pasta")
        abrir_pasta_button.clicked.connect(self.abrir_pasta_sicaf)

        # Botão "Atualizar"
        atualizar_button = QPushButton("Atualizar")
        atualizar_button.clicked.connect(self.atualizar_lista)

        # Adiciona os botões ao layout horizontal
        top_right_layout.addWidget(abrir_pasta_button)
        top_right_layout.addWidget(atualizar_button)

        return top_right_layout

    def obter_texto_arquivos_pdf(self):
        """Gera o texto exibido para a quantidade de arquivos PDF encontrados."""
        quantidade = self.count_pdf_files()
        if quantidade == 0:
            return "Nenhum arquivo PDF encontrado na pasta."
        elif quantidade == 1:
            return "1 arquivo PDF encontrado na pasta."
        else:
            return f"{quantidade} arquivos PDF encontrados na pasta."
        
    def count_pdf_files(self):
        """Conta os arquivos PDF na pasta sicaf_dir."""
        if self.sicaf_dir.exists() and self.sicaf_dir.is_dir():
            return len(list(self.sicaf_dir.glob("*.pdf")))
        return 0
            
    def atualizar_lista(self):
        """Atualiza o conteúdo de self.left_list_widget com dados de empresa e cnpj e o conteúdo de self.pdf_list_widget com os arquivos PDF."""
        
        # Atualiza a lista de empresas e CNPJs no layout esquerdo
        self.left_list_widget.clear()
        unique_combinations = self.homologacao_dataframe[['empresa', 'cnpj']].drop_duplicates()

        for _, row in unique_combinations.iterrows():
            empresa = row['empresa']
            cnpj = row['cnpj']
            
            # Ignora combinações onde 'empresa' ou 'cnpj' são nulos
            if pd.isnull(empresa) or pd.isnull(cnpj):
                continue
            
            # Criação de um item no QListWidget
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

            # Define o ícone de acordo com a existência do CNPJ no banco de dados
            icon_label = QLabel()
            icon_label.setPixmap(self.get_icon_for_cnpj(cnpj).pixmap(24, 24))

            empresa_label = QLabel(f"{cnpj} - {empresa}")
            copiar_button = QPushButton("Copiar CNPJ")
            
            # Conectar o botão de cópia ao método de cópia
            copiar_button.clicked.connect(lambda _, cnpj=cnpj: self.copiar_para_area_de_transferencia(cnpj))

            # Adicionar ícone, botão e label ao layout do item
            item_layout.addWidget(icon_label)
            item_layout.addWidget(copiar_button)
            item_layout.addWidget(empresa_label)
            
            # Adiciona o item personalizado à QListWidget
            list_item = QListWidgetItem(self.left_list_widget)
            list_item.setSizeHint(item_widget.sizeHint())
            self.left_list_widget.addItem(list_item)
            self.left_list_widget.setItemWidget(list_item, item_widget)

        # Atualiza a lista de arquivos PDF no layout direito
        self.pdf_list_widget.clear()
        pdf_files = list(self.sicaf_dir.glob("*.pdf"))

        if pdf_files:
            for pdf_file in pdf_files:
                self.pdf_list_widget.addItem(pdf_file.name)
        else:
            self.pdf_list_widget.addItem("Nenhum arquivo PDF encontrado.")

        # Atualiza o texto do right_label com a contagem de arquivos PDF
        quantidade = len(pdf_files)
        if quantidade == 0:
            right_label_text = "Nenhum arquivo PDF encontrado na pasta."
        elif quantidade == 1:
            right_label_text = "1 arquivo PDF encontrado na pasta."
        else:
            right_label_text = f"{quantidade} arquivos PDF encontrados na pasta."

        # Atualiza o texto do right_label dinamicamente
        self.right_label.setText(right_label_text)

    def abrir_pasta_sicaf(self):
        """Abre o diretório sicaf_dir no explorador de arquivos, criando-o se não existir."""
        if not self.sicaf_dir.exists():
            self.sicaf_dir.mkdir(parents=True, exist_ok=True)
            
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.sicaf_dir)))


    def get_icon_for_cnpj(self, cnpj):
        """Verifica se o CNPJ existe na tabela registro_sicaf usando db_manager e retorna o ícone em cache correspondente."""
        try:
            query = "SELECT 1 FROM registro_sicaf WHERE cnpj = ?"
            result = self.db_manager.execute_query(query, (cnpj,))  # Retorna uma lista de resultados
            return self.icon_cache["confirm"] if result else self.icon_cache["cancel"]
        except Exception as e:
            QMessageBox.critical(self, "Erro no Banco de Dados", f"Erro ao acessar o banco de dados: {e}")
            return self.icon_cache["cancel"]  # Ícone padrão em caso de erro

    def load_icons(self):
        """Carrega ícones e os armazena em cache."""
        icon_cache = {}
        icon_paths = {
            "confirm": self.icons_dir / "confirm.png",
            "cancel": self.icons_dir / "cancel.png"
        }

        for key, path in icon_paths.items():
            icon = QIcon(str(path)) if path.exists() else QIcon()
            icon_cache[key] = icon

        return icon_cache

    def copiar_para_area_de_transferencia(self, cnpj):
        clipboard = QApplication.clipboard()
        clipboard.setText(cnpj)
        
        # Cria a QMessageBox manualmente
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("CNPJ Copiado")
        msg_box.setText(f"O CNPJ {cnpj} foi copiado para a área de transferência.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Cria um temporizador para fechar a mensagem automaticamente
        QTimer.singleShot(2000, msg_box.close)  # 2000 milissegundos = 2 segundos
        
        # Exibe a mensagem
        msg_box.exec()


padrao_1 = (r"UASG\s+(?P<uasg>\d+)\s+-\s+(?P<orgao_responsavel>.+?)\s+PREGÃO\s+(?P<num_pregao>\d+)/(?P<ano_pregao>\d+)")
padrao_srp = r"(?P<srp>SRP - Registro de Preço|SISPP - Tradicional)"
padrao_objeto = (r"Objeto da compra:\s*(?P<objeto>.*?)\s*Entrega de propostas:")

padrao_grupo2 = (
    r"Item\s+(?P<item>\d+)(?:\s+do\s+Grupo\s+G(?P<grupo>\d+))?.*?"
    r"Valor\s+estimado:\s+R\$\s+(?P<valor>[\d,\.]+).*?"
    r"(?:Critério\s+de\s+julgamento:\s+(?P<crit_julgamento>.*?))?\s*"
    r"Quantidade:\s+(?P<quantidade>\d+)\s+"
    r"Unidade\s+de\s+fornecimento:\s+(?P<unidade>.*?)\s+"
    r"Situação:\s+(?P<situacao>Adjudicado e Homologado|Deserto e Homologado|Fracassado e Homologado|Anulado e Homologado)"
)

padrao_item2 = (
    r"Item\s+(?P<item>\d+)\s+-\s+.*?"
    r"Quantidade:\s+(?P<quantidade>\d+)\s+"
    r"Valor\s+estimado:\s+R\$\s+(?P<valor>[\d,.]+)\s+"
    r"Unidade\s+de\s+fornecimento:\s+(?P<unidade>.*?)\s+"
    r"Situação:\s+(?P<situacao>Adjudicado e Homologado|Deserto e Homologado|Fracassado e Homologado|Anulado e Homologado)"
)


padrao_4 = (
    r"Proposta\s+adjudicada.*?"
    r"Marca/Fabricante\s*:\s*(?P<marca_fabricante>.*?)\s*"
    r"Modelo/versão\s*:\s*(?P<modelo_versao>.*?)(?=\s*\d{2}/\d{2}/\d{4}|\s*Valor\s+proposta\s*:)"
)

padrao_3 = (
    r"Adjucado\s+e\s+Homologado\s+por\s+CPF\s+(?P<cpf_od>\*\*\*.\d{3}.\*\*\*-\*\d{1})\s+-\s+"
    r"(?P<ordenador_despesa>[^\d,]+?)\s+para\s+"
    r"(?P<empresa>.*?)(?=\s*,\s*CNPJ\s+)"  # Captura o nome da empresa até a próxima vírgula e "CNPJ"
    r"\s*,\s*CNPJ\s+(?P<cnpj>\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}),\s+"
    r"melhor\s+lance\s*:\s*R\$\s*(?P<melhor_lance>[\d,.]+)"
    r"(?:,\s+valor\s+negociado\s*:\s*R\$\s*(?P<valor_negociado>[\d,.]+))?\s+"  # Captura opcional de "valor negociado"
    r"Propostas\s+do\s+Item"  # Finaliza a captura em "Propostas do Item"
)


def processar_item(match, conteudo: str, ultima_posicao_processada: int, padrao_3: str, padrao_4: str) -> dict:
    item = match.groupdict()
    item_data = {
        "item": int(item['item']) if 'item' in item and item['item'].isdigit() else 'N/A',
        "grupo": item.get('grupo', 'N/A'),
        "valor_estimado": item.get('valor', 'N/A'),
        "quantidade": item.get('quantidade', 'N/A'),
        "unidade": item.get('unidade', 'N/A'),
        "situacao": item.get('situacao', 'N/A')
    }

    # Somente tenta buscar correspondências de padrões adicionais se a situação não for 'Anulado e Homologado'
    if item_data['situacao'] not in ['Anulado e Homologado', 'Revogado e Homologado']:
        # Processamento do padrão 3
        match_3 = re.search(padrao_3, conteudo[ultima_posicao_processada:], re.DOTALL | re.IGNORECASE)
        if match_3:
            ultima_posicao_processada += match_3.end()
            empresa_name = match_3.group('empresa').replace('\n', ' ').strip() if match_3.group('empresa') else 'N/A'
            cnpj_value = match_3.group('cnpj').replace(" ", "").replace("\n", "") if match_3.group('cnpj') else 'N/A'
            melhor_lance = match_3.group('melhor_lance').replace(" ", "").replace("\n", "") if match_3.group('melhor_lance') else 'N/A'
            valor_negociado = match_3.group('valor_negociado')

            # Remove espaços e quebras de linha se valor_negociado não for None
            valor_negociado = valor_negociado.replace(" ", "").replace("\n", "") if valor_negociado else 'N/A'

            item_data.update({
                "melhor_lance": melhor_lance,
                "valor_negociado": valor_negociado,
                "ordenador_despesa": match_3.group('ordenador_despesa') or 'N/A',
                "empresa": empresa_name,
                "cnpj": cnpj_value,
            })

        # Processamento do padrão 4
        match_4 = re.search(padrao_4, conteudo[ultima_posicao_processada:], re.DOTALL | re.IGNORECASE)
        if match_4:
            item_data.update({
                "marca_fabricante": match_4.group('marca_fabricante') or 'N/A',
                "modelo_versao": match_4.group('modelo_versao') or 'N/A',
            })

    return item_data, ultima_posicao_processada

def create_dataframe_from_pdf_files(extracted_data):
    """
    Cria um DataFrame a partir de dados extraídos de arquivos de texto.
    
    Args:
        extracted_data (list): Lista de dicionários com os dados extraídos dos arquivos de texto.

    Returns:
        pd.DataFrame: DataFrame criado com os dados extraídos.
    """
    if not isinstance(extracted_data, list):
        raise TypeError("extracted_data deve ser uma lista de dicionários.")

    all_data = []
    print("\nIniciando processamento de extracted_data...\n")

    for idx, item in enumerate(extracted_data):
        # Verifica se 'item' é um dicionário e contém a chave 'text'
        if isinstance(item, dict) and 'text' in item and isinstance(item['text'], str):
            content = item['text']
            print(f"\nProcessando item {idx + 1} de {len(extracted_data)}:")
            print(f"Conteúdo: {content[:100]}...")  # Exibe os primeiros 100 caracteres para verificar o conteúdo

            uasg_pregao_data = extrair_uasg_e_pregao(content, padrao_1, padrao_srp, padrao_objeto)
            print(f"Dados UASG e Pregão extraídos: {uasg_pregao_data}")

            compra_data = extrair_objeto_da_compra(content)
            print(f"Dados de Objeto da Compra extraídos: {compra_data}")

            items_data = identificar_itens_e_grupos(content, padrao_grupo2, padrao_item2, padrao_3, padrao_4, pd.DataFrame())
            print(f"Dados dos Itens e Grupos extraídos: {items_data}")

            for item_data in items_data:
                # Verifica se item_data é um dicionário antes de adicionar a all_data
                if isinstance(item_data, dict):
                    all_data.append({
                        **uasg_pregao_data,
                        "objeto": compra_data,  # Ajusta para ter "objeto" como string do campo extraído
                        **item_data
                    })
                else:
                    print(f"Formato inesperado em item_data: {item_data}")
        else:
            print(f"Formato inválido em extracted_data: {item} (Tipo: {type(item)})")

    # Verifica se o all_data não está vazio antes de criar o DataFrame
    if not all_data:
        raise ValueError("Nenhum dado válido foi encontrado para criar o DataFrame.")

    dataframe_licitacao = pd.DataFrame(all_data)
    print("\nDataFrame criado com os dados extraídos:")
    print(dataframe_licitacao.head())  # Verifica os primeiros registros do DataFrame

    if "item" not in dataframe_licitacao.columns:
        raise ValueError("A coluna 'item' não foi encontrada no DataFrame.")
    
    return dataframe_licitacao.sort_values(by="item")

# Verificações adicionais nos pontos críticos da função de extração
def identificar_itens_e_grupos(conteudo: str, padrao_grupo2: str, padrao_item2: str, padrao_3: str, padrao_4: str, df: pd.DataFrame) -> list:
    conteudo = re.sub(r'\s+', ' ', conteudo).strip()
    itens_data = []
    itens = buscar_itens(conteudo, padrao_grupo2, padrao_item2)

    print(f"Total de itens encontrados: {len(itens)}")
    if len(itens) == 0:
        print("Nenhuma correspondência encontrada para os padrões fornecidos.")
    else:
        print(f"Itens encontrados: {[match.groupdict() for match in itens]}")

    ultima_posicao_processada = 0

    for idx, match in enumerate(itens):
        item_data, ultima_posicao_processada = processar_item(match, conteudo, ultima_posicao_processada, padrao_3, padrao_4)
        
        print(f"\nProcessando item {idx + 1}: {item_data}")
        
        item_data = process_cnpj_data(item_data)
        print(f"Item {idx + 1} após processar dados CNPJ: {item_data}")

        itens_data.append(item_data)

    print(f"\nItens finais processados: {itens_data}")
    return itens_data


def process_cnpj_data(cnpj_dict):
    """Converter "valor_estimado", "melhor_lance", e "valor_negociado" para float se não for possível deverá pular"""
    for field in ["valor_estimado", "melhor_lance", "valor_negociado"]:
        valor = cnpj_dict.get(field, 'N/A')  # Usa 'N/A' como valor padrão se a chave não existir
        if isinstance(valor, str):
            try:
                cnpj_dict[field] = float(valor.replace(".", "").replace(",", "."))
            except ValueError:
                cnpj_dict[field] = 'N/A'

    # Convert "quantidade" to integer if possible, otherwise keep as is
    quantidade = cnpj_dict.get("quantidade", 'N/A')
    try:
        cnpj_dict["quantidade"] = int(quantidade)
    except ValueError:
        pass

    # Ensure valor_homologado_item_unitario is defined
    valor_negociado = cnpj_dict.get("valor_negociado", 'N/A')
    if valor_negociado in [None, "N/A", "", "none", "null"]:
        cnpj_dict["valor_homologado_item_unitario"] = cnpj_dict.get("melhor_lance", 'N/A')
    else:
        cnpj_dict["valor_homologado_item_unitario"] = valor_negociado

    # Now perform the other calculations
    valor_estimado = cnpj_dict.get("valor_estimado", 'N/A')
    valor_homologado_item_unitario = cnpj_dict.get("valor_homologado_item_unitario", 'N/A')
    if valor_estimado != 'N/A' and valor_homologado_item_unitario != 'N/A':
        try:
            cnpj_dict["valor_estimado_total_do_item"] = cnpj_dict["quantidade"] * float(valor_estimado)
            cnpj_dict["valor_homologado_total_item"] = cnpj_dict["quantidade"] * float(valor_homologado_item_unitario)
            cnpj_dict["percentual_desconto"] = (1 - (float(valor_homologado_item_unitario) / float(valor_estimado))) * 100
        except ValueError:
            pass
            
    return cnpj_dict

def buscar_itens(conteudo: str, padrao_grupo2: str, padrao_item2: str) -> list:
    """
    Busca itens no conteúdo fornecido utilizando os padrões especificados.

    Args:
        conteudo (str): O texto onde os itens serão buscados.
        padrao_grupo2 (str): O padrão regex para capturar itens com estrutura 'Item do Grupo'.
        padrao_item2 (str): O padrão regex para capturar itens com estrutura 'Item -'.

    Returns:
        list: Uma lista de correspondências encontradas ou uma mensagem de falha.
    """
    # Normaliza os espaços em branco para tratar quebras de linha e múltiplos espaços
    conteudo = re.sub(r'\s+', ' ', conteudo).strip()

    # Primeiro, busca correspondências para padrao_item2 com re.DOTALL e re.IGNORECASE
    matches_item2 = list(re.finditer(padrao_item2, conteudo, re.DOTALL | re.IGNORECASE))
    if matches_item2:
        print(f"Total de correspondências para padrao_item2: {len(matches_item2)}")
        for idx, match in enumerate(matches_item2, start=1):
            print(f"Correspondência {idx} para padrao_item2: {match.groupdict()}")
        return matches_item2  # Retorna se encontrar correspondências para padrao_item2

    # Se não encontrou padrao_item2, tenta buscar correspondências para padrao_grupo2 com re.DOTALL e re.IGNORECASE
    matches_grupo2 = list(re.finditer(padrao_grupo2, conteudo, re.DOTALL | re.IGNORECASE))
    if matches_grupo2:
        print(f"Total de correspondências para padrao_grupo2: {len(matches_grupo2)}")
        for idx, match in enumerate(matches_grupo2, start=1):
            print(f"Correspondência {idx} para padrao_grupo2: {match.groupdict()}")
        return matches_grupo2  # Retorna se encontrar correspondências para padrao_grupo2

    # Se não encontrou correspondências para nenhum dos padrões, indica a falha
    print("Nenhuma correspondência encontrada para padrao_item2 ou padrao_grupo2.")
    return []  # Retorna uma lista vazia para indicar que não houve correspondências

def extrair_objeto_da_compra(conteudo: str) -> str:
    """
    Extrai o valor do 'Objeto da compra' usando uma regex mais robusta.

    Args:
        conteudo (str): O texto que contém o termo 'Objeto da compra'.

    Returns:
        str: O valor do 'Objeto da compra' se encontrado, caso contrário 'N/A'.
    """
    # Regex mais robusta para capturar o objeto da compra entre "Objeto da compra:" e "Entrega de propostas:"
    padrao_objeto_forte = r"Objeto\s+da\s+compra\s*:\s*(?P<objeto>.*?)\s*Entrega\s+de\s+propostas\s*:"

    # Tentar encontrar a correspondência usando o padrão fornecido
    match = re.search(padrao_objeto_forte, conteudo, re.DOTALL | re.IGNORECASE)

    # Verificar se a correspondência foi encontrada
    if match:
        print("Padrão Objeto encontrado:")
        print(f"Valor do Objeto: {match.group('objeto')}")
        return match.group("objeto").strip()
    else:
        print("Padrão Objeto não encontrado.")
        return "N/A"
    
def extrair_uasg_e_pregao(conteudo: str, padrao_1: str, padrao_srp: str, padrao_objeto: str) -> dict: 
    match = re.search(padrao_1, conteudo)
    match2 = re.search(padrao_srp, conteudo)
    match3 = re.search(padrao_objeto, conteudo)

    srp_valor = match2.group("srp") if match2 else "N/A"
    objeto_valor = match3.group("objeto") if match3 else "N/A"

    # Caso o padrao_objeto não encontre, tente com o padrao_objeto_forte
    if not match3:
        # Regex mais robusta para capturar o objeto da compra entre "Objeto da compra:" e "Entrega de propostas:"
        padrao_objeto_forte = r"Objeto\s+da\s+compra\s*:\s*(?P<objeto>.*?)\s*Entrega\s+de\s+propostas\s*:"
        match_forte = re.search(padrao_objeto_forte, conteudo, re.DOTALL | re.IGNORECASE)
        if match_forte:
            print("Padrão Objeto Forte encontrado:")
            print(f"Valor do Objeto: {match_forte.group('objeto')}")
            objeto_valor = match_forte.group("objeto").strip()
        else:
            print("Padrão Objeto Forte não encontrado.")

    # Adicionando prints para verificar se os padrões foram encontrados
    if match:
        print("Padrão 1 encontrado:")
    else:
        print("Padrão 1 não encontrado.")

    if match2:
        print("Padrão SRP encontrado")
    else:
        print("Padrão SRP não encontrado.")

    if match3 or match_forte:
        print("Padrão Objeto encontrado")
    else:
        print("Padrão Objeto não encontrado.")

    if match:
        return {
            "uasg": match.group("uasg"),
            "orgao_responsavel": match.group("orgao_responsavel"),
            "num_pregao": match.group("num_pregao"),
            "ano_pregao": match.group("ano_pregao"),
            "srp": srp_valor,
            "objeto": objeto_valor
        }
    return {}


def save_to_dataframe(extracted_data, tr_variavel_df_carregado, existing_dataframe=None):
    df_extracted = create_dataframe_from_pdf_files(extracted_data)
    df_extracted['item'] = pd.to_numeric(df_extracted['item'], errors='coerce').astype('Int64')
    
    if tr_variavel_df_carregado is not None:
        tr_variavel_df_carregado['item'] = pd.to_numeric(tr_variavel_df_carregado['item'], errors='coerce').astype('Int64')
        merged_df = pd.merge(tr_variavel_df_carregado, df_extracted, on='item', how='outer', suffixes=('_x', '_y'))

        for column in merged_df.columns:
            if column.endswith('_y'):
                col_x = column[:-2] + '_x'
                if col_x in merged_df.columns:
                    merged_df[col_x] = merged_df[col_x].combine_first(merged_df[column])
                merged_df.drop(columns=[column], inplace=True)
                merged_df.rename(columns={col_x: col_x[:-2]}, inplace=True)

        # Reordenando as colunas
        column_order = ['grupo', 'item', 'catalogo', 'descricao', 'unidade', 'quantidade', 'valor_estimado', 
                        'valor_homologado_item_unitario', 'percentual_desconto', 'valor_estimado_total_do_item', 'valor_homologado_total_item',
                        'marca_fabricante', 'modelo_versao', 'situacao', 'descricao_detalhada', 'uasg', 'orgao_responsavel', 'num_pregao', 'ano_pregao', 
                        'srp', 'objeto', 'melhor_lance', 'valor_negociado', 'ordenador_despesa', 'empresa', 'cnpj',
                        ]
        merged_df = merged_df.reindex(columns=column_order)

        if existing_dataframe is not None:
            final_df = pd.concat([existing_dataframe, merged_df]).drop_duplicates(subset='item').reset_index(drop=True)
        else:
            final_df = merged_df

        return final_df
    else:
        QMessageBox.warning(None, "Aviso", "Nenhum DataFrame de termo de referência carregado.")
        return None
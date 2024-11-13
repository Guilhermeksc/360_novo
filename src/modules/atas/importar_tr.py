import pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtSql import *
from PyQt6.QtCore import Qt
import os
import sqlite3
import logging
import subprocess

class DatabaseATASManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None

    def set_database_path(self, db_path):
        """Permite alterar dinamicamente o caminho do banco de dados."""
        self.db_path = db_path
        logging.info(f"Database path set to: {self.db_path}")

    def connect_to_database(self):
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            logging.info(f"Conexão com o banco de dados aberta em {self.db_path}")
        return self.connection

    def close_connection(self):
        if self.connection:
            logging.info("Fechando conexão com o banco de dados...")
            self.connection.close()
            self.connection = None
            logging.info(f"Conexão com o banco de dados fechada em {self.db_path}")

    def is_closed(self):
        return self.connection is None

    def __enter__(self):
        self.connect_to_database()
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def save_dataframe(self, df, table_name):
        conn = self.connect_to_database()
        try:
            df.to_sql(table_name, conn, if_exists='append', index=False)
            logging.info(f"DataFrame salvo na tabela {table_name}.")
        except sqlite3.IntegrityError as e:
            valor_duplicado = df.loc[df.duplicated(subset=['item'], keep=False), 'item']
            mensagem_erro = f"Erro ao salvar o DataFrame: Valor duplicado(s) encontrado(s) na coluna 'item': {valor_duplicado.to_list()}."
            logging.error(mensagem_erro)
            QMessageBox.warning(None, "Erro de Duplicação", mensagem_erro)
        except sqlite3.Error as e:
            logging.error(f"Erro ao salvar DataFrame: {e}")
        finally:
            self.close_connection()

    def delete_record(self, table_name, column, value):
        conn = self.connect_to_database()
        try:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE {column} = ?", (value,))
            conn.commit()
            logging.info(f"Registro deletado da tabela {table_name} onde {column} = {value}.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao deletar registro: {e}")
        finally:
            self.close_connection()

    def execute_query(self, query, params=None):
        conn = self.connect_to_database()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Erro ao executar consulta: {query}, Erro: {e}")
            return None
        finally:
            self.close_connection()

class SqlModel:
    def __init__(self, icons_dir, database_manager, parent=None):
        self.icons_dir = icons_dir
        self.database_manager = database_manager
        self.parent = parent
        self.init_database()

    def init_database(self):
        if QSqlDatabase.contains("my_conn"):
            QSqlDatabase.removeDatabase("my_conn")
        self.db = QSqlDatabase.addDatabase('QSQLITE', "my_conn")
        self.db.setDatabaseName(str(self.database_manager.db_path))
        if not self.db.open():
            print("Não foi possível abrir a conexão com o banco de dados.")
        else:
            print("Conexão com o banco de dados aberta com sucesso.")
            self.adjust_table_structure()

    def adjust_table_structure(self):
        query = QSqlQuery(self.db)
        if not query.exec("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_atas'"):
            print("Erro ao verificar existência da tabela:", query.lastError().text())
        if not query.next():
            print("Tabela 'controle_atas' não existe. Criando tabela...")
            self.create_table_if_not_exists()
        else:
            print("Tabela 'controle_atas' existe. Verificando estrutura da coluna...")

    def create_table_if_not_exists(self):
        query = QSqlQuery(self.db)
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS controle_atas (
                item INTEGER PRIMARY KEY AUTOINCREMENT, catalogo TEXT, descricao TEXT, descricao_detalhada TEXT
            )
        """):
            print("Erro ao criar a tabela 'controle_atas':", query.lastError().text())

    def setup_model(self, table_name, editable=False):
        self.model = CustomSqlTableModel(parent=self.parent, db=self.db, non_editable_columns=None, icons_dir=self.icons_dir)
        self.model.setTable(table_name)
        self.model.table_name = table_name  # Armazena o table_name no modelo

        if editable:
            self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        
        self.model.select()
        return self.model


    def configure_columns(self, table_view, visible_columns):
        for column in range(self.model.columnCount()):
            header = self.model.headerData(column, Qt.Orientation.Horizontal)
            if column not in visible_columns:
                table_view.hideColumn(column)
            else:
                self.model.setHeaderData(column, Qt.Orientation.Horizontal, header)

class CustomSqlTableModel(QSqlTableModel):
    def __init__(self, parent=None, db=None, non_editable_columns=None, icons_dir=None):
        super().__init__(parent, db)
        self.non_editable_columns = non_editable_columns or []
        self.icons_dir = icons_dir

    def flags(self, index):
        flags = super().flags(index)
        if index.column() in self.non_editable_columns:
            flags &= ~Qt.ItemFlag.ItemIsEditable
        return flags

class TermoReferenciaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Termo de Referência")
        self.resize(800, 600)
        self.parent = parent

        # Configuração do layout principal
        self.layout = QVBoxLayout(self)

        # Caminho do arquivo de banco de dados
        self.db_path = os.path.join(os.getcwd(), "termo_referencia.db")

        # Instanciar o DatabaseATASManager
        self.database_manager = DatabaseATASManager(self.db_path)

        # Instanciar o SqlModel
        self.sql_model_manager = SqlModel(icons_dir=None, database_manager=self.database_manager, parent=self)

        # Configurar o QTableView para exibir os dados
        self.table_view = QTableView(self)
        self.layout.addWidget(self.table_view)

        # Criar layout horizontal para os botões
        button_layout = QHBoxLayout()

        # Botão "Abrir Tabela Nova"
        self.btn_abrir_tabela_nova = QPushButton("Abrir Tabela Nova")
        self.btn_abrir_tabela_nova.clicked.connect(self.abrir_tabela_nova)
        button_layout.addWidget(self.btn_abrir_tabela_nova)

        # Botão "Carregar Tabela"
        self.btn_carregar_tabela = QPushButton("Carregar Tabela")
        self.btn_carregar_tabela.clicked.connect(self.carregar_tabela)
        button_layout.addWidget(self.btn_carregar_tabela)

        # Adicionar layout de botões ao layout principal
        self.layout.addLayout(button_layout)

        # Configurar o modelo SQL para visualização
        self.configurar_sql_model()

    def abrir_tabela_nova(self):
        # Define o caminho do arquivo Excel
        file_path = os.path.join(os.getcwd(), "tabela_nova.xlsx")
        
        # Cria um DataFrame vazio com as colunas especificadas
        df = pd.DataFrame(columns=["item", "catalogo", "descricao", "descricao_detalhada"])
        
        # Salva o DataFrame no arquivo Excel
        df.to_excel(file_path, index=False)

        # Abre o arquivo Excel após a criação (opcional)
        os.startfile(file_path)

    def carregar_tabela(self):
        try:
            caminho_arquivo, _ = QFileDialog.getOpenFileName(self, "Carregar Tabela", "", "Arquivos Excel (*.xlsx);;Todos os Arquivos (*)")
            if not caminho_arquivo:
                return  # Se o usuário cancelar o diálogo, saia da função

            # Carregar o arquivo Excel, filtrando apenas as colunas desejadas
            tabela = pd.read_excel(caminho_arquivo, usecols=['item', 'catalogo', 'descricao', 'descricao_detalhada'])
            
            # Inserir os dados no banco de dados
            self.inserir_dados_no_banco(tabela)
            
            # Atualizar o modelo após a inserção
            self.configurar_sql_model()
        
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar a tabela: {e}")
            print(f"Erro ao carregar a tabela: {e}")


    def inserir_dados_no_banco(self, tabela: pd.DataFrame):
        # Inserir os dados do DataFrame na tabela usando DatabaseATASManager
        try:
            self.database_manager.save_dataframe(tabela, "controle_atas")
            print("Dados inseridos no banco com sucesso.")
        except Exception as e:
            print(f"Erro ao inserir dados no banco: {e}")

    def configurar_sql_model(self):
        # Configurar o SqlModel para usar a tabela "controle_atas"
        self.model = self.sql_model_manager.setup_model("controle_atas", editable=True)
        
        # Configurar o QTableView com o modelo
        self.table_view.setModel(self.model)
        
        # Configurar colunas visíveis
        visible_columns = [1, 2, 3, 4]  # Especificar as colunas desejadas (ajustando de acordo com os índices)
        self.sql_model_manager.configure_columns(self.table_view, visible_columns)

        # Ajustar o tamanho das colunas
        self.table_view.setColumnWidth(0, 50)  # Primeira coluna com 50 de largura
        self.table_view.setColumnWidth(1, 50)  # Segunda coluna com 50 de largura
        self.table_view.setColumnWidth(2, 100) # Terceira coluna com 100 de largura
        self.table_view.horizontalHeader().setStretchLastSection(True) # Expandir a última coluna

        # Redimensionar para ajustar as colunas ao conteúdo
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_view.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
from src.modules.atas_novo.database_manager.db_manager import DatabaseATASManager
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import os
import pandas as pd
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery

class GerarAtasModel(QObject):
    tabelaCarregada = pyqtSignal() 

    def __init__(self, database_path, parent=None):
        super().__init__(parent)
        self.database_ata_manager = DatabaseATASManager(database_path)
        self.sql_model_manager = SqlModel(icons_dir=None, database_manager=self.database_ata_manager)


        self.db = None  # Adiciona um atributo para o banco de dados
        self.model = None  # Atributo para o modelo SQL
        self.init_database()  # Inicializa a conexão e a estrutura do banco de dados

    def init_database(self):
        """Inicializa a conexão com o banco de dados e ajusta a estrutura da tabela."""
        if QSqlDatabase.contains("my_conn"):
            QSqlDatabase.removeDatabase("my_conn")
        self.db = QSqlDatabase.addDatabase('QSQLITE', "my_conn")
        self.db.setDatabaseName(str(self.database_ata_manager.db_path))
        
        if not self.db.open():
            print("Não foi possível abrir a conexão com o banco de dados.")
        else:
            print("Conexão com o banco de dados aberta com sucesso.")
            self.adjust_table_atas_structure()  # Ajusta a estrutura da tabela, se necessário

    def setup_model(self, table_name, editable=False):
        """Configura o modelo SQL para a tabela especificada."""
        # Passa o database_manager para o modelo personalizado
        self.model = CustomSqlTableModel(parent=self, db=self.db, database_manager=self.database_ata_manager, non_editable_columns=[4, 8, 10, 13])
        self.model.setTable(table_name)
        
        if editable:
            self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        
        self.model.select()
        return self.model
    
    def adjust_table_atas_structure(self):
        """Verifica e cria a tabela 'controle_dispensas' se não existir."""
        query = QSqlQuery(self.db)
        if not query.exec("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_ata'"):
            print("Erro ao verificar existência da tabela:", query.lastError().text())
        if not query.next():
            print("Tabela 'controle_dispensas' não existe. Criando tabela...")
            self.create_table_if_not_exists()
        else:
            pass
            # print("Tabela 'controle_atas' existe. Verificando estrutura da coluna...")

    def create_table_if_not_exists(self):
        """Cria a tabela 'controle_dispensas' com a estrutura definida, caso ainda não exista."""
        query = QSqlQuery(self.db)
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS controle_atas (
                grupo TEXT,                         
                item TEXT PRIMARY KEY,
                catalogo TEXT,
                descrição TEXT,
                unidade TEXT,
                quantidade TEXT,
                valor_estimado TEXT,
                valor_homologado_item_unitario TEXT,
                percentual_desconto TEXT,
                valor_estimado_total_do_item TEXT,
                valor_homologado_total_item TEXT,
                marca_fabricante TEXT,
                modelo_versao TEXT,
                situacao TEXT,descricao_detalhada TEXT,
                uasg TEXT,
                orgao_responsavel TEXT,
                num_pregao TEXT,ano_pregao TEXT,
                srp TEXT,
                objeto TEXT,
                melhor_lance TEXT,
                valor_negociado TEXT,
                ordenador_despesa TEXT,
                empresa TEXT,
                cnpj TEXT,
                endereco TEXT,
                cep TEXT,
                municipio TEXT,
                telefone TEXT,
                email TEXT,
                responsavel_legal TEXT,
        ]          
            )
        """):
            print("Falha ao criar a tabela 'controle_atas':", query.lastError().text())
        else:
            print("Tabela 'controle_atas' criada com sucesso.")

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
            caminho_arquivo, _ = QFileDialog.getOpenFileName(None, "Carregar Tabela", "", "Arquivos Excel (*.xlsx);;Todos os Arquivos (*)")
            if not caminho_arquivo:
                return None  # Se o usuário cancelar o diálogo, saia da função

            # Carregar o arquivo Excel, filtrando apenas as colunas desejadas
            tabela = pd.read_excel(caminho_arquivo, usecols=['item', 'catalogo', 'descricao', 'descricao_detalhada'])
            
            # Inserir os dados no banco de dados
            self.inserir_dados_no_banco(tabela)
            
            # Emite o sinal indicando que a tabela foi carregada
            self.tabelaCarregada.emit()

        except Exception as e:
            print(f"Erro ao carregar a tabela: {e}")
            QMessageBox.critical(None, "Erro", f"Erro ao carregar a tabela: {e}")

    def inserir_dados_no_banco(self, tabela: pd.DataFrame):
        try:
            self.database_manager.save_dataframe(tabela, "controle_atas")
            print("Dados inseridos no banco com sucesso.")
        except Exception as e:
            print(f"Erro ao inserir dados no banco: {e}")

    def obter_sql_model(self):
        # Configura e retorna o modelo SQL para a tabela "controle_atas"
        return self.sql_model_manager.setup_model("controle_atas", editable=True)

class CustomSqlTableModel(QSqlTableModel):
    def __init__(self, parent=None, db=None, database_manager=None, non_editable_columns=None):
        super().__init__(parent, db)
        self.database_manager = database_manager
        self.non_editable_columns = non_editable_columns if non_editable_columns is not None else []
        
        # Define os nomes das colunas
        self.column_names = [
            'grupo', 'item', 'catalogo', 'descricao', 'unidade', 'quantidade', 'valor_estimado', 
            'valor_homologado_item_unitario', 'percentual_desconto', 'valor_estimado_total_do_item', 
            'valor_homologado_total_item', 'marca_fabricante', 'modelo_versao', 'situacao', 
            'descricao_detalhada', 'uasg', 'orgao_responsavel', 'num_pregao', 'ano_pregao', 
            'srp', 'objeto', 'melhor_lance', 'valor_negociado', 'ordenador_despesa', 'empresa', 
            'cnpj', 'endereco', 'cep', 'municipio', 'telefone', 'email', 'responsavel_legal'
        ]

    def flags(self, index):
        if index.column() in self.non_editable_columns:
            return super().flags(index) & ~Qt.ItemFlag.ItemIsEditable  # Remove a permissão de edição
        return super().flags(index)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # Verifica se a coluna deve ser não editável e ajusta o retorno para DisplayRole
        if role == Qt.ItemDataRole.DisplayRole and index.column() in self.non_editable_columns:
            return super().data(index, role)

        return super().data(index, role)
    
    def obter_sql_model(self):
        pass

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

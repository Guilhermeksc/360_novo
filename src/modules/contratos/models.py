from src.modules.planejamento.database_manager.db_manager import DatabaseManager
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from functools import partial
import sqlite3  
import re
from src.config.paths import BASE_DIR, DATA_CONTRATOS_PATH
from datetime import datetime

def create_table_if_not_exists():
    """Cria a tabela 'controle_contratos' com a estrutura definida, caso ainda não exista."""
    print("Conectando ao banco de dados...")
    try:
        connection = sqlite3.connect(DATA_CONTRATOS_PATH)
        cursor = connection.cursor()
        print(f"Banco de dados conectado: {DATA_CONTRATOS_PATH}")

        print("Verificando/criando a tabela 'controle_contratos'...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS controle_contratos (
                status TEXT, 
                dias INTEGER,
                prorrogavel TEXT,                         
                codigo_uasg TEXT,
                contrato_numero TEXT,
                tipo TEXT,
                licitacao_numero TEXT,
                nome_fornecedor TEXT,
                objeto TEXT,
                valor_global REAL,
                       sigla_om TEXT,                 
                nome_om TEXT, 
                cnpj_cpf_idgener TEXT,
                subtipo TEXT,                 
                custeio TEXT, 
                situacao TEXT, 
                categoria TEXT, 
                processo TEXT, 
                amparo_legal TEXT, 
                modalidade TEXT, 
                data_assinatura TEXT, 
                data_publicacao TEXT, 
                vigencia_inicial TEXT,
                vigencia_final TEXT,
                id VARCHAR(100) PRIMARY KEY
                                                         
            )
        ''')
        print("Tabela 'controle_contratos' verificada/criada com sucesso.")

        connection.commit()
        print("Alterações no banco de dados foram salvas.")
    except Exception as e:
        print(f"Erro ao criar/verificar a tabela 'controle_contratos': {e}")
    finally:
        connection.close()
        print("Conexão com o banco de dados encerrada.")

def salvar_dados_no_sqlite(df, db_path):
    """
    Salva o DataFrame no banco de dados SQLite, atualizando registros existentes e inserindo novos registros.

    :param df: pandas.DataFrame contendo os dados a serem salvos
    :param db_path: Caminho para o banco de dados SQLite
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Verificar se a tabela existe e possui a coluna 'id' no índice correto
            cursor.execute("PRAGMA table_info(controle_contratos);")
            columns_info = cursor.fetchall()
            id_column_info = next((col for col in columns_info if col[1] == 'id'), None)

            if id_column_info is None or id_column_info[0] != 24:
                raise ValueError("A tabela 'controle_contratos' não possui 'id' no índice correto.")

            # Definir as colunas necessárias para inserir ou atualizar
            columns = [
                'status', 'dias', 'prorrogavel', 'codigo_uasg', 'contrato_numero', 'tipo', 'licitacao_numero',
                'nome_fornecedor', 'objeto', 'valor_global', 'sigla_om',
                'nome_om', 'cnpj_cpf_idgener', 'subtipo', 'custeio', 'situacao', 'categoria', 'processo', 'amparo_legal',
                'modalidade', 'data_assinatura', 'data_publicacao', 'vigencia_inicial', 'vigencia_final', 'id'
            ]

            for _, row in df.iterrows():
                # Exibe o valor de 'status' e 'id' antes de salvar no banco de dados
                print(f"Status antes de salvar: {row['status']}, ID: {row['id']}")

                # Converter a linha em uma tupla com todos os valores necessários
                row_data = tuple(row.get(col, None) for col in columns)

                # Verificar se o registro já existe
                cursor.execute("SELECT COUNT(1) FROM controle_contratos WHERE id = ?", (row['id'],))
                exists = cursor.fetchone()[0] > 0

                if exists:
                    # Se o registro existir, execute UPDATE
                    update_query = f"""
                    UPDATE controle_contratos SET
                        {", ".join([f"{col} = ?" for col in columns if col != 'id'])}
                    WHERE id = ?;
                    """
                    # Garante que o número de valores corresponde aos placeholders
                    update_values = row_data[:-1] + (row_data[10],)  # row['id'] está na posição 10
                    cursor.execute(update_query, update_values)
                else:
                    # Se o registro não existir, execute INSERT
                    insert_query = f"""
                    INSERT INTO controle_contratos ({", ".join(columns)})
                    VALUES ({", ".join(["?" for _ in columns])});
                    """
                    cursor.execute(insert_query, row_data)

                # Exibe o valor de 'status' e 'id' após salvar no banco de dados
                print(f"Status salvo no banco: {row['status']}, ID: {row['id']}")

            conn.commit()
            print("Dados salvos no banco de dados com sucesso!")
    except Exception as e:
        print(f"Erro ao salvar no banco de dados: {e}")

class ContratosModel(QObject):
    def __init__(self, database_path, parent=None):
        super().__init__(parent)
        self.database_contratos_manager = DatabaseManager(database_path)
        self.db = None
        self.model = None
        self.init_database() 

    def init_database(self):
        """Inicializa a conexão com o banco de dados e ajusta a estrutura da tabela."""
        if QSqlDatabase.contains("my_conn"):
            QSqlDatabase.removeDatabase("my_conn")
        self.db = QSqlDatabase.addDatabase('QSQLITE', "my_conn")
        self.db.setDatabaseName(str(self.database_contratos_manager.db_path))
        
        if not self.db.open():
            print("Não foi possível abrir a conexão com o banco de dados.")
        else:
            print("Conexão com o banco de dados aberta com sucesso.")
    #         self.adjust_table_structure()  # Ajusta a estrutura da tabela, se necessário

    # def adjust_table_structure(self):
    #     query = QSqlQuery(self.db)
    #     if not query.exec("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_contratos'"):
    #         print("Erro ao verificar existência da tabela:", query.lastError().text())
    #     if not query.next():
    #         print("Tabela 'controle_contratos' não existe. Criando tabela... ContratosModel")
    #         create_table_if_not_exists()
    #     else:
    #         print("Tabela 'controle_contratos' existe. Verificando estrutura da coluna... ContratosModel")
    #         query.exec("PRAGMA table_info(controle_contratos);")
    #         columns = []
    #         while query.next():
    #             column_name = query.value(1)  # Coluna 1 contém o nome da coluna
    #             column_type = query.value(2)  # Coluna 2 contém o tipo da coluna
    #             columns.append((column_name, column_type))
            
    #         print("Estrutura atual da tabela 'controle_contratos':")
    #         for column_name, column_type in columns:
    #             print(f"Coluna: {column_name}, Tipo: {column_type}")

    #         # Exemplo de checagem de estrutura
    #         required_columns = [
    #             ("status", "TEXT"),
    #             ("dias", "INTEGER"),
    #             ("prorrogavel", "TEXT"),
    #             ("sigla_om", "TEXT"),
    #             ("contrato_numero", "TEXT"),
    #             ("tipo", "TEXT"),
    #             ("licitacao_numero", "TEXT"),
    #             ("nome_fornecedor", "TEXT"),
    #             ("objeto", "TEXT"),
    #             ("valor_global", "REAL"),
    #             ("codigo_uasg", "TEXT"),
    #             ("nome_om", "TEXT"),
    #             ("cnpj_cpf_idgener", "TEXT"),
    #             ("subtipo", "TEXT"),
    #             ("custeio", "TEXT"),
    #             ("situacao", "TEXT"),
    #             ("categoria", "TEXT"),
    #             ("processo", "TEXT"),
    #             ("amparo_legal", "TEXT"),
    #             ("modalidade", "TEXT"),
    #             ("data_assinatura", "TEXT"),
    #             ("data_publicacao", "TEXT"),
    #             ("vigencia_inicial", "TEXT"),
    #             ("vigencia_final", "TEXT"),
    #             ("id", "VARCHAR(100) PRIMARY KEY")
    #         ]

    #         missing_columns = [
    #             col for col, col_type in required_columns 
    #             if col not in [c[0] for c in columns] or col_type not in [c[1] for c in columns if c[0] == col]
    #         ]

    #         if missing_columns:
    #             print(f"As seguintes colunas estão ausentes ou têm tipos incompatíveis: {missing_columns}")
    #         else:
    #             print("Todas as colunas necessárias estão presentes e com tipos corretos.")


    def setup_model(self, table_name, editable=False):
        """Configura o modelo SQL para a tabela especificada."""
        # Passa o database_contratos_manager para o modelo personalizado
        self.model = CustomSqlTableModel(parent=self, db=self.db, database_manager=self.database_contratos_manager, non_editable_columns=[0, 4, 8, 10, 13])
        self.model.setTable(table_name)
        
        if editable:
            self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        
        self.model.select()
        return self.model

    def get_data(self, table_name):
        """Retorna todos os dados da tabela especificada."""
        return self.database_contratos_manager.fetch_all(f"SELECT * FROM {table_name}")
 

class CustomSqlTableModel(QSqlTableModel):
    def __init__(self, parent=None, db=None, database_manager=None, non_editable_columns=None):
        super().__init__(parent, db)
        self.database_contratos_manager = database_manager
        self.non_editable_columns = non_editable_columns if non_editable_columns is not None else []
        
        # Define os nomes das colunas
        self.column_names = [
                'status', 'dias', 'prorrogavel', 'codigo_uasg', 'contrato_numero', 'tipo', 'licitacao_numero', 
                'nome_fornecedor', 'objeto', 'valor_global', 'id',  'sigla_om',
                'nome_om', 'cnpj_cpf_idgener','subtipo', 'custeio', 'situacao', 'categoria', 'processo',  'amparo_legal', 
                'modalidade', 'data_assinatura', 'data_publicacao', 'vigencia_inicial', 'vigencia_final'
            ]

    def flags(self, index):
        if index.column() in self.non_editable_columns:
            return super().flags(index) & ~Qt.ItemFlag.ItemIsEditable  # Remove a permissão de edição
        return super().flags(index)

    def sort_by_column(self, column_index, order=Qt.SortOrder.AscendingOrder):
        """Ordena o modelo SQL pela coluna especificada."""
        print(f"Ordenando pela coluna {column_index} em ordem {'ascendente' if order == Qt.SortOrder.AscendingOrder else 'descendente'}")
        self.setSort(column_index, order)
        self.select()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # Coluna 'dias'
        if index.column() == self.fieldIndex("dias"):
            if role == Qt.ItemDataRole.DisplayRole:
                # Obtém o índice e valor da coluna "vigencia_final"
                vigencia_final_index = self.fieldIndex("vigencia_final")
                vigencia_final = self.index(index.row(), vigencia_final_index).data()

                # print(f"Vigência final obtida: {vigencia_final}")  # Print da data obtida

                if vigencia_final:
                    try:
                        # Tentativa de conversão para 'DD/MM/YYYY'
                        vigencia_final_date = datetime.strptime(vigencia_final, '%d/%m/%Y')
                        # print(f"Vigência final convertida (DD/MM/YYYY): {vigencia_final_date}")  # Print da conversão
                    except ValueError:
                        try:
                            # Tentativa de conversão para 'YYYY-MM-DD'
                            vigencia_final_date = datetime.strptime(vigencia_final, '%Y-%m-%d')
                            # print(f"Vigência final convertida (YYYY-MM-DD): {vigencia_final_date}")  # Print da conversão
                        except ValueError:
                            print("Erro na conversão da data. Formato inválido.")  # Print de erro
                            return "Data Inválida"

                    # Calcula os dias restantes
                    hoje = datetime.today()
                    dias = (vigencia_final_date - hoje).days
                    # print(f"Hoje: {hoje}, Vigência final: {vigencia_final_date}, Dias restantes: {dias}")  # Print do cálculo
                    return dias  # Retorna o contador de dias restantes ou vencidos
                else:
                    # print("Sem data para calcular.")  # Print caso não haja data
                    return "Erro"

            elif role == Qt.ItemDataRole.ForegroundRole:
                # Altera a cor do texto com base no valor de dias
                value = self.data(index, Qt.ItemDataRole.DisplayRole)
                if isinstance(value, int):  # Certifica-se de que o valor é numérico
                    if value < 0:
                        return QColor(195, 195, 195)  # Cinza
                    elif 0 <= value < 30:
                        return QColor(255, 0, 0)  # Vermelho vivo
                    elif 30 <= value < 60:
                        return QColor(255, 140, 0)  # Laranja forte
                    elif 60 <= value < 90:
                        return QColor(255, 200, 0)  # Amarelo alaranjado
                    elif 90 <= value < 120:
                        return QColor(255, 255, 0)  # Amarelo vivo
                    elif 120 <= value < 180:
                        return QColor(173, 255, 47)  # Verde amarelado
                    elif 180 <= value < 360:
                        return QColor(50, 205, 50)  # Verde médio
                    elif value > 360:
                        return QColor(0, 150, 255)  # Azul vivo para valores maiores que 360

        # Coluna 'prorrogável'
        if index.column() == self.fieldIndex("prorrogavel"):
            value = super().data(index, Qt.ItemDataRole.DisplayRole)
            if role == Qt.ItemDataRole.ForegroundRole:
                if value == "Sim":
                    return QColor(50, 205, 50) 
                elif value == "Não":
                    return QColor(255, 0, 0)

        return super().data(index, role)
    


        
    # def insert_or_update_data(self, data):
    #     print("Dados recebidos para salvar:", data)
    #     upsert_sql = '''
    #     INSERT INTO controle_contratos (
    #         status, dias, renova, sigla_om, contrato_numero, 
    #         tipo, licitacao_numero, nome_fornecedor, objeto, 
    #         valor_global, id, codigo_uasg, nome_om, cnpj_cpf_idgener, 
    #         subtipo, prorrogavel, custeio, categoria, processo, 
    #         amparo_legal, modalidade, data_assinatura, data_publicacao, 
    #         vigencia_inicial, vigencia_final        
    #     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #     ON CONFLICT(id) DO UPDATE SET
    #         status = excluded.status, dias = excluded.dias, renova = excluded.renova, sigla_om = excluded.sigla_om, contrato_numero = excluded.contrato_numero,
    #         tipo = excluded.tipo, licitacao_numero = excluded.licitacao_numero, nome_fornecedor = excluded.nome_fornecedor, objeto = excluded.objeto,
    #         valor_global = excluded.valor_global, codigo_uasg = excluded.codigo_uasg, nome_om = excluded.nome_om, cnpj_cpf_idgener = excluded.cnpj_cpf_idgener,
    #         subtipo = excluded.subtipo, prorrogavel = excluded.prorrogavel, custeio = excluded.custeio, categoria = excluded.categoria, processo = excluded.processo,
    #         amparo_legal = excluded.amparo_legal, modalidade = excluded.modalidade, data_assinatura,
    #         data_publicacao = excluded.data_publicacao, vigencia_inicial = excluded.vigencia_inicial, vigencia_final = excluded.vigencia_final

    #     '''

    #     # Verifica se 'situacao' está dentro dos valores válidos
    #     valid_situations = ["Seção de Contratos", "Aprovado", "Sessão Pública", "Homologado", "Empenhado", "Concluído", "Arquivado"]
    #     data['status'] = data.get('status', 'Seção de Contratos')
    #     if data['status'] not in valid_situations:
    #         data['status'] = 'Seção de Contratos'

    #     # Executa a inserção ou atualização
    #     try:
    #         with self.database_contratos_manager as conn:
    #             cursor = conn.cursor()
    #             cursor.execute(upsert_sql, (
    #                 data.get('status'), 
    #                 data.get('dias'),
    #                 data.get('renova'),
    #                 data.get('sigla_om'),
    #                 data.get('contrato_numero'),
    #                 data.get('tipo'),
    #                 data.get('licitacao_numero'),
    #                 data.get('nome_fornecedor'),
    #                 data.get('objeto'),
    #                 data.get('valor_global'), data.get('id'), data.get('codigo_uasg'), data.get('nome_om'), data.get('cnpj_cpf_idgener'),
    #                 data.get('subtipo'), data.get('prorrogavel'), data.get('custeio'), data.get('categoria'), data.get('processo'),
    #                 data.get('objeto'), data.get('amparo_legal'), data.get('modalidade'), data.get('data_assinatura'), data.get('data_publicacao'),
    #                 data.get('vigencia_inicial'), data.get('vigencia_final')                                                                           
    #             ))
    #             conn.commit()

    #     except sqlite3.OperationalError as e:
    #         if "no such table" in str(e):
    #             QMessageBox.warning(None, "Erro", "A tabela 'controle_contratos' não existe. Por favor, crie a tabela primeiro.")
    #             return
    #         else:
    #             QMessageBox.warning(None, "Erro", f"Ocorreu um erro ao tentar salvar os dados: {str(e)}")  
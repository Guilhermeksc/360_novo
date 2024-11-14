from PyQt6.QtWidgets import *
import sqlite3
import logging
import pandas as pd

class DatabaseATASManager:
    def __init__(self, db_path):
        self.db_path = str(db_path)
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
            # Identifica itens duplicados na tabela e exclui-os
            cursor = conn.cursor()
            duplicados = df['item'].tolist()
            placeholders = ', '.join('?' for _ in duplicados)
            delete_query = f"DELETE FROM {table_name} WHERE item IN ({placeholders})"
            cursor.execute(delete_query, duplicados)
            
            # Insere o novo DataFrame após excluir os duplicados
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
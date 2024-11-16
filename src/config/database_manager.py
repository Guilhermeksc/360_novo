import sqlite3
from pathlib import Path

class DatabaseManager:
    def __init__(self, database_path):
        self.database_path = Path(database_path)
        self._validate_database()

    def _validate_database(self):
        """Verifica se o banco de dados e seu diretório existem, cria se necessário."""
        if not self.database_path.parent.exists():
            print(f"Creating directory: {self.database_path.parent}")
            self.database_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.database_path.exists():
            print(f"Creating database file: {self.database_path}")
            with sqlite3.connect(self.database_path) as conn:
                pass  # Cria um arquivo vazio, se não existir.

    def execute_query(self, query, params=None):
        """
        Executa uma consulta no banco de dados.

        Args:
            query (str): Consulta SQL.
            params (tuple, optional): Parâmetros para a consulta. Defaults to None.

        Returns:
            list: Resultado da consulta.
        """
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise Exception(f"Erro ao executar consulta: {e}")

    def execute_non_query(self, query, params=None):
        """
        Executa uma operação no banco de dados que não retorna resultados (INSERT, UPDATE, DELETE).

        Args:
            query (str): Consulta SQL.
            params (tuple, optional): Parâmetros para a consulta. Defaults to None.
        """
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Erro ao executar operação: {e}")

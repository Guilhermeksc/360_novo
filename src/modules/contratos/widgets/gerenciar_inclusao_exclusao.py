from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import pandas as pd
import sqlite3
from contextlib import contextmanager
import os
import json
import requests
from src.config.paths import BASE_DIR, DATA_CONTRATOS_PATH

class RequestThread(QThread):
    data_received = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    save_json = pyqtSignal(object, str)

    def __init__(self, unidade_codigo):
        super().__init__()
        self.unidade_codigo = unidade_codigo

    def run(self):
        url = "https://contratos.comprasnet.gov.br/api/contrato/ug/{self.unidade_codigo}"
        print(f"Request endpoint: {url}")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)

            print("Raw response content:", response.text)

            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                data = {"data": data}  # Certificando-se de que o dado é um dicionário conforme o formato esperado

            self.data_received.emit(data)
            self.save_json.emit(data, self.unidade_codigo)
        except requests.exceptions.HTTPError as http_err:
            error_message = f"HTTP error occurred: {http_err}"
            print(error_message)
            self.error_occurred.emit(error_message)
        except Exception as err:
            error_message = f"Other error occurred: {err}"
            print(error_message)
            self.error_occurred.emit(error_message)

class GerenciarInclusaoExclusaoContratos(QDialog):
    def __init__(self, icons_dir, model, required_columns, parent=None):
        super().__init__(parent)
        self.icons_dir = icons_dir
        self.model = model
        self.required_columns = required_columns
        self.setWindowTitle("Sincronizar Contratos")
        self.setFixedSize(400, 300)  # Define o tamanho fixo da janela
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        # Adicionando o ícone e o label "Sincronizar"
        icon_confirm = QIcon(str(self.icons_dir / "synchronize.png"))
        sync_layout = QHBoxLayout()

        sync_icon_label = QLabel()
        sync_icon_label.setPixmap(icon_confirm.pixmap(80, 80))  # Adiciona o ícone ao QLabel

        sync_label = QLabel("Sincronizar")
        sync_label.setStyleSheet("font-size: 40px; font-weight: bold;")  # Define o tamanho da fonte para 40 e negrito

        sync_layout.addWidget(sync_icon_label)  # Adiciona o QLabel com o ícone ao layout
        sync_layout.addWidget(sync_label)  # Adiciona o QLabel "Sincronizar" ao layout
        sync_layout.addStretch()
        self.layout.addLayout(sync_layout)

        # Adicionando link para documentação da API
        link_label = QLabel('<a href="https://contratos.comprasnet.gov.br/api/docs">Documentação da API</a>')
        link_label.setStyleSheet("font-size: 16px")
        link_label.setOpenExternalLinks(True)
        self.layout.addWidget(link_label)

        # Adicionando labels de informações da API
        get_label = QLabel('GET "/api/contrato/ug/{unidade_codigo}"')
        get_label.setStyleSheet("font-size: 16px")
        self.layout.addWidget(get_label)

        unidade_codigo_info_label = QLabel('"{unidade_codigo} = uasg"')
        unidade_codigo_info_label.setStyleSheet("font-size: 16px")
        self.layout.addWidget(unidade_codigo_info_label)

        # Layout horizontal para o label e o QLineEdit
        unidade_layout = QHBoxLayout()

        unidade_label = QLabel("Digite o número da UASG:")
        unidade_label.setStyleSheet("font-size: 16px")
        unidade_layout.addWidget(unidade_label)

        self.unidade_codigo_input = QLineEdit(self)
        self.unidade_codigo_input.setPlaceholderText("Digite o código da unidade (6 dígitos)")
        unidade_layout.addWidget(self.unidade_codigo_input)



        self.baixar_json_button = QPushButton("Sincronizar", self)
        self.baixar_json_button.clicked.connect(self.baixar_json)
        unidade_layout.addWidget(self.baixar_json_button)

        self.layout.addLayout(unidade_layout)  # Adiciona o layout horizontal ao layout principal
        # Adicionando os botões existentes
        self.layout.addLayout(self.create_button_layout())

    def create_button_layout(self):
        button_layout = QHBoxLayout()
        self.excluir_database_button = QPushButton("Excluir Database", self)
        self.excluir_database_button.clicked.connect(self.excluir_database)
        button_layout.addWidget(self.excluir_database_button)

        self.carregar_tabela_button = QPushButton("Carregar Tabela", self)
        self.carregar_tabela_button.clicked.connect(self.carregar_tabela)
        button_layout.addWidget(self.carregar_tabela_button)

        self.sincronizar_csv_button = QPushButton("Sincronizar CSV", self)
        self.sincronizar_csv_button.clicked.connect(self.sincronizar_csv)
        button_layout.addWidget(self.sincronizar_csv_button)

        return button_layout

    def baixar_json(self):
        unidade_codigo = self.unidade_codigo_input.text()
        if len(unidade_codigo) == 6 and unidade_codigo.isdigit():
            self.thread = RequestThread(unidade_codigo)
            self.thread.data_received.connect(self.on_data_received)
            self.thread.error_occurred.connect(self.on_error_occurred)
            self.thread.save_json.connect(self.save_json)
            self.thread.start()
        else:
            QMessageBox.warning(self, "Entrada Inválida", "Por favor, insira um código de unidade válido de 6 dígitos.")

    def on_data_received(self, data):
        # QMessageBox.information(self, "Sucesso", "Dados recebidos com sucesso!")
        self.processar_dados_para_tabela(data)

    def on_error_occurred(self, error_message):
        QMessageBox.critical(self, "Erro", error_message)

    def save_json(self, data, unidade_codigo):
        """Salvar o JSON recebido no diretório base do projeto."""
        file_path = os.path.join(BASE_DIR, f"contratos_{unidade_codigo}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "Sucesso", f"Arquivo JSON salvo em {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar o arquivo JSON: {e}")

    def processar_dados_para_tabela(self, data):
        """Processa os dados JSON para criar uma tabela e salva em um banco de dados SQLite."""
        contratos_list = []
        for contrato in json ...:
            prorrogavel = "Sim" if contrato.get("prorrogavel") == "Sim" else "Não"
            custeio = ""
            dias = ""
            status = "Seção de Contratos"
            
            contrato_info = {
                "status": status,
                "dias": dias,
                "id": contrato.get("id"),
                "licitacao_numero": contrato.get("licitacao_numero"),
                "contrato_numero": contrato.get("numero"),
                "codigo_uasg": contrato["contratante"]["orgao"]["unidade_gestora"].get("codigo"),
                "sigla_om": contrato["contratante"]["orgao"]["unidade_gestora"].get("nome_resumido"),
                "nome_om": contrato["contratante"]["orgao"]["unidade_gestora"].get("nome"),
                "cnpj_cpf_idgener": contrato["fornecedor"].get("cnpj_cpf_idgener"),
                "nome_fornecedor": contrato["fornecedor"].get("nome"),
                "tipo": contrato.get("tipo"),
                "subtipo": contrato.get("subtipo"),
                "prorrogavel": prorrogavel,
                "custeio": custeio,
                "situacao": contrato.get("situacao"),
                "categoria": contrato.get("categoria"),
                "processo": contrato.get("processo"),
                "objeto": contrato.get("objeto"),
                "amparo_legal": contrato.get("amparo_legal"),
                "modalidade": contrato.get("modalidade"),
                "licitacao_numero": contrato.get("licitacao_numero"),
                "data_assinatura": contrato.get("data_assinatura"),
                "data_publicacao": contrato.get("data_publicacao"),
                "vigencia_inicial": contrato.get("vigencia_inicio"),
                "vigencia_final": contrato.get("vigencia_final"),
                "valor_global": contrato.get("valor_global")
            }
            contratos_list.append(contrato_info)

        df = pd.DataFrame(contratos_list)

        for column in self.required_columns:
            if column not in df.columns:
                df[column] = None 

        self.salvar_dados_no_sqlite(df)
        
    def hide_unwanted_columns(self):
        # Função para ocultar colunas não desejadas
        for column in range(self.parent().model.columnCount()):
            if column not in [4, 7, 8, 9]:
                self.table_view.setColumnHidden(column, True)
            else:
                self.table_view.setColumnHidden(column, False)

    def create_button_layout(self):
        button_layout = QHBoxLayout()
        self.excluir_database_button = QPushButton("Excluir Database", self)
        self.excluir_database_button.clicked.connect(self.excluir_database)
        button_layout.addWidget(self.excluir_database_button)

        return button_layout

    def excluir_database(self):
        reply = QMessageBox.question(self, 'Confirmar Exclusão', 'Tem certeza que deseja excluir a tabela controle_contratos?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.database_manager.execute_query("DROP TABLE IF EXISTS controle_contratos")
                QMessageBox.information(self, "Sucesso", "Tabela controle_contratos excluída com sucesso.")
            except Exception as e:
                QMessageBox.warning(self, "Erro ao excluir", f"Erro ao excluir a tabela: {str(e)}")

    def format_numero_contrato(self, contrato, uasg):
        numero, ano = contrato.split('/')
        ano_formatado = ano[-2:]
        numero_formatado = numero.lstrip('0')  # Remove apenas os zeros à esquerda
        if len(numero_formatado) < 3:
            numero_formatado = numero_formatado.zfill(3)  # Garante que tenha pelo menos 3 dígitos
        numero_contrato = f'{uasg}/{ano_formatado}-{numero_formatado}/00'
        print(f"Original: {contrato} -> Formatado: {numero_contrato}")
        return numero_contrato
    
class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """Estabelece uma conexão com o banco de dados."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path, timeout=10)  # Ajuste o timeout conforme necessário
        return self.connection

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.connection:
            self.connection.close()
            self.connection = None

    @contextmanager
    def transaction(self):
        """Gerencia uma transação de banco de dados."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()  # Confirma a transação se tudo correr bem
        except sqlite3.DatabaseError as e:
            conn.rollback()  # Reverte a transação em caso de erro
            QMessageBox.critical(None, "Erro", f"Erro ao acessar o banco de dados: {e}")
        finally:
            self.close()
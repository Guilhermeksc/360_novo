from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sqlite3
import requests
import sqlite3
from src.config.paths import DATA_CONTRATOS_PATH, JSON_DIR, JSON_CONTRATOS_DIR
from src.modules.contratos.models import create_table_if_not_exists, salvar_dados_no_sqlite
from src.modules.utils.add_button import add_button_func
import os
import json
import pandas as pd

class ContratosManager(QWidget):
    def __init__(self, icons, dados):
        super().__init__()
        self.icons = icons
        self.dados = dados
        self.model = self.create_model()  # Crie um modelo para gerenciar a inclusão dos dados no banco de dados SQLite
        self.init_ui()

    def create_model(self):
        # Conexão com o banco de dados SQLite
        connection = sqlite3.connect(DATA_CONTRATOS_PATH)
        create_table_if_not_exists()  # Garante que a tabela está criada antes de qualquer operação
        return connection

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        # Adicionando o ícone e o label "Sincronizar"
        icon_confirm = QIcon()
        icon_confirm = self.icons.get("synchronize", QIcon())
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

        # Adicionando o campo CustomQLineEdit
        unidade_layout = QHBoxLayout()
        unidade_label = QLabel("Digite o número da UASG:")
        unidade_label.setStyleSheet("font-size: 16px")
        unidade_layout.addWidget(unidade_label)

        self.unidade_codigo_input = CustomQLineEdit(self)
        unidade_layout.addWidget(self.unidade_codigo_input)

        add_button_func(
            "Consultar", 
            "json", 
            self.baixar_json, 
            unidade_layout, 
            self.icons, 
            tooltip="Clique para baixar os dados em JSON da unidade"
        )

        self.layout.addLayout(unidade_layout)  # Adiciona o layout horizontal ao layout principal

        # Adicionando layout de mensagens de progresso
        self.layout_mensagens_progresso()

        self.setLayout(self.layout)

        add_button_func(
            "Sincronizar", 
            "synchronize", 
            self.consolidar_dados, 
            unidade_layout, 
            self.icons, 
            tooltip="Clique para sincronizar os dados das unidades consultadas"
        )

    def baixar_json(self):
        unidade_codigo = self.unidade_codigo_input.text()
        if len(unidade_codigo) == 6 and unidade_codigo.isdigit():
            self.thread = RequestThread(unidade_codigo)
            self.thread.error_occurred.connect(self.on_error_occurred)
            self.thread.save_json.connect(self.save_json)
            self.thread.start()
        else:
            QMessageBox.warning(self, "Entrada Inválida", "Por favor, insira um código de unidade válido de 6 dígitos.")

    def layout_mensagens_progresso(self):
        self.layout_progresso = QVBoxLayout()
        self.layout.addLayout(self.layout_progresso)

        self.progresso_label = QLabel("Sincronizando...")
        self.progresso_label.setStyleSheet("font-size: 16px")
        self.layout_progresso.addWidget(self.progresso_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.layout_progresso.addWidget(self.progress_bar)

    def consolidar_dados(self):
        print("Etapa 1: Verificando a estrutura dos arquivos JSON.")
        try:
            self.verificar_estrutura_json()
            print("Estrutura dos arquivos JSON verificada com sucesso.")
        except Exception as e:
            print(f"Erro ao verificar a estrutura dos arquivos JSON: {e}")
            return

        print("Etapa 2: Consolidando os arquivos JSON.")
        try:
            self.consolidar_arquivos_json()
            print("Arquivos JSON consolidados com sucesso.")
        except Exception as e:
            print(f"Erro ao consolidar os arquivos JSON: {e}")
            return

        print("Etapa 3: Processando dados para tabela.")
        try:
            caminho_consolidado = os.path.join(JSON_DIR, "contratos_consolidados.json")
            with open(caminho_consolidado, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                self.processar_dados_para_tabela(dados)
        except Exception as e:
            print(f"Erro ao processar dados para tabela: {e}")
            return

        print("Processo de consolidação de dados concluído com sucesso.")

    def verificar_estrutura_json(self):
        estrutura_correta = {
            "data": [
                {
                    "id": int,
                    "receita_despesa": str,
                    "numero": str,
                    "contratante": {
                        "orgao_origem": {
                            "codigo": str,
                            "nome": str,
                            "unidade_gestora_origem": {
                                "codigo": str,
                                "nome_resumido": str,
                                "nome": str,
                                "sisg": str,
                                "utiliza_siafi": str,
                                "utiliza_antecipagov": str,
                            },
                        },
                        "orgao": {
                            "codigo": str,
                            "nome": str,
                            "unidade_gestora": {
                                "codigo": str,
                                "nome_resumido": str,
                                "nome": str,
                                "sisg": str,
                                "utiliza_siafi": str,
                                "utiliza_antecipagov": str,
                            },
                        },
                    },
                    "fornecedor": {
                        "tipo": str,
                        "cnpj_cpf_idgener": str,
                        "nome": str,
                    },
                    "codigo_tipo": str,
                    "tipo": str,
                    "subtipo": (str, type(None)),
                    "prorrogavel": (str, type(None)),  # Ajuste aqui
                    "situacao": str,
                    "justificativa_inativo": (str, type(None)),
                    "categoria": str,
                    "subcategoria": (str, type(None)),
                    "unidades_requisitantes": (str, type(None)),
                    "processo": str,
                    "objeto": str,
                    "amparo_legal": str,
                    "informacao_complementar": (str, type(None)),
                    "codigo_modalidade": str,
                    "modalidade": str,
                    "unidade_compra": str,
                    "licitacao_numero": str,
                    "sistema_origem_licitacao": (str, type(None)),
                    "data_assinatura": str,
                    "data_publicacao": (str, type(None)),
                    "data_proposta_comercial": (str, type(None)),
                    "vigencia_inicio": str,
                    "vigencia_fim": (str, type(None)),
                    "valor_inicial": str,
                    "valor_global": str,
                    "num_parcelas": int,
                    "valor_parcela": str,
                    "valor_acumulado": str,
                    "links": dict,
                }
            ]
        }

        for file_name in os.listdir(JSON_CONTRATOS_DIR):
            if file_name.endswith(".json"):
                file_path = os.path.join(JSON_CONTRATOS_DIR, file_name)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        if self._validar_estrutura(data, estrutura_correta):
                            print(f"{file_name}: Estrutura correta")
                        else:
                            print(f"{file_name}: Estrutura incorreta")
                except Exception as e:
                    QMessageBox.critical(self, "Erro ao processar JSON", f"Erro no arquivo {file_name}: {e}")

    def _validar_estrutura(self, data, estrutura):
        """Valida se o JSON corresponde à estrutura esperada."""
        if isinstance(estrutura, dict):
            if not isinstance(data, dict):
                print(f"Erro: Esperado dict, recebido {type(data).__name__}")
                return False
            for key, value in estrutura.items():
                if key not in data:
                    print(f"Erro: Campo '{key}' ausente no JSON")
                    return False
                if not self._validar_estrutura(data[key], value):
                    print(f"Erro: Estrutura incorreta para o campo '{key}'")
                    return False
        elif isinstance(estrutura, list):
            if not isinstance(data, list):
                print(f"Erro: Esperado list, recebido {type(data).__name__}")
                return False
            if len(estrutura) > 0:
                for item in data:
                    if not self._validar_estrutura(item, estrutura[0]):
                        print("Erro: Estrutura incorreta dentro da lista")
                        return False
        elif isinstance(estrutura, tuple):
            if not any(isinstance(data, t) for t in estrutura):
                print(f"Erro: Tipo esperado {estrutura}, recebido {type(data).__name__}")
                return False
        else:
            if not isinstance(data, estrutura):
                print(f"Erro: Tipo esperado {estrutura.__name__}, recebido {type(data).__name__}")
                return False
        return True

    def on_error_occurred(self, error_message):
        QMessageBox.critical(self, "Erro", error_message)

    def save_json(self, data, unidade_codigo):
        """Salvar o JSON recebido no diretório base do projeto."""
        file_path = os.path.join(JSON_CONTRATOS_DIR, f"contratos_{unidade_codigo}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "Sucesso", f"Arquivo JSON salvo em {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar o arquivo JSON: {e}")
            
    def consolidar_arquivos_json(self):
        """Consolida todos os arquivos JSON no diretório em um único arquivo."""
        consolidado = []
        arquivos_json = [f for f in os.listdir(JSON_CONTRATOS_DIR) if f.endswith('.json')]

        for arquivo in arquivos_json:
            caminho_arquivo = os.path.join(JSON_CONTRATOS_DIR, arquivo)
            try:
                with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    for contrato in dados.get("data", []):
                        prorrogavel = "Sim" if contrato.get("prorrogavel") == "Sim" else "Não"
                        contrato_info = {
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
                            "situacao": contrato.get("situacao"),
                            "categoria": contrato.get("categoria"),
                            "processo": contrato.get("processo"),
                            "objeto": contrato.get("objeto"),
                            "amparo_legal": contrato.get("amparo_legal"),
                            "modalidade": contrato.get("modalidade"),
                            "data_assinatura": contrato.get("data_assinatura"),
                            "data_publicacao": contrato.get("data_publicacao"),
                            "vigencia_inicial": contrato.get("vigencia_inicio"),
                            "vigencia_final": contrato.get("vigencia_fim"),
                            "valor_global": contrato.get("valor_global"),
                        }
                        consolidado.append(contrato_info)
            except Exception as e:
                print(f"Erro ao processar {arquivo}: {e}")

        # Salvar o arquivo consolidado
        caminho_consolidado = os.path.join(JSON_DIR, "contratos_consolidados.json")
        try:
            with open(caminho_consolidado, 'w', encoding='utf-8') as f:
                json.dump(consolidado, f, ensure_ascii=False, indent=4)
            print(f"Arquivo consolidado salvo em {caminho_consolidado}")
        except Exception as e:
            print(f"Erro ao salvar o arquivo consolidado: {e}")

    def processar_dados_para_tabela(self, data):
        """Processa os dados JSON para criar uma tabela e salva em um banco de dados SQLite."""
        print("Iniciando processamento de dados para tabela...")

        # Verifica se os dados são uma lista ou um dicionário com chave 'data'
        if isinstance(data, dict) and "data" in data:
            contratos = data["data"]
        elif isinstance(data, list):
            contratos = data
        else:
            raise ValueError("Estrutura de dados inválida para processamento.")

        contratos_list = []

        for contrato in contratos:
            try:

                prorrogavel = "Sim" if contrato.get("prorrogavel") == "Sim" else "Não"
                custeio = ""
                dias = ""
                status = "Seção de Contratos"

                contrato_info = {
                    "status": status,
                    "dias": dias,
                    "id": contrato.get("id"),
                    "licitacao_numero": contrato.get("licitacao_numero"),
                    "contrato_numero": contrato.get("contrato_numero"),
                    "codigo_uasg": contrato.get("codigo_uasg", ""),
                    "sigla_om": contrato.get("sigla_om", ""),
                    "nome_om": contrato.get("nome_om", ""),
                    "cnpj_cpf_idgener": contrato.get("cnpj_cpf_idgener", ""),
                    "nome_fornecedor": contrato.get("nome_fornecedor", ""),
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
                    "vigencia_inicial": contrato.get("vigencia_inicial"),
                    "vigencia_final": contrato.get("vigencia_final"),
                    "valor_global": contrato.get("valor_global")
                }
                contratos_list.append(contrato_info)

            except Exception as e:
                print(f"Erro ao processar contrato ID {contrato.get('id', 'desconhecido')}: {e}")

        # Criação do DataFrame
        df = pd.DataFrame(contratos_list)
        # Salvar os dados no banco de dados SQLite
        salvar_dados_no_sqlite(df, DATA_CONTRATOS_PATH)


class RequestThread(QThread):
    data_received = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    save_json = pyqtSignal(object, str)

    def __init__(self, unidade_codigo):
        super().__init__()
        self.unidade_codigo = unidade_codigo

    def run(self):
        # Corrigido o uso de f-string para interpolar a unidade_codigo na URL
        url = f"https://contratos.comprasnet.gov.br/api/contrato/ug/{self.unidade_codigo}"
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

class CustomQLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPlaceholderText("Digite o código da unidade (6 dígitos)")
        self.textChanged.connect(self.validar_valor)
        self.botao_sincronizar = None  # Para associar o botão de sincronizar

    def validar_valor(self):
        """Valida o valor digitado pelo usuário."""
        texto_atual = self.text().strip()
        if not texto_atual.isdigit() or len(texto_atual) > 6:
            # Se não for um número ou tiver mais de 6 dígitos, exibe borda vermelha
            self.setStyleSheet("border: 1px solid red;")
            if self.botao_sincronizar:
                self.botao_sincronizar.setEnabled(False)  # Desativa o botão
        else:
            # Valor válido (6 dígitos)
            self.setStyleSheet("")
            if self.botao_sincronizar:
                self.botao_sincronizar.setEnabled(True)  # Ativa o botão

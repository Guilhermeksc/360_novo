from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from datetime import datetime
import sqlite3
from src.modules.utils.add_button import add_button_func

class AddItemDialog(QDialog):
    def __init__(self, icons, database_path, controle_om, parent=None):
        super().__init__(parent)
        self.icons = icons
        self.database_path = database_path
        self.controle_om = controle_om
        self.om_details = {}  # Inicializa como dicionário vazio para evitar erros
        self.setWindowTitle("Adicionar Item")
        self.setWindowIcon(self.icons["plus"])

        self.layout = QVBoxLayout(self)
        self.setStyleSheet("QWidget { font-size: 14px; }")

        self.setup_ui()
        self.load_sigla_om()  # Preenche self.om_details com dados do banco
        self.load_next_numero()

    def setup_ui(self):
        self.tipo_cb, self.numero_le, self.ano_le = self.setup_first_line()
        self.situacao_cb = self.setup_second_line()  # Adicionei este método
        self.objeto_le = self.setup_third_line()
        self.nup_le, self.sigla_om_cb = self.setup_fourth_line()
        self.material_radio, self.servico_radio = self.setup_fifth_line()
        add_button_func("Adicionar", "plus", self.on_save, self.layout, self.icons, tooltip="Adicionar Item ao Banco de Dados")
                    
    def setup_first_line(self):
        hlayout = QHBoxLayout()
        tipo_cb = QComboBox()
        numero_le = QLineEdit()
        ano_le = QLineEdit()

        [tipo_cb.addItem(option[0]) for option in [("Pregão Eletrônico (PE)", "Pregão Eletrônico")]]
        tipo_cb.setCurrentText("Pregão Eletrônico (PE)")
        numero_le.setValidator(QIntValidator(1, 99999))
        ano_le.setValidator(QIntValidator(1000, 9999))
        ano_le.setText(str(datetime.now().year))
        hlayout.addWidget(QLabel("Tipo:"))
        hlayout.addWidget(tipo_cb)
        hlayout.addWidget(QLabel("Número:"))
        hlayout.addWidget(numero_le)
        hlayout.addWidget(QLabel("Ano:"))
        hlayout.addWidget(ano_le)
        add_button_func("Renumerar", "rotate", self.open_id_processo_dialog, hlayout, self.icons, tooltip="Renumerar Licitação")
        self.layout.addLayout(hlayout)

        return tipo_cb, numero_le, ano_le

    def setup_second_line(self):
        hlayout = QHBoxLayout()
        situacao_cb = QComboBox()
        situacoes = ["Planejamento", "Consolidação de Demanda", "Em andamento", "Concluído"]
        situacao_cb.addItems(situacoes)
        situacao_cb.setCurrentIndex(0)
        hlayout.addWidget(QLabel("Situação:"))
        hlayout.addWidget(situacao_cb)
        self.layout.addLayout(hlayout)
        return situacao_cb

    def setup_third_line(self):
        hlayout = QHBoxLayout()
        objeto_le = QLineEdit()
        objeto_le.setPlaceholderText("Exemplo: 'Material de Limpeza' (Utilizar no máximo 3 palavras)")
        hlayout.addWidget(QLabel("Objeto:"))
        hlayout.addWidget(objeto_le)
        self.layout.addLayout(hlayout)
        return objeto_le

    def setup_fourth_line(self):
        hlayout = QHBoxLayout()
        nup_le = QLineEdit()
        sigla_om_cb = QComboBox()
        nup_le.setPlaceholderText("Exemplo: '00000.00000/0000-00'")
        hlayout.addWidget(QLabel("Nup:"))
        hlayout.addWidget(nup_le)
        hlayout.addWidget(QLabel("OM:"))
        hlayout.addWidget(sigla_om_cb)
        self.layout.addLayout(hlayout)
        return nup_le, sigla_om_cb

    def setup_fifth_line(self):
        hlayout = QHBoxLayout()
        material_radio = QRadioButton("Material")
        servico_radio = QRadioButton("Serviço")
        group = QButtonGroup(self)
        group.addButton(material_radio)
        group.addButton(servico_radio)
        material_radio.setChecked(True)

        hlayout.addWidget(QLabel("Material/Serviço:"))
        hlayout.addWidget(material_radio)
        hlayout.addWidget(servico_radio)
        self.layout.addLayout(hlayout)
        return material_radio, servico_radio

    def on_save(self):
        data = self.get_data()
        print(f"Dados recebidos para salvar: {data}")  # Adicionado para depuração
        try:
            if self.check_id_exists(data['id_processo']):
                res = QMessageBox.question(
                    self, "Confirmação",
                    "ID do processo já existe. Deseja sobrescrever?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if res == QMessageBox.StandardButton.Yes:
                    self.accept()  # Substitui o diálogo aceitar com a sobreposição
            else:
                self.accept()  # Aceita normalmente se o ID do processo não existir
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                QMessageBox.warning(self, "Erro", "A tabela 'controle_licitacao' não existe. Por favor, atualize a interface gráfica do módulo.")
            else:
                QMessageBox.warning(self, "Erro", f"Ocorreu um erro: {str(e)}")

    def check_id_exists(self, id_processo):
        query = "SELECT 1 FROM controle_licitacao WHERE id_processo = ?"
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (id_processo,))
                return cursor.fetchone() is not None
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                QMessageBox.warning(self, "Erro", "A tabela 'controle_licitacao' não existe. Por favor, crie a tabela primeiro.")
            else:
                raise 

    def load_next_numero(self):
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                # Converte o campo `numero` em um inteiro para garantir a comparação correta
                cursor.execute("SELECT MAX(CAST(numero AS INTEGER)) FROM controle_licitacao")
                max_number = cursor.fetchone()[0]
                next_number = 1 if max_number is None else int(max_number) + 1
                self.numero_le.setText(str(next_number))
        except Exception as e:
            print(f"Erro ao carregar o próximo número: {e}")

    def get_data(self):
        # Define o valor de 'sigla_om' como "CeIMBra" se a seleção atual estiver vazia
        sigla_selected = self.sigla_om_cb.currentText() or "CeIMBra"

        # Define valores padrão para 'orgao_responsavel' e 'uasg' caso 'sigla_selected' não esteja em 'self.om_details'
        orgao_responsavel = self.om_details.get(sigla_selected, {}).get('orgao_responsavel', "Orgão Padrão")
        uasg = self.om_details.get(sigla_selected, {}).get('uasg', "000000")

        material_servico = "Material" if self.material_radio.isChecked() else "Serviço"
        tipo_de_processo = self.tipo_cb.currentText()

        # Ajuste para obter o valor correto de 'situacao'
        if hasattr(self, 'situacao'):
            situacao = self.situacao  # Valor atribuído no open_id_processo_dialog
        else:
            situacao = self.situacao_cb.currentText()  # Valor selecionado no combo box

        data = {
            'tipo': tipo_de_processo,
            'numero': self.numero_le.text(),
            'ano': self.ano_le.text(),
            'nup': self.nup_le.text(),
            'objeto': self.objeto_le.text(),
            'sigla_om': sigla_selected,
            'orgao_responsavel': orgao_responsavel,
            'uasg': uasg,
            'material_servico': material_servico,
            'objeto_completo': getattr(self, 'objeto_completo', ''),
            'valor_total': getattr(self, 'valor_total', 0.0),
            'srp': getattr(self, 'srp', False),
            'situacao': situacao,
        }

        # Mapeamento do tipo de processo para o nome interno
        tipo_map = {
            "Pregão Eletrônico (PE)": ("PE", "Pregão Eletrônico"),
            "Concorrência": ("CC", "Concorrência"),
            "Termo de Justificativa de Dispensa de Licitação": ("TJDL", "Termo de Justificativa de Dispensa de Licitação"),
            "Termo de Justificativa de Inexigibilidade de Licitação": ("TJIL", "Termo de Justificativa de Inexigibilidade de Licitação"),
            "Chamada Pública para Agricultura Familiar": ("AF", "Chamada Pública"),
            "Adesão a Ata de Registro de Preços": ("AD", "Adesão a Ata de Registro de Preços"),
        }
        
        if tipo_de_processo in tipo_map:
            abreviatura, nome_interno = tipo_map[tipo_de_processo]
            data['tipo'] = nome_interno
            data['id_processo'] = f"{abreviatura} {data['numero']}/{data['ano']}"
        else:
            data['tipo'] = "Tipo Desconhecido"
            data['id_processo'] = f"Desconhecido {data['numero']}/{data['ano']}"

        return data
    
    def load_sigla_om(self):
        try:
            with sqlite3.connect(self.controle_om) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT sigla_om, orgao_responsavel, uasg FROM controle_om ORDER BY sigla_om")
                self.om_details = {"CeIMBra": {"orgao_responsavel": "Centro de Intendência da Marinha em Brasília", "uasg": "787010"}}
                self.sigla_om_cb.clear()
                ceimbra_found = False
                default_index = 0

                for index, row in enumerate(cursor.fetchall()):
                    sigla, orgao, uasg = row
                    self.sigla_om_cb.addItem(sigla)
                    self.om_details[sigla] = {"orgao_responsavel": orgao, "uasg": uasg}
                    if sigla == "CeIMBra":
                        ceimbra_found = True
                        default_index = index

                if ceimbra_found:
                    self.sigla_om_cb.setCurrentIndex(default_index)
                else:
                    self.sigla_om_cb.setCurrentText("CeIMBra")

        except Exception as e:
            print(f"Erro ao carregar siglas de OM: {e}")
            # Garantindo a existência de "CeIMBra" em caso de erro de carregamento
            self.om_details = {"CeIMBra": {"orgao_responsavel": "Centro de Intendência da Marinha em Brasília", "uasg": "787010"}}
            self.sigla_om_cb.addItem("CeIMBra")
            self.sigla_om_cb.setCurrentText("CeIMBra")


    def open_id_processo_dialog(self):
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id_processo, objeto FROM controle_licitacao ORDER BY id_processo")
                id_processo_objeto_list = cursor.fetchall()

            if not id_processo_objeto_list:
                QMessageBox.information(self, "Informação", "Não há id_processo disponível.")
                return

            # Cria uma instância do diálogo personalizado
            dialog = IdProcessoDialog(self.icons, id_processo_objeto_list, parent=self)
            if dialog.exec():
                selected_id = dialog.get_selected_id()
                if selected_id:
                    # Busca os dados correspondentes ao 'id_processo' selecionado
                    with sqlite3.connect(self.database_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT tipo, numero, ano, objeto, nup, sigla_om, material_servico, objeto_completo, valor_total, srp, situacao
                            FROM controle_licitacao WHERE id_processo = ?
                        """, (selected_id,))
                        result = cursor.fetchone()
                        if result:
                            (tipo, numero_antigo, ano_antigo, objeto_antigo, nup, sigla_om, material_servico,
                             objeto_completo, valor_total, srp, situacao) = result
                        else:
                            QMessageBox.warning(self, "Erro", "Dados não encontrados para o id_processo selecionado.")
                            return

                    # Exibe a mensagem de confirmação
                    res = QMessageBox.question(
                        self,
                        "Confirmação",
                        f"Deseja renumerar a licitação {selected_id} - {objeto_antigo}?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if res == QMessageBox.StandardButton.Yes:
                        print(f"Renumerando a licitação: {selected_id} - {objeto_antigo}")
                        # Atualiza os campos com os dados selecionados
                        self.tipo_cb.setCurrentText(tipo)
                        # self.numero_le.setText(numero)  # Comentado conforme seu código
                        self.ano_le.setText(ano_antigo)
                        self.objeto_le.setText(objeto_antigo)
                        self.nup_le.setText(nup)
                        index = self.sigla_om_cb.findText(sigla_om)
                        if index != -1:
                            self.sigla_om_cb.setCurrentIndex(index)
                        else:
                            self.sigla_om_cb.setCurrentText(sigla_om)
                        # Atualiza o radio button de material/serviço
                        if material_servico == "Material":
                            self.material_radio.setChecked(True)
                        else:
                            self.servico_radio.setChecked(True)
                        # Salva outras variáveis não visíveis
                        self.objeto_completo = objeto_completo
                        self.valor_total = valor_total
                        self.srp = srp
                        self.situacao = situacao

                        # Atualiza o combo box de situação
                        index = self.situacao_cb.findText(situacao)
                        if index != -1:
                            self.situacao_cb.setCurrentIndex(index)
                        else:
                            self.situacao_cb.addItem(situacao)
                            self.situacao_cb.setCurrentText(situacao)

                        # **Início das alterações para adicionar o texto ao objeto do item original**

                        # Obter os valores de 'numero' e 'ano' da nova licitação
                        novo_numero = self.numero_le.text()
                        novo_ano = self.ano_le.text()

                        # Construir o texto a ser adicionado
                        renumerado_texto = f"(Renumerado {novo_numero}/{novo_ano}) "

                        # Atualizar o campo 'objeto' do item original no banco de dados
                        novo_objeto_antigo = renumerado_texto + objeto_antigo

                        try:
                            with sqlite3.connect(self.database_path) as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE controle_licitacao
                                    SET objeto = ?
                                    WHERE id_processo = ?
                                """, (novo_objeto_antigo, selected_id))
                                conn.commit()
                                print(f"Objeto do item original atualizado para: {novo_objeto_antigo}")
                        except Exception as e:
                            print(f"Erro ao atualizar o objeto do item original: {e}")

                        # **Fim das alterações**

        except Exception as e:
            print(f"Erro ao carregar id_processo: {e}")
            QMessageBox.warning(self, "Erro", f"Não foi possível carregar os id_processo.\nErro: {e}")


# Classe do diálogo personalizado
class IdProcessoDialog(QDialog):
    def __init__(self, icons, id_processo_objeto_list, parent=None):
        super().__init__(parent)
        self.icons = icons
        self.id_processo_objeto_list = id_processo_objeto_list
        self.selected_id = None
        self.setWindowTitle("Renumerar Licitação")
        self.setWindowIcon(self.icons["rotate"])  # Define o ícone da janela como "rotate"

        self.layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        label = QLabel("Selecione o id_processo:")
        self.list_widget = QListWidget()
        # Adiciona os itens no formato "id_processo - objeto"
        for id_processo, objeto in self.id_processo_objeto_list:
            self.list_widget.addItem(f"{id_processo} - {objeto}")
        self.list_widget.itemDoubleClicked.connect(self.accept_selection)

        btn_layout = QHBoxLayout()
        # Utiliza o 'add_button_func' conforme o seu código
        add_button_func("Selecionar", "check", self.accept_selection, btn_layout, self.icons, tooltip="Selecionar o número da licitação para ser renumerado")        
        add_button_func("Cancelar", "cancel", self.reject, btn_layout, self.icons, tooltip="Fechar a Janela")        

        self.layout.addWidget(label)
        self.layout.addWidget(self.list_widget)
        self.layout.addLayout(btn_layout)

    def accept_selection(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            # Extrai o 'id_processo' do item selecionado
            text = current_item.text()
            id_processo = text.split(' - ')[0]  # Assume que o 'id_processo' não contém ' - '
            self.selected_id = id_processo
            self.accept()
        else:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um id_processo.")

    def get_selected_id(self):
        return self.selected_id

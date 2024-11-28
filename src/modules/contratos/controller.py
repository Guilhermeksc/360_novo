from src.modules.planejamento.models import LicitacaoModel
from src.modules.planejamento.views import LicitacaoWidget
from src.modules.planejamento.dialogs.add_item import AddItemDialog
from src.modules.planejamento.dialogs.salvar_tabela import DataManager
from src.modules.planejamento.dialogs.graficos import GraficTableDialog
from src.modules.planejamento.dialogs.gerar_tabela import TabelaResumidaManager
from src.modules.contratos.widgets.edit_data import EditarDadosContratos
from src.modules.planejamento.database_manager.db_manager import DatabaseManager
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import pandas as pd
from src.config.paths import CONTROLE_DADOS
import sqlite3
import os
from src.modules.dispensa_eletronica.dados_api.api_consulta import ConsultaAPIDialog
from PyQt6.QtSql import QSqlQuery

class ContratosController(QObject): 
    def __init__(self, icons, view, model):
        super().__init__()
        self.icons = icons
        self.view = view
        self.edit_data_dialog = None
        self.model_add = model
        self.model = model.setup_model("controle_contratos")
        self.controle_om = CONTROLE_DADOS  # Atribui o caminho diretamente ao controle_om                
        self.setup_connections()

    def setup_connections(self):
        # Conecta os sinais da view aos métodos do controlador
        self.view.alterar_status.connect(self.handle_alterar_status)
        self.view.rowDoubleClicked.connect(self.handle_edit_item)

    def handle_edit_item(self, data):
        # Passa os valores para a instância de handle_edit_item
        self.edit_data_dialog = EditarDadosContratos(
            data, self.icons, self.view
        )
        # Conecta o sinal para salvar os dados
        self.edit_data_dialog.save_data_signal.connect(self.handle_save_data)

        # Conecta o sinal de fechamento para atualizar o modelo
        self.edit_data_dialog.window_closed.connect(self._atualizar_modelo_apos_edicao)

        # Exibe a janela de edição
        self.edit_data_dialog.show()

    def _atualizar_modelo_apos_edicao(self):
        """
        Atualiza o modelo após o fechamento do diálogo de edição.
        """
        print("Atualizando o modelo após edição...")
        self.model.select()  # Recarrega os dados no modelo
        self.view.refresh_model()  # Atualiza a exibição na interface
        print("Modelo atualizado com sucesso.")

    def refresh_view(self):
        # Atualiza a visualização da tabela após alterações nos dados
        self.view.model.select()  # Recarrega os dados no modelo

    def handle_alterar_status(self, data):
        """Atualiza o status no banco de dados e recarrega a view."""
        try:
            # Atualiza o status no banco de dados
            row_id = data.get("id")  # Certifique-se de que a coluna ID está nos dados
            new_status = data.get("status")
            if row_id is not None and new_status:
                query = QSqlQuery(self.model.database())
                query.prepare("UPDATE controle_contratos SET status = :status WHERE id = :id")
                query.bindValue(":status", new_status)
                query.bindValue(":id", row_id)
                if not query.exec():
                    raise sqlite3.Error(query.lastError().text())
                self.refresh_view()
            else:
                QMessageBox.warning(self.view, "Erro", "Dados incompletos para alterar o status.")
        except sqlite3.Error as e:
            QMessageBox.warning(self.view, "Erro", f"Ocorreu um erro ao alterar o status: {str(e)}")
            
    def handle_save_data(self, data):
        try:
            # Use `self.model_add` que se refere a uma instância de `DispensaEletronicaModel`
            self.model_add.insert_or_update_data(data)
            self.view.refresh_model()  # Atualiza a visualização da tabela
        except AttributeError as e:
            QMessageBox.warning(self.view, "Erro", f"Ocorreu um erro ao salvar os dados: {str(e)}")

    def salvar_tabela_completa(self):
        try:
            self.model.select()
            tabela_manager = TabelaResumidaManager(self.model)
            tabela_manager.carregar_dados()
            output_path = os.path.join(os.getcwd(), "tabela_completa.xlsx")
            tabela_manager.exportar_df_completo_para_excel(output_path)
            tabela_manager.abrir_arquivo_excel(output_path)
        except PermissionError:
            QMessageBox.warning(self.view, "Erro de Permissão", 
                                "Feche o arquivo 'tabela_completa.xlsx' se ele estiver aberto e tente novamente.")

    def salvar_tabela_resumida(self):
        try:
            self.model.select()
            tabela_manager = TabelaResumidaManager(self.model)
            tabela_manager.carregar_dados()
            output_path = os.path.join(os.getcwd(), "tabela_resumida.xlsx")
            tabela_manager.exportar_para_excel(output_path)
            tabela_manager.abrir_arquivo_excel(output_path)
        except PermissionError:
            QMessageBox.warning(self.view, "Erro de Permissão", 
                                "Feche o arquivo 'tabela_resumida.xlsx' se ele estiver aberto e tente novamente.")
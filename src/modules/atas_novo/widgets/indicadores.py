from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt
import pandas as pd
import os
import locale
from src.modules.utils.add_button import add_button_func
from src.modules.utils.linha_layout import linha_divisoria_layout

# Configurar o locale para formato brasileiro
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

class IndicadoresWidget(QWidget):
    def __init__(self, icons, database_ata_manager, main_window, parent=None):
        super().__init__(parent)
        self.icons = icons
        self.db_manager = database_ata_manager
        self.main_window = main_window
        self.homologacao_dataframe = None  # Inicializa como None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Configuração inicial e widgets
        header_title = QLabel("Indicadores")
        header_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(header_title)

        # Carregar os dados iniciais, se disponíveis
        if self.homologacao_dataframe is None:
            self.homologacao_dataframe = pd.DataFrame()  # Inicializa com um DataFrame vazio

        # Criação do ComboBox para seleção de tabelas
        selecao_layout = QHBoxLayout()

        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        selecao_layout.addItem(spacer)

        selecao_label = QLabel("Selecione a Licitação:")
        selecao_label.setFont(QFont('Arial', 14))
        selecao_layout.addWidget(selecao_label)

        self.selecao_combobox = QComboBox()
        self.selecao_combobox.setFixedWidth(350)
        self.selecao_combobox.setFont(QFont('Arial', 12))
        selecao_layout.addWidget(self.selecao_combobox)
        layout.addLayout(selecao_layout)

        indicador_layout = QHBoxLayout()
        indicador_layout.addStretch()
        # Inicialização do QLabel para valor de economicidade (vazio inicialmente)
        self.valor_economicidade = QLabel("Clique em 'Recalcular' para calcular o Indicador de Economicidade.")
        self.valor_economicidade.setFont(QFont('Arial', 14))
        self.valor_economicidade.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Botão para recalcular economicidade

        indicador_layout.addWidget(self.valor_economicidade)
        add_button_func("Recalcular", "economy", self.atualizar_economicidade, indicador_layout, self.icons, "Clique para calcular o indicador de Economicidade.")  
        indicador_layout.addStretch()        
        layout.addLayout(indicador_layout)

        # Inicialização do QTableView
        self.table_view = QTableView(self)
        self.table_view.setFont(QFont('Arial', 10))
        layout.addWidget(self.table_view)

        linha_divisoria1, spacer_baixo_linha1 = linha_divisoria_layout()
        layout.addWidget(linha_divisoria1)
        layout.addSpacerItem(spacer_baixo_linha1)   

        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Espaço flexível à esquerda
        add_button_func("Gerar Tabela XLSX", "process", self.gerar_tabela_excel, button_layout, self.icons, "Clique para Gerar a Tabela em Excel")  
        button_layout.addStretch()  # Espaço flexível à direita
        layout.addLayout(button_layout)

        # Carregar tabelas no ComboBox
        self.carregar_tabelas_result()

        # Configuração do layout principal
        self.setLayout(layout)

    def carregar_tabelas_result(self):
        # Obtém tabelas cujo nome começa com "result"
        tabelas_result = self.db_manager.get_tables_with_keyword("result")
        print(f"Tabelas encontradas: {tabelas_result}")

        # Limpa o ComboBox antes de adicionar novos itens
        self.selecao_combobox.clear()

        if len(tabelas_result) == 1:
            tabela = tabelas_result[0]
            self.homologacao_dataframe = self.db_manager.load_table_to_dataframe(tabela)
            print(f"Carregando tabela única: {tabela}")
            print(self.homologacao_dataframe.head())

            self.selecao_combobox.addItem(tabela)
            self.selecao_combobox.setCurrentIndex(0)
        else:
            for tabela in tabelas_result:
                if tabela.startswith("result"):
                    self.selecao_combobox.addItem(tabela)
            self.selecao_combobox.currentIndexChanged.connect(self.atualizar_dataframe_selecionado)

    def atualizar_economicidade(self):
        """Atualiza o QLabel com o valor da economicidade e informações detalhadas."""
        print("Chamando calcular_economicidade...")
        economicidade_percentual = self.calcular_economicidade()
        
        # Obtém o texto atual do combobox
        selecao_texto = self.selecao_combobox.currentText()

        # Extrai número, ano e UASG a partir do padrão do texto
        try:
            if selecao_texto.startswith("resultAPI_"):
                _, numero, ano, uasg = selecao_texto.split("_", 3)
            else:
                _, numero, ano, uasg = selecao_texto.split("_", 3)

            # Atualiza o texto do QLabel com as informações detalhadas
            self.valor_economicidade.setText(
                f"{economicidade_percentual:.2f}% de economia média ({numero}/{ano} - UASG: {uasg})"
            )
        except ValueError as e:
            print(f"Erro ao processar o texto do ComboBox: {e}")
            # Caso o texto do ComboBox não esteja no formato esperado
            self.valor_economicidade.setText(
                f"{economicidade_percentual:.2f}% de economia média (Informações adicionais indisponíveis)"
            )

    def atualizar_dataframe_selecionado(self):
        tabela = self.selecao_combobox.currentText()
        print(f"Tabela selecionada no ComboBox: {tabela}")

        if tabela:
            self.homologacao_dataframe = self.db_manager.load_table_to_dataframe(tabela)
            print(f"DataFrame carregado da tabela '{tabela}':")
            print(self.homologacao_dataframe.head())  # Exibe uma amostra da tabela carregada

            # Verificar se a coluna 'situacao' existe
            if 'situacao' not in self.homologacao_dataframe.columns:
                print("Coluna 'situacao' ausente. Adicionando...")
                self.homologacao_dataframe['situacao'] = None  # Adicionar coluna com valores padrão

            self.atualizar_tabela()
        else:
            print("Nenhuma tabela selecionada.")

    def atualizar_tabela(self):
        """Atualiza a QTableView com o DataFrame e configura os títulos das colunas."""
        if self.homologacao_dataframe is not None:
            model = QStandardItemModel()

            # Definir os títulos personalizados para as colunas
            column_titles = {
                1: "Item",
                3: "Descrição",
                5: "Unidade de\nFornecimento",
                7: "Valor\nEstimado",
                8: "Valor\nHomologado",
                9: "Percentual\nDesconto (%)",
                14: "Situação"
            }

            # Aplicar os títulos personalizados ou os padrões
            headers = [column_titles.get(i, f"Coluna {i}") for i in range(self.homologacao_dataframe.shape[1])]
            model.setHorizontalHeaderLabels(headers)

            # Adicionar os dados ao modelo
            for row in self.homologacao_dataframe.itertuples(index=False):
                items = []
                for col, value in enumerate(row):
                    if col in [7, 8]:  # Colunas 7 e 8 (Valor Estimado e Valor Homologado)
                        try:
                            # Verificar se o valor é NaN ou inválido
                            if pd.isnull(value):
                                formatted_value = ""  # Não exibir nada para valores NaN
                            else:
                                # Converter para numérico e formatar como moeda
                                numeric_value = float(value)
                                formatted_value = locale.currency(numeric_value, grouping=True)
                        except (ValueError, TypeError):
                            formatted_value = ""  # Valor inválido ou ausente
                        items.append(QStandardItem(formatted_value))
                    elif col == 9:  # Coluna 8 (Percentual de Desconto)
                        try:
                            # Verificar se o valor é NaN ou inválido
                            if pd.isnull(value):
                                formatted_value = ""
                            else:
                                # Converter para numérico e formatar como percentual
                                numeric_value = float(value)
                                formatted_value = f"{numeric_value:.2f}%"
                        except (ValueError, TypeError):
                            formatted_value = ""  # Valor inválido ou ausente
                        items.append(QStandardItem(formatted_value))
                    else:
                        items.append(QStandardItem(str(value)))
                model.appendRow(items)

            # Definir o modelo na QTableView
            self.table_view.setModel(model)

            # Configurar visual e redimensionamento das colunas
            self.configurar_tabela()
        else:
            print("Nenhuma tabela foi carregada para exibição.")


    def calcular_economicidade(self):
        """Calcula a média dos percentuais de desconto."""
        # Verifica se o DataFrame foi inicializado
        if self.homologacao_dataframe is None:
            print("Erro: Nenhum DataFrame foi carregado para calcular a economicidade.")
            return 0  # Retorna 0 ou outro valor padrão apropriado

        print("Iniciando cálculo de economicidade...")

        # Verifica as colunas do DataFrame
        print("Colunas disponíveis no DataFrame:")
        print(self.homologacao_dataframe.columns)

        # Verifica os dados no DataFrame
        print("Amostra do DataFrame:")
        print(self.homologacao_dataframe.head())

        # Confirma se a coluna 'situacao' existe
        if 'situacao' not in self.homologacao_dataframe.columns:
            print("Erro: A coluna 'situacao' não existe no DataFrame.")
            return 0

        try:
            # Filtrar linhas com situação 'Adjudicado e Homologado'
            df_homologado = self.homologacao_dataframe[
                self.homologacao_dataframe['situacao'] == 'Adjudicado e Homologado'
            ].copy()

            print("DataFrame filtrado para 'Adjudicado e Homologado':")
            print(df_homologado)

            # Garantir que as colunas sejam numéricas
            df_homologado['valor_estimado'] = pd.to_numeric(
                df_homologado['valor_estimado'], errors='coerce'
            )
            df_homologado['valor_homologado_item_unitario'] = pd.to_numeric(
                df_homologado['valor_homologado_item_unitario'], errors='coerce'
            )

            print("Após conversão para numérico:")
            print(df_homologado[['valor_estimado', 'valor_homologado_item_unitario']])

            # Remover linhas onde 'valor_estimado' seja zero ou nulo
            df_homologado = df_homologado[df_homologado['valor_estimado'] > 0]

            print("Após remover linhas com 'valor_estimado' <= 0:")
            print(df_homologado)

            # Calcular percentual de desconto para cada linha
            df_homologado['percentual_desconto'] = (
                (df_homologado['valor_estimado'] - df_homologado['valor_homologado_item_unitario'])
                / df_homologado['valor_estimado']
            ) * 100

            print("Percentuais de desconto calculados:")
            print(df_homologado[['percentual_desconto']])

            # Calcular média dos percentuais de desconto
            media_percentual = df_homologado['percentual_desconto'].mean()

            print(f"Média calculada: {media_percentual:.2f}%")

            # Retorna 0 se o DataFrame estiver vazio
            return media_percentual if not pd.isna(media_percentual) else 0

        except KeyError as e:
            print(f"Erro: Coluna ausente no DataFrame - {e}")
            return 0  # Retorna 0 ou outro valor padrão em caso de erro
        except Exception as e:
            print(f"Erro inesperado ao calcular economicidade: {e}")
            return 0
    
    def gerar_tabela_excel(self):
        """Gera e abre uma tabela Excel com valores de economicidade usando fórmulas."""
        # Filtrar dados com situação 'Adjudicado e Homologado'
        df_homologado = self.homologacao_dataframe[self.homologacao_dataframe['situacao'] == 'Adjudicado e Homologado'].copy()

        # Selecionar colunas para exportação e garantir que valores são numéricos
        df_to_export = df_homologado[['item', 'descricao', 'valor_estimado', 'valor_homologado_item_unitario']].copy()
        df_to_export['valor_estimado'] = pd.to_numeric(df_to_export['valor_estimado'], errors='coerce')
        df_to_export['valor_homologado_item_unitario'] = pd.to_numeric(df_to_export['valor_homologado_item_unitario'], errors='coerce')

        # Nome do arquivo para salvar
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Tabela", "", "Excel Files (*.xlsx)")

        if file_path:
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                workbook = writer.book
                worksheet = workbook.add_worksheet('Indicador')
                writer.sheets['Indicador'] = worksheet

                # Adicionar título
                worksheet.write(0, 0, "Indicador NORMCEIM")

                # Escrever cabeçalho manualmente
                headers = ["Item", "Descrição", "Valor Estimado", "Valor Homologado Item Unitário", "Percentual Desconto"]
                for col_num, header in enumerate(headers):
                    worksheet.write(2, col_num, header)

                # Escrever dados das colunas (sem a coluna percentual_desconto)
                for row_num, row_data in enumerate(df_to_export.values, start=3):
                    worksheet.write_row(row_num, 0, row_data)
                    
                    # Forçar formatação numérica para colunas de valores
                    worksheet.set_column('C:D', None, workbook.add_format({'num_format': '#,##0.00'}))

                    # Adicionar fórmula para calcular o percentual de desconto na coluna E
                    valor_estimado_cell = f"C{row_num + 1}"
                    valor_homologado_cell = f"D{row_num + 1}"
                    worksheet.write_formula(row_num, 4, f"=({valor_estimado_cell} - {valor_homologado_cell}) / {valor_estimado_cell} * 100")

                # Inserir a fórmula de média na última linha
                media_row = len(df_to_export) + 4
                worksheet.write(media_row, 3, "Média do Percentual de Desconto")
                worksheet.write_formula(media_row, 4, f"=AVERAGE(E4:E{media_row - 1})")

                # Filtrar e listar itens não homologados
                df_nao_homologado = self.homologacao_dataframe[
                    (self.homologacao_dataframe['situacao'] != 'Adjudicado e Homologado') |
                    (self.homologacao_dataframe['valor_homologado_item_unitario'].isna())
                ][['item', 'descricao', 'valor_estimado', 'valor_homologado_item_unitario']].copy()

                # Substituir valores nulos por '-'
                df_nao_homologado['valor_homologado_item_unitario'] = df_nao_homologado['valor_homologado_item_unitario'].fillna('-')

                # Adicionar título para itens não computados
                non_computed_start_row = media_row + 2
                worksheet.write(non_computed_start_row, 0, "Itens não computados na média por não terem sido homologados")

                # Escrever cabeçalhos dos itens não homologados
                for col_num, header in enumerate(['Item', 'Descrição', 'Valor Estimado', 'Valor Homologado Item Unitário']):
                    worksheet.write(non_computed_start_row + 1, col_num, header)

                # Escrever dados dos itens não homologados, substituindo NaN com '-'
                for row_num, row_data in enumerate(df_nao_homologado.fillna('-').values, start=non_computed_start_row + 2):
                    worksheet.write_row(row_num, 0, row_data)

            # Abrir o arquivo Excel após salvar
            os.startfile(file_path)

    def configurar_tabela(self):
        """Configura o estilo e visualização da QTableView."""
        # Aplicar estilo à tabela
        self.table_view.setStyleSheet("""
            QTableView {
                background-color: #181928;
                color: #FFFFFF;
                gridline-color: #3C3C5A;
                alternate-background-color: #2C2F3F;
                selection-background-color: #2C2F3F;
                selection-color: #D4F8F2;
                border: none;
                font-size: 14px;
            }
            QTableView::item:selected {
                background-color: #2C2F3F;
                color: #D4F8F2;
            }
            QTableView::item {
                border: 1px solid transparent;
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #2C9E97;
                color: black;
                font-weight: bold;
                font-size: 14px;
                padding: 4px;
                border: 1px solid #3C3C5A;
            }
        """)

        # Ocultar a coluna de índice (cabeçalho vertical)
        self.table_view.verticalHeader().setVisible(False)
        
        # Configurar a visualização das colunas
        self.configurar_visualizacao_tabela_tr(self.table_view)

    def configurar_visualizacao_tabela_tr(self, table_view):
        """Configura colunas visíveis e redimensionamento na QTableView."""
        # Verifica se o modelo foi configurado antes de prosseguir
        if table_view.model() is None:
            print("O modelo de dados não foi configurado para table_view.")
            return  # Sai da função se o modelo não estiver configurado

        # Define colunas visíveis
        visible_columns = [1, 3, 5, 7, 8, 9, 14]  # Colunas visíveis
        for col in range(table_view.model().columnCount()):
            if col not in visible_columns:
                table_view.hideColumn(col)  # Oculta as colunas que não estão na lista
            else:
                header = table_view.model().headerData(col, Qt.Orientation.Horizontal)
                table_view.model().setHeaderData(col, Qt.Orientation.Horizontal, header)

        # Configuração de redimensionamento das colunas
        table_view.setColumnWidth(1, 50)
        table_view.setColumnWidth(3, 250)
        table_view.setColumnWidth(5, 100)
        table_view.setColumnWidth(9, 100)

        table_view.horizontalHeader().setStretchLastSection(True)
        table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        table_view.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        table_view.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        table_view.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        table_view.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        table_view.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        table_view.horizontalHeader().setSectionResizeMode(14, QHeaderView.ResizeMode.Stretch)

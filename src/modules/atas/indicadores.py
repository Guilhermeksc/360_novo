from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt

class IndicadoresWidget(QWidget):
    def __init__(self, homologacao_dataframe, icons_dir, db_manager, parent=None):
        super().__init__(parent)
        self.homologacao_dataframe = homologacao_dataframe
        self.icons_dir = icons_dir
        self.db_manager = db_manager
        self.icons = self.load_icons()
        self.setup_ui()
        
    def load_icons(self):
        """Carrega ícones e os armazena em cache."""
        icon_cache = {}
        icon_paths = {
            "check": self.icons_dir / "check.png",
            "cancel": self.icons_dir / "cancel.png",
            "processing": self.icons_dir / "processing.png"
        }

        for key, path in icon_paths.items():
            icon = QIcon(str(path)) if path.exists() else QIcon()
            icon_cache[key] = icon

        return icon_cache
    
    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Título principal
        header_title = QLabel("Indicadores")
        header_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(header_title)

        # Indicador de Economicidade
        economicidade_label = QLabel("Indicador de Economicidade")
        economicidade_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        economicidade_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(economicidade_label)
        
        # Cálculo do indicador de economicidade
        economicidade_percentual = self.calcular_economicidade()
        
        # Exibir o valor calculado
        valor_economicidade = QLabel(f"{economicidade_percentual:.2f}% de economia média")
        valor_economicidade.setFont(QFont('Arial', 14))
        valor_economicidade.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(valor_economicidade)

        # Configuração do layout principal
        self.setLayout(layout)
    
    def calcular_economicidade(self):
        """Calcula a média dos percentuais de desconto."""
        # Filtrar linhas com situação 'Adjudicado e Homologado' e criar uma cópia
        df_homologado = self.homologacao_dataframe[self.homologacao_dataframe['situacao'] == 'Adjudicado e Homologado'].copy()
        
        # Calcular percentual de desconto para cada linha
        df_homologado['percentual_desconto'] = ((df_homologado['valor_estimado'] - df_homologado['valor_homologado_item_unitario']) 
                                                / df_homologado['valor_estimado']) * 100
        
        # Calcular média dos percentuais de desconto
        return df_homologado['percentual_desconto'].mean()
    
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import pandas as pd
import os

class IndicadoresWidget(QWidget):
    def __init__(self, homologacao_dataframe, icons_dir, db_manager, parent=None):
        super().__init__(parent)
        self.homologacao_dataframe = homologacao_dataframe
        self.icons_dir = icons_dir
        self.db_manager = db_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Título principal
        header_title = QLabel("Indicadores")
        header_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(header_title)

        # Indicador de Economicidade
        economicidade_label = QLabel("Indicador de Economicidade")
        economicidade_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        economicidade_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(economicidade_label)
        
        # Cálculo do indicador de economicidade
        economicidade_percentual = self.calcular_economicidade()
        
        # Exibir o valor calculado
        valor_economicidade = QLabel(f"{economicidade_percentual:.2f}% de economia média")
        valor_economicidade.setFont(QFont('Arial', 14))
        valor_economicidade.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(valor_economicidade)

        # Botão para gerar e abrir a tabela Excel
        gerar_tabela_button = QPushButton("Gerar Tabela XLSX")
        gerar_tabela_button.clicked.connect(self.gerar_tabela_excel)
        layout.addWidget(gerar_tabela_button)

        # Configuração do layout principal
        self.setLayout(layout)
    
    def calcular_economicidade(self):
        """Calcula a média dos percentuais de desconto."""
        # Filtrar linhas com situação 'Adjudicado e Homologado' e criar uma cópia
        df_homologado = self.homologacao_dataframe[self.homologacao_dataframe['situacao'] == 'Adjudicado e Homologado'].copy()
        
        # Calcular percentual de desconto para cada linha
        df_homologado['percentual_desconto'] = ((df_homologado['valor_estimado'] - df_homologado['valor_homologado_item_unitario']) 
                                                / df_homologado['valor_estimado']) * 100
        
        # Calcular média dos percentuais de desconto
        return df_homologado['percentual_desconto'].mean()
    
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

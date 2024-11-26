from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from pathlib import Path
import os
import pandas as pd
from src.modules.utils.treeview_utils import open_folder, create_button
import PyPDF2
from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black
import io
from functools import partial
from docxtpl import DocxTemplate
import string
from datetime import datetime
from num2words import num2words
import webbrowser
from functools import partial
import subprocess
import sys
from src.config.paths import *
from src.modules.utils.add_button import add_button_func
from src.modules.utils.linha_layout import linha_divisoria_layout

def remover_caracteres_especiais(texto):
    mapa_acentos = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
        'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
        'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'ç': 'c', 'Ç': 'C', 'ñ': 'n', 'Ñ': 'N'
    }
    for caractere_original, caractere_novo in mapa_acentos.items():
        texto = texto.replace(caractere_original, caractere_novo)

    # Adicionando substituição para caracteres impeditivos em nomes de arquivos e pastas
    caracteres_impeditivos = r'\\/:*?"<>|'
    for caractere in caracteres_impeditivos:
        texto = texto.replace(caractere, '-')

    return texto

class DraggableTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super(DraggableTreeWidget, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.previous_values = {}  # Dicionário para armazenar os valores anteriores
        self.itemChanged.connect(self.onItemChanged)
        self.itemDoubleClicked.connect(self.onItemDoubleClicked)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

    def open_context_menu(self, position):
        menu = QMenu(self)
        add_item_action = QAction("Adicionar item", self)
        delete_item_action = QAction("Excluir item", self)

        add_item_action.triggered.connect(partial(self.inserir_item))
        delete_item_action.triggered.connect(self.delete_selected_rows)

        menu.addAction(add_item_action)
        menu.addAction(delete_item_action)

        menu.exec(self.viewport().mapToGlobal(position))

    def inserir_item(self, identificacao=None, marcador_sapiens="definir_marcador"):
        if identificacao is None or isinstance(identificacao, bool):
            identificacao = "-------Definir o novo documento--------"
        
        print(f"Valores recebidos - Identificação: {identificacao}, Marcador Sapiens: {marcador_sapiens}")
        selected_items = self.selectedItems()
        if selected_items:
            last_item = selected_items[-1]
            insert_position = self.indexOfTopLevelItem(last_item) + 1
            last_fim_value = int(last_item.text(4))
        else:
            if self.topLevelItemCount() > 0:
                last_item = self.topLevelItem(self.topLevelItemCount() - 1)
                last_fim_value = int(last_item.text(4))
                insert_position = self.topLevelItemCount()
            else:
                last_fim_value = 0
                insert_position = 0

        inicio = last_fim_value + 1
        fim = inicio + 1
        num_paginas = fim - inicio + 1

        formatted_position = f"{insert_position:02}"
        print(f"Insert Position Formatado: {formatted_position}")  # Debug para ver o valor formatado

        new_item = QTreeWidgetItem([
            formatted_position,
            str(identificacao),
            str(marcador_sapiens),
            str(inicio),
            str(fim),
            str(num_paginas)
        ])

        self.insertTopLevelItem(insert_position, new_item)
        print(f"Valor no Item: {self.topLevelItem(insert_position).text(0)}")  # Debug para verificar o valor no widget

        self.reordenar_treeview()

    def delete_selected_rows(self):
        selected_items = self.selectedItems()
        for item in selected_items:
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))

        # Reordenar os índices e ajustar os dados
        self.reordenar_treeview()
        
    def reordenar_treeview(self):
        df = self.save_treeview_to_dataframe()
        df = self.ajustar_dataframe(df)
        self.atualizar_tree_from_dataframe(df)

    def ajustar_dataframe(self, df):
        inicio_atual = 1
        for index, row in df.iterrows():
            df.at[index, 'Início'] = inicio_atual
            fim_atual = inicio_atual + int(row['qnt_pag']) - 1
            df.at[index, 'Fim'] = fim_atual
            inicio_atual = fim_atual + 1
        return df

    def atualizar_tree_from_dataframe(self, df):
        self.clear()  # Limpar todos os itens existentes antes de adicionar novos
        for idx, (_, row) in enumerate(df.iterrows(), start=1):
            # Criar um novo QTreeWidgetItem com os valores corretos
            item = QTreeWidgetItem([
                f"{idx:02}",  # Formatação explícita como texto com dois dígitos
                str(row["Identificação"]),
                str(row["Marcador"]),
                str(row["Início"]),
                str(row["Fim"]),
                str(row["qnt_pag"])
            ])
            # Adicionar o novo item ao QTreeWidget
            self.addTopLevelItem(item)


    def save_treeview_to_dataframe(self):
        items = [self.topLevelItem(i) for i in range(self.topLevelItemCount())]
        data = [(item.text(1), item.text(2), item.text(3), item.text(4), item.text(5)) for item in items]
        df = pd.DataFrame(data, columns=["Identificação", "Marcador", "Início", "Fim", "qnt_pag"])
        # Aqui você deve definir o TREEVIEW_DATA_PATH se ainda não foi definido
        df.to_csv(TREEVIEW_DATA_PATH, index=False)
        return df

    def onItemChanged(self, item, column):
        # Verificar se a coluna editada é a coluna "Fim"
        if column == 4:
            try:
                inicio = int(item.text(3))
                fim = int(item.text(4))
                qnt_pag = fim - inicio + 1
                if qnt_pag < 1:
                    raise ValueError("O número de fim é menor que o de início")
                item.setText(5, str(qnt_pag))
                self.ajustar_itens()
            except ValueError as e:
                QMessageBox.critical(self, "Erro de Validação", str(e))
                # Reverter para o valor anterior se houver um erro
                item.setText(4, self.previous_values.get(id(item), ""))
                self.clearSelection()
        self.save_data_to_csv()

    def onItemDoubleClicked(self, item, column):
        # Verifique se a coluna clicada é uma das que devem ser editáveis
        editable_columns = [1, 2, 4]  # "Identificação", "SAPIENS" e "Fim"
        if column in editable_columns:
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

            self.editItem(item, column)
            if column == 4:  # Armazenar o valor anterior apenas para a coluna "Fim"
                self.previous_values[id(item)] = item.text(column)
        else:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def dropEvent(self, event):
        # Obter a posição onde o item será solto
        pointer_position = event.position().toPoint()
        target_item = self.itemAt(pointer_position)
        
        if not target_item:
            # Se o destino não for um item (por exemplo, espaço vazio), ignore o evento
            event.ignore()
            return

        # Obter o item arrastado
        dragged_item = self.currentItem()

        if dragged_item == target_item:
            # Se o item arrastado for solto sobre si mesmo, ignore o evento
            event.ignore()
            return

        # Salvar as informações do item arrastado
        item_data = self.mimeData(self.selectedItems())
        parent_item = dragged_item.parent() if dragged_item.parent() else self.invisibleRootItem()
        index = parent_item.indexOfChild(dragged_item)
        parent_item.takeChild(index)
        # Descobrir onde inserir o item arrastado
        parent_of_target = target_item.parent() if target_item.parent() else self.invisibleRootItem()
        index_of_target = parent_of_target.indexOfChild(target_item)
        # Inserir o item arrastado na nova posição
        parent_of_target.insertChild(index_of_target, dragged_item)
        # Redefinir os dados do item arrastado (se necessário)
        self.clearSelection()
        self.selectionModel().select(self.indexFromItem(dragged_item), QItemSelectionModel.SelectionFlag.Select)

        # Aceitar o evento de soltar
        self.ajustar_itens()
        # Chamar atualizar_idx para reordenar os números
        self.atualizar_idx()
        self.save_data_to_csv()
        event.accept()
        
    def ajustar_itens(self):
        inicio_atual = 1
        for index in range(self.topLevelItemCount()):
            item = self.topLevelItem(index)
            try:
                qnt_pag_text = item.text(5)
                qnt_pag = int(qnt_pag_text) if qnt_pag_text else 2  # Default to 2 if empty
            except ValueError:
                qnt_pag = 2  # Default to 2 if conversion fails
            fim_atual = inicio_atual + qnt_pag - 1
            
            item.setText(3, str(inicio_atual))  # Atualiza a coluna 'Início'
            item.setText(4, str(fim_atual))     # Atualiza a coluna 'Fim'
            
            inicio_atual = fim_atual + 1

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Delete:

            selected_items = self.selectedItems()
            for item in selected_items:
                parent = item.parent() or self.invisibleRootItem()
                parent.removeChild(item)
            self.atualizar_idx()  # Atualizar os índices após a exclusão
            self.ajustar_itens()  # Adicionado para recalcular as colunas Início e Fim
        else:
            super().keyPressEvent(event)
        self.save_data_to_csv()

    def atualizar_idx(self):
        for idx in range(self.topLevelItemCount()):
            item = self.topLevelItem(idx)
            item.setText(0, f"{idx + 1:02}") 

    def collect_data(self):
        # Coletar os dados dos itens do QTreeWidget e retornar como um DataFrame
        data = []
        for index in range(self.topLevelItemCount()):
            item = self.topLevelItem(index)
            row_data = [item.text(column) for column in range(self.columnCount())]
            data.append(row_data)
        columns = [self.headerItem().text(i) for i in range(self.columnCount())]
        df = pd.DataFrame(data, columns=columns)
        return df

    def save_data_to_csv(self):
        # Salvar os dados coletados em um arquivo CSV
        df = self.collect_data()
        df.to_csv(TREEVIEW_DATA_PATH, index=False)

class ChecklistWidget(QWidget):
    def __init__(self, parent, icons_path, df_registro_selecionado):
        super().__init__(parent)
        self.icons = icons_path
        self.config_manager = ConfigManager(BASE_DIR / "config.json")
        self.df_registro = df_registro_selecionado

        # Print para verificar o tipo e conteúdo de df_registro
        print(f"Tipo de self.df_registro: {type(self.df_registro)}")
        print(f"Conteúdo de self.df_registro: {self.df_registro}")
        self.layout = QVBoxLayout(self)

        self.tree = DraggableTreeWidget(self)
        self.font = QFont()
        self.font.setPointSize(12)
        self.tree.setFont(self.font)
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels(["Nº", "Identificação", "Marcador", "Início", "Fim", "Págs"])
        self.header = self.tree.header()
        self.header.setFont(self.font)
        self.header.setStyleSheet(
            "QHeaderView::section { font-size: 12pt; background-color: #333; color: white; }")
        self.tree.setColumnWidth(1, 700)
        self.tree.setColumnWidth(2, 300)
        self.layout.addWidget(self.tree)
        linha_divisoria, spacer_baixo_linha = linha_divisoria_layout()
        self.layout.addWidget(linha_divisoria)
        self.layout.addSpacerItem(spacer_baixo_linha)        
        self.setupBottomButtons()
        self.load_data()

        self.lv_split_final_dir = None
        self.config_manager.config_updated.connect(self.update_save_location)

        self.pasta_base = Path(self.config_manager.get_config('save_location', str(Path.home() / 'Desktop')))
        
    def update_save_location(self, key, new_path):
        if key == 'save_location':
            self.pasta_base = new_path
            print(f"Local de salvamento atualizado para: {self.pasta_base}")

    def load_treeview_data(self):
        # Supondo que TREEVIEW_DATA_PATH seja um atributo ou esteja globalmente acessível
        return pd.read_csv(TREEVIEW_DATA_PATH)
    
    def processar_pdf_na_integra_e_gerar_documentos(self):
        # Abrir caixa de diálogo para selecionar o arquivo PDF numerado
        arquivo_numerado, _ = QFileDialog.getOpenFileName(caption="Selecione o arquivo PDF numerado", filter="PDF Files (*.pdf)")
        if not arquivo_numerado:
            return

        # Processamento do ID do processo e criação do nome da pasta principal
        id_processo_original = self.df_registro.get('id_processo', 'N/A')
        id_processo_novo = id_processo_original.replace('/', '-')  # Substituir '/' por '-'
        objeto = self.df_registro.get('objeto', '')
        nome_pasta = f"{id_processo_novo} - {remover_caracteres_especiais(objeto)}"

        # Caminho para a pasta principal usando self.pasta_base
        pasta_destino = self.pasta_base / nome_pasta
        pasta_destino.mkdir(parents=True, exist_ok=True)

        # Definição da subpasta "Checklist"
        subpasta_checklist = f"{id_processo_novo} - Checklist"
        subpasta_destino = pasta_destino / subpasta_checklist

        # Verifica se a subpasta existe e cria se necessário
        subpasta_destino.mkdir(parents=True, exist_ok=True)

        # Verificar se o template existe antes de continuar
        template_path = TEMPLATE_DIR / "template_checklist.docx"
        if not template_path.exists():
            QMessageBox.warning(self, "Erro", f"O template não foi encontrado em: {template_path}")
            return  # Interrompe a execução e volta ao estado anterior

        template_path_nota = TEMPLATE_DIR / "template_nota_tecnica.docx"
        # Verificar se o arquivo de template existe
        if not template_path_nota.exists():
            QMessageBox.warning(self, "Erro", f"O template não foi encontrado em: {template_path_nota}")
            return

        template_path_autuacao = TEMPLATE_DIR / "template_autuacao.docx"
        # Verificar se o arquivo de template existe
        if not template_path_autuacao.exists():
            QMessageBox.warning(self, "Erro", f"O template não foi encontrado em: {template_path_autuacao}")
            return
        
        # Chamada para processar o PDF e substituir marcadores
        split_pdf_using_dataframe(arquivo_numerado, self.pasta_base, subpasta_destino)
        
        # Carrega os dados necessários para a substituição de variáveis
        df_treeview = self.load_treeview_data()
        self.substituir_variaveis_docx(df_treeview)
        self.substituir_variaveis_nota_tecnica()  # Corrigido para refletir a nova assinatura do método
        substituir_marcadores_com_relacao(TEMPLATE_AUTUACAO, subpasta_destino, self.df_registro)

        # Abre a pasta no gerenciador de arquivos
        open_folder(subpasta_destino)


    def substituir_variaveis_nota_tecnica(self):
        if self.df_registro is None:
            QMessageBox.warning(None, "Seleção Necessária", "Por favor, selecione um registro na tabela antes de gerar um documento.")
            return None
        
        # Carrega os dados de TREEVIEW_DATA_PATH diretamente na classe
        df = self.load_treeview_data()

        ultima_folha = df['Fim'].iloc[-1]
        quantidade_folhas = f"{ultima_folha} ({num2words(ultima_folha, lang='pt_BR')}) folhas"
        id_processo_original = self.df_registro.get('id_processo', 'N/A')
        id_processo_novo = id_processo_original.replace('/', '-')
        objeto = remover_caracteres_especiais(self.df_registro.get('objeto', ''))
        
        template_path = TEMPLATE_DIR / "template_nota_tecnica.docx"
        # Verificar se o arquivo de template existe
        if not template_path.exists():
            QMessageBox.warning(self, "Erro", f"O template não foi encontrado em: {template_path}")
            return
                
        doc = DocxTemplate(template_path)
        
        context = {
            'numero': self.df_registro.get('numero', 'N/A'),
            'ano': self.df_registro.get('ano', 'N/A'),
            'nup': self.df_registro.get('nup', 'N/A'),
            'tipo': self.df_registro.get('tipo', 'N/A'),
            'objeto_completo': self.df_registro.get('objeto_completo', 'N/A'),
            'quantidade_folhas': quantidade_folhas,
            'descricao_servico': "Aquisição de" if self.df_registro.get('material_servico', '') == "material" else "Contratação de empresa especializada em"
        }


        # Adição de informações dinâmicas de páginas ao contexto
        additional_context = {row['Marcador']: f"Fls. {row['Início']} a {row['Fim']}" for _, row in df.iterrows()}
        context.update(additional_context)

        nome_pasta = f"{id_processo_novo} - {remover_caracteres_especiais(objeto)}"
        desktop_path = self.pasta_base / nome_pasta
        desktop_path.mkdir(parents=True, exist_ok=True)

        subpasta_destino = desktop_path / f"{id_processo_novo} -Nota Técnica"
        subpasta_destino.mkdir(parents=True, exist_ok=True)
        
        doc.render(context)
        output_path = subpasta_destino / f"{id_processo_novo} - Nota Técnica.docx"
        doc.save(output_path)

        return output_path
        
    def substituir_variaveis_docx(self, df_treeview):
        num_pregao = self.df_registro.get('numero', 'N/A')
        ano_pregao = self.df_registro.get('ano', 'N/A')
        id_processo_original = self.df_registro.get('id_processo', 'N/A')
        id_processo_novo = id_processo_original.replace('/', '-')
        objeto = remover_caracteres_especiais(self.df_registro.get('objeto', ''))
        nome_pasta = f"{id_processo_novo} - {objeto}"

        # Caminho para a pasta principal usando pasta_base atualizada
        pasta_destino = self.pasta_base / nome_pasta
        pasta_destino.mkdir(parents=True, exist_ok=True)

        # Definição da subpasta "Checklist"
        subpasta_checklist = f"{id_processo_novo} - Checklist"
        subpasta_final = pasta_destino / subpasta_checklist
        subpasta_final.mkdir(parents=True, exist_ok=True)

        # Caminho para o template
        template_path = TEMPLATE_DIR / "template_checklist.docx"

        # Verificar se o arquivo de template existe
        if not template_path.exists():
            QMessageBox.warning(self, "Erro", f"O template não foi encontrado em: {template_path}")
            return

        # Inicialização do DocxTemplate
        doc = DocxTemplate(template_path)

        # Renderizar o contexto
        context = {row['Marcador']: f"Fls. {row['Início']} a {row['Fim']}" for index, row in df_treeview.iterrows()}
        doc.render(context)

        # Salvar o documento gerado
        output_path = subpasta_final / f"PE {num_pregao}-{ano_pregao} - Checklist.docx"
        doc.save(output_path)
        print(f"Documento salvo em: {output_path}")


    def process_pdf(self, arquivo_numerado):
        try:
            df_divisao = pd.read_csv(TREEVIEW_DATA_PATH)
            if "Início" not in df_divisao.columns or "Fim" not in df_divisao.columns or "Identificação" not in df_divisao.columns:
                print("Erro: DataFrame não contém as colunas necessárias ('Início', 'Fim', 'Identificação').")
                return

            # Definir e verificar se lv_split_final_dir está definido
            if self.lv_split_final_dir is None:
                self.lv_split_final_dir = Path("caminho/para/diretório")

            self.lv_split_final_dir = split_pdf_using_dataframe(arquivo_numerado, df_divisao, self.lv_split_final_dir)
            print(f"Processamento concluído. Arquivos salvos em: {self.lv_split_final_dir}")

        except Exception as e:
            print(f"Erro ao processar o PDF: {e}")

    def setupBottomButtons(self):
        self.buttons_layout = QHBoxLayout()
        self.create_buttons()
        self.layout.addLayout(self.buttons_layout)
                 
    def create_buttons(self):
        add_button_func("Sapiens", "sapiens", self.abrir_link_sapiens, self.buttons_layout, self.icons, tooltip="Carregar o Formulário")       
        add_button_func("Resetar Padrão", "rotate", self.resetar_treeview, self.buttons_layout, self.icons, tooltip="Carregar o Formulário")       
        add_button_func("Numerar", "reckoning", numerar_pdf_gui, self.buttons_layout, self.icons, tooltip="Carregar o Formulário")       
        add_button_func("Processar", "processing", lambda: self.processar_pdf_na_integra_e_gerar_documentos(), self.buttons_layout, self.icons, tooltip="Carregar o Formulário")       
        add_button_func("Importar", "excel_down", self.onLoadItems, self.buttons_layout, self.icons, tooltip="Carregar o Formulário")       
        add_button_func("Salvar", "excel_up", self.onSaveItems, self.buttons_layout, self.icons, tooltip="Carregar o Formulário")       

    def abrir_link_sapiens(self):
        url = "https://supersapiens.agu.gov.br/auth/login"
        webbrowser.open(url)

    def onSaveItems(self):
        # Pedir ao usuário para escolher o local e o nome do arquivo para salvar
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Arquivo", "", "Arquivos CSV (*.csv);;Todos os Arquivos (*)"
        )

        if filepath:
            # Verificar se o caminho tem a extensão .csv, se não, adicionar
            if not filepath.endswith('.csv'):
                filepath += '.csv'

            try:
                # Carregar o dataframe de TREEVIEW_DATA_PATH e salvá-lo no local escolhido
                df = pd.read_csv(TREEVIEW_DATA_PATH)
                df.to_csv(filepath, index=False)
                print(f"Arquivo salvo com sucesso: {filepath}")
            except Exception as e:
                print(f"Erro ao salvar o arquivo: {e}")

    def onLoadItems(self):
        # Pedir ao usuário para escolher o arquivo para carregar
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Carregar Arquivo", "", "Arquivos CSV (*.csv);;Todos os Arquivos (*)"
        )

        if filepath:
            try:
                # Carregar o dataframe do arquivo escolhido
                dataframe_carregado = pd.read_csv(filepath)

                # Atualizar TREEVIEW_DATA_PATH com o novo dataframe
                dataframe_carregado.to_csv(TREEVIEW_DATA_PATH, index=False)

                # Aqui você pode atualizar a sua interface com o dataframe carregado
                # ...

                print(f"Arquivo carregado com sucesso: {filepath}")
            except Exception as e:
                print(f"Erro ao carregar o arquivo: {e}")    

    def showEvent(self, event):
        # Este método é chamado automaticamente quando o widget é exibido
        super().showEvent(event)
        self.header.setFont(self.font)

    def add_item(self, identificacao, sapiens, inicio, fim):
        # Calcular a quantidade de páginas
        qnt_pag = int(fim) - int(inicio) + 1
        # Criar um novo item com os dados especificados
        item = QTreeWidgetItem([identificacao, sapiens, inicio, fim, str(qnt_pag)])
        self.tree.addTopLevelItem(item)

    def get_title(self):
        return "Check-list"

    def get_content_widget(self):
        return self
    
    def adjust_column_sizes(self):
        self.header.setStretchLastSection(False)

        # Ajustar as colunas para um tamanho específico ou baseado no conteúdo
        self.header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta ao conteúdo da coluna Nº
        self.header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # A primeira coluna com texto esticado
        self.header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta ao conteúdo da coluna SAPIENS
        self.header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta ao conteúdo da coluna Início
        self.header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta ao conteúdo da coluna Fim
        self.header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)   

    def load_data(self):
        # Dados a serem inseridos no treeview
        dados = [
            ("Capa de Abertura do Pregão Eletrônico e Termo de Autuação", "termo_autuacao", "1", "4"),
            ("Autorização para Abertura de Processo", "termo_abertura", "5", "6"),
            ("Documento de Formalização da Demanda (DFD)", "dfd", "7", "16"),
            ("Comprovação da Divulgação da Intenção do Registro de Preços", "termo_irp", "17", "18"),
            ("Despacho", "Despacho", "19", "20"),
            ("Portaria XXXX de Designação de Ordenador de Despesas", "portaria_od", "21", "23"),
            ("Portaria XXXX de Designação de Militares para Comissão de Licitação", "portaria_comissao", "24", "27"),
            ("Portaria XXXX Com7°DN de Designação de Equipe de Planejamento", "portaria_plan", "28", "31"),
            ("Termo de Referência", "tr", "32", "51"),
            ("Estudo Técnico Preliminar (ETP)", "etp", "52", "68"),
            ("Matriz de Gerenciamento de Riscos", "mr", "69", "79"),
            ("Pesquisa de Preços", "pesquisa_precos", "80", "137"),   
            ("Minuta do Edital", "minuta_edital", "138", "164"),
            ("Minuta do Contrato", "minuta_contrato", "165", "173"),
            ("Minuta da Ata de Registro de Preços", "minuta_arp", "174", "183"),
            ("Lista de Verificação", "checklist", "184", "190"),    
            ("Despacho", "despacho", "191", "192"),
            ("Nota Técnica", "nota_tecnica", "193", "200"),
            ("Comunicação Padronizada", "termo", "201", "202"),
            ("Despacho de Encaminhamento para AGU", "termo", "203", "204"),
        ]
        
        # Verificar se o arquivo TREEVIEW_DATA_PATH existe
        if os.path.exists(TREEVIEW_DATA_PATH):
            df = pd.read_csv(TREEVIEW_DATA_PATH, usecols=['Identificação', 'Marcador', 'Início', 'Fim'])
            dados_from_file = df.values.tolist()
        else:
            dados_from_file = dados  # Use a lista padrão de dados se o arquivo não existir
        
        # Adicionar os itens ao treeview
        for idx, (identificacao, marcador, inicio, fim) in enumerate(dados_from_file, 1):  # Começar a contar do 1
            try:
                qnt_pag = int(fim) - int(inicio) + 1
            except ValueError:
                # Handle the case where "fim" or "inicio" cannot be converted to integers
                qnt_pag = 0  # or some other appropriate default value
            item = QTreeWidgetItem([f"{idx:02}", identificacao, marcador, str(inicio), str(fim), str(qnt_pag)])
            # Não defina as colunas como editáveis aqui
            self.tree.addTopLevelItem(item)
        
        # Após adicionar todos os itens, ajustar o tamanho das colunas
        self.adjust_column_sizes()

    def get_default_data(self):
        # Retorna a lista de dados padrão
        return [
            ("Capa de Abertura do Pregão Eletrônico e Termo de Autuação", "termo_autuacao", "1", "4"),
            ("Autorização para Abertura de Processo", "termo_abertura", "5", "6"),
            ("Documento de Formalização da Demanda (DFD)", "dfd", "7", "16"),
            ("Comprovação da Divulgação da Intenção do Registro de Preços", "termo_irp", "17", "18"),
            ("Despacho", "Despacho", "19", "20"),
            ("Portaria XXXX de Designação de Ordenador de Despesas", "portaria_od", "21", "23"),
            ("Portaria XXXX de Designação de Militares para Comissão de Licitação", "portaria_comissao", "24", "27"),
            ("Portaria XXXX Com7°DN de Designação de Equipe de Planejamento", "portaria_plan", "28", "31"),
            ("Termo de Referência", "tr", "32", "51"),
            ("Estudo Técnico Preliminar (ETP)", "etp", "52", "68"),
            ("Matriz de Gerenciamento de Riscos", "mr", "69", "79"),
            ("Pesquisa de Preços", "pesquisa_precos", "80", "137"),   
            ("Minuta do Edital", "minuta_edital", "138", "164"),
            ("Minuta do Contrato", "minuta_contrato", "165", "173"),
            ("Minuta da Ata de Registro de Preços", "minuta_arp", "174", "183"),
            ("Lista de Verificação", "checklist", "184", "190"),    
            ("Despacho", "despacho", "191", "192"),
            ("Nota Técnica", "nota_tecnica", "193", "200"),
            ("Comunicação Padronizada", "termo", "201", "202"),
            ("Despacho de Encaminhamento para AGU", "termo", "203", "204"),
        ]
        
    def resetar_treeview(self):
        # Carrega a lista de dados padrão no treeview
        self.tree.clear()
        dados_to_load = self.get_default_data()
        for idx, (identificacao, marcador, inicio, fim) in enumerate(dados_to_load, 1):  # Começar a contar do 1
            qnt_pag = int(fim) - int(inicio) + 1
            item = QTreeWidgetItem([f"{idx:02}", identificacao, marcador, str(inicio), str(fim), str(qnt_pag)])
            self.tree.addTopLevelItem(item)
        self.adjust_column_sizes()

    def _on_item_click(self, index):
        # Your code here to handle the item click event
        pass   
 

import webbrowser

def numerar_pdf_gui():
    arquivo_entrada, _ = QFileDialog.getOpenFileName(caption="Selecione o arquivo PDF de entrada", filter="PDF Files (*.pdf)")
    
    # Se nenhum arquivo for selecionado, retorne
    if not arquivo_entrada:
        return None

    # Construir o nome do arquivo de saída baseado no arquivo de entrada
    base, ext = os.path.splitext(arquivo_entrada)
    arquivo_saida = base + "_numerado" + ext
    
    numerar_pdf_com_pypdf2(arquivo_entrada, arquivo_saida)

    # Abrir o arquivo no navegador padrão do usuário
    webbrowser.open(arquivo_saida)

def numerar_pdf_com_pypdf2(arquivo_entrada, output_pdf_path):
    # arquivo_entrada = filedialog.askopenfilename(title="Selecione o arquivo PDF de entrada")
    # Crie um novo PdfFileWriter object
    output = PdfWriter()
    input_pdf = PdfReader(open(arquivo_entrada, "rb"))

    # Processo de numeração
    for i in range(len(input_pdf.pages)):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        width = input_pdf.pages[i].mediabox[2]
        height = input_pdf.pages[i].mediabox[3]

        # Aqui, estamos colocando o número no canto superior direito.
        can = canvas.Canvas(packet, pagesize=(width, height))
        can.setFont("Helvetica", 14)
        can.setFillColor(black)  # Definindo a cor da fonte para preto
        can.drawString(float(width) - 30, float(height) - 30, str(i + 1))

        can.save()

        # Mova o buffer de posição para o início e crie um novo objeto PDF a partir dele
        packet.seek(0)
        new_pdf = PdfReader(packet)

        # Combine as páginas
        page = input_pdf.pages[i]
        page.merge_page(new_pdf.pages[0])

        output.add_page(page)

    # Escreva a saída
    with open(output_pdf_path, "wb") as output_file_handle:
        output.write(output_file_handle)

def load_treeview_data():
    return pd.read_csv(TREEVIEW_DATA_PATH)

def split_pdf_using_dataframe(arquivo_numerado, df, lv_split_final_dir):
    df = pd.read_csv(TREEVIEW_DATA_PATH)
    pdf_file_path = arquivo_numerado
    with open(pdf_file_path, "rb") as original_pdf_file:
        original_pdf = PyPDF2.PdfReader(original_pdf_file)
        for idx, (_, row) in enumerate(df.iterrows(), 1):
            start_page = int(row["Início"]) - 1
            end_page = int(row["Fim"])
            output_filename = lv_split_final_dir / f"{idx:02} - {row['Identificação']} (Fls {row['Início']} a {row['Fim']}).pdf"
            new_pdf = PyPDF2.PdfWriter()
            for page_num in range(start_page, end_page):
                page = original_pdf.pages[page_num]
                new_pdf.add_page(page)
            with open(output_filename, "wb") as output_pdf_file:
                new_pdf.write(output_pdf_file)
    return lv_split_final_dir

def substituir_variaveis_docx(df_registro_selecionado, df):
    num_pregao = df_registro_selecionado['numero'].iloc[0]
    ano_pregao = df_registro_selecionado['ano'].iloc[0]
    id_processo_original = df_registro_selecionado['id_processo'].iloc[0]
    id_processo_novo = id_processo_original.replace('/', '-')  # Substituir '/' por '-' para compatibilidade de nome de pasta
    objeto = remover_caracteres_especiais(df_registro_selecionado['objeto'].iloc[0])
    nome_pasta = f"{id_processo_novo} - {objeto}"

    # Caminho para a pasta principal no desktop
    desktop_path = Path.home() / 'Desktop' / nome_pasta
    desktop_path.mkdir(parents=True, exist_ok=True)

    # Definição da subpasta "Checklist"
    subpasta_checklist = f"{id_processo_novo} - Checklist"
    subpasta_destino = desktop_path / subpasta_checklist
    subpasta_destino.mkdir(parents=True, exist_ok=True)

    # Inicializando o template DOCX
    doc = DocxTemplate(TEMPLATE_CHECKLIST)

    # Dicionário para mapear as variáveis para os valores de forma dinâmica
    context = {row['Marcador']: f"Fls. {row['Início']} a {row['Fim']}" if row['Início'] != row['Fim'] else f"Fl. {row['Início']}"
               for index, row in df.iterrows()}

    # Substituindo as variáveis no documento
    doc.render(context)

    # Determinando o nome do arquivo modificado
    output_path = subpasta_destino / f"PE {num_pregao}-{ano_pregao} - Checklist.docx"
    
    # Salvando o documento modificado
    doc.save(output_path)
    return output_path

def substituir_marcadores_com_relacao(docx_path, lv_split_final_dir, df_registro_selecionado):
    if not isinstance(df_registro_selecionado, dict):
        QMessageBox.warning(None, "Erro", "Os dados do registro selecionado não estão no formato esperado.")
        return

    df = load_treeview_data()
    relacao_documentos = []
    for idx, row in enumerate(df.itertuples(), 1):
        terminacao = ";" if idx < len(df) else "."
        if idx == len(df) - 1:
            terminacao = "; e"
        relacao = f"{string.ascii_lowercase[idx-1]}) {row.Identificação} (Fls. {row.Início} a {row.Fim}){terminacao}"
        relacao_documentos.append(relacao)

    relacao_documentos_str = "\n".join(relacao_documentos)
    ultima_folha = df['Fim'].iloc[-1]
    quantidade_folhas = f"{ultima_folha} ({num2words(ultima_folha, lang='pt_BR')}) folhas"
    hoje = datetime.now().strftime("%d/%m/%Y")

    # Verificação e obtenção segura dos dados
    num_pregao = df_registro_selecionado.get('numero', 'N/A')
    ano_pregao = df_registro_selecionado.get('ano', 'N/A')
    nup = df_registro_selecionado.get('nup', 'N/A')
    objeto = df_registro_selecionado.get('objeto', '')

    doc = DocxTemplate(docx_path)
    context = {
        'relacao_documentos': relacao_documentos_str,
        'quantidade_folhas': quantidade_folhas,
        'hoje': hoje,
        'num_pregao': num_pregao,
        'ano_pregao': ano_pregao,
        'nup': nup,
        'objeto': objeto
    }
    doc.render(context)
    
    output_path = lv_split_final_dir / f"PE {num_pregao}-{ano_pregao} - Relação de Documentos.docx"
    doc.save(output_path)
    return output_path

def substituir_variaveis_nota_tecnica(df_registro_selecionado, df):
    if not isinstance(df_registro_selecionado, dict):
        QMessageBox.warning(None, "Erro", "Os dados do registro selecionado não estão no formato esperado.")
        return

    if df_registro_selecionado is None:
        QMessageBox.warning(None, "Seleção Necessária", "Por favor, selecione um registro na tabela antes de gerar um documento.")
        return

    df = load_treeview_data()
    ultima_folha = df['Fim'].iloc[-1]
    quantidade_folhas = f"{ultima_folha} ({num2words(ultima_folha, lang='pt_BR')}) folhas"
    objeto = df_registro_selecionado.get('objeto', '')
    id_processo_original = df_registro_selecionado.get('id_processo', 'N/A')
    id_processo_novo = id_processo_original.replace('/', '-')

    template_path = TEMPLATE_DIR / "template_nota_tecnica.docx"
    if not template_path.exists():
        QMessageBox.warning(None, "Erro", f"O template não foi encontrado em: {template_path}")
        return

    doc = DocxTemplate(template_path)
    context = {
        'numero': df_registro_selecionado.get('numero', 'N/A'),
        'ano': df_registro_selecionado.get('ano', 'N/A'),
        'nup': df_registro_selecionado.get('nup', 'N/A'),
        'tipo': df_registro_selecionado.get('tipo', 'N/A'),
        'objeto_completo': df_registro_selecionado.get('objeto_completo', 'N/A'),
        'quantidade_folhas': quantidade_folhas,
        'descricao_servico': "Aquisição de" if df_registro_selecionado.get('material_servico', '') == "material" else "Contratação de empresa especializada em"
    }

    additional_context = {row['Marcador']: f"Fls. {row['Início']} a {row['Fim']}" if row['Início'] != row['Fim'] else f"Fl. {row['Início']}"
                          for index, row in df.iterrows()}
    context.update(additional_context)

    nome_pasta = f"{id_processo_novo} - {remover_caracteres_especiais(objeto)}"
    desktop_path = Path.home() / 'Desktop' / nome_pasta
    desktop_path.mkdir(parents=True, exist_ok=True)

    subpasta_destino = desktop_path / f"{id_processo_novo} - Nota Técnica"
    subpasta_destino.mkdir(parents=True, exist_ok=True)

    doc.render(context)
    output_path = subpasta_destino / f"{id_processo_novo} - Nota Técnica.docx"
    doc.save(output_path)

    return output_path

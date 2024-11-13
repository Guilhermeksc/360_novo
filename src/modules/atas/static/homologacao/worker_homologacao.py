from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from utils import *
import re
import time
import pandas as pd
from utils import *
import pdfplumber

class Worker(QThread):
    processing_complete = pyqtSignal(list)  # Sinal para emitir os dados processados
    update_context_signal = pyqtSignal(str)  # Sinal para atualizar o contexto no diálogo
    progress_signal = pyqtSignal(int)  # Sinal para atualizar a barra de progresso

    def __init__(self, pdf_dir, parent=None):
        super().__init__(parent)
        self.pdf_dir = pdf_dir

    def run(self):
        # Método que será executado na thread
        extracted_data = []
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        total_files = len(pdf_files)

        for index, pdf_file in enumerate(pdf_files):
            text = self.process_single_pdf(pdf_file)
            if text:
                extracted_data.append({
                    "nome_arquivo": pdf_file.name,
                    "text": text
                })
                # Atualiza a área de contexto informando que a análise foi concluída
                self.update_context_signal.emit(f"Análise do PDF {pdf_file.name} concluída com êxito.")
            else:
                # Atualiza a área de contexto informando que a análise falhou
                self.update_context_signal.emit(f"Não foi possível obter os dados corretamente de {pdf_file.name}.")

            # Atualiza a barra de progresso
            progress = int((index + 1) / total_files * 100)
            self.progress_signal.emit(progress)

            # Adiciona um pequeno intervalo para permitir que a interface seja atualizada
            QThread.msleep(100)

        # Emite o sinal de conclusão com os dados extraídos
        self.processing_complete.emit(extracted_data)

    def process_single_pdf(self, pdf_file):
        # Processa um único arquivo PDF e retorna o texto extraído
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        self.update_context_signal.emit(f"Aviso: Página de {pdf_file.name} não contém texto extraível.")
                return text
        except Exception as e:
            self.update_context_signal.emit(f"Erro ao processar {pdf_file.name}: {e}")
            return None

class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cnpj = ""

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return

        item = self.model().itemFromIndex(index)
        if item and " - " in item.text():
            # Usar QTextDocument para extrair texto puro a partir do HTML
            doc = QTextDocument()
            doc.setHtml(item.text())
            plain_text = doc.toPlainText()

            # Extração do CNPJ sem HTML
            if " - " in plain_text:
                self.cnpj = plain_text.split(' - ')[0]

            menu = QMenu(self)
            copyAction = QAction(f"Copiar CNPJ {self.cnpj}", self)
            copyAction.triggered.connect(lambda: self.copy_cnpj(plain_text))
            menu.addAction(copyAction)
            menu.exec(event.globalPos())

    def copy_cnpj(self, text):
        if " - " in text:
            self.cnpj = text.split(' - ')[0]  # Extrai o CNPJ
        QApplication.clipboard().setText(self.cnpj)
        QToolTip.showText(QCursor.pos(), f"CNPJ {self.cnpj} copiado para área de transferência", self)

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid() and event.button() == Qt.MouseButton.LeftButton:
            # Expande ou colapsa o item clicado
            self.setExpanded(index, not self.isExpanded(index))
            
            # Se o item foi expandido, expanda também o primeiro nível de subitens
            if self.isExpanded(index):
                model = self.model()
                numRows = model.rowCount(index)
                for row in range(numRows):
                    childIndex = model.index(row, 0, index)
                    self.setExpanded(childIndex, True)
                    # Colapsa todos os subníveis abaixo do primeiro nível
                    self.collapseAllChildren(childIndex)

        super().mousePressEvent(event)

    def collapseAllChildren(self, parentIndex):
        """Recursivamente colapsa todos os subníveis de um dado índice."""
        model = self.model()
        numRows = model.rowCount(parentIndex)
        for row in range(numRows):
            childIndex = model.index(row, 0, parentIndex)
            self.collapseAllChildren(childIndex)
            self.setExpanded(childIndex, False)

    def update_treeview_with_dataframe(self, dataframe):
        if dataframe is None:
            QMessageBox.critical(self, "Erro", "O DataFrame não está disponível para atualizar a visualização.")
            return
        
        creator = ModeloTreeview(self.icons_dir)
        self.model = creator.criar_modelo(dataframe)
        
        # Verifique se o treeView está inicializado
        if not hasattr(self, 'treeView'):
            self.setup_treeview()

        self.treeView.setModel(self.model)
        # self.treeView.setItemDelegate(HTMLDelegate())
        self.treeView.reset()

    def setup_treeview(self):
        # Verificar se o treeView já existe, e criar se não existir
        if not hasattr(self, 'treeView') or self.treeView is None:
            self.treeView = CustomTreeView()  # Inicializar o treeView se ele não existir

        # Remover ou ocultar a mensagem quando o treeView for exibido
        if hasattr(self, 'message_label') and self.message_label:
            self.message_label.hide()

        # Verificar se o modelo já foi inicializado
        if not hasattr(self, 'model') or self.model is None:
            self.model = QStandardItemModel()  # Inicializando o modelo se ainda não foi inicializado

        # Configurar o treeView com o modelo
        self.treeView.setModel(self.model)

        # Verificar se o dynamic_content_layout existe e é válido antes de tentar modificar
        if hasattr(self, 'dynamic_content_layout') and self.dynamic_content_layout is not None:
            # Limpar widgets antigos do layout dinâmico
            while self.dynamic_content_layout.count():
                widget_to_remove = self.dynamic_content_layout.takeAt(0).widget()
                if widget_to_remove is not None:
                    widget_to_remove.deleteLater()

            # Adicionar o treeView ao layout dinâmico
            self.dynamic_content_layout.addWidget(self.treeView)

        # Configurações adicionais para o treeView
        self.treeView.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.treeView.setAnimated(True)  # Facilita a visualização da expansão/colapso
        self.treeView.setUniformRowHeights(True)  # Uniformiza a altura das linhas
        self.treeView.setItemsExpandable(True)  # Garantir que o botão para expandir esteja visível
        self.treeView.setExpandsOnDoubleClick(False)  # Evita a expansão por duplo clique
        self.setup_treeview_styles()

    def setup_treeview_styles(self):
        header = self.treeView.header()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
class CustomProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Arial", 16))  # Aumentar a fonte do percentual
        self.setTextVisible(False)  # Desativar o texto padrão do QProgressBar

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QColor(Qt.GlobalColor.black))
        rect = self.rect()
        font_metrics = self.fontMetrics()
        progress_percent = self.value()
        text = f"{progress_percent}%" if progress_percent >= 0 else ""
        text_width = font_metrics.horizontalAdvance(text)
        text_height = font_metrics.height()
        painter.drawText(int((rect.width() - text_width) / 2), int((rect.height() + text_height) / 2), text)
        painter.end()

class TreeViewWindow(QDialog): 
    processing_complete = pyqtSignal(pd.DataFrame)  # Signal to emit processed DataFrame

    def __init__(self, dataframe, icons_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resultados do Processamento")
        self.dataframe = dataframe
        self.icons_dir = icons_dir
        # Define the minimum size of the window
        self.setMinimumSize(800, 600)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create the TreeView
        self.treeView = CustomTreeView()
        self.populate_treeview()

        layout.addWidget(self.treeView)

        # Create a QHBoxLayout for buttons
        button_layout = QHBoxLayout()

        # Button "Maximizar Vertical"
        maximizar_button = QPushButton("Maximizar Vertical")
        maximizar_button.clicked.connect(self.maximizar_vertical)
        button_layout.addWidget(maximizar_button)

        # Button "Processar SICAF"
        processar_sicaf_button = QPushButton("Processar SICAF")
        processar_sicaf_button.clicked.connect(self.finalizar_processamento_sicaf)  # Connect to the method
        button_layout.addWidget(processar_sicaf_button)

        # Button "Ajuda"
        ajuda_button = QPushButton("Ajuda")
        ajuda_button.clicked.connect(self.show_ajuda)
        button_layout.addWidget(ajuda_button)

        # Button "Fechar"
        fechar_button = QPushButton("Fechar")
        fechar_button.clicked.connect(self.close)
        button_layout.addWidget(fechar_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def populate_treeview(self):
        # Populate the tree view with the provided dataframe
        creator = ModeloTreeview(self.icons_dir)
        model = creator.criar_modelo(self.dataframe)
        self.treeView.setModel(model)

    def maximizar_vertical(self):
        # Maximize the window vertically
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry.x(), screen_geometry.y(), screen_geometry.width(), screen_geometry.height())

    def show_ajuda(self):
        # Implemente a lógica para mostrar a ajuda
        QMessageBox.information(self, "Ajuda", "A função 'Ajuda' ainda não foi implementada.")

    def iniciar_processamento_sicaf(self):
        # Check if the SICAF directory exists
        if not self.sicaf_dir.exists():
            QMessageBox.warning(self, "Erro", "A pasta SICAF não existe.")
            return
        print(f"Iniciando processamento dos arquivos em: {self.sicaf_dir}")

        # Create an instance of WorkerSICAF
        self.worker = WorkerSICAF(self.sicaf_dir)
        self.worker.processing_complete.connect(self.on_processing_complete)
        self.worker.update_context_signal.connect(self.on_update_context)
        self.worker.progress_signal.connect(self.on_progress_update)

        # Start the thread
        self.worker.start()


    def on_processing_complete(self, extracted_data):
        # Lista para armazenar os DataFrames individuais
        dataframes = []

        for idx, data in enumerate(extracted_data):
            # Extrair dados usando a expressão regular dados_sicaf
            df = extrair_dados_sicaf(data)

            if not df.empty:
                dataframes.append(df)
                print(f"Dados extraídos do arquivo {idx + 1}:")
                print(df)
            else:
                print(f"Nenhum dado extraído do arquivo {idx + 1}.")

        if dataframes:
            # Concatenar todos os DataFrames em um único DataFrame
            final_df = pd.concat(dataframes, ignore_index=True)
            print("Dados extraídos de todos os arquivos:")
            print(final_df)
        else:
            print("Nenhum dado foi extraído de nenhum dos textos.")
            
    def processar_sicaf(self):
        # Implemente a lógica para processar SICAF
        QMessageBox.information(self, "Processar SICAF", "A função 'Processar SICAF' ainda não foi implementada.")

    def show_ajuda(self):
        # Implemente a lógica para mostrar a ajuda
        QMessageBox.information(self, "Ajuda", "A função 'Ajuda' ainda não foi implementada.")

    def show_ajuda(self):
        # Implement your help logic here
        QMessageBox.information(self, "Ajuda", "Esta é a seção de ajuda.")

    def finalizar_processamento_sicaf(self, extracted_data, dataframe):
        self.update_context("Processamento SICAF concluído.")
        self.timer.stop()  # Para o temporizador
        elapsed_time = int(time.time() - self.start_time)
        self.time_label.setText(f"Tempo total: {elapsed_time}s")
        try:
            dados_extraidos = []
            for arquivo_txt in arquivos_txt:
                dados_arquivo = self.processar_arquivo(extracted_data)
                dados_extraidos.append(dados_arquivo)

            df = pd.DataFrame(dados_extraidos)
            if 'empresa' not in df.columns:
                df['empresa'] = None

            if loaded_dataframe is not None and not loaded_dataframe.empty:
                df_final = pd.merge(df, loaded_dataframe, on='cnpj', how='right')
                
                # Preservar todos os dados de loaded_dataframe
                df_final['match'] = df_final['empresa_x'] == df_final['empresa_y']
                
                print("DataFrame após merge e antes de limpeza:")
                print(df_final)

                # Limpeza e ajuste final das colunas
                for col in ['empresa', 'cep', 'endereco', 'municipio', 'telefone', 'email', 'responsavel_legal']:
                    df_final[col] = df_final[col + '_y'].fillna(df_final[col + '_x'])
                    df_final.drop(columns=[col + '_x', col + '_y'], inplace=True)

                df_final = df_final.sort_values(by='item', ascending=True)
                print("DataFrame final após ajustes e limpeza:")
                print(df_final)

            else:
                df_final = df  # Use o DataFrame original se não houver dados para combinar
                print("Não há loaded_dataframe disponível, usando df original.")

        except Exception as e:
            print(f"Erro durante o processamento: {e}")
            df_final = pd.DataFrame()  # Retorne um DataFrame vazio em caso de erro

        return df_final
    
    def processar_arquivo(self, extracted_data):
        item = extrair_dados_sicaf(extracted_data)
        if not item:
            return {'Erro': "Dados do SICAF não encontrados."}
        
        dados_responsavel = extrair_dados_responsavel(extracted_data)
        if dados_responsavel:
            item.update(dados_responsavel)
        else:
            item['Erro'] = "Dados do Responsável Legal não encontrados."
        
        return item

    def update_context(self, text):
        # Update the context area in the dialog
        print(text)  # You might want to display this in a QLabel or QTextEdit instead

    def update_progress(self, value):
        # Update the progress bar in the dialog
        print(f"Progresso: {value}%")  # You might want to update a QProgressBar instead

    def show_ajuda(self):
        # Implement your help logic here
        QMessageBox.information(self, "Ajuda", "Esta é a seção de ajuda.")

    def receber_df_final(self,dataframe):
        if isinstance(dataframe, pd.DataFrame):
            self.current_dataframe = dataframe  # Atualize o DataFrame atual
            print("DataFrame final recebido do SICAF:")
            print(dataframe)

            # Verifica se as colunas necessárias existem
            if {'num_pregao', 'ano_pregao', 'uasg'}.issubset(self.current_dataframe.columns):
                # Filtra linhas onde qualquer uma das colunas chave contém NaN
                filtered_df = self.current_dataframe.dropna(subset=['num_pregao', 'ano_pregao', 'uasg'])
                
                # Gera o nome da tabela apenas para linhas sem NaN
                def create_table_name(row):
                    return f"{row['num_pregao']}-{row['ano_pregao']}-{row['uasg']}-Homolog-Sicaf"

                filtered_df['table_name'] = filtered_df.apply(create_table_name, axis=1)
                
                # Debugging output
                print("Valores de 'num_pregao':", filtered_df['num_pregao'].unique())
                print("Valores de 'ano_pregao':", filtered_df['ano_pregao'].unique())
                print("Valores de 'uasg':", filtered_df['uasg'].unique())
                print("Nomes de tabelas gerados:", filtered_df['table_name'].unique())
                
                if filtered_df['table_name'].nunique() == 1:
                    table_name = filtered_df['table_name'].iloc[0]
                    self.save_data(table_name)  # Chama a função de salvar com o nome da tabela
                else:
                    QMessageBox.critical(self, "Erro", "A combinação de 'num_pregao', 'ano_pregao', e 'uasg' não é única. Por favor, verifique os dados.")
            else:
                QMessageBox.critical(self, "Erro", "Dados necessários para criar o nome da tabela não estão presentes.")
            return self.current_dataframe  # Retorna o DataFrame atualizado
        else:
            QMessageBox.warning(self, "Erro", "Dados recebidos não são válidos.")

class ModeloTreeview:
    def __init__(self, icons_dir):
        self.icon_cache = icons_dir

    def get_icon_for_cnpj(self, cnpj):
        """Verifica se o CNPJ existe na tabela registro_sicaf e retorna o ícone correspondente."""
        try:
            query = "SELECT 1 FROM registro_sicaf WHERE cnpj = ?"
            result = self.db_manager.execute_query(query, (cnpj,))
            return self.icon_cache["check"] if result else self.icon_cache["alert"]
        except Exception as e:
            print(f"Erro ao acessar o banco de dados: {e}")
            return self.icon_cache["alert"]

    def determinar_itens_iguais(self, row, empresa_items):
        empresa_name = str(row['empresa']) if pd.notna(row['empresa']) else ""
        cnpj = str(row['cnpj']) if pd.notna(row['cnpj']) else ""
        situacao = str(row['situacao']) if pd.notna(row['situacao']) else "Não definido"
        is_situacao_only = not empresa_name and not cnpj
        parent_key = f"{situacao}" if is_situacao_only else f"{cnpj} - {empresa_name}".strip(" -")

        if parent_key not in empresa_items:
            parent_item = QStandardItem()
            parent_item.setEditable(False)
            
            # Determina o ícone usando get_icon_for_cnpj
            if cnpj:
                icon = self.get_icon_for_cnpj(cnpj)
            else:
                icon = self.icons.get("alert", QIcon())  # Ícone de alerta caso o CNPJ seja vazio ou ausente

            parent_item.setIcon(icon)
            return parent_key, parent_item

        return parent_key, None

    def update_view(self, view):
        # Força a atualização da view para garantir que os ícones sejam exibidos
        view.viewport().update()
        
    def criar_modelo(self, dataframe):
        model, header = self.initializar_modelo(dataframe)
        empresa_items = self.processar_linhas(dataframe, model)
        self.atualizar_contador_cabecalho(empresa_items, model)
        return model

    def initializar_modelo(self, dataframe):
        total_items = len(dataframe)
        situacoes_analizadas = ['Adjudicado e Homologado', 'Fracassado e Homologado', 'Deserto e Homologado', 'Anulado e Homologado']
        nao_analisados = len(dataframe[~dataframe['situacao'].isin(situacoes_analizadas)])
        header = f"Total de itens da licitação {total_items} | Total de itens analisados {total_items - nao_analisados} | Total de itens não analisados {nao_analisados}"
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([header])
        return model, header

    def processar_linhas(self, dataframe, model):
        empresa_items = {}
        for _, row in dataframe.iterrows():
            self.processar_linhas_individualmente(row, model, empresa_items)
        return empresa_items

    def processar_linhas_individualmente(self, row, model, empresa_items):
        parent_key, parent_item = self.determinar_itens_iguais(row, empresa_items)
        if parent_item:
            model.appendRow(parent_item)
            if parent_key not in empresa_items:
                empresa_items[parent_key] = {
                    'item': parent_item,
                    'count': 0,
                    'details_added': False,
                    'items_container': QStandardItem()  # Não defina o texto aqui
                }
                empresa_items[parent_key]['items_container'].setEditable(False)

        # Ajuste para incrementar a contagem em todas as situações
        if parent_key in empresa_items:
            empresa_items[parent_key]['count'] += 1

        self.adicionar_informacao_ao_item(row, empresa_items[parent_key]['item'], empresa_items, parent_key)

    def adicionar_informacao_ao_item(self, row, parent_item, empresa_items, parent_key):
        font_size = "14px"  # Define o tamanho da fonte
        situacoes_especificas = ['Fracassado e Homologado', 'Deserto e Homologado', 'Anulado e Homologado']
        situacao = row['situacao']

        # Determinar se a situação é específica ou "Não definido"
        if situacao not in situacoes_especificas and situacao != 'Adjudicado e Homologado':
            situacao = 'Não definido'

        if situacao in situacoes_especificas or situacao == 'Não definido':
            # Cria um item com informações básicas sem detalhes extras para situações específicas
            item_text = f"Item {row['item']} - {row['descricao']} - {situacao}"
            item_info = QStandardItem(item_text)
            item_info.setEditable(False)
            parent_item.appendRow(item_info)
        else:
            # Processo normal para 'Adjudicado e Homologado'
            if not empresa_items[parent_key]['details_added']:
                self.adicionar_detalhes_empresa(row, parent_item)
                empresa_items[parent_key]['items_container'].setText("")  # Limpa o texto se necessário
                parent_item.appendRow(empresa_items[parent_key]['items_container'])
                empresa_items[parent_key]['details_added'] = True

            # Adicionando itens específicos da licitação
            self.adicionar_subitens_detalhados(row, empresa_items[parent_key]['items_container'])

        # Atualizar o texto do container com base na contagem de itens
        item_count_text = "Item" if empresa_items[parent_key]['count'] == 1 else "Relação de itens:"
        empresa_items[parent_key]['items_container'].setText(f"{item_count_text} ({empresa_items[parent_key]['count']})")
        
    def atualizar_contador_cabecalho(self, empresa_items, model):
        font_size = "16px"  # Definir o tamanho da fonte para os cabeçalhos dos itens
        for chave_item_pai, empresa in empresa_items.items():
            count = empresa['count']
            # Formatar o texto com HTML para ajustar o tamanho da fonte
            display_text = f"{chave_item_pai} (1 item)" if count == 1 else f"{chave_item_pai} ({count} itens)"
            empresa['item'].setText(display_text)

    def adicionar_detalhes_empresa(self, row, parent_item):
        infos = [
            f"Endereço: {row['endereco']}, CEP: {row['cep']}, Município: {row['municipio']}" if pd.notna(row['endereco']) else "Endereço: Não informado",
            f"Contato: {row['telefone']} Email: {row['email']}" if pd.notna(row['telefone']) else "Contato: Não informado",
            f"Responsável Legal: {row['responsavel_legal']}" if pd.notna(row['responsavel_legal']) else "Responsável Legal: Não informado"
        ]
        for info in infos:
            info_item = QStandardItem(info)
            info_item.setEditable(False)
            parent_item.appendRow(info_item)

    def criar_dados_sicaf_do_item(self, row):
        fields = ['endereco', 'cep', 'municipio', 'telefone', 'email', 'responsavel_legal']
        return [self.criar_detalhe_item(field.capitalize(), row[field]) for field in fields if pd.notna(row[field])]

    def adicionar_subitens_detalhados(self, row, sub_items_layout):
        item_info_html = f"Item {row['item']} - {row['descricao']} - {row['situacao']}"
        item_info = QStandardItem(item_info_html)
        item_info.setEditable(False)
        sub_items_layout.appendRow(item_info)

        detalhes = [
            f"Descrição Detalhada: {row['descricao_detalhada']}",
            f"Unidade de Fornecimento: {row['unidade']} Quantidade: {self.formatar_quantidade(row['quantidade'])} "
            f"Valor Estimado: {self.formatar_brl(row['valor_estimado'])} Valor Homologado: {self.formatar_brl(row['valor_homologado_item_unitario'])} "
            f"Desconto: {self.formatar_percentual(row['percentual_desconto'])} Marca: {row['marca_fabricante']} Modelo: {row['modelo_versao']}",
        ]

        for detalhe in detalhes:
            detalhe_item = QStandardItem(detalhe)
            detalhe_item.setEditable(False)
            item_info.appendRow(detalhe_item)


    def criar_detalhe_item(self, label, data):
        return QStandardItem(f"<b>{label}:</b> {data if pd.notna(data) else 'Não informado'}")

    def formatar_brl(self, valor):
        try:
            if valor is None:
                return "Não disponível"  # ou outra representação adequada para seu caso de uso
            return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except ValueError:
            return "Valor inválido"

    def formatar_quantidade(self, valor):
        try:
            float_value = float(valor)
            if float_value.is_integer():
                return f"{int(float_value)}"
            else:
                return f"{float_value:.2f}".replace('.', ',')
        except ValueError:
            return "Erro de Formatação"

    def formatar_percentual(self, valor):
        try:
            percent_value = float(valor)
            return f"{percent_value:.2f}%"
        except ValueError:
            return "Erro de Formatação"

import re
import pandas as pd

class WorkerSICAF(QThread):
    processing_complete = pyqtSignal(list)  # Signal to emit list of DataFrames
    update_context_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, sicaf_dir, parent=None):
        super().__init__(parent)
        self.sicaf_dir = sicaf_dir

    def run(self):
        dataframes = []
        pdf_files = list(self.sicaf_dir.glob("*.pdf"))
        total_files = len(pdf_files)

        for index, pdf_file in enumerate(pdf_files):
            text = self.process_single_pdf(pdf_file)
            print(f"Texto extraído do arquivo {pdf_file.name}:\n{text}\n{'-'*80}")
            if text:
                # Extrair dados usando as expressões regulares
                df_sicaf = extrair_dados_sicaf(text)
                df_responsavel = extrair_dados_responsavel(text)

                # Verificar se pelo menos um dos DataFrames não está vazio
                if not df_sicaf.empty or not df_responsavel.empty:
                    # Combinar os DataFrames
                    df_combined = pd.concat([df_sicaf, df_responsavel], axis=1)
                    dataframes.append(df_combined)
                    message = f"Análise do PDF {pdf_file.name} concluída com êxito."
                    self.update_context_signal.emit(message)
                    print(message)
                else:
                    message = f"Nenhum dado extraído de {pdf_file.name}."
                    self.update_context_signal.emit(message)
                    print(message)
            else:
                message = f"Não foi possível obter os dados corretamente de {pdf_file.name}."
                self.update_context_signal.emit(message)
                print(message)

            progress = int((index + 1) / total_files * 100)
            self.progress_signal.emit(progress)
            QThread.msleep(100)  # Simulando tempo de processamento

        # Emitir o sinal com a lista de DataFrames
        self.processing_complete.emit(dataframes)



    def process_single_pdf(self, pdf_file):
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        self.update_context_signal.emit(
                            f"Aviso: Página de {pdf_file.name} não contém texto extraível."
                        )
                return text
        except Exception as e:
            self.update_context_signal.emit(f"Erro ao processar {pdf_file.name}: {e}")
            return None


def extrair_dados_sicaf(text):
    # Definir a expressão regular para extração dos dados
    dados_sicaf = (
        r"CNPJ:\s*(?P<cnpj>[\d./-]+)\s*"
        r"(DUNS®:\s*(?P<duns>[\d]+)\s*)?"
        r"Razão Social:\s*(?P<empresa>.*?)\s*"
        r"Nome Fantasia:\s*(?P<nome_fantasia>.*?)\s*"
        r"Situação do Fornecedor:\s*(?P<situacao_cadastro>.*?)\s*"
        r"Data de Vencimento do Cadastro:\s*(?P<data_vencimento>\d{2}/\d{2}/\d{4})\s*"
        r"(Data de Emissão do Certificado:\s*(?P<data_emissao>\d{2}/\d{2}/\d{4})\s*)?"
        r"(Data de Validade do Certificado:\s*(?P<data_validade>\d{2}/\d{2}/\d{4})\s*)?"
        r"(Data de Última Atualização:\s*(?P<data_atualizacao>\d{2}/\d{2}/\d{4})\s*)?"
        r"Dados do Nível.*?Dados para Contato\s*"
        r"CEP:\s*(?P<cep>[\d.-]+)\s*"
        r"Endereço:\s*(?P<endereco>.*?)\s*"
        r"Município / UF:\s*(?P<municipio>.*?)\s*/\s*(?P<uf>.*?)\s*"
        r"Telefone:\s*(?P<telefone>.*?)\s*"
        r"E-mail:\s*(?P<email>.*?)\s*"
        r"Dados do Responsável Legal CPF:\s*(?P<cpf>[\d.-]+)"
    )

    # Procurar todos os matches no texto fornecido
    matches = re.finditer(dados_sicaf, text, re.DOTALL)

    # Extrair os dados e armazenar em uma lista de dicionários
    extracted_data = [match.groupdict() for match in matches]

    # Criar um DataFrame com os dados extraídos
    df = pd.DataFrame(extracted_data)

    return df

# def extrair_dados_sicaf(texto: str) -> pd.DataFrame:
#     dados_sicaf = (
#         r"CNPJ:\s*(?P<cnpj>[\d./-]+)\s*"
#         r"(?:DUNS®:\s*(?P<duns>[\d]+)\s*)?"
#         r"Razão Social:\s*(?P<empresa>.*?)\s*"
#         r"Nome Fantasia:\s*(?P<nome_fantasia>.*?)\s*"
#         r"Situação do Fornecedor:\s*(?P<situacao_cadastro>.*?)\s*"
#         r"Data de Vencimento do Cadastro:\s*(?P<data_vencimento>\d{2}/\d{2}/\d{4})\s*"
#         r"Dados do Nível.*?Dados para Contato\s*"
#         r"CEP:\s*(?P<cep>[\d.-]+)\s*"
#         r"Endereço:\s*(?P<endereco>.*?)\s*"
#         r"Município\s*/\s*UF:\s*(?P<municipio>.*?)\s*/\s*(?P<uf>.*?)\s*"
#         r"Telefone:\s*(?P<telefone>.*?)\s*"
#         r"E-mail:\s*(?P<email>.*?)\s*"
#         r"Dados do Responsável Legal"
#     )

#     match = re.search(dados_sicaf, texto, re.S)
#     if not match:
#         return pd.DataFrame()  # Retorna um DataFrame vazio

#     data = {key: [value.strip()] if value else [None] for key, value in match.groupdict().items()}

#     df = pd.DataFrame(data)
#     return df

def extrair_dados_responsavel(texto: str) -> pd.DataFrame:
    dados_responsavel_sicaf = (
        r"Dados do Responsável Legal\s*CPF:\s*(?P<cpf>\d{3}\.\d{3}\.\d{3}-\d{2})\s*Nome:\s*"
        r"(?P<nome>[^\n\r]*?)(?:\s*Dados do Responsável pelo Cadastro|\s*Emitido em:|\s*CPF:|$)"
    )

    match = re.search(dados_responsavel_sicaf, texto, re.S)
    if not match:
        return pd.DataFrame()  # Retorna um DataFrame vazio

    data = {key: [value.strip()] if value else [None] for key, value in match.groupdict().items()}

    df = pd.DataFrame(data)
    return df

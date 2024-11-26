import json 
from datetime import datetime, timedelta
from pathlib import Path
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QDateEdit, QLineEdit
)
from PyQt6.QtCore import Qt
from src.modules.utils.linha_layout import linha_divisoria_layout

class EtapasManager:
    def __init__(self, db_path, icons):
        self.db_path = db_path
        self.icons = icons
        self.data = self.load_data()

    def load_data(self):
        """Carrega os dados do arquivo JSON."""
        if not Path(self.db_path).exists():
            return {}
        with open(self.db_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def save_data(self):
        """Salva os dados no arquivo JSON."""
        with open(self.db_path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4, ensure_ascii=False)

    def criar_layout_etapas(self, id_processo):
        """Cria o layout das etapas para exibição no PyQt."""
        frame = QFrame()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Layout para o título e contador de dias
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Label principal com o id do processo
        label = QLabel(f"{id_processo} -")
        header_layout.addWidget(label)

        # Calcular o somatório de dias_na_etapa
        total_dias = 0
        if id_processo in self.data:
            total_dias = sum(etapa.get('dias_na_etapa', 0) for etapa in self.data[id_processo])

        # Adicionar o "Contador de Dias"
        contador_label = QLabel(f"Contador de Dias: {total_dias}")
        header_layout.addWidget(contador_label)

        header_layout.addStretch()
        # Adicionar o ícone 'timer' se disponível
        if 'timer' in self.icons:
            timer_icon_label = QLabel()
            timer_icon_label.setPixmap(self.icons['timer'].pixmap(48, 48))
            header_layout.addWidget(timer_icon_label)

        # Adicionar o layout do header ao layout principal
        layout.addLayout(header_layout)

        linha_divisoria, spacer_baixo_linha = linha_divisoria_layout()
        layout.addWidget(linha_divisoria)
        layout.addSpacerItem(spacer_baixo_linha)

        if id_processo not in self.data:
            layout.addWidget(QLabel("Nenhuma etapa encontrada para o processo."))
            frame.setLayout(layout)
            return frame

        etapas = self.data[id_processo]

        # Lista para armazenar widgets e referências
        etapa_widgets = []

        for i, etapa in enumerate(etapas):
            # Obter informações da etapa
            situacao = etapa.get("situacao", "N/A")
            data_inicial = etapa.get("data_inicial", "")
            data_final = etapa.get("data_final", "")
            dias_na_etapa = etapa.get("dias_na_etapa", 0)

            # Criar um layout grid para a etapa
            etapa_layout = QGridLayout()
            etapa_layout.setSpacing(10)

            # Índices das colunas
            ICON_COL = 0
            SITUACAO_COL = 1
            DATA_INICIAL_COL = 2
            DATA_FINAL_COL = 3
            DIAS_COL = 4

            # Adicionar o ícone baseado na situação
            icon_key = {
                'Planejamento': 'priority',
                'Consolidação de Demanda': 'jigsaw',
                'Montagem do Processo': 'montagem',
                'Nota Técnica': 'deal',
                'AGU': 'agu',
                'Aprovado': 'verify_menu',
                'Assinatura Contrato': 'sign',
                'Recomendações AGU': 'report',
                'Pré-Publicação': 'loading_table',
                'Sessão Pública': 'session',
                'Atendimento da NT': 'alert',
                'Concluído': 'aproved',
                'Arquivado': 'archive'
            }.get(situacao)

            if icon_key and icon_key in self.icons:
                icon_label = QLabel()
                icon_label.setPixmap(self.icons[icon_key].pixmap(24, 24))
                etapa_layout.addWidget(icon_label, 0, ICON_COL, alignment=Qt.AlignmentFlag.AlignLeft)

            # Texto da situação
            situacao_label = QLabel(f"Situação: {situacao}")
            etapa_layout.addWidget(situacao_label, 0, SITUACAO_COL, alignment=Qt.AlignmentFlag.AlignLeft)

            # Campos de data editáveis
            date_inicial_edit = QDateEdit()
            date_inicial_edit.setCalendarPopup(True)
            if data_inicial:
                date_inicial_edit.setDate(datetime.strptime(data_inicial, "%Y-%m-%d").date())
            etapa_layout.addWidget(date_inicial_edit, 0, DATA_INICIAL_COL)

            date_final_edit = QDateEdit()
            date_final_edit.setCalendarPopup(True)
            if data_final:
                date_final_edit.setDate(datetime.strptime(data_final, "%Y-%m-%d").date())
            etapa_layout.addWidget(date_final_edit, 0, DATA_FINAL_COL)

            # Campo de dias na etapa (não editável)
            dias_na_etapa_label = QLabel(f"Dias na Etapa: {dias_na_etapa}")
            etapa_layout.addWidget(dias_na_etapa_label, 0, DIAS_COL, alignment=Qt.AlignmentFlag.AlignLeft)

            # Adicionar os widgets à lista para manipulação posterior
            etapa_widgets.append({
                "layout": etapa_layout,
                "date_inicial": date_inicial_edit,
                "date_final": date_final_edit,
                "dias_label": dias_na_etapa_label,
                "index": i
            })

            # Conectar os sinais de alteração de data
            date_inicial_edit.dateChanged.connect(
                lambda _, idx=i, contador_label=contador_label: self.atualizar_datas(id_processo, idx, "inicial", etapa_widgets, contador_label)
            )
            date_final_edit.dateChanged.connect(
                lambda _, idx=i, contador_label=contador_label: self.atualizar_datas(id_processo, idx, "final", etapa_widgets, contador_label)
            )

            # Configurar stretch para as colunas, se necessário
            etapa_layout.setColumnMinimumWidth(DATA_FINAL_COL, 150)  # Coluna 3: DATA_FINAL_COL
            etapa_layout.setColumnMinimumWidth(DATA_INICIAL_COL, 150)  # Coluna 3: DATA_FINAL_COL

            etapa_layout.setColumnMinimumWidth(DIAS_COL, 150)       # Coluna 4: DIAS_COL

            # Configurar stretch para as colunas, se necessário
            # Por exemplo, permitir que a coluna de situação ocupe mais espaço
            etapa_layout.setColumnStretch(SITUACAO_COL, 2)

            # Adicionar o layout da etapa ao layout principal
            layout.addLayout(etapa_layout)

        frame.setLayout(layout)
        return frame

    def atualizar_datas(self, id_processo, idx, campo, widgets, contador_label):
        """
        Atualiza as datas e recalcula as etapas, mantendo a sequência cronológica.
        """
        etapas = self.data[id_processo]
        widget = widgets[idx]

        # Obter a nova data do widget
        nova_data = widget["date_inicial"].date().toPyDate() if campo == "inicial" else widget["date_final"].date().toPyDate()

        # Bloquear sinais para evitar recursão infinita
        widget["date_inicial"].blockSignals(True)
        widget["date_final"].blockSignals(True)

        # Atualizar a data na etapa atual
        etapa = etapas[idx]
        if campo == "inicial":
            etapa["data_inicial"] = nova_data.strftime("%Y-%m-%d")
        else:
            etapa["data_final"] = nova_data.strftime("%Y-%m-%d")

        # Garantir que data_inicial <= data_final na etapa atual
        data_inicial = datetime.strptime(etapa["data_inicial"], "%Y-%m-%d").date()
        data_final = datetime.strptime(etapa["data_final"], "%Y-%m-%d").date()
        if data_inicial > data_final:
            if campo == "inicial":
                data_final = data_inicial
                etapa["data_final"] = data_final.strftime("%Y-%m-%d")
                widget["date_final"].setDate(data_final)
            else:
                data_inicial = data_final
                etapa["data_inicial"] = data_inicial.strftime("%Y-%m-%d")
                widget["date_inicial"].setDate(data_inicial)

        # Ajustar etapas anteriores
        for i in range(idx - 1, -1, -1):
            prev_etapa = etapas[i]
            prev_widget = widgets[i]

            # Garantir que data_final da etapa anterior <= data_inicial da etapa atual
            prev_data_final = datetime.strptime(prev_etapa["data_final"], "%Y-%m-%d").date()
            if prev_data_final > data_inicial:
                prev_data_final = data_inicial
                prev_etapa["data_final"] = prev_data_final.strftime("%Y-%m-%d")
                prev_widget["date_final"].blockSignals(True)
                prev_widget["date_final"].setDate(prev_data_final)
                prev_widget["date_final"].blockSignals(False)

            # Garantir que data_inicial da etapa anterior <= data_final da etapa anterior
            prev_data_inicial = datetime.strptime(prev_etapa["data_inicial"], "%Y-%m-%d").date()
            if prev_data_inicial > prev_data_final:
                prev_data_inicial = prev_data_final
                prev_etapa["data_inicial"] = prev_data_inicial.strftime("%Y-%m-%d")
                prev_widget["date_inicial"].blockSignals(True)
                prev_widget["date_inicial"].setDate(prev_data_inicial)
                prev_widget["date_inicial"].blockSignals(False)

            # Atualizar "Dias na Etapa" da etapa anterior
            prev_etapa["dias_na_etapa"] = max(0, (prev_data_final - prev_data_inicial).days)
            prev_widget["dias_label"].setText(f"Dias na Etapa: {prev_etapa['dias_na_etapa']}")

            # Atualizar data_inicial para a etapa atual
            data_inicial = prev_data_final

        # Ajustar etapas subsequentes
        data_final = datetime.strptime(etapa["data_final"], "%Y-%m-%d").date()
        for i in range(idx + 1, len(etapas)):
            next_etapa = etapas[i]
            next_widget = widgets[i]

            # Garantir que data_inicial da próxima etapa >= data_final da etapa atual
            next_data_inicial = datetime.strptime(next_etapa["data_inicial"], "%Y-%m-%d").date()
            if next_data_inicial < data_final:
                next_data_inicial = data_final
                next_etapa["data_inicial"] = next_data_inicial.strftime("%Y-%m-%d")
                next_widget["date_inicial"].blockSignals(True)
                next_widget["date_inicial"].setDate(next_data_inicial)
                next_widget["date_inicial"].blockSignals(False)

            # Garantir que data_final da próxima etapa >= data_inicial da próxima etapa
            next_data_final = datetime.strptime(next_etapa["data_final"], "%Y-%m-%d").date()
            if next_data_final < next_data_inicial:
                next_data_final = next_data_inicial
                next_etapa["data_final"] = next_data_final.strftime("%Y-%m-%d")
                next_widget["date_final"].blockSignals(True)
                next_widget["date_final"].setDate(next_data_final)
                next_widget["date_final"].blockSignals(False)

            # Atualizar "Dias na Etapa" da próxima etapa
            next_etapa["dias_na_etapa"] = max(0, (next_data_final - next_data_inicial).days)
            next_widget["dias_label"].setText(f"Dias na Etapa: {next_etapa['dias_na_etapa']}")

            # Atualizar data_final para a etapa atual
            data_final = next_data_inicial

        # Atualizar "Dias na Etapa" para a etapa atual
        etapa["dias_na_etapa"] = max(0, (data_final - data_inicial).days)
        widget["dias_label"].setText(f"Dias na Etapa: {etapa['dias_na_etapa']}")

        # Desbloquear sinais
        widget["date_inicial"].blockSignals(False)
        widget["date_final"].blockSignals(False)

        # Atualizar o Contador de Dias
        total_dias = sum(etapa.get('dias_na_etapa', 0) for etapa in etapas)
        contador_label.setText(f"Contador de Dias: {total_dias}")

        # Salvar os dados
        self.save_data()

# ui/dashboard_static.py
"""
Módulo que define o DashboardStatic.

Este widget reutilizável exibe um dashboard estático com os principais
indicadores financeiros, uma lista dos próximos vencimentos e botões de atalho
para as ações mais comuns do sistema.
"""
from decimal import Decimal
from typing import Callable, Optional

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
                             QHeaderView, QLabel, QMessageBox, QPushButton,
                             QStyle, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget)

from models.usuario import Usuario
from services.cliente_service import ClienteService
from services.emprestimo_service import EmprestimoService
from . import styles
from .relogio_widget import RelogioWidget


class DashboardStatic(QWidget):
    """
    Um widget reutilizável que exibe um dashboard estático.

    Este componente é responsável por:
    - Exibir os principais indicadores financeiros (e.g., empréstimos ativos, valor a receber).
    - Mostrar uma tabela com as próximas parcelas a vencer.
    - Fornecer botões de atalho para ações rápidas, como "Novo Empréstimo".
    - Encapsular a lógica de busca e atualização dos dados do dashboard,
      oferecendo uma API clara através do método `refresh()`.
    """
    # Constantes para as colunas da tabela, mantendo o padrão do projeto.
    class _VencimentosTableCols:
        CLIENTE, EMPRESTIMO_ID, PARCELA, VENCIMENTO = range(4)
        HEADERS = ["Cliente", "Empréstimo ID", "Parcela Nº", "Vencimento"]

    def __init__(self,
                 usuario_logado: Usuario,
                 emprestimo_service: EmprestimoService,
                 cliente_service: ClienteService,
                 on_novo_emprestimo: Optional[Callable] = None,
                 on_relatorios: Optional[Callable] = None,
                 on_exportar: Optional[Callable] = None,
                 parent: QWidget = None):
        """
        Inicializa o widget do dashboard.

        Args:
            usuario_logado (Usuario): O objeto do usuário atualmente logado.
            emprestimo_service (EmprestimoService): A instância do serviço de empréstimo.
            cliente_service (ClienteService): A instância do serviço de cliente.
            on_novo_emprestimo (Optional[Callable]): Callback para a ação "Novo Empréstimo".
            on_relatorios (Optional[Callable]): Callback para a ação "Relatórios".
            on_exportar (Optional[Callable]): Callback para a ação "Exportar".
            parent (Optional[QWidget]): O widget pai.
        """
        super().__init__(parent)
        self.usuario_logado = usuario_logado
        self.emprestimo_service = emprestimo_service
        self.cliente_service = cliente_service  # Guardado para futuras evoluções
        self._setup_ui(on_novo_emprestimo, on_relatorios, on_exportar)
        self.update_data()

    def _setup_ui(self, on_novo_emprestimo: Optional[Callable], on_relatorios: Optional[Callable], on_exportar: Optional[Callable]):
        """
        Configura a interface do dashboard, incluindo indicadores, tabelas e botões.

        Args:
            on_novo_emprestimo (Optional[Callable]): Função a ser chamada ao clicar no botão "Novo Empréstimo".
            on_relatorios (Optional[Callable]): Função a ser chamada ao clicar no botão "Relatórios".
            on_exportar (Optional[Callable]): Função a ser chamada ao clicar no botão "Exportar".
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(20)

        # --- Relógio ---
        relogio = RelogioWidget()
        layout.addWidget(relogio, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        # --- Cartões de Indicadores ---
        indicators_layout = QHBoxLayout()
        indicators_layout.setSpacing(20)

        card1, self.emprestimos_ativos_label = self._create_indicator_card("Empréstimos Ativos")
        card2, self.valor_total_label = self._create_indicator_card("Valor Total")
        card3, self.parcelas_atrasadas_label = self._create_indicator_card("Parcelas Atrasadas")
        card4, self.a_receber_label = self._create_indicator_card("A Receber")

        indicators_layout.addWidget(card1)
        indicators_layout.addWidget(card2)
        indicators_layout.addWidget(card3)
        indicators_layout.addWidget(card4)
        layout.addLayout(indicators_layout)

        # --- Tabela de Próximos Vencimentos ---
        self.vencimentos_table = QTableWidget()
        self.vencimentos_table.setObjectName("vencimentosTable")
        self.vencimentos_table.setColumnCount(len(self._VencimentosTableCols.HEADERS))
        self.vencimentos_table.setHorizontalHeaderLabels(self._VencimentosTableCols.HEADERS)
        self.vencimentos_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.vencimentos_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.vencimentos_table.verticalHeader().setVisible(False)
        self.vencimentos_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vencimentos_table.setMinimumHeight(300)
        layout.addWidget(self.vencimentos_table)

        # --- Barra de Atalhos ---
        shortcut_bar = QHBoxLayout()
        shortcut_bar.setSpacing(20)
        shortcut_bar.addStretch()

        # O botão "Novo Empréstimo" só aparece para administradores
        if self.usuario_logado.role.value == 'admin' and on_novo_emprestimo:
            btn_novo_emprestimo = self._create_shortcut_button(
                "Novo Empréstimo",
                self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon),
                on_novo_emprestimo
            )
            shortcut_bar.addWidget(btn_novo_emprestimo)

        if on_relatorios:
            btn_relatorios = self._create_shortcut_button(
                "Relatórios",
                self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView),
                on_relatorios
            )
            shortcut_bar.addWidget(btn_relatorios)
        
        if on_exportar:
            btn_exportar = self._create_shortcut_button(
                "Exportar",
                self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton),
                on_exportar
            )
            shortcut_bar.addWidget(btn_exportar)
        shortcut_bar.addStretch()

        layout.addStretch()
        layout.addLayout(shortcut_bar)

    def _create_shortcut_button(self, text: str, icon: QIcon, on_click: Callable) -> QPushButton:
        """
        Cria e estiliza um botão de atalho para a barra inferior do dashboard.

        Args:
            text (str): O texto a ser exibido no botão.
            icon (QIcon): O ícone do botão.
            on_click (Callable): A função a ser conectada ao evento de clique.

        Returns:
            QPushButton: O widget do botão criado e configurado.
        """
        button = QPushButton(f" {text}")
        button.setIcon(icon)
        button.setIconSize(QSize(24, 24))
        button.setStyleSheet(styles.SHORTCUT_BUTTON_STYLE)
        button.setMinimumHeight(50)
        button.clicked.connect(on_click)
        return button

    def _create_indicator_card(self, title: str) -> tuple[QFrame, QLabel]:
        """
        Cria um cartão de indicador estilizado com título e um QLabel para o valor.

        Args:
            title (str): O título a ser exibido no topo do cartão.

        Returns:
            tuple[QFrame, QLabel]: Uma tupla contendo o QFrame do cartão e a QLabel
                                   onde o valor do indicador será exibido.
        """
        card = QFrame()
        card.setObjectName("indicatorCard")
        card.setStyleSheet(styles.INDICATOR_CARD_STYLE)
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(styles.INDICATOR_TITLE_STYLE)
        value_label = QLabel("0")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(styles.INDICATOR_VALUE_STYLE)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        shadow = QGraphicsDropShadowEffect(blurRadius=15, xOffset=0, yOffset=2, color=QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)
        return card, value_label

    def update_data(self):
        """
        Carrega e exibe os dados mais recentes nos componentes do dashboard.

        Busca os indicadores financeiros e os próximos vencimentos através do
        `emprestimo_service` e atualiza os QLabels e a QTableWidget.
        Lida com exceções que possam ocorrer durante a busca de dados.
        """
        try:
            indicators = self.emprestimo_service.get_dashboard_indicators()
            self.emprestimos_ativos_label.setText(str(indicators.get("emprestimos_ativos", 0)))
            self.valor_total_label.setText(f"R$ {indicators.get('valor_total_emprestado', Decimal('0.0')):,.2f}")
            self.parcelas_atrasadas_label.setText(str(indicators.get("parcelas_atrasadas", 0)))
            self.a_receber_label.setText(f"R$ {indicators.get('a_receber', Decimal('0.0')):,.2f}")
            vencimentos = self.emprestimo_service.get_proximos_vencimentos_detalhados(limit=10)
            self.vencimentos_table.setRowCount(len(vencimentos))
            for row, vencimento in enumerate(vencimentos):
                self.vencimentos_table.setItem(row, self._VencimentosTableCols.CLIENTE, QTableWidgetItem(vencimento['cliente_nome']))
                self.vencimentos_table.setItem(row, self._VencimentosTableCols.EMPRESTIMO_ID, QTableWidgetItem(str(vencimento['emprestimo_id'])))
                self.vencimentos_table.setItem(row, self._VencimentosTableCols.PARCELA, QTableWidgetItem(str(vencimento['parcela_numero'])))
                self.vencimentos_table.setItem(row, self._VencimentosTableCols.VENCIMENTO, QTableWidgetItem(vencimento['data_vencimento'].strftime('%d/%m/%Y')))
        except Exception as e:
            QMessageBox.critical(self, "Erro no Dashboard", f"Não foi possível carregar os dados do dashboard: {e}")

    def refresh(self):
        """
        Método público para solicitar a atualização dos dados do dashboard.

        Funciona como um alias para `update_data`, fornecendo uma API pública
        clara e consistente com os outros widgets de aba.
        """
        self.update_data()
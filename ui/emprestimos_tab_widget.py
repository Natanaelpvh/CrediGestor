# ui/emprestimos_tab_widget.py
"""
Módulo que define o EmprestimosTabWidget.

Este widget encapsula toda a funcionalidade da aba de gerenciamento de empréstimos,
incluindo a busca de clientes, listagem de empréstimos e parcelas, e todas as
operações de CRUD relacionadas.
"""
from decimal import Decimal
from typing import Optional

from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtWidgets import (QCompleter, QHeaderView, QHBoxLayout, QLabel,
                             QMenu, QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QLineEdit, QVBoxLayout, QWidget)

from models.emprestimo import Emprestimo
from models.parcela import Parcela
from models.usuario import UserRole, Usuario
from services.cliente_service import ClienteService
from services.emprestimo_service import EmprestimoService
from services.usuario_service import UsuarioService
from . import styles
from .authorization_dialog import AuthorizationDialog
from .edit_emprestimo_dialog import EditEmprestimoDialog
from .edit_parcela_dialog import EditParcelaDialog
from .emprestimo_dialog import EmprestimoDialog
from .relatorio_parcelas_dialog import RelatorioParcelasDialog


class EmprestimosTabWidget(QWidget):
    """
    Um widget de aba para gerenciar empréstimos e parcelas.
    """
    # Constantes para as colunas das tabelas, movidas de MainWindow
    class _EmprestimoTableCols:
        ID, VALOR, JUROS, PARCELAS, ACOES = range(5)
        HEADERS = ["ID", "Valor", "Juros", "Parcelas", "Ações"]

    class _ParcelaTableCols:
        NUMERO, VALOR, VENCIMENTO, PAGO, ACOES = range(5)
        HEADERS = ["Nº", "Valor", "Vencimento", "Pago", "Ações"]

    def __init__(self, usuario_logado: Usuario, emprestimo_service: EmprestimoService,
                 cliente_service: ClienteService, usuario_service: UsuarioService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.usuario_logado = usuario_logado
        self.emprestimo_service = emprestimo_service
        self.cliente_service = cliente_service
        self.usuario_service = usuario_service

        # Estado interno do widget
        self.selected_cliente_id = None
        self.completer_cliente_map = {}
        self.current_emprestimo_id_for_parcelas = None

        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface da aba de empréstimos."""
        layout = QVBoxLayout(self)

        # Layout de busca de cliente
        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar Cliente (Nome/CPF):")
        self.cliente_search_input = QLineEdit()
        self.cliente_search_input.setPlaceholderText("Digite 2+ caracteres para buscar...")
        self.cliente_search_input.textChanged.connect(self._update_cliente_completer)

        completer = QCompleter(self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.cliente_search_input.setCompleter(completer)

        self.cliente_completer_model = QStringListModel(self)
        completer.setModel(self.cliente_completer_model)
        completer.activated.connect(self._on_cliente_selected_from_completer)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.cliente_search_input)
        layout.addLayout(search_layout)

        self.selected_cliente_label = QLabel("Nenhum cliente selecionado.")
        self.selected_cliente_label.setStyleSheet("font-style: italic; color: #555; padding: 5px 0;")
        layout.addWidget(self.selected_cliente_label)

        btn_layout = QHBoxLayout()
        self.btn_novo_emprestimo = QPushButton("Novo Empréstimo")
        self.btn_novo_emprestimo.clicked.connect(self.novo_emprestimo)
        btn_layout.addWidget(self.btn_novo_emprestimo)
        layout.addLayout(btn_layout)

        self.emprestimos_table = QTableWidget()
        self.emprestimos_table.setColumnCount(len(self._EmprestimoTableCols.HEADERS))
        self.emprestimos_table.setHorizontalHeaderLabels(self._EmprestimoTableCols.HEADERS)
        self.emprestimos_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.emprestimos_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.emprestimos_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self._EmprestimoTableCols.ID, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self._EmprestimoTableCols.VALOR, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(self._EmprestimoTableCols.PARCELAS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self._EmprestimoTableCols.ACOES, QHeaderView.ResizeMode.ResizeToContents)
        self.emprestimos_table.setColumnWidth(self._EmprestimoTableCols.VALOR, 120)
        self.emprestimos_table.setColumnWidth(self._EmprestimoTableCols.JUROS, 220)
        self.emprestimos_table.setColumnWidth(self._EmprestimoTableCols.ACOES, 360)
        layout.addWidget(self.emprestimos_table)

        self.parcelas_table = QTableWidget()
        self.parcelas_table.setColumnCount(len(self._ParcelaTableCols.HEADERS))
        self.parcelas_table.setHorizontalHeaderLabels(self._ParcelaTableCols.HEADERS)
        self.parcelas_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.parcelas_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        parcelas_header = self.parcelas_table.horizontalHeader()
        parcelas_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        parcelas_header.setSectionResizeMode(self._ParcelaTableCols.NUMERO, QHeaderView.ResizeMode.ResizeToContents)
        parcelas_header.setSectionResizeMode(self._ParcelaTableCols.ACOES, QHeaderView.ResizeMode.ResizeToContents)
        self.parcelas_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.parcelas_table.customContextMenuRequested.connect(self._show_parcela_context_menu)
        self.parcelas_table.setColumnWidth(self._ParcelaTableCols.ACOES, 220)
        layout.addWidget(self.parcelas_table)

    def _update_cliente_completer(self, text: str):
        if text in self.completer_cliente_map: return
        if len(text) < 2:
            self.cliente_completer_model.setStringList([])
            self.completer_cliente_map.clear()
            return
        try:
            clientes = self.cliente_service.search_clientes(text, limit=10)
            new_map = {f"{c.nome} ({c.cpf})": c.id for c in clientes}
            self.completer_cliente_map = new_map
            self.cliente_completer_model.setStringList(list(new_map.keys()))
        except Exception as e:
            print(f"Erro ao buscar clientes para o completer: {e}")
            self.cliente_completer_model.setStringList([])
            self.completer_cliente_map.clear()

    def _on_cliente_selected_from_completer(self, text: str):
        cliente_id = self.completer_cliente_map.get(text)
        if cliente_id:
            self.selected_cliente_id = cliente_id
            self.selected_cliente_label.setText(f"Cliente Selecionado: <b>{text}</b>")
            self.load_emprestimos()
        else:
            self._reset_state()

    def load_emprestimos(self):
        self.emprestimos_table.setRowCount(0)
        self.parcelas_table.setRowCount(0)
        if not self.selected_cliente_id: return
        emprestimos = self.emprestimo_service.get_emprestimos_by_cliente_id(self.selected_cliente_id)
        self.emprestimos_table.setRowCount(len(emprestimos))
        for row, emp in enumerate(emprestimos):
            self.emprestimos_table.setItem(row, self._EmprestimoTableCols.ID, QTableWidgetItem(str(emp.id)))
            self.emprestimos_table.setItem(row, self._EmprestimoTableCols.VALOR, QTableWidgetItem(f"R$ {emp.valor:,.2f}"))
            taxas = f"Simples: {emp.taxa_juros_simples}% | Composto: {emp.taxa_juros_composto}% | Mora: {emp.taxa_juros_mora}%"
            self.emprestimos_table.setItem(row, self._EmprestimoTableCols.JUROS, QTableWidgetItem(taxas))
            self.emprestimos_table.setItem(row, self._EmprestimoTableCols.PARCELAS, QTableWidgetItem(str(emp.numero_parcelas)))
            self.emprestimos_table.setCellWidget(row, self._EmprestimoTableCols.ACOES, self._create_emprestimo_actions(emp))

    def _create_emprestimo_actions(self, emprestimo: Emprestimo) -> QWidget:
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(5, 0, 5, 0)
        actions_layout.setSpacing(5)
        btn_ver_parcelas = QPushButton("Parcelas")
        btn_ver_parcelas.setStyleSheet(styles.get_button_style('imprimir'))
        btn_ver_parcelas.clicked.connect(lambda _, eid=emprestimo.id: self.load_parcelas(eid))
        actions_layout.addWidget(btn_ver_parcelas)
        btn_imprimir = QPushButton("Imprimir")
        btn_imprimir.setStyleSheet(styles.get_button_style('imprimir'))
        btn_imprimir.clicked.connect(lambda _, eid=emprestimo.id: self.imprimir_relatorio_emprestimo(eid))
        actions_layout.addWidget(btn_imprimir)
        btn_editar = QPushButton("Editar")
        btn_editar.setStyleSheet(styles.get_button_style('editar'))
        btn_editar.clicked.connect(lambda _, eid=emprestimo.id: self.edit_emprestimo(eid))
        actions_layout.addWidget(btn_editar)
        btn_excluir = QPushButton("Excluir")
        btn_excluir.setStyleSheet(styles.get_button_style('excluir'))
        btn_excluir.clicked.connect(lambda _, eid=emprestimo.id, v=emprestimo.valor: self.delete_emprestimo(eid, v))
        actions_layout.addWidget(btn_excluir)
        return actions_widget

    def novo_emprestimo(self):
        if not self.selected_cliente_id:
            QMessageBox.warning(self, "Seleção Necessária", "Selecione um cliente para adicionar empréstimo.")
            return
        dialog = EmprestimoDialog(self.cliente_service, self.emprestimo_service, parent=self)
        dialog.set_initial_client(self.selected_cliente_id)
        if dialog.exec():
            self.load_emprestimos()

    def edit_emprestimo(self, emprestimo_id: int):
        emprestimo = self.emprestimo_service.get_emprestimo_by_id(emprestimo_id)
        if not emprestimo:
            QMessageBox.warning(self, "Erro", "Empréstimo não encontrado.")
            return
        dialog = EditEmprestimoDialog(emprestimo, self.emprestimo_service, self)
        if dialog.exec():
            self.load_emprestimos()
            self.parcelas_table.setRowCount(0)

    def delete_emprestimo(self, emprestimo_id: int, valor_emprestimo: Decimal):
        reply = QMessageBox.question(self, "Confirmar Exclusão", f"Você tem certeza que deseja excluir o empréstimo de R$ {valor_emprestimo:,.2f} e todas as suas parcelas?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            auth_dialog = AuthorizationDialog(self.usuario_service, [UserRole.ADMIN], f"excluir o empréstimo ID {emprestimo_id}", self)
            if auth_dialog.exec():
                self.emprestimo_service.delete_emprestimo(emprestimo_id)
                QMessageBox.information(self, "Sucesso", "Empréstimo excluído com sucesso.")
                self.load_emprestimos()
                self.parcelas_table.setRowCount(0)

    def imprimir_relatorio_emprestimo(self, emprestimo_id: int):
        relatorio_html = self.emprestimo_service.gerar_relatorio_html_emprestimo(emprestimo_id)
        if not relatorio_html:
            QMessageBox.warning(self, "Relatório Vazio", "Não foi possível gerar o relatório.")
            return
        dialog = RelatorioParcelasDialog(relatorio_html, self)
        dialog.exec()

    def load_parcelas(self, emprestimo_id: int):
        self.current_emprestimo_id_for_parcelas = emprestimo_id
        parcelas = self.emprestimo_service.get_parcelas_by_emprestimo_id(emprestimo_id)
        self.parcelas_table.setRowCount(len(parcelas))
        for row, parcela in enumerate(parcelas):
            self.parcelas_table.setItem(row, self._ParcelaTableCols.NUMERO, QTableWidgetItem(str(parcela.numero)))
            self.parcelas_table.setItem(row, self._ParcelaTableCols.VALOR, QTableWidgetItem(f"R$ {parcela.valor:,.2f}"))
            self.parcelas_table.setItem(row, self._ParcelaTableCols.VENCIMENTO, QTableWidgetItem(parcela.data_vencimento.strftime('%d/%m/%Y')))
            status_item = QTableWidgetItem("Sim" if parcela.pago else "Não")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.parcelas_table.setItem(row, self._ParcelaTableCols.PAGO, status_item)
            self.parcelas_table.setCellWidget(row, self._ParcelaTableCols.ACOES, self._create_parcela_actions(parcela))

    def _create_parcela_actions(self, parcela: Parcela) -> QWidget:
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(5, 0, 5, 0)
        actions_layout.setSpacing(5)
        btn_editar = QPushButton("Editar")
        btn_editar.setStyleSheet(styles.get_button_style('editar'))
        btn_editar.setEnabled(not parcela.pago)
        btn_editar.clicked.connect(lambda _, pid=parcela.id: self.edit_parcela(pid))
        actions_layout.addWidget(btn_editar)
        btn_pagar = QPushButton("Registrar Pagamento")
        btn_pagar.setStyleSheet(styles.get_button_style('pagar'))
        btn_pagar.setEnabled(not parcela.pago)
        btn_pagar.clicked.connect(lambda _, pid=parcela.id: self.registrar_pagamento(pid))
        actions_layout.addWidget(btn_pagar)
        return actions_widget

    def edit_parcela(self, parcela_id: int):
        if not self._request_authorization(f"editar a parcela Nº {parcela_id}"): return
        parcela = self.emprestimo_service.get_parcela_by_id(parcela_id)
        if not parcela or parcela.pago: return
        emprestimo = self.emprestimo_service.get_emprestimo_by_id(parcela.emprestimo_id)
        if not emprestimo: return
        dialog = EditParcelaDialog(parcela, emprestimo.taxa_juros_mora, self)
        if dialog.exec():
            self.emprestimo_service.update_valor_parcela(parcela_id, dialog.get_novo_valor())
            QMessageBox.information(self, "Sucesso", "Valor da parcela atualizado.")
            self.load_parcelas(parcela.emprestimo_id)

    def registrar_pagamento(self, parcela_id: int):
        if not self._request_authorization(f"registrar o pagamento da parcela Nº {parcela_id}"): return
        parcela_atualizada = self.emprestimo_service.registrar_pagamento_parcela(parcela_id)
        if parcela_atualizada:
            QMessageBox.information(self, "Pagamento Registrado", "Pagamento registrado com sucesso.")
            self.load_parcelas(parcela_atualizada.emprestimo_id)
        else:
            QMessageBox.warning(self, "Aviso", "A parcela não foi encontrada ou já estava paga.")

    def _request_authorization(self, action_name: str) -> bool:
        allowed_roles = [UserRole.ADMIN, UserRole.OPERADOR]
        auth_dialog = AuthorizationDialog(self.usuario_service, allowed_roles, action_name, self)
        return auth_dialog.exec()

    def _show_parcela_context_menu(self, pos):
        if self.parcelas_table.rowAt(pos.y()) < 0: return
        menu = QMenu(self)
        details_action = menu.addAction("Ver Detalhes do Empréstimo")
        details_action.triggered.connect(self._show_emprestimo_details_from_parcela)
        menu.exec(self.parcelas_table.mapToGlobal(pos))

    def _show_emprestimo_details_from_parcela(self):
        if self.current_emprestimo_id_for_parcelas:
            self.imprimir_relatorio_emprestimo(self.current_emprestimo_id_for_parcelas)

    def _reset_state(self):
        """Limpa o estado da aba, preparando-a para uma nova consulta."""
        self.selected_cliente_id = None
        self.cliente_search_input.blockSignals(True)
        self.cliente_search_input.clear()
        self.cliente_search_input.blockSignals(False)
        self.selected_cliente_label.setText("Nenhum cliente selecionado.")
        self.emprestimos_table.setRowCount(0)
        self.parcelas_table.setRowCount(0)

    def refresh_data(self):
        """Método público para ser chamado quando a aba se torna visível."""
        self._reset_state()
# ui/clientes_tab_widget.py
"""
Módulo que define o ClientesTabWidget.

Este widget encapsula toda a funcionalidade da aba de gerenciamento de clientes,
incluindo a interface do usuário (tabela, botões, campo de busca) e as operações
de CRUD (Criar, Ler, Atualizar, Deletar).
"""
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from PyQt6.QtWidgets import (QHeaderView, QHBoxLayout, QLabel, QMessageBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QLineEdit, QVBoxLayout, QWidget)

from models.cliente import Cliente
from services.cliente_service import ClienteService
from .cliente_dialog import ClienteDialog


class ClientesTabWidget(QWidget):
    """
    Um widget de aba para gerenciar clientes (CRUD e busca).
    Encapsula toda a lógica e UI da aba de clientes.
    """
    # Constantes para as colunas da tabela, movidas de MainWindow
    class _ClienteTableCols:
        ID, NOME, CPF, TELEFONE, EMAIL, ENDERECO = range(6)
        HEADERS = ["ID", "Nome", "CPF", "Telefone", "Email", "Endereço"]
    def __init__(self, cliente_service: ClienteService, db_session: Session, parent: Optional[QWidget] = None):
        """
        Inicializa o widget da aba de clientes.

        Args:
            cliente_service (ClienteService): A instância do serviço de cliente.
            db_session (Session): A sessão do SQLAlchemy para controle de transação
                em caso de erros.
            parent (Optional[QWidget]): O widget pai.
        """
        super().__init__(parent)
        self.cliente_service = cliente_service
        self.db_session = db_session
        self._setup_ui()
        self.load_clientes()

    def _setup_ui(self):
        """Configura a interface da aba de clientes."""
        layout = QVBoxLayout(self)

        # Layout de controle (busca e botões)
        control_layout = QHBoxLayout()
        self.search_label = QLabel("Buscar por Nome ou CPF:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite para buscar...")
        self.search_input.textChanged.connect(self.search_clientes)
        
        self.add_button = QPushButton("Novo Cliente")
        self.add_button.clicked.connect(self.add_cliente)
        
        self.edit_button = QPushButton("Editar Cliente")
        self.edit_button.clicked.connect(self.edit_cliente)
        
        self.delete_button = QPushButton("Excluir Cliente")
        self.delete_button.clicked.connect(self.delete_cliente)

        control_layout.addWidget(self.search_label)
        control_layout.addWidget(self.search_input)
        control_layout.addStretch()
        control_layout.addWidget(self.add_button)
        control_layout.addWidget(self.edit_button)
        control_layout.addWidget(self.delete_button)
        layout.addLayout(control_layout)

        # Tabela de clientes
        self.table = QTableWidget()
        self.table.setColumnCount(len(self._ClienteTableCols.HEADERS))
        self.table.setHorizontalHeaderLabels(self._ClienteTableCols.HEADERS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(self._ClienteTableCols.NOME, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

    def load_clientes(self, clientes: Optional[List[Cliente]] = None):
        """Carrega os dados dos clientes na tabela."""
        try:
            clientes_a_carregar = clientes if clientes is not None else self.cliente_service.get_all_clientes()
            self.table.setRowCount(len(clientes_a_carregar))
            for row, cliente in enumerate(clientes_a_carregar):
                self.table.setItem(row, self._ClienteTableCols.ID, QTableWidgetItem(str(cliente.id)))
                self.table.setItem(row, self._ClienteTableCols.NOME, QTableWidgetItem(cliente.nome))
                self.table.setItem(row, self._ClienteTableCols.CPF, QTableWidgetItem(cliente.cpf))
                self.table.setItem(row, self._ClienteTableCols.TELEFONE, QTableWidgetItem(cliente.telefone))
                self.table.setItem(row, self._ClienteTableCols.EMAIL, QTableWidgetItem(cliente.email))
                self.table.setItem(row, self._ClienteTableCols.ENDERECO, QTableWidgetItem(cliente.endereco))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível carregar os clientes: {e}")

    def search_clientes(self):
        """Filtra a lista de clientes com base no termo de busca."""
        search_term = self.search_input.text()
        self.load_clientes(self.cliente_service.search_clientes(search_term))

    def add_cliente(self):
        """Abre o diálogo para adicionar um novo cliente."""
        dialog = ClienteDialog(parent=self)
        if dialog.exec():
            try:
                self.cliente_service.create_cliente(**dialog.get_data())
                self.load_clientes()
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Erro", f"Não foi possível criar o cliente: {e}")

    def edit_cliente(self):
        """Abre o diálogo para editar o cliente selecionado."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um cliente para editar.")
            return
        cliente_id = int(self.table.item(selected_row, self._ClienteTableCols.ID).text())
        cliente = self.cliente_service.get_cliente_by_id(cliente_id)
        if cliente:
            dialog = ClienteDialog(cliente=cliente, parent=self)
            if dialog.exec():
                try:
                    self.cliente_service.update_cliente(cliente_id, **dialog.get_data())
                    self.load_clientes()
                except Exception as e:
                    self.db_session.rollback()
                    QMessageBox.critical(self, "Erro", f"Não foi possível atualizar o cliente: {e}")

    def delete_cliente(self):
        """Exclui o cliente selecionado."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um cliente para excluir.")
            return
        cliente_id = int(self.table.item(selected_row, self._ClienteTableCols.ID).text())
        cliente_nome = self.table.item(selected_row, self._ClienteTableCols.NOME).text()
        reply = QMessageBox.question(self, "Confirmar Exclusão", f"Você tem certeza que deseja excluir o cliente '{cliente_nome}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cliente_service.delete_cliente(cliente_id)
                self.load_clientes()
            except IntegrityError:
                # É crucial reverter a sessão para um estado limpo após um erro.
                self.db_session.rollback()
                QMessageBox.critical(self, "Operação Inválida", "Este cliente não pode ser excluído, pois possui um ou mais empréstimos ativos associados.")
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Erro", f"Ocorreu um erro inesperado ao excluir o cliente: {e}")

    def refresh_data(self):
        """Método público para recarregar os dados da aba, limpando a busca."""
        self.search_input.clear()
        self.load_clientes()
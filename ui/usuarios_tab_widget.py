# ui/usuarios_tab_widget.py
"""
Módulo que define o UsuariosTabWidget.

Este widget encapsula toda a funcionalidade da aba de gerenciamento de usuários,
incluindo a interface do usuário (tabela, botões, campo de busca) e as operações
de CRUD (Criar, Ler, Atualizar, Deletar).
"""
from typing import List, Optional

from sqlalchemy.orm import Session
from PyQt6.QtWidgets import (QHeaderView, QHBoxLayout, QLabel, QMessageBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QLineEdit, QVBoxLayout, QWidget)

from models.usuario import Usuario
from services.usuario_service import UsuarioService
from .usuario_dialog import UsuarioDialog


class UsuariosTabWidget(QWidget):
    """
    Um widget de aba para gerenciar usuários (CRUD e busca).
    """
    # Constantes para as colunas da tabela, movidas de MainWindow
    class _UsuarioTableCols:
        ID, NOME, EMAIL, CARGO = range(4)
        HEADERS = ["ID", "Nome", "Email", "Cargo"]

    def __init__(self, usuario_service: UsuarioService, usuario_logado: Usuario, db_session: Session, parent: Optional[QWidget] = None):
        """
        Inicializa o widget da aba de usuários.

        Args:
            usuario_service (UsuarioService): A instância do serviço de usuário.
            usuario_logado (Usuario): O usuário atualmente logado na aplicação.
            db_session (Session): A sessão do SQLAlchemy para controle de transação.
            parent (Optional[QWidget]): O widget pai.
        """
        super().__init__(parent)
        self.usuario_service = usuario_service
        self.usuario_logado = usuario_logado
        self.db_session = db_session
        self._setup_ui()
        self.load_usuarios()

    def _setup_ui(self):
        """Configura a interface da aba de usuários."""
        layout = QVBoxLayout(self)

        # Layout de controle
        control_layout = QHBoxLayout()
        self.search_label = QLabel("Buscar por Nome ou Email:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite para buscar...")
        self.search_input.textChanged.connect(self.search_usuarios)
        
        self.add_button = QPushButton("Novo Usuário")
        self.add_button.clicked.connect(self.add_usuario)
        
        self.edit_button = QPushButton("Editar Usuário")
        self.edit_button.clicked.connect(self.edit_usuario)
        
        self.delete_button = QPushButton("Excluir Usuário")
        self.delete_button.clicked.connect(self.delete_usuario)

        control_layout.addWidget(self.search_label)
        control_layout.addWidget(self.search_input)
        control_layout.addStretch()
        control_layout.addWidget(self.add_button)
        control_layout.addWidget(self.edit_button)
        control_layout.addWidget(self.delete_button)
        layout.addLayout(control_layout)

        # Tabela de usuários
        self.table = QTableWidget()
        self.table.setColumnCount(len(self._UsuarioTableCols.HEADERS))
        self.table.setHorizontalHeaderLabels(self._UsuarioTableCols.HEADERS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load_usuarios(self, usuarios: Optional[List[Usuario]] = None):
        """Carrega os dados dos usuários na tabela."""
        try:
            usuarios_a_carregar = usuarios if usuarios is not None else self.usuario_service.get_all_usuarios()
            self.table.setRowCount(len(usuarios_a_carregar))
            for row, usuario in enumerate(usuarios_a_carregar):
                self.table.setItem(row, self._UsuarioTableCols.ID, QTableWidgetItem(str(usuario.id)))
                self.table.setItem(row, self._UsuarioTableCols.NOME, QTableWidgetItem(usuario.nome))
                self.table.setItem(row, self._UsuarioTableCols.EMAIL, QTableWidgetItem(usuario.email))
                self.table.setItem(row, self._UsuarioTableCols.CARGO, QTableWidgetItem(usuario.role.value))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível carregar os usuários: {e}")

    def search_usuarios(self):
        """Filtra a lista de usuários com base no termo de busca."""
        search_term = self.search_input.text()
        self.load_usuarios(self.usuario_service.search_usuarios(search_term))

    def add_usuario(self):
        """Abre o diálogo para adicionar um novo usuário."""
        dialog = UsuarioDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.usuario_service.create_usuario(**data)
                self.load_usuarios()
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Erro", f"Não foi possível criar o usuário: {e}")

    def edit_usuario(self):
        """Abre o diálogo para editar o usuário selecionado."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um usuário para editar.")
            return
        usuario_id = int(self.table.item(selected_row, self._UsuarioTableCols.ID).text())
        usuario = self.usuario_service.get_usuario_by_id(usuario_id)
        if usuario:
            dialog = UsuarioDialog(usuario=usuario, parent=self)
            if dialog.exec():
                data = dialog.get_data()
                if not data.get('senha'):  # Senha é opcional na edição
                    data.pop('senha', None)
                try:
                    self.usuario_service.update_usuario(usuario_id, **data)
                    self.load_usuarios()
                except Exception as e:
                    self.db_session.rollback()
                    QMessageBox.critical(self, "Erro", f"Não foi possível atualizar o usuário: {e}")

    def delete_usuario(self):
        """Exclui o usuário selecionado."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Seleção Necessária", "Por favor, selecione um usuário para excluir.")
            return
        usuario_id = int(self.table.item(selected_row, self._UsuarioTableCols.ID).text())
        
        if usuario_id == self.usuario_logado.id:
            QMessageBox.critical(self, "Ação Inválida", "Você não pode excluir o seu próprio usuário.")
            return
            
        usuario_nome = self.table.item(selected_row, self._UsuarioTableCols.NOME).text()
        reply = QMessageBox.question(self, "Confirmar Exclusão", f"Você tem certeza que deseja excluir o usuário '{usuario_nome}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.usuario_service.delete_usuario(usuario_id)
                self.load_usuarios()
            except Exception as e:
                self.db_session.rollback()
                QMessageBox.critical(self, "Erro", f"Não foi possível excluir o usuário: {e}")

    def refresh_data(self):
        """Método público para recarregar os dados da aba, limpando a busca."""
        self.search_input.clear()
        self.load_usuarios()
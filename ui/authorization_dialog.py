# ui/authorization_dialog.py

from typing import Optional, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QLabel,
                             QLineEdit, QMessageBox, QVBoxLayout)

from models.usuario import Usuario, UserRole
from services.usuario_service import UsuarioService


class AuthorizationDialog(QDialog):
    """
    Um diálogo modal para solicitar autorização de um usuário qualificado.
    """
    def __init__(self, usuario_service: UsuarioService, allowed_roles: List[UserRole],
                 action_name: str, parent=None):
        super().__init__(parent)
        self.usuario_service = usuario_service
        self.allowed_roles = allowed_roles
        self.action_name = action_name

        self.setWindowTitle("Autorização Necessária")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # --- Mensagem de Ação ---
        self.action_label = QLabel(f"É necessária a autorização de um usuário qualificado para <b>{self.action_name}</b>.")
        self.action_label.setWordWrap(True)
        layout.addWidget(self.action_label)

        # --- Widgets de Entrada ---
        self.email_label = QLabel("Email do Autorizador:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email.autorizador@example.com")
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)

        self.senha_label = QLabel("Senha do Autorizador:")
        self.senha_input = QLineEdit()
        self.senha_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.senha_label)
        layout.addWidget(self.senha_input)

        # --- Botões ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Autorizar")
        self.button_box.accepted.connect(self._attempt_authorization)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _attempt_authorization(self):
        """Lida com a tentativa de autorização quando o botão OK é clicado."""
        email = self.email_input.text().strip()
        senha = self.senha_input.text()

        if not email or not senha:
            QMessageBox.warning(self, "Autorização Inválida", "Email e senha são obrigatórios.")
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            authorizing_user = self.usuario_service.verify_credentials(email, senha)

            if not authorizing_user:
                QMessageBox.warning(self, "Autorização Falhou", "Email ou senha incorretos.")
                self.senha_input.clear()
                self.senha_input.setFocus()
                return

            if authorizing_user.role not in self.allowed_roles:
                allowed_roles_str = ", ".join([role.value.capitalize() for role in self.allowed_roles])
                QMessageBox.warning(self, "Não Autorizado",
                                    f"O usuário '{authorizing_user.nome}' não tem permissão para autorizar esta ação.\n"
                                    f"Perfis permitidos: {allowed_roles_str}.")
                return

            # Se todas as verificações passaram, a autorização é bem-sucedida
            QMessageBox.information(self, "Autorizado", f"Ação autorizada por {authorizing_user.nome}.")
            super().accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro de Autorização", f"Ocorreu um erro inesperado: {e}")
        finally:
            QApplication.restoreOverrideCursor()
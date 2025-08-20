# ui/login_dialog.py

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QLabel,
                             QLineEdit, QMessageBox, QVBoxLayout)

from models.usuario import Usuario
from services.usuario_service import UsuarioService


class LoginDialog(QDialog):
    """
    Um diálogo modal para autenticação de usuário.

    Este diálogo agora contém a lógica de verificação, permitindo
    mostrar um feedback de "carregando" para o usuário.
    """
    def __init__(self, usuario_service: UsuarioService, parent=None):
        super().__init__(parent)
        self.usuario_service = usuario_service
        self.usuario_logado: Optional[Usuario] = None

        self.setWindowTitle("Login do Sistema")
        self.setModal(True)
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        # --- Widgets de Entrada ---
        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("seu.email@example.com")
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)

        self.senha_label = QLabel("Senha:")
        self.senha_input = QLineEdit()
        self.senha_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.senha_label)
        layout.addWidget(self.senha_input)

        # --- Widget de Status (Carregando) ---
        self.status_label = QLabel("Verificando credenciais...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #555;")
        self.status_label.hide()  # Oculto inicialmente
        layout.addWidget(self.status_label)

        # --- Botões ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        # Conectamos o sinal 'accepted' (botão OK) ao nosso método de login
        self.button_box.accepted.connect(self._attempt_login)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _set_ui_enabled(self, enabled: bool):
        """Ativa ou desativa os elementos da UI durante o processamento."""
        self.email_input.setEnabled(enabled)
        self.senha_input.setEnabled(enabled)
        self.button_box.setEnabled(enabled)

    def _attempt_login(self):
        """Lida com a tentativa de login quando o botão OK é clicado."""
        email = self.email_input.text().strip()
        senha = self.senha_input.text()

        if not email or not senha:
            QMessageBox.warning(self, "Login Inválido", "Email e senha são obrigatórios.")
            return

        self._set_ui_enabled(False)
        self.status_label.show()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
            authenticated_user = self.usuario_service.verify_credentials(email, senha)
            if authenticated_user:
                self.usuario_logado = authenticated_user
                super().accept()  # Fecha o diálogo com sucesso
            else:
                QMessageBox.warning(self, "Login Falhou", "Email ou senha incorretos.")
                self._set_ui_enabled(True)
                self.senha_input.clear()
                self.senha_input.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "Erro de Login", f"Ocorreu um erro inesperado: {e}")
            self._set_ui_enabled(True)
        finally:
            self.status_label.hide()
            QApplication.restoreOverrideCursor()

    def get_authenticated_user(self) -> Optional[Usuario]:
        """Retorna o objeto do usuário se a autenticação foi bem-sucedida."""
        return self.usuario_logado
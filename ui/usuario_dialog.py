# ui/usuario_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QComboBox, QFormLayout, QMessageBox,
    QDialogButtonBox
)
from typing import Optional, Dict, Any
from models.usuario import Usuario, UserRole

class UsuarioDialog(QDialog):
    """
    Janela de diálogo para criar ou editar um usuário.
    """
    def __init__(self, usuario: Optional[Usuario] = None, parent=None):
        super().__init__(parent)
        self.usuario = usuario

        if self.usuario:
            self.setWindowTitle("Editar Usuário")
        else:
            self.setWindowTitle("Novo Usuário")

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # --- Campos do formulário ---
        self.nome_input = QLineEdit(self)
        self.email_input = QLineEdit(self)
        self.senha_input = QLineEdit(self)
        self.senha_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.role_input = QComboBox(self)
        # Adiciona os papéis (roles) do Enum ao ComboBox
        for role in UserRole:
            self.role_input.addItem(role.value.capitalize(), role)

        # --- Adiciona campos ao layout do formulário ---
        self.form_layout.addRow("Nome:", self.nome_input)
        self.form_layout.addRow("Email:", self.email_input)
        self.form_layout.addRow("Senha:", self.senha_input)
        self.form_layout.addRow("Papel (Role):", self.role_input)

        self.layout.addLayout(self.form_layout)

        # --- Botões ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.button_box)

        # --- Preenche os campos se estiver editando ---
        if self.usuario:
            self.nome_input.setText(self.usuario.nome)
            self.email_input.setText(self.usuario.email)
            self.senha_input.setPlaceholderText("Deixe em branco para não alterar")
            # Encontra e seleciona o papel (role) correto no ComboBox
            index = self.role_input.findData(self.usuario.role)
            if index >= 0:
                self.role_input.setCurrentIndex(index)

    def get_data(self) -> Dict[str, Any]:
        """Retorna os dados dos campos do formulário em um dicionário."""
        data = {
            "nome": self.nome_input.text().strip(),
            "email": self.email_input.text().strip(),
            "role": self.role_input.currentData()  # Retorna o valor do Enum UserRole
        }
        # Apenas inclui a senha se ela for preenchida
        if self.senha_input.text():
            data["senha"] = self.senha_input.text()
        return data

    def accept(self):
        """Valida os dados antes de fechar o diálogo."""
        data = self.get_data()
        if not data["nome"] or not data["email"]:
            QMessageBox.warning(self, "Campos Obrigatórios", "Os campos Nome e Email são obrigatórios.")
            return

        # A senha é obrigatória apenas ao criar um novo usuário
        if not self.usuario and 'senha' not in data:
            QMessageBox.warning(self, "Campo Obrigatório", "O campo Senha é obrigatório para novos usuários.")
            return

        # Se a validação passar, aceita o diálogo
        super().accept()
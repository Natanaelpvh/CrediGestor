# ui/cliente_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QPushButton, QFormLayout, QMessageBox,
    QDialogButtonBox
)
from typing import Optional
from models.cliente import Cliente

class ClienteDialog(QDialog):
    """
    Janela de diálogo para criar ou editar um cliente.
    """
    def __init__(self, cliente: Optional[Cliente] = None, parent=None):
        super().__init__(parent)
        self.cliente = cliente
        
        if self.cliente:
            self.setWindowTitle("Editar Cliente")
        else:
            self.setWindowTitle("Novo Cliente")

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # Campos do formulário
        self.nome_input = QLineEdit(self)
        self.cpf_input = QLineEdit(self)
        # Adiciona uma máscara para o campo CPF para guiar o usuário
        self.cpf_input.setInputMask("000.000.000-00")
        self.telefone_input = QLineEdit(self)
        self.email_input = QLineEdit(self)
        self.endereco_input = QLineEdit(self)
        
        # Adiciona campos ao layout do formulário
        self.form_layout.addRow("Nome:", self.nome_input)
        self.form_layout.addRow("CPF:", self.cpf_input)
        self.form_layout.addRow("Telefone:", self.telefone_input)
        self.form_layout.addRow("Email:", self.email_input)
        self.form_layout.addRow("Endereço:", self.endereco_input)

        self.layout.addLayout(self.form_layout)

        # Botões
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.layout.addWidget(self.button_box)

        # Preenche os campos se estiver editando
        if self.cliente:
            self.nome_input.setText(self.cliente.nome)
            self.cpf_input.setText(self.cliente.cpf)
            self.telefone_input.setText(self.cliente.telefone)
            self.email_input.setText(self.cliente.email)
            self.endereco_input.setText(self.cliente.endereco)

    def get_data(self) -> dict:
        """Retorna os dados dos campos do formulário."""
        return {
            "nome": self.nome_input.text().strip(),
            "cpf": self.cpf_input.text().strip(),
            "telefone": self.telefone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "endereco": self.endereco_input.text().strip()
        }

    def accept(self):
        """Valida os dados antes de fechar o diálogo."""
        data = self.get_data()
        if not data["nome"] or not data["cpf"]:
            QMessageBox.warning(self, "Campo Obrigatório", "Os campos Nome e CPF são obrigatórios.")
            return
        super().accept()
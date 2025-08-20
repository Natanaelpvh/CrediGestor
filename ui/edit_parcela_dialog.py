# ui/edit_parcela_dialog.py

from decimal import Decimal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox,
    QMessageBox, QDoubleSpinBox, QLabel
)
from models.parcela import Parcela

class EditParcelaDialog(QDialog):
    """
    Janela de diálogo para editar uma parcela, aplicando juros de mora.
    """
    def __init__(self, parcela: Parcela, taxa_juros_mora_padrao: Decimal, parent=None):
        super().__init__(parent)
        self.parcela = parcela
        self.setWindowTitle(f"Editar Parcela Nº {self.parcela.numero}")
        self.setModal(True)
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Informações da Parcela ---
        self.valor_original_label = QLabel(f"R$ {self.parcela.valor:,.2f}")
        self.novo_valor_label = QLabel()

        # --- Campo para Juros de Mora ---
        self.juros_mora_input = QDoubleSpinBox()
        self.juros_mora_input.setSuffix("%")
        self.juros_mora_input.setRange(0.0, 100.0)
        self.juros_mora_input.setDecimals(2)
        self.juros_mora_input.setValue(float(taxa_juros_mora_padrao or 0.0))
        self.juros_mora_input.valueChanged.connect(self.calcular_novo_valor)

        form_layout.addRow("Valor Original:", self.valor_original_label)
        form_layout.addRow("Taxa de Juros de Mora:", self.juros_mora_input)
        form_layout.addRow("Novo Valor da Parcela:", self.novo_valor_label)

        layout.addLayout(form_layout)

        # --- Botões ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.novo_valor_calculado = self.parcela.valor
        self.calcular_novo_valor()

    def calcular_novo_valor(self):
        """Calcula e atualiza o novo valor da parcela com base nos juros."""
        taxa_juros = Decimal(str(self.juros_mora_input.value())) / Decimal(100)
        valor_juros = self.parcela.valor * taxa_juros
        self.novo_valor_calculado = round(self.parcela.valor + valor_juros, 2)
        self.novo_valor_label.setText(f"R$ {self.novo_valor_calculado:,.2f}")

    def get_novo_valor(self) -> Decimal:
        """Retorna o novo valor calculado para a parcela."""
        return self.novo_valor_calculado

    def accept(self):
        """Valida os dados antes de fechar o diálogo."""
        if self.get_novo_valor() < self.parcela.valor:
            QMessageBox.warning(self, "Valor Inválido", "O novo valor não pode ser menor que o valor original.")
            return
        super().accept()

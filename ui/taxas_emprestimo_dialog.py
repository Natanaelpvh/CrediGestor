from PyQt6.QtWidgets import QDialog, QFormLayout, QDoubleSpinBox, QPushButton, QMessageBox
from services.taxas_emprestimo_service import TaxaJurosService
from decimal import Decimal

class TaxaJurosDialog(QDialog):
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Taxas de Juros")
        self.service = TaxaJurosService(db_session)
        taxas = self.service.get_taxas()
        layout = QFormLayout(self)

        self.simples = QDoubleSpinBox()
        self.simples.setSuffix("%")
        self.simples.setMaximum(100)
        self.simples.setValue(float(taxas.taxa_juros_simples or 0.0))
        layout.addRow("Juros Simples:", self.simples)

        self.composto = QDoubleSpinBox()
        self.composto.setSuffix("%")
        self.composto.setMaximum(100)
        self.composto.setValue(float(taxas.taxa_juros_composto or 0.0))
        layout.addRow("Juros Composto:", self.composto)

        self.mora = QDoubleSpinBox()
        self.mora.setSuffix("%")
        self.mora.setMaximum(100)
        self.mora.setValue(float(taxas.taxa_juros_mora or 0.0))
        layout.addRow("Juros Mora:", self.mora)

        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(self.salvar)
        layout.addRow(btn_salvar)

    def salvar(self):
        self.service.atualizar_taxas(
            Decimal(str(self.simples.value())),
            Decimal(str(self.composto.value())),
            Decimal(str(self.mora.value()))
        )
        QMessageBox.information(self, "Taxas Atualizadas", "Taxas salvas com sucesso!")
        self.accept()

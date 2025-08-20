# ui/relatorio_parcelas_dialog.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QPushButton, QMessageBox
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtCore import Qt

class RelatorioParcelasDialog(QDialog):
    """
    Janela de diálogo para exibir e imprimir o relatório de parcelas de um cliente.
    """
    def __init__(self, relatorio_html: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Relatório de Parcelas do Cliente")
        self.setModal(True)
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # --- Editor de Texto para exibir o HTML ---
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setHtml(relatorio_html)
        layout.addWidget(self.text_edit)

        # --- Botões ---
        self.button_box = QDialogButtonBox()
        
        # Botão de Imprimir
        self.print_button = QPushButton("Imprimir")
        self.print_button.clicked.connect(self.imprimir_relatorio)
        self.button_box.addButton(self.print_button, QDialogButtonBox.ButtonRole.ActionRole)

        # Botão de Fechar
        self.close_button = self.button_box.addButton(QDialogButtonBox.StandardButton.Close)
        self.close_button.clicked.connect(self.reject)

        layout.addWidget(self.button_box)

    def imprimir_relatorio(self):
        """Abre o diálogo de impressão do sistema."""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.text_edit.print(printer)
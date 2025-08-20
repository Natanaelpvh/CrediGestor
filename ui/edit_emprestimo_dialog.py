# ui/edit_emprestimo_dialog.py

from decimal import Decimal
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout,
                             QDialogButtonBox, QMessageBox, QDoubleSpinBox,
                             QSpinBox, QRadioButton, QHBoxLayout, QLabel, QDateEdit)
from models.emprestimo import Emprestimo, TipoJuros
from services.emprestimo_service import EmprestimoService

class EditEmprestimoDialog(QDialog):
    """
    Janela de diálogo para editar os detalhes de um empréstimo existente.

    Esta classe fornece um formulário para modificar o valor, número de parcelas,
    data de início e tipo de juros de um empréstimo. Implementa uma regra de
    negócio crucial: o valor do empréstimo não pode ser alterado se já houver
    parcelas pagas, desativando o campo correspondente na interface para
    garantir a integridade dos dados.
    """
    def __init__(self, emprestimo: Emprestimo, emprestimo_service: EmprestimoService, parent=None):
        """
        Inicializa o diálogo de edição de empréstimo.

        Args:
            emprestimo (Emprestimo): O objeto do empréstimo a ser editado.
            emprestimo_service (EmprestimoService): A instância do serviço para
                interagir com a lógica de negócio de empréstimos.
            parent (QWidget, optional): O widget pai. Defaults to None.
        """
        super().__init__(parent)
        self.emprestimo = emprestimo
        self.emprestimo_service = emprestimo_service

        self.setWindowTitle("Editar Empréstimo")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Widgets para edição
        self.valor_input = QDoubleSpinBox()
        self.valor_input.setPrefix("R$ ")
        self.valor_input.setRange(0.01, 1_000_000.00)
        self.valor_input.setDecimals(2)
        self.valor_input.setValue(float(self.emprestimo.valor))
        form_layout.addRow("Valor:", self.valor_input)

        self.num_parcelas_input = QSpinBox()
        self.num_parcelas_input.setRange(1, 120)
        self.num_parcelas_input.setValue(self.emprestimo.numero_parcelas)
        form_layout.addRow("Número de Parcelas:", self.num_parcelas_input)

        self.data_inicio_input = QDateEdit(self)
        self.data_inicio_input.setDate(QDate(self.emprestimo.data_inicio))
        self.data_inicio_input.setCalendarPopup(True)
        self.data_inicio_input.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow(QLabel("Data de Início:"), self.data_inicio_input)

        self.juros_simples_radio = QRadioButton("Juros Simples")
        self.juros_composto_radio = QRadioButton("Juros Composto")
        if self.emprestimo.tipo_juros == TipoJuros.SIMPLES:
            self.juros_simples_radio.setChecked(True)
        else:
            self.juros_composto_radio.setChecked(True)
        juros_layout = QHBoxLayout()
        juros_layout.addWidget(self.juros_simples_radio)
        juros_layout.addWidget(self.juros_composto_radio)
        form_layout.addRow("Tipo de Juros:", juros_layout)

        layout.addLayout(form_layout)

        # Botões
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Verifica se existem parcelas pagas para este empréstimo
        self.has_paid_installments = any(
            p.pago for p in self.emprestimo_service.get_parcelas_by_emprestimo_id(self.emprestimo.id)
        )

        # Se houver parcelas pagas, desativa o campo de valor para evitar alterações
        if self.has_paid_installments:
            self.valor_input.setEnabled(False)
            self.valor_input.setToolTip("O valor não pode ser alterado pois já existem parcelas pagas.")

    def get_data(self):
        """
        Coleta os dados do formulário e os retorna em um dicionário estruturado.

        Returns:
            dict: Um dicionário contendo os valores atuais dos campos do formulário.
        """
        tipo_juros = TipoJuros.SIMPLES if self.juros_simples_radio.isChecked() else TipoJuros.COMPOSTO
        return {
            "valor": Decimal(str(self.valor_input.value())),
            "numero_parcelas": self.num_parcelas_input.value(),
            "data_inicio": self.data_inicio_input.date().toPyDate(),
            "tipo_juros": tipo_juros,
        }

    def accept(self):
        """
        Valida os dados e, após confirmação do usuário, salva as alterações.

        Este método primeiro verifica a regra de negócio sobre a alteração do valor.
        Em seguida, solicita uma confirmação do usuário, pois a edição de um
        empréstimo recalcula todas as suas parcelas. Se confirmado, chama o
        serviço para persistir as alterações.
        """
        data = self.get_data()

        # Validação extra para garantir que o valor não seja alterado se houver parcelas pagas
        if self.has_paid_installments and data['valor'] != self.emprestimo.valor:
            QMessageBox.critical(self, "Operação Inválida",
                                 "Não é possível alterar o valor de um empréstimo que já possui parcelas pagas.")
            return

        reply = QMessageBox.question(self, "Confirmar Alteração",
                                     "Alterar este empréstimo irá remover e recalcular todas as suas parcelas. Deseja continuar?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.emprestimo_service.update_emprestimo_com_parcelas(self.emprestimo.id, data)
                QMessageBox.information(self, "Sucesso", "Empréstimo atualizado com sucesso!")
                super().accept()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível atualizar o empréstimo: {e}")
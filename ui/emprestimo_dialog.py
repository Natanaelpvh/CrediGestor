# ui/emprestimo_dialog.py

from decimal import Decimal
from typing import Dict, Any, Optional

from PyQt6.QtCore import QDate, Qt, QStringListModel
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QDoubleSpinBox,
                             QFormLayout, QLabel, QMessageBox, QSpinBox,
                             QVBoxLayout, QPushButton, QHBoxLayout,
                             QRadioButton, QLineEdit, QCompleter, QDateEdit, QWidget)

from services.cliente_service import ClienteService
from services.emprestimo_service import EmprestimoService
from ui.cliente_dialog import ClienteDialog
from ui import styles
from models.emprestimo import TipoJuros


class EmprestimoDialog(QDialog):
    """
    Janela de diálogo para cadastrar ou editar um empréstimo.
 
    Esta classe fornece um formulário completo para a criação de um novo empréstimo.
    A seleção de cliente é feita através de um campo de busca dinâmica, melhorando
    a usabilidade. Oferece também uma prévia em tempo real do valor da parcela e a opção
    de cadastrar um novo cliente diretamente do diálogo.
    """
    def __init__(self, cliente_service: ClienteService, emprestimo_service: EmprestimoService, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa o diálogo de empréstimo.
 
        Args:
            cliente_service (ClienteService): Instância do serviço de cliente para interações com o banco de dados.
            emprestimo_service (EmprestimoService): Instância do serviço de empréstimo para criar o empréstimo.
            parent (Optional[QWidget]): O widget pai desta janela.
        """
        super().__init__(parent)
        self.cliente_service = cliente_service
        self.emprestimo_service = emprestimo_service
        self.taxas = None
        self.selected_cliente_id: Optional[int] = None
        self.completer_cliente_map: Dict[str, int] = {}

        try:
            self.taxas = self.emprestimo_service.get_taxas_config()
        except Exception as e:
            QMessageBox.warning(self, "Erro de Configuração",
                                f"Não foi possível carregar as taxas de juros. A prévia pode não funcionar.\nErro: {e}")

        self.setWindowTitle("Novo Empréstimo")
        self.setModal(True)
        self.setMinimumWidth(450)

        # --- Configuração da UI ---
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Cliente (Campo de Busca com Autocompletar)
        self.cliente_search_input = QLineEdit(self)
        self.cliente_search_input.setPlaceholderText("Digite 2+ caracteres para buscar...")
        self.cliente_search_input.textChanged.connect(self._update_cliente_completer)
        
        # Configuração do QCompleter para a busca
        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        
        self.cliente_completer_model = QStringListModel(self)
        self.completer.setModel(self.cliente_completer_model)
        self.cliente_search_input.setCompleter(self.completer)
        self.completer.activated.connect(self._set_selected_cliente)

        btn_novo_cliente = QPushButton("Novo Cliente")
        btn_novo_cliente.setStyleSheet(styles.get_button_style('novo'))
        btn_novo_cliente.clicked.connect(self.criar_novo_cliente)
        
        cliente_row_layout = QHBoxLayout()
        cliente_row_layout.addWidget(self.cliente_search_input)
        cliente_row_layout.addWidget(btn_novo_cliente)
        
        form_layout.addRow("Buscar Cliente (Nome/CPF):", cliente_row_layout)

        # Valor (DoubleSpinBox)
        self.valor_input = QDoubleSpinBox(self)
        self.valor_input.setPrefix("R$ ")
        self.valor_input.setDecimals(2)
        self.valor_input.setMinimum(0.01)
        self.valor_input.setMaximum(1_000_000.00)
        self.valor_input.setValue(1000.00)
        form_layout.addRow("Valor do Empréstimo:", self.valor_input)

        # Número de Parcelas (SpinBox)
        self.num_parcelas_input = QSpinBox(self)
        self.num_parcelas_input.setMinimum(1)
        self.num_parcelas_input.setMaximum(120)
        self.num_parcelas_input.setValue(12)
        form_layout.addRow("Número de Parcelas:", self.num_parcelas_input)

        # Data de Início (DateEdit)
        self.data_inicio_input = QDateEdit(self)
        self.data_inicio_input.setDate(QDate.currentDate())
        self.data_inicio_input.setCalendarPopup(True)
        self.data_inicio_input.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Data de Início:", self.data_inicio_input)

        # Tipo de Juros (RadioButtons)
        self.juros_simples_radio = QRadioButton("Juros Simples")
        self.juros_simples_radio.setChecked(True)
        self.juros_composto_radio = QRadioButton("Juros Composto")
        juros_layout = QHBoxLayout()
        juros_layout.addWidget(self.juros_simples_radio)
        juros_layout.addWidget(self.juros_composto_radio)
        form_layout.addRow("Tipo de Juros:", juros_layout)

        # Prévia do Valor da Parcela
        self.parcela_preview_label = QLabel("R$ 0,00")
        self.parcela_preview_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: #2980b9;")
        form_layout.addRow("Valor Estimado da Parcela:", self.parcela_preview_label)

        layout.addLayout(form_layout)

        # Botões
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Conexões de Sinais para a prévia
        self.valor_input.valueChanged.connect(self._update_parcela_preview)
        self.num_parcelas_input.valueChanged.connect(self._update_parcela_preview)
        self.juros_simples_radio.toggled.connect(self._update_parcela_preview)

        self._update_parcela_preview()

    def set_initial_client(self, client_id: Optional[int]) -> None:
        """
        Pré-seleciona um cliente no diálogo ao ser aberto.
 
        Busca o cliente pelo ID e, se encontrado, preenche o campo de busca
        e armazena o estado do cliente selecionado.
 
        Args:
            client_id (Optional[int]): O ID do cliente a ser pré-selecionado.
        """
        if not client_id:
            return
        try:
            cliente = self.cliente_service.get_cliente_by_id(client_id)
            if cliente:
                display_text = f"{cliente.nome} ({cliente.cpf})"
                self.selected_cliente_id = cliente.id
                self.completer_cliente_map[display_text] = cliente.id
                self.cliente_search_input.setText(display_text)
        except Exception as e:
            print(f"Erro ao pré-selecionar cliente: {e}")

    def _update_cliente_completer(self, text: str) -> None:
        """
        Slot para o sinal textChanged do campo de busca de cliente.
 
        Atualiza a lista de autocompletar com base no texto digitado e reseta a 
        seleção se o texto for alterado manualmente pelo usuário.
 
        Args:
            text (str): O texto atual no QLineEdit de busca.
        """
        # Se o texto atual não for uma chave válida no mapa, reseta a seleção.
        # Isso acontece se o usuário selecionar um cliente e depois editar o texto manualmente.
        if text not in self.completer_cliente_map:
            self.selected_cliente_id = None

        if len(text) < 2:
            self.cliente_completer_model.setStringList([])
            self.completer_cliente_map.clear()
            return

        # Evita busca se o texto já é uma chave válida (foi selecionado)
        if text in self.completer_cliente_map:
            return

        try:
            clientes = self.cliente_service.search_clientes(text, limit=10)
            new_map = {f"{c.nome} ({c.cpf})": c.id for c in clientes}
            self.completer_cliente_map = new_map
            self.cliente_completer_model.setStringList(list(new_map.keys()))
        except Exception as e:
            print(f"Erro ao buscar clientes: {e}")
            self.cliente_completer_model.setStringList([])
            self.completer_cliente_map.clear()
    
    def _set_selected_cliente(self, completion_text: str) -> None:
        """
        Slot para o sinal activated do QCompleter.
 
        Armazena o ID e o texto do cliente selecionado na lista de autocompletar 
        e atualiza o campo de busca.
 
        Args:
            completion_text (str): O texto do item selecionado na lista.
        """
        self.selected_cliente_id = self.completer_cliente_map.get(completion_text)

    def criar_novo_cliente(self) -> None:
        """
        Abre o diálogo para criar um novo cliente e o seleciona automaticamente.
        """
        dialog = ClienteDialog(parent=self)
        if not dialog.exec():
            return

        data = dialog.get_data()
        try:
            novo_cliente = self.cliente_service.create_cliente(**data)
            QMessageBox.information(self, "Sucesso", "Novo cliente criado com sucesso!")

            display_text = f"{novo_cliente.nome} ({novo_cliente.cpf})"
            self.selected_cliente_id = novo_cliente.id
            self.completer_cliente_map[display_text] = novo_cliente.id
            
            self.cliente_search_input.blockSignals(True)
            self.cliente_search_input.setText(display_text)
            self.cliente_search_input.blockSignals(False)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível criar o cliente: {e}")

    def _calcular_valor_parcela(self) -> Decimal:
        """
        Calcula o valor da parcela com base nos dados do formulário para a prévia.
 
        Returns:
            Decimal: O valor da parcela calculado, arredondado para 2 casas decimais.
        """
        if not self.taxas: return Decimal('0.00')
        valor_principal = Decimal(str(self.valor_input.value()))
        num_parcelas = self.num_parcelas_input.value()
        if num_parcelas <= 0: return Decimal('0.00')

        if self.juros_simples_radio.isChecked():
            taxa_juros = self.taxas.taxa_juros_simples / Decimal(100)
            valor_total_juros = valor_principal * taxa_juros * Decimal(num_parcelas)
            valor_parcela = (valor_principal + valor_total_juros) / Decimal(num_parcelas)
        else:
            taxa_juros_mensal = self.taxas.taxa_juros_composto / Decimal(100)
            if taxa_juros_mensal == 0: return valor_principal / Decimal(num_parcelas)
            fator = (1 + taxa_juros_mensal) ** num_parcelas
            valor_parcela = valor_principal * (taxa_juros_mensal * fator) / (fator - 1)
        return round(valor_parcela, 2)

    def _update_parcela_preview(self) -> None:
        """
        Atualiza o rótulo da interface com o valor estimado da parcela em tempo real.
        """
        try:
            valor_parcela = self._calcular_valor_parcela()
            self.parcela_preview_label.setText(f"R$ {valor_parcela:,.2f}")
        except Exception:
            self.parcela_preview_label.setText("Cálculo inválido")

    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        Coleta e valida os dados do formulário.
 
        Returns:
            Optional[Dict[str, Any]]: Um dicionário com os dados do empréstimo se a validação for bem-sucedida,
            se a validação for bem-sucedida, ou None caso contrário.
        """
        # A validação agora checa apenas se um cliente foi selecionado,
        # tornando o processo mais robusto e corrigindo o bug do atalho do dashboard.
        if not self.selected_cliente_id:
            QMessageBox.warning(self, "Seleção Inválida", "Por favor, busque e selecione um cliente da lista.")
            return None

        tipo_juros = TipoJuros.SIMPLES if self.juros_simples_radio.isChecked() else TipoJuros.COMPOSTO
        return {
            "cliente_id": self.selected_cliente_id,
            "valor": Decimal(str(self.valor_input.value())),
            "numero_parcelas": self.num_parcelas_input.value(),
            "data_inicio": self.data_inicio_input.date().toPyDate(),
            "tipo_juros": tipo_juros,
        }

    def accept(self) -> None:
        """
        Slot para o botão 'Salvar'. Valida os dados e cria o empréstimo.
        Chama `get_data` para obter os dados do formulário e, se forem válidos, invoca o `EmprestimoService`.
        """
        data = self.get_data()
        if not data:
            return

        try:
            self.emprestimo_service.create_emprestimo_com_parcelas(data)
            QMessageBox.information(self, "Sucesso", "Empréstimo cadastrado com sucesso!")
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar o empréstimo: {e}")
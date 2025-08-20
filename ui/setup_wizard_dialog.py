# ui/setup_wizard_dialog.py
from typing import Dict, Optional

from PyQt6.QtWidgets import (QApplication, QComboBox, QDialog, QDialogButtonBox,
                             QFormLayout, QGroupBox, QLabel, QLineEdit,
                             QMessageBox, QRadioButton, QSpinBox,
                             QStackedWidget, QVBoxLayout, QWidget)

class SetupWizardDialog(QDialog):
    """
    Um diálogo de assistente de configuração para o banco de dados.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assistente de Configuração")
        self.setModal(True)
        self.setMinimumWidth(500)

        self.config_data: Optional[Dict[str, str]] = None

        # --- Layout Principal e Stacked Widget ---
        main_layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # --- Página 1: Escolha Inicial ---
        page1 = QWidget()
        page1_layout = QVBoxLayout(page1)
        
        welcome_label = QLabel("<b>Bem-vindo ao Assistente de Configuração</b>")
        welcome_label.setStyleSheet("font-size: 14pt;")
        
        info_label = QLabel("É necessário configurar a conexão com o banco de dados para o primeiro uso.")
        info_label.setWordWrap(True)

        group_box = QGroupBox("Escolha uma opção:")
        group_layout = QVBoxLayout(group_box)
        
        self.sqlite_radio = QRadioButton("Usar banco de dados local (SQLite)")
        self.sqlite_radio.setToolTip("Recomendado para testes e uso rápido. Nenhum outro software é necessário.")
        self.sqlite_radio.setChecked(True)
        
        self.external_db_radio = QRadioButton("Configurar um banco de dados externo (Ex: PostgreSQL, MySQL)")
        self.external_db_radio.setToolTip("Para ambientes de produção ou quando um banco de dados central é necessário.")

        group_layout.addWidget(self.sqlite_radio)
        group_layout.addWidget(self.external_db_radio)
        
        page1_layout.addWidget(welcome_label)
        page1_layout.addWidget(info_label)
        page1_layout.addWidget(group_box)
        page1_layout.addStretch()

        # --- Página 2: Configuração Externa ---
        page2 = QWidget()
        page2_layout = QFormLayout(page2)
        page2_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        info_external_label = QLabel("Informe as credenciais do seu banco de dados externo.")
        
        self.db_type_input = QComboBox()
        self.db_type_input.addItems(["postgresql", "mysql"])
        self.db_type_input.currentTextChanged.connect(self._update_default_port)
        
        self.db_user_input = QLineEdit()
        self.db_host_input = QLineEdit("localhost")
        self.db_port_input = QSpinBox()
        self.db_port_input.setRange(1, 65535)
        self.db_port_input.setValue(5432)
        
        self.db_name_input = QLineEdit()
        self.db_password_input = QLineEdit()
        self.db_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        page2_layout.addRow(info_external_label)
        page2_layout.addRow("Tipo de Banco de Dados:", self.db_type_input)
        page2_layout.addRow("Usuário:", self.db_user_input)
        page2_layout.addRow("Host/Endereço IP:", self.db_host_input)
        page2_layout.addRow("Porta:", self.db_port_input)
        page2_layout.addRow("Nome do Banco de Dados:", self.db_name_input)
        page2_layout.addRow("Senha:", self.db_password_input)

        # Adiciona as páginas ao Stacked Widget
        self.stacked_widget.addWidget(page1)
        self.stacked_widget.addWidget(page2)

        # --- Botões ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText("Salvar e Sair")
        main_layout.addWidget(self.button_box)

        # --- Conexões de Sinais ---
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.external_db_radio.toggled.connect(self._toggle_pages)
        self._update_default_port(self.db_type_input.currentText())

    def _toggle_pages(self, checked: bool):
        """Alterna entre a página de escolha e a de configuração externa."""
        self.stacked_widget.setCurrentIndex(1 if checked else 0)

    def _update_default_port(self, db_type: str):
        """Atualiza a porta padrão com base no tipo de banco de dados selecionado."""
        port_map = {"postgresql": 5432, "mysql": 3306}
        self.db_port_input.setValue(port_map.get(db_type, 5432))

    def accept(self):
        """Valida os dados e prepara o dicionário de configuração antes de fechar."""
        if self.sqlite_radio.isChecked():
            self.config_data = {"DATABASE_URL": "sqlite:///./app.db"}
            super().accept()
            return

        if self.external_db_radio.isChecked():
            db_type = self.db_type_input.currentText()
            db_user = self.db_user_input.text().strip()
            db_host = self.db_host_input.text().strip()
            db_port = self.db_port_input.text()
            db_name = self.db_name_input.text().strip()
            db_password = self.db_password_input.text()

            if not all([db_user, db_host, db_name, db_password]):
                QMessageBox.warning(self, "Campos Obrigatórios", "Todos os campos (usuário, host, nome do banco e senha) são obrigatórios.")
                return

            driver_map = {"postgresql": "psycopg2", "mysql": "pymysql"}
            driver = driver_map.get(db_type)
            driver_str = f"+{driver}" if driver else ""
            db_url = f"{db_type}{driver_str}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            self.config_data = {"DATABASE_URL": db_url}
            super().accept()

    def get_config_data(self) -> Optional[Dict[str, str]]:
        """Retorna os dados de configuração coletados."""
        return self.config_data
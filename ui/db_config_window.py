# ui/db_config_window.py
"""
Módulo que define a DBConfigWindow, uma janela para configurar a conexão
com o banco de dados e salvar as informações no arquivo .env.
"""

import sys
from typing import Dict
from sqlalchemy import create_engine, exc

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QComboBox, QDialog,
                             QFormLayout, QGroupBox, QLineEdit,
                             QMessageBox, QPushButton, QRadioButton,
                             QSpinBox, QHBoxLayout,
                             QVBoxLayout)

class DBConfigWindow(QDialog):
    """
    Uma janela para configurar a conexão com o banco de dados e salvar em .env.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuração do Banco de Dados")
        self.setModal(True)
        self.setMinimumWidth(450)

        # --- Layout Principal ---
        main_layout = QVBoxLayout(self)

        # --- Grupo de Opções ---
        options_group = QGroupBox("Tipo de Conexão")
        options_layout = QVBoxLayout(options_group)
        
        self.local_radio = QRadioButton("Local (SQLite)")
        self.local_radio.setToolTip("Recomendado para testes e uso rápido.")
        self.local_radio.setChecked(True)
        
        self.remote_radio = QRadioButton("Remoto (PostgreSQL, MySQL, etc.)")
        self.remote_radio.setToolTip("Para ambientes de produção.")
        
        options_layout.addWidget(self.local_radio)
        options_layout.addWidget(self.remote_radio)
        main_layout.addWidget(options_group)

        # --- Formulário de Configuração Remota (inicialmente oculto) ---
        self.remote_config_group = QGroupBox("Credenciais do Banco de Dados Remoto")
        remote_form_layout = QFormLayout(self.remote_config_group)
        
        self.db_type_input = QComboBox()
        self.db_type_input.addItems(["postgresql", "mysql"])
        
        self.db_host_input = QLineEdit("localhost")
        self.db_port_input = QSpinBox()
        self.db_port_input.setRange(1, 65535)
        
        self.db_user_input = QLineEdit()
        self.db_name_input = QLineEdit()
        self.db_password_input = QLineEdit()
        self.db_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        remote_form_layout.addRow("Tipo de Banco:", self.db_type_input)
        remote_form_layout.addRow("Host/Endereço IP:", self.db_host_input)
        remote_form_layout.addRow("Porta:", self.db_port_input)
        remote_form_layout.addRow("Usuário:", self.db_user_input)
        remote_form_layout.addRow("Nome do Banco:", self.db_name_input)
        remote_form_layout.addRow("Senha:", self.db_password_input)
        
        main_layout.addWidget(self.remote_config_group)
        self.remote_config_group.setVisible(False)

        # --- Botões ---
        button_layout = QHBoxLayout()
        self.test_button = QPushButton("Testar Conexão")
        self.save_button = QPushButton("Salvar Configuração")
        button_layout.addStretch()
        button_layout.addWidget(self.test_button)
        button_layout.addWidget(self.save_button)
        main_layout.addLayout(button_layout)

        # --- Conexões de Sinais ---
        self.remote_radio.toggled.connect(self.remote_config_group.setVisible)
        self.db_type_input.currentTextChanged.connect(self._update_default_port)
        self.test_button.clicked.connect(self._test_connection)
        self.save_button.clicked.connect(self._save_config)

        # Inicializa a porta padrão
        self._update_default_port(self.db_type_input.currentText())

    def _update_default_port(self, db_type: str):
        """Atualiza a porta padrão com base no tipo de banco de dados."""
        port_map = {"postgresql": 5432, "mysql": 3306}
        self.db_port_input.setValue(port_map.get(db_type, 5432))

    def _write_to_env(self, config_data: Dict[str, str]):
        """Escreve o dicionário de configuração no arquivo .env."""
        try:
            with open('.env', 'w', encoding='utf-8') as f:
                for key, value in config_data.items():
                    f.write(f'{key}="{value}"\n')
            return True
        except IOError as e:
            QMessageBox.critical(self, "Erro de Gravação", f"Não foi possível escrever no arquivo '.env'.\nVerifique as permissões.\n\nErro: {e}")
            return False

    def _test_connection(self):
        """Tenta conectar ao banco de dados com as credenciais fornecidas."""
        if not self.remote_radio.isChecked():
            QMessageBox.information(self, "Ação Inválida", "O teste de conexão é aplicável apenas para bancos de dados remotos.")
            return

        # Coleta os dados do formulário
        db_type, host, port, user, password, db_name = (
            self.db_type_input.currentText(), self.db_host_input.text().strip(),
            self.db_port_input.text(), self.db_user_input.text().strip(),
            self.db_password_input.text(), self.db_name_input.text().strip()
        )

        if not all([host, port, user, db_name]):
            QMessageBox.warning(self, "Campos Incompletos", "Para testar a conexão, preencha todos os campos de credenciais (exceto senha, se não houver).")
            return

        # Constrói a URL de conexão
        driver = {"postgresql": "+psycopg2", "mysql": "+pymysql"}.get(db_type, "")
        db_url = f"{db_type}{driver}://{user}:{password}@{host}:{port}/{db_name}"

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            # Tenta criar uma engine e conectar, com um timeout de 5 segundos
            engine = create_engine(db_url, connect_args={'connect_timeout': 5})
            with engine.connect():
                QMessageBox.information(self, "Sucesso", "Conexão com o banco de dados bem-sucedida!")
        except exc.SQLAlchemyError as e:
            QMessageBox.critical(self, "Falha na Conexão", f"Não foi possível conectar ao banco de dados.\n\nVerifique as credenciais e a rede.\n\nErro: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _save_config(self):
        """Coleta os dados, valida, salva no .env e fecha a janela."""
        if self.local_radio.isChecked():
            config_data = {"DATABASE_URL": "sqlite:///./app.db"}
        else:
            db_type, host, port, user, password, db_name = (self.db_type_input.currentText(), self.db_host_input.text().strip(), self.db_port_input.text(), self.db_user_input.text().strip(), self.db_password_input.text(), self.db_name_input.text().strip())
            if not all([host, port, user, db_name]):
                QMessageBox.warning(self, "Campos Incompletos", "Todos os campos (exceto senha) são obrigatórios para a configuração remota.")
                return
            driver = {"postgresql": "+psycopg2", "mysql": "+pymysql"}.get(db_type, "")
            db_url = f"{db_type}{driver}://{user}:{password}@{host}:{port}/{db_name}"
            config_data = {"DATABASE_URL": db_url}

        if self._write_to_env(config_data):
            QMessageBox.information(self, "Sucesso", "Configuração salva com sucesso no arquivo .env!")
            self.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DBConfigWindow()
    window.show()
    sys.exit(app.exec())
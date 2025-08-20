# main.py
"""
Ponto de entrada da aplicação Gestor System.

Este script define a classe `App` que encapsula toda a lógica de inicialização,
execução e encerramento da aplicação, seguindo um padrão orientado a objetos.
"""

import sys
import os

# Adiciona o diretório raiz do projeto ao Python path
# Isso permite importações absolutas de qualquer script no projeto,
# resolvendo problemas de 'ModuleNotFoundError' e 'ImportError'.
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# As verificações de dependências e configuração (.env) agora são
# tratadas pelo script 'start.py', que é o ponto de entrada oficial.

import logging
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMessageBox

# Importações que dependem da configuração (que já foi garantida por start.py)
from config import DEFAULT_ADMIN_NOME, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_SENHA
from db.database import DatabaseManager
from models.usuario import Usuario, UserRole
from services.usuario_service import UsuarioService
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow

class App:
    """
    Encapsula a lógica de inicialização e execução da aplicação Gestor System.

    Esta classe é responsável por:
    - Configurar o ambiente da aplicação (logging, banco de dados).
    - Gerenciar o ciclo de vida da sessão do banco de dados.
    - Orquestrar o fluxo de autenticação.
    - Iniciar a janela principal.
    - Lidar com o encerramento limpo da aplicação.
    """
    def __init__(self):
        """Inicializa a aplicação, configurando logging e a instância do QApplication."""
        self._setup_logging()
        self.db_manager = DatabaseManager()
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setStyle('Fusion')
        self.db_session = None
        self.usuario_service = None

    def _setup_logging(self):
        """Configura o sistema de logging básico."""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def _init_database(self):
        """
        Inicializa a conexão com o banco de dados e os serviços.
        Encerra a aplicação se a conexão falhar.
        """
        try:
            logging.info("Iniciando a conexão com o banco de dados...")
            self.db_manager.create_tables()
            self.db_session = self.db_manager.get_session()
            self.usuario_service = UsuarioService(self.db_session)
        except Exception as e:
            logging.critical(f"Falha ao inicializar o banco de dados. A aplicação será encerrada. Erro: {e}")
            QMessageBox.critical(None, "Erro Crítico", f"Falha ao inicializar o banco de dados: {e}")
            sys.exit(1)

    def _create_default_admin_if_not_exists(self):
        """
        Verifica se existem usuários e, se não, cria um administrador padrão.
        """
        if not self.usuario_service.get_all_usuarios():
            logging.warning("Nenhum usuário encontrado. Criando usuário 'admin' padrão.")
            try:
                self.usuario_service.create_usuario(
                    nome=DEFAULT_ADMIN_NOME,
                    email=DEFAULT_ADMIN_EMAIL,
                    senha=DEFAULT_ADMIN_SENHA,
                    role=UserRole.ADMIN
                )
                logging.info(f"Usuário '{DEFAULT_ADMIN_NOME}' criado com sucesso. Senha padrão: '{DEFAULT_ADMIN_SENHA}'")
            except Exception as e:
                raise RuntimeError(f"Não foi possível criar o usuário admin padrão. Verifique as permissões do banco de dados. Erro: {e}") from e

    def _handle_authentication(self) -> Optional[Usuario]:
        """
        Gerencia a autenticação do usuário exibindo o LoginDialog.

        Returns:
            Optional[Usuario]: O objeto do usuário autenticado ou None se o login for cancelado.
        """
        login_dialog = LoginDialog(self.usuario_service)
        if login_dialog.exec():
            return login_dialog.get_authenticated_user()
        logging.info("Login cancelado pelo usuário.")
        return None

    def run(self) -> int:
        """
        Executa o fluxo principal da aplicação.

        Orquestra a inicialização do banco de dados, criação do admin, autenticação
        e o lançamento da janela principal. Garante o fechamento da sessão do BD.

        Returns:
            int: O código de saída da aplicação.
        """
        try:
            self._init_database()
            self._create_default_admin_if_not_exists()

            usuario_logado = self._handle_authentication()

            if not usuario_logado:
                logging.info("Autenticação falhou ou foi cancelada. Encerrando a aplicação.")
                return 0

            logging.info(f"Usuário '{usuario_logado.nome}' logado com sucesso.")

            main_window = MainWindow(usuario_logado, self.db_session)
            main_window.show()

            logging.info("Aplicação iniciada com sucesso.")
            return self.qt_app.exec()

        except Exception as e:
            logging.critical(f"Ocorreu um erro fatal na aplicação: {e}", exc_info=True)
            QMessageBox.critical(None, "Erro Crítico", f"A aplicação encontrou um erro fatal e será encerrada.\n\n{e}")
            return 1
        finally:
            if self.db_session:
                logging.info("Fechando a sessão do banco de dados.")
                self.db_session.close()

def main():
    """
    Ponto de entrada principal: cria e executa a instância da aplicação.
    """
    app_instance = App()
    exit_code = app_instance.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

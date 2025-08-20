# start.py
"""
Ponto de entrada principal e orquestrador da aplicação.

Este script define a classe `ApplicationLauncher`, que gerencia a sequência
de inicialização de forma orientada a objetos, garantindo que o ambiente
esteja pronto antes de executar a aplicação principal.
"""
import sys
import os
import logging

class ApplicationLauncher:
    """
    Orquestra o processo de inicialização da aplicação, garantindo que o
    ambiente esteja corretamente configurado antes da execução.
    """
    def __init__(self):
        """Inicializa o launcher e configura o logging."""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Iniciando verificação de ambiente...")

    def _check_dependencies(self) -> bool:
        """
        Etapa 1: Verifica e instala as dependências do ambiente.

        Utiliza o `SetupManager` para comparar os pacotes listados em
        `requirements.txt` com os pacotes instalados no ambiente. Se houver
        dependências faltando, tenta instalá-las.

        Returns:
            bool: True se todas as dependências estiverem satisfeitas (ou foram
                  instaladas com sucesso), False caso contrário.
        """
        from setup import SetupManager
        setup = SetupManager()
        return setup.check_and_install()

    def _check_configuration(self) -> bool:
        """
        Etapa 2: Garante que o arquivo .env exista.

        Se o arquivo `.env` não for encontrado na raiz do projeto, esta função
        inicia um assistente de configuração gráfico (`DBConfigWindow`) para
        permitir que o usuário configure a conexão com o banco de dados.

        Returns:
            bool: True se o arquivo .env já existia ou foi criado com sucesso.
                  False se o usuário cancelou o assistente de configuração.
        """
        if not os.path.exists('.env'):
            logging.warning("Arquivo de configuração .env não encontrado. Iniciando assistente de configuração.")
            from PyQt6.QtWidgets import QApplication, QDialog
            from ui.db_config_window import DBConfigWindow

            app = QApplication.instance() or QApplication(sys.argv)
            dialog = DBConfigWindow()
            if dialog.exec() == QDialog.DialogCode.Accepted:
                logging.info("Configuração salva com sucesso. Continuando para a aplicação...")
            else:
                return False  # Configuração cancelada pelo usuário
        return True

    def _launch_app(self):
        """
        Etapa 3: Importa e inicia a aplicação principal.

        Esta função realiza a importação do módulo `main` localmente para
        garantir que ela só ocorra após a verificação bem-sucedida de
        dependências e configuração. Isso evita `ImportError` ou erros de
        configuração na inicialização.
        """
        logging.info("Dependências e configuração verificadas. Iniciando a aplicação principal...")
        try:
            from main import main as launch_main_app
            launch_main_app()
        except ImportError as e:
            logging.critical(f"Erro ao importar a aplicação principal: {e}")
            logging.critical("Isso pode ocorrer se uma dependência foi instalada mas a aplicação precisa ser reiniciada.")
            sys.exit(1)

    def run(self):
        """
        Executa a sequência de inicialização completa.

        Orquestra a chamada das etapas de verificação de dependências e
        configuração. Se qualquer uma das etapas falhar, a aplicação é
        encerrada com uma mensagem de erro. Se tudo estiver correto,
        inicia a aplicação principal.
        """
        if not self._check_dependencies():
            logging.error("A aplicação não pode iniciar devido a um erro na configuração das dependências.")
            sys.exit(1)

        if not self._check_configuration():
            logging.warning("Configuração do banco de dados cancelada. A aplicação não pode continuar.")
            sys.exit(1)

        self._launch_app()

def main():
    """
    Ponto de entrada: cria e executa a instância do ApplicationLauncher.
    """
    launcher = ApplicationLauncher()
    launcher.run()

if __name__ == "__main__":
    main()
# config_manager.py
"""
Módulo para gerenciar a configuração inicial da aplicação.

Este módulo fornece um assistente de configuração interativo para ajudar
o usuário a criar o arquivo .env necessário na primeira execução.
"""
import os
import sys
from typing import Dict, Optional

from PyQt6.QtWidgets import QApplication
from ui.setup_wizard_dialog import SetupWizardDialog

class ConfigManager:
    """
    Gerencia a criação e verificação do arquivo de configuração .env.
    """
    def __init__(self, env_file: str = '.env'):
        """
        Inicializa o gerenciador de configuração.

        Args:
            env_file (str): O caminho para o arquivo .env.
        """
        self.env_file = env_file

    def ensure_configured(self):
        """
        Garante que o arquivo .env exista. Se não existir, inicia o assistente
        de configuração.
        """
        if not os.path.exists(self.env_file):
            print("Arquivo de configuração (.env) não encontrado.")
            config_data = self.run_setup_wizard()
            if config_data:
                # Após coletar os dados, salva no arquivo .env
                self._save_env_file(config_data)
                print(f"\n✅ Configuração concluída com sucesso! O arquivo '{self.env_file}' foi criado.")
                print("Por favor, reinicie a aplicação para que as alterações tenham efeito.")
                sys.exit(0) # Encerra para que a app possa ser reiniciada e carregar o .env
            else:
                print("\nConfiguração cancelada pelo usuário. A aplicação não pode continuar.")
                sys.exit(1)

    def _save_env_file(self, config_data: Dict[str, str]):
        """
        Salva os dados de configuração em um arquivo .env no formato CHAVE="VALOR".

        Args:
            config_data (Dict[str, str]): Um dicionário contendo as variáveis de ambiente.
        """
        try:
            # Abre o arquivo .env na raiz do projeto para escrita.
            # Se o arquivo não existir, ele será criado.
            with open(self.env_file, 'w', encoding='utf-8') as f:
                for key, value in config_data.items():
                    # Escreve cada configuração no formato CHAVE="VALOR" para lidar
                    # com possíveis caracteres especiais no valor.
                    f.write(f'{key}="{value}"\n')
        except IOError as e:
            print(f"ERRO CRÍTICO: Não foi possível escrever no arquivo '{self.env_file}'. Verifique as permissões. Erro: {e}", file=sys.stderr)
            sys.exit(1)

    def run_setup_wizard(self) -> Optional[Dict[str, str]]:
        """
        Exibe um assistente de configuração gráfico para o banco de dados.

        Returns:
            Optional[Dict[str, str]]: Um dicionário com a configuração da DATABASE_URL
                                      ou None se o usuário cancelar.
        """
        # Garante que uma instância do QApplication exista para exibir a janela.
        # Isso é crucial porque este código pode rodar antes da inicialização principal.
        app = QApplication.instance()
        if app is None:
            # Se não houver instância, cria uma temporária.
            app = QApplication(sys.argv)

        dialog = SetupWizardDialog()
        if dialog.exec():
            # Se o usuário clicou em "Salvar", obtém os dados.
            return dialog.get_config_data()

        # Se o usuário cancelou, retorna None.
        return None
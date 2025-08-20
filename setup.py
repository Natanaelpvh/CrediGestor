# setup.py
"""
Módulo de Gerenciamento de Dependências do Ambiente.

Este módulo define a classe `SetupManager`, responsável por verificar se
todas as dependências do projeto listadas em 'requirements.txt' estão
instaladas no ambiente Python atual e, se não estiverem, instalá-las.
"""
import sys
import subprocess
import logging
from importlib import metadata
from typing import List, Set

class SetupManager:
    """
    Verifica e instala as dependências do projeto a partir de um arquivo
    de requerimentos.
    """
    def __init__(self, requirements_file: str = 'requirements.txt'):
        """
        Inicializa o gerenciador de dependências.

        Args:
            requirements_file (str): O caminho para o arquivo de dependências.
        """
        self.requirements_file = requirements_file
        self.required_packages = self._read_requirements()

    def _read_requirements(self) -> List[str]:
        """
        Lê o arquivo requirements.txt e retorna uma lista de pacotes.

        Ignora comentários e linhas em branco. Extrai apenas o nome do pacote,
        removendo especificadores de versão (ex: '==', '>=').

        Returns:
            List[str]: Uma lista com os nomes dos pacotes requeridos.
        """
        logging.info(f"Lendo dependências de '{self.requirements_file}'...")
        packages = []
        try:
            with open(self.requirements_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        package_name = line.split('#')[0].strip().split('==')[0].split('>=')[0]
                        if package_name:
                            packages.append(package_name)
        except FileNotFoundError:
            logging.critical(f"ERRO: O arquivo de dependências '{self.requirements_file}' não foi encontrado.")
            sys.exit(1)
        return packages

    def _get_installed_packages(self) -> Set[str]:
        """
        Obtém um conjunto de todos os pacotes instalados no ambiente.

        Returns:
            Set[str]: Um conjunto com os nomes normalizados dos pacotes instalados.
        """
        return {dist.metadata['name'].lower() for dist in metadata.distributions()}

    def check_and_install(self) -> bool:
        """
        Verifica se os pacotes necessários estão instalados e, se não, os instala.

        Returns:
            bool: True se todas as dependências estiverem satisfeitas (ou foram
                  instaladas com sucesso), False em caso de falha na instalação.
        """
        logging.info("Verificando dependências do ambiente...")
        installed_packages = self._get_installed_packages()
        
        missing_packages = [
            pkg for pkg in self.required_packages 
            if pkg.lower().replace('_', '-') not in installed_packages
        ]

        if not missing_packages:
            logging.info("✅ Todas as dependências já estão instaladas.")
            return True

        print("-" * 50)
        print(f"⚠️ Dependências faltando. Instalando: {', '.join(missing_packages)}")
        print("-" * 50)

        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing_packages])
            logging.info("✅ Dependências instaladas com sucesso!")
            print("\nPor favor, reinicie a aplicação para que as alterações tenham efeito.")
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            logging.critical(f"❌ Falha ao instalar dependências. Erro: {e}")
            print("\nPor favor, instale os pacotes manualmente e tente novamente.")
            return False
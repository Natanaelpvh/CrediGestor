# config.py
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env.
# O ConfigManager garante que este arquivo exista antes deste módulo ser importado.
load_dotenv()

# Acessa a variável de ambiente para a URL do banco de dados.
# Se não for encontrada, lança um erro, pois é uma configuração crítica.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não foi encontrada. Execute a configuração.")

# Default Admin User
DEFAULT_ADMIN_NOME = "Administrador"
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_SENHA = "admin"
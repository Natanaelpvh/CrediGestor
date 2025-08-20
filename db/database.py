# db/database.py
"""
Módulo de Gerenciamento de Banco de Dados.

Este módulo define a classe `DatabaseManager`, que encapsula toda a lógica
de conexão, criação de tabelas e gerenciamento de sessões com o banco de dados
usando SQLAlchemy.

A abordagem orientada a objetos centraliza a configuração do banco de dados,
promovendo um código mais limpo, reutilizável e fácil de manter.
"""

import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Importa todos os modelos para garantir que o SQLAlchemy os reconheça.
# Quando `Base.metadata.create_all()` é chamado, ele precisa ter visibilidade
# de todas as classes de modelo que herdam de `Base` para criar as tabelas.
from models import base_model, cliente, emprestimo, parcela, taxas_emprestimo, usuario

class DatabaseManager:
    """
    Gerencia a conexão, a criação de tabelas e as sessões do banco de dados.
    """
    def __init__(self):
        """
        Inicializa o gerenciador do banco de dados.

        Carrega a configuração do banco de dados a partir de variáveis de ambiente
        (do arquivo .env) e cria a engine do SQLAlchemy.

        Raises:
            ValueError: Se a variável de ambiente DATABASE_URL não estiver definida.
            Exception: Se ocorrer outro erro ao criar a engine do SQLAlchemy.
        """
        load_dotenv() # Carrega as variáveis do arquivo .env

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logging.critical("Variável de ambiente 'DATABASE_URL' não encontrada. O .env existe?")
            raise ValueError("A variável de ambiente 'DATABASE_URL' não foi encontrada.")

        # Converte a string 'true'/'false' para booleano para o log de SQL
        echo_sql = os.getenv("ECHO_SQL", "False").lower() in ('true', '1', 't')

        try:
            self.engine = create_engine(
                db_url,
                # O argumento 'check_same_thread' é específico para SQLite.
                connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
                echo=echo_sql,
                # pool_pre_ping verifica a "saúde" da conexão antes de cada uso,
                # o que ajuda a lidar com desconexões inesperadas (ex: timeout do BD).
                pool_pre_ping=True
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logging.info("Engine do banco de dados e SessionLocal criados com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao criar a engine do banco de dados: {e}")
            raise

    def create_tables(self):
        """
        Cria todas as tabelas no banco de dados com base nos modelos registrados.

        Este método inspeciona os modelos que herdam de `Base` e cria as tabelas
        correspondentes se elas ainda não existirem no banco de dados.

        Raises:
            Exception: Se ocorrer um erro durante a criação das tabelas.
        """
        try:
            base_model.Base.metadata.create_all(bind=self.engine)
            logging.info("Tabelas do banco de dados criadas/verificadas com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao criar as tabelas do banco de dados: {e}")
            raise

    def get_session(self) -> Session:
        """
        Cria e retorna uma nova sessão do banco de dados.

        Cada chamada a este método retorna uma nova instância de `Session`,
        garantindo que diferentes partes da aplicação possam operar em
        transações isoladas.

        Returns:
            Session: Uma nova instância de sessão do SQLAlchemy.
        """
        return self.SessionLocal()
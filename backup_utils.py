# backup_utils.py
"""
Módulo para gerenciar operações de backup do banco de dados para o sistema CrediGestor.

A classe BackupManager encapsula a lógica para realizar backups de diferentes
tipos de bancos de dados (SQLite, PostgreSQL, MySQL) com base na configuração
do ambiente.
"""
import os
import shutil
import subprocess
import logging
from datetime import datetime
from typing import Tuple

from dotenv import load_dotenv
from sqlalchemy.engine import make_url


class BackupManager:
    """
    Gerencia a criação de backups para diferentes sistemas de banco de dados.
    """
    def __init__(self):
        """
        Inicializa o gerenciador de backup, carregando a configuração do banco de dados.
        """
        load_dotenv()
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("A variável de ambiente 'DATABASE_URL' não foi encontrada.")

        self.url_obj = make_url(self.db_url)
        self.db_type = self.url_obj.drivername.split('+')[0]

    def _backup_sqlite(self, backup_dir: str, timestamp: str) -> Tuple[bool, str]:
        """Realiza o backup de um banco de dados SQLite."""
        source_path = self.url_obj.database
        if not os.path.exists(source_path):
            return False, f"Arquivo do banco de dados SQLite não encontrado em: {source_path}"

        backup_filename = f"backup_{timestamp}.db"
        dest_path = os.path.join(backup_dir, backup_filename)
        shutil.copy(source_path, dest_path)
        logging.info(f"Backup do SQLite copiado para: {dest_path}")
        return True, f"Backup do SQLite salvo em {dest_path}"

    def _backup_postgresql(self, backup_dir: str, timestamp: str) -> Tuple[bool, str]:
        """Realiza o backup de um banco de dados PostgreSQL usando pg_dump."""
        backup_filename = f"backup_{timestamp}.sql"
        dest_path = os.path.join(backup_dir, backup_filename)

        cmd = [
            'pg_dump',
            '-h', self.url_obj.host,
            '-p', str(self.url_obj.port or 5432),
            '-U', self.url_obj.username,
            '-d', self.url_obj.database,
            '--no-password', # Evita prompt de senha, usa PGPASSWORD
        ]

        env = os.environ.copy()
        if self.url_obj.password:
            env['PGPASSWORD'] = self.url_obj.password

        with open(dest_path, 'w', encoding='utf-8') as f:
            process = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True, check=False)

        if process.returncode != 0:
            error_msg = f"Falha no pg_dump: {process.stderr}"
            logging.error(error_msg)
            os.remove(dest_path) # Remove arquivo de backup incompleto
            return False, error_msg

        logging.info(f"Backup do PostgreSQL salvo em: {dest_path}")
        return True, f"Backup do PostgreSQL salvo em {dest_path}"

    def _backup_mysql(self, backup_dir: str, timestamp: str) -> Tuple[bool, str]:
        """Realiza o backup de um banco de dados MySQL usando mysqldump."""
        backup_filename = f"backup_{timestamp}.sql"
        dest_path = os.path.join(backup_dir, backup_filename)

        cmd = [
            'mysqldump',
            '-h', self.url_obj.host,
            '-P', str(self.url_obj.port or 3306),
            '-u', self.url_obj.username,
            self.url_obj.database,
        ]

        env = os.environ.copy()
        if self.url_obj.password:
            env['MYSQL_PWD'] = self.url_obj.password

        with open(dest_path, 'w', encoding='utf-8') as f:
            process = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True, check=False)

        if process.returncode != 0:
            error_msg = f"Falha no mysqldump: {process.stderr}"
            logging.error(error_msg)
            os.remove(dest_path)
            return False, error_msg

        logging.info(f"Backup do MySQL salvo em: {dest_path}")
        return True, f"Backup do MySQL salvo em {dest_path}"

    def perform_backup(self, backup_dir: str) -> Tuple[bool, str]:
        """Executa o processo de backup com base no tipo de banco de dados."""
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        try:
            if self.db_type == 'sqlite':
                return self._backup_sqlite(backup_dir, timestamp)
            if self.db_type == 'postgresql':
                return self._backup_postgresql(backup_dir, timestamp)
            if self.db_type == 'mysql':
                return self._backup_mysql(backup_dir, timestamp)
            return False, f"Tipo de banco de dados '{self.db_type}' não suportado para backup."
        except Exception as e:
            logging.critical(f"Erro inesperado durante o backup: {e}", exc_info=True)
            return False, f"Ocorreu um erro inesperado: {e}"

    def _restore_sqlite(self, backup_file_path: str) -> Tuple[bool, str]:
        """Restaura um banco de dados SQLite a partir de um arquivo de backup."""
        dest_path = self.url_obj.database
        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy(backup_file_path, dest_path)
            logging.info(f"Backup '{backup_file_path}' restaurado para '{dest_path}'.")
            return True, "Restauração do SQLite concluída."
        except Exception as e:
            error_msg = f"Falha ao restaurar o backup do SQLite: {e}"
            logging.error(error_msg)
            return False, error_msg

    def _restore_postgresql(self, backup_file_path: str) -> Tuple[bool, str]:
        """Restaura um banco de dados PostgreSQL a partir de um arquivo .sql."""
        logging.warning("Para restaurar o PostgreSQL, o utilitário 'psql' deve estar instalado e no PATH do sistema.")
        cmd = ['psql', '-h', self.url_obj.host, '-p', str(self.url_obj.port or 5432), '-U', self.url_obj.username, '-d', self.url_obj.database, '--no-password', '--single-transaction']
        env = os.environ.copy()
        if self.url_obj.password:
            env['PGPASSWORD'] = self.url_obj.password
        try:
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                process = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, env=env, text=True, check=False)
            if process.returncode != 0:
                error_msg = f"Falha no psql: {process.stderr}"
                logging.error(error_msg)
                return False, error_msg
            logging.info(f"Backup '{backup_file_path}' restaurado com sucesso no PostgreSQL.")
            return True, "Restauração do PostgreSQL concluída."
        except FileNotFoundError:
            return False, "Comando 'psql' não encontrado. Verifique se o PostgreSQL Client está instalado e no PATH."

    def _restore_mysql(self, backup_file_path: str) -> Tuple[bool, str]:
        """Restaura um banco de dados MySQL a partir de um arquivo .sql."""
        logging.warning("Para restaurar o MySQL, o utilitário 'mysql' deve estar instalado e no PATH do sistema.")
        cmd = ['mysql', '-h', self.url_obj.host, '-P', str(self.url_obj.port or 3306), '-u', self.url_obj.username, self.url_obj.database]
        env = os.environ.copy()
        if self.url_obj.password:
            env['MYSQL_PWD'] = self.url_obj.password
        try:
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                process = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, env=env, text=True, check=False)
            if process.returncode != 0:
                error_msg = f"Falha no mysql: {process.stderr}"
                logging.error(error_msg)
                return False, error_msg
            logging.info(f"Backup '{backup_file_path}' restaurado com sucesso no MySQL.")
            return True, "Restauração do MySQL concluída."
        except FileNotFoundError:
            return False, "Comando 'mysql' não encontrado. Verifique se o MySQL Client está instalado e no PATH."

    def perform_restore(self, backup_file_path: str) -> Tuple[bool, str]:
        """Executa o processo de restauração com base no tipo de banco de dados."""
        if not os.path.exists(backup_file_path):
            return False, f"Arquivo de backup não encontrado em: {backup_file_path}"
        try:
            dispatch_map = {'sqlite': self._restore_sqlite, 'postgresql': self._restore_postgresql, 'mysql': self._restore_mysql}
            restore_func = dispatch_map.get(self.db_type)
            if not restore_func:
                return False, f"Tipo de banco de dados '{self.db_type}' não suportado para restauração."
            success, msg = restore_func(backup_file_path)
            return (True, "Restauração concluída com sucesso. É recomendado reiniciar a aplicação.") if success else (False, msg)
        except Exception as e:
            logging.critical(f"Erro inesperado durante a restauração: {e}", exc_info=True)
            return False, f"Ocorreu um erro inesperado: {e}"
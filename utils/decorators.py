# utils/decorators.py

import functools
import logging
from sqlalchemy.orm import Session

def db_session_manager(func):
    """
    Um decorator para gerenciar sessões de banco de dados para métodos de serviço.
    Ele lida com commit, rollback e log de erros genérico.
    Assume que o primeiro argumento da função decorada é 'self'
    e que 'self' possui um atributo 'db_session'.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        session: Session = self.db_session
        try:
            result = func(self, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            logging.error(f"Falha na transação do banco de dados em {func.__name__}. Revertendo. Erro: {e}")
            raise
    return wrapper
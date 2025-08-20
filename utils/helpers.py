# utils/helpers.py

import bcrypt
import logging

def hash_password(password: str) -> bytes:
    """
    Gera o hash de uma senha usando bcrypt.
    Retorna o hash como bytes, que é o formato ideal para armazenar.
    """
    try:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password
    except Exception as e:
        logging.error(f"Erro ao gerar hash da senha: {e}")
        raise

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    """Verifica se uma senha corresponde ao seu hash."""
    try:
        if not plain_password or not hashed_password:
            return False
        # O hash do banco já vem como bytes, não precisa de .encode()
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)
    except (ValueError, TypeError) as e:
        logging.warning(f"Erro ao verificar a senha (hash inválido ou corrompido): {e}")
        return False
    except Exception as e:
        logging.error(f"Erro inesperado ao verificar a senha: {e}")
        return False

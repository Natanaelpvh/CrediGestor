# services/usuario_service.py

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.usuario import Usuario, UserRole
from utils.decorators import db_session_manager
from utils.helpers import hash_password, verify_password
import logging

class UsuarioService:
    """
    Serviço para gerenciar as operações de CRUD para Usuários.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session

    @db_session_manager
    def create_usuario(self, nome: str, email: str, senha: str, role: UserRole) -> Usuario:
        """Cria um novo usuário no banco de dados com senha criptografada."""
        senha_hashed = hash_password(senha)
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=senha_hashed,
            role=role
        )
        self.db_session.add(novo_usuario)
        self.db_session.flush()
        self.db_session.refresh(novo_usuario)
        logging.info(f"Usuário '{nome}' criado com sucesso.")
        return novo_usuario

    def get_usuario_by_email(self, email: str) -> Optional[Usuario]:
        """Busca um usuário pelo seu email de forma case-insensitive."""
        if not email:
            return None
        # Compara o email em minúsculas para garantir a busca case-insensitive.
        # O método .strip() remove espaços em branco acidentais.
        return self.db_session.query(Usuario).filter(func.lower(Usuario.email) == email.strip().lower()).first()

    def get_usuario_by_id(self, usuario_id: int) -> Optional[Usuario]:
        """Busca um usuário pelo seu ID."""
        return self.db_session.query(Usuario).filter(Usuario.id == usuario_id).first()

    @db_session_manager
    def update_usuario(self, usuario_id: int, **kwargs) -> Optional[Usuario]:
        """Atualiza os dados de um usuário existente. Se a senha for fornecida, ela será atualizada."""
        usuario = self.get_usuario_by_id(usuario_id)
        if not usuario:
            return None
        
        if 'senha' in kwargs:
            kwargs['senha_hash'] = hash_password(kwargs.pop('senha'))

        for key, value in kwargs.items():
            setattr(usuario, key, value)
        self.db_session.flush()
        self.db_session.refresh(usuario)
        logging.info(f"Usuário ID {usuario_id} atualizado com sucesso.")
        return usuario

    @db_session_manager
    def delete_usuario(self, usuario_id: int) -> bool:
        """Deleta um usuário do banco de dados."""
        usuario = self.get_usuario_by_id(usuario_id)
        if not usuario:
            return False
        
        self.db_session.delete(usuario)
        logging.info(f"Usuário ID {usuario_id} deletado com sucesso.")
        return True

    def verify_credentials(self, email: str, senha: str) -> Optional[Usuario]:
        """Verifica as credenciais do usuário (email e senha) e retorna o usuário se forem válidas."""
        usuario = self.get_usuario_by_email(email)
        if usuario and verify_password(senha, usuario.senha_hash):
            logging.info(f"Credenciais válidas para o usuário: {email}")
            return usuario
        logging.warning(f"Tentativa de login inválida para o usuário: {email}")
        return None

    def get_all_usuarios(self) -> List[Usuario]:
        """Retorna uma lista de todos os usuários."""
        return self.db_session.query(Usuario).all()

    def search_usuarios(self, search_term: str) -> List[Usuario]:
        """Busca usuários por nome ou email."""
        if not search_term:
            return self.get_all_usuarios()

        search_filter = f"%{search_term}%"
        return self.db_session.query(Usuario).filter(
            (Usuario.nome.ilike(search_filter)) | (Usuario.email.ilike(search_filter))
        ).all()
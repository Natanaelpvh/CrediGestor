# models/usuario.py

import enum
from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum, LargeBinary
from .base_model import Base, TimestampMixin

class UserRole(str, enum.Enum):
    """Enum para os papéis (roles) de usuário."""
    ADMIN = "admin"
    GERENTE = "gerente"
    OPERADOR = "operador"

class Usuario(Base, TimestampMixin):
    """
    Modelo ORM para a tabela de Usuários.
    """
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    senha_hash = Column(LargeBinary, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.OPERADOR)

    def __repr__(self):
        return f"<Usuario(id={self.id}, nome='{self.nome}', email='{self.email}', role='{self.role.value}')>"
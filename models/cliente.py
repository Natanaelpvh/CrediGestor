# models/cliente.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base_model import Base, TimestampMixin

class Cliente(Base, TimestampMixin):
    """
    Modelo ORM para a tabela de Clientes.
    """
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, index=True)
    cpf = Column(String(14), nullable=False, unique=True, index=True)
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    endereco = Column(String(255), nullable=True)

    emprestimos = relationship("Emprestimo", back_populates="cliente")

    def __repr__(self):
        return f"<Cliente(id={self.id}, nome='{self.nome}', cpf='{self.cpf}')>"
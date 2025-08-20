# models/emprestimo.py

import enum
from datetime import date
from decimal import Decimal
from sqlalchemy import (Column, Date, Enum as SQLAlchemyEnum, ForeignKey,
                        Integer, Numeric)
from sqlalchemy.orm import relationship

from .base_model import Base, TimestampMixin


class TipoJuros(str, enum.Enum):
    """Enum para os tipos de juros."""
    SIMPLES = "simples"
    COMPOSTO = "composto"


class Emprestimo(Base, TimestampMixin):
    """Modelo ORM para a tabela de Empréstimos."""
    __tablename__ = "emprestimos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    numero_parcelas = Column(Integer, nullable=False)
    data_inicio = Column(Date, nullable=False, default=date.today)
    tipo_juros = Column(SQLAlchemyEnum(TipoJuros, name="tipo_juros_enum"), nullable=False)

    # Snapshot das taxas no momento do empréstimo
    taxa_juros_simples = Column(Numeric(5, 2), nullable=False, default=Decimal("0.0"))
    taxa_juros_composto = Column(Numeric(5, 2), nullable=False, default=Decimal("0.0"))
    taxa_juros_mora = Column(Numeric(5, 2), nullable=False, default=Decimal("0.0"))

    # Relacionamentos bidirecionais
    cliente = relationship("Cliente", back_populates="emprestimos")
    parcelas = relationship("Parcela", back_populates="emprestimo", cascade="all, delete-orphan")
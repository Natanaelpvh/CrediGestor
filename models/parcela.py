# models/parcela.py

from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Integer,
                        Numeric)
from sqlalchemy.orm import relationship

from .base_model import Base, TimestampMixin


class Parcela(Base, TimestampMixin):
    __tablename__ = "parcelas"

    id = Column(Integer, primary_key=True, index=True)
    emprestimo_id = Column(Integer, ForeignKey("emprestimos.id"), nullable=False)
    numero = Column(Integer, nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    data_vencimento = Column(Date, nullable=False)
    pago = Column(Boolean, default=False, nullable=False)
    data_pagamento = Column(Date, nullable=True)

    emprestimo = relationship("Emprestimo", back_populates="parcelas")

    def __repr__(self):
        return f"<Parcela(id={self.id}, emprestimo_id={self.emprestimo_id}, numero={self.numero}, valor={self.valor})>"
from models.base_model import Base
from sqlalchemy import Column, Integer, Numeric
from decimal import Decimal

class TaxaJuros(Base):
    __tablename__ = "taxa_juros"

    id = Column(Integer, primary_key=True)
    taxa_juros_simples = Column(Numeric(5, 2), nullable=False, default=Decimal("0.0"))
    taxa_juros_composto = Column(Numeric(5, 2), nullable=False, default=Decimal("0.0"))
    taxa_juros_mora = Column(Numeric(5, 2), nullable=False, default=Decimal("0.0"))

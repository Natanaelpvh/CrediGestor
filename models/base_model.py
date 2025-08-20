# models/base_model.py

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

# Base declarativa para os modelos ORM
Base = declarative_base()

class TimestampMixin:
    """
    Mixin que adiciona colunas de timestamp (created_at, updated_at)
    automaticamente a qualquer modelo que herde dela.
    """
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
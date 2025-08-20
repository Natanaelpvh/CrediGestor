# models/__init__.py
from .base_model import Base, TimestampMixin
from .cliente import Cliente
from .usuario import Usuario, UserRole
from .emprestimo import Emprestimo, TipoJuros
from .parcela import Parcela
from .taxas_emprestimo import TaxaJuros

# Importe outros modelos aqui conforme forem criados
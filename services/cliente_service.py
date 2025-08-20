# services/cliente_service.py
"""
Módulo de Serviço de Cliente.

Este módulo define a classe `ClienteService`, que encapsula toda a lógica de
negócio para as operações de CRUD (Criar, Ler, Atualizar, Deletar) relacionadas
aos clientes. Ele atua como uma camada intermediária entre a interface do usuário
e o modelo de dados do cliente.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.cliente import Cliente

class ClienteService:
    """
    Serviço para gerenciar as operações de negócio relacionadas a clientes.

    Fornece métodos para criar, ler, atualizar, deletar e buscar clientes,
    abstraindo as interações diretas com a sessão do banco de dados.
    """
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_all_clientes(self) -> List[Cliente]:
        """Retorna todos os clientes, ordenados por nome."""
        return self.db.query(Cliente).order_by(Cliente.nome).all()

    def get_cliente_by_id(self, cliente_id: int) -> Optional[Cliente]:
        """
        Busca um cliente específico pelo seu ID.

        Args:
            cliente_id (int): O ID do cliente a ser buscado.

        Returns:
            Optional[Cliente]: O objeto Cliente se encontrado, caso contrário None.
        """
        return self.db.query(Cliente).filter(Cliente.id == cliente_id).first()

    def create_cliente(self, **data) -> Cliente:
        """
        Cria um novo cliente no banco de dados.

        Args:
            **data: Um dicionário contendo os dados do cliente (nome, cpf, etc.).

        Returns:
            Cliente: O objeto Cliente recém-criado e persistido.
        """
        novo_cliente = Cliente(**data)
        self.db.add(novo_cliente)
        self.db.commit()
        self.db.refresh(novo_cliente)
        return novo_cliente

    def update_cliente(self, cliente_id: int, **data) -> Optional[Cliente]:
        """
        Atualiza os dados de um cliente existente.

        Args:
            cliente_id (int): O ID do cliente a ser atualizado.
            **data: Um dicionário com os campos a serem atualizados.

        Returns:
            Optional[Cliente]: O objeto Cliente atualizado, ou None se não for encontrado.
        """
        cliente = self.get_cliente_by_id(cliente_id)
        if cliente:
            for key, value in data.items():
                setattr(cliente, key, value)
            self.db.commit()
            self.db.refresh(cliente)
        return cliente

    def delete_cliente(self, cliente_id: int):
        """
        Exclui um cliente do banco de dados.

        Args:
            cliente_id (int): O ID do cliente a ser excluído.
        """
        cliente = self.get_cliente_by_id(cliente_id)
        if cliente:
            self.db.delete(cliente)
            self.db.commit()

    def search_clientes(self, search_term: str, limit: Optional[int] = None) -> List[Cliente]:
        """
        Busca clientes por nome ou CPF, com um limite opcional.

        Args:
            search_term (str): O termo para buscar.
            limit (Optional[int]): O número máximo de resultados a retornar.

        Returns:
            List[Cliente]: Uma lista de clientes que correspondem à busca.
        """
        query = self.db.query(Cliente).order_by(Cliente.nome)
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(or_(Cliente.nome.ilike(search_pattern), Cliente.cpf.ilike(search_pattern)))

        if limit:
            query = query.limit(limit)
        
        return query.all()
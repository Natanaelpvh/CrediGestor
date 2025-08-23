# services/cliente_service.py
"""
Define a camada de serviço para a entidade Cliente.

Este módulo contém a classe `ClienteService`, que centraliza a lógica de
negócio para manipulação de dados de clientes, servindo como uma ponte
entre a interface do usuário e o acesso ao banco de dados.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.cliente import Cliente

class ClienteService:
    """
    Encapsula a lógica de negócio para operações com clientes.

    Esta classe abstrai as interações com o banco de dados para a entidade
    Cliente, fornecendo uma API clara para as operações de CRUD e busca.
    """
    def __init__(self, db_session: Session):
        """
        Inicializa o serviço de cliente.

        Args:
            db_session (Session): A sessão do SQLAlchemy para interagir com o banco.
        """
        self.db = db_session

    def get_all_clientes(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Cliente]:
        """
        Recupera uma lista paginada de clientes.

        Args:
            limit (Optional[int]): O número máximo de clientes a retornar.
            offset (Optional[int]): O número de clientes a pular (para paginação).

        Returns:
            List[Cliente]: A lista de clientes, ordenada por ID para paginação estável.
        """
        query = self.db.query(Cliente).order_by(Cliente.id)
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def get_cliente_by_id(self, cliente_id: int) -> Optional[Cliente]:
        """
        Recupera um cliente específico pelo seu ID.

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
            **data: Atributos do cliente a serem criados (ex: nome, cpf, email).
                    Os nomes das chaves devem corresponder aos atributos do modelo Cliente.

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
            **data: Dicionário contendo os campos e os novos valores a serem atualizados.

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
        Exclui um cliente do banco de dados, se ele existir.

        Args:
            cliente_id (int): O ID do cliente a ser excluído.
        """
        cliente = self.get_cliente_by_id(cliente_id)
        if cliente:
            self.db.delete(cliente)
            self.db.commit()

    def search_clientes(self, search_term: str, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Cliente]:
        """
        Busca clientes por nome ou CPF com suporte para paginação.

        Args:
            search_term (str): O termo para buscar (case-insensitive).
            limit (Optional[int]): O número máximo de clientes a retornar.
            offset (Optional[int]): O número de clientes a pular (para paginação).

        Returns:
            List[Cliente]: Uma lista paginada de clientes que correspondem aos critérios.
        """
        # Ordena por nome e depois por ID para garantir uma ordem estável para paginação
        query = self.db.query(Cliente).order_by(Cliente.nome, Cliente.id)
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(or_(Cliente.nome.ilike(search_pattern), Cliente.cpf.ilike(search_pattern)))

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        
        return query.all()
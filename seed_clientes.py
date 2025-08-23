import random
from faker import Faker

from db.database import DatabaseManager
from services.cliente_service import ClienteService

# Configuração do Faker em português do Brasil
fake = Faker("pt_BR")


def gerar_cpf():
    """Gera um CPF válido fictício no formato 000.000.000-00"""
    cpf = [random.randint(0, 9) for _ in range(9)]
    soma1 = sum([(10 - i) * cpf[i] for i in range(9)])
    d1 = (soma1 * 10 % 11) % 10
    cpf.append(d1)
    soma2 = sum([(11 - i) * cpf[i] for i in range(10)])
    d2 = (soma2 * 10 % 11) % 10
    cpf.append(d2)
    return "{}{}{}.{}{}{}.{}{}{}-{}{}".format(*cpf)


def seed_clientes(qtd=50):
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    cliente_service = ClienteService(session)

    for _ in range(qtd):
        try:
            cliente_service.create_cliente(
                nome=fake.name(),
                cpf=gerar_cpf(),
                telefone=fake.phone_number(),
                email=fake.email(),
                endereco=fake.address(),
                outras_informacoes=fake.text(max_nb_chars=50),
            )
        except Exception as e:
            session.rollback()
            print(f"Erro ao inserir cliente: {e}")

    print(f"{qtd} clientes fictícios cadastrados com sucesso!")


if __name__ == "__main__":
    seed_clientes(50)

<div align="center">
  <h1>CrediGestor</h1>
  <p>
    <strong>Um sistema de gestão de empréstimos e parcelas, desenvolvido em Python com PyQt6.</strong>
  </p>
</div>

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![PyQt6](https://img.shields.io/badge/UI-PyQt6-blue?logo=qt)
![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL%20%7C%20MySQL-orange)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

**CrediGestor** é uma solução de desktop robusta para o gerenciamento completo de empréstimos e clientes. Ele permite controlar usuários, clientes, empréstimos e parcelas de forma organizada, segura e eficiente.

## 🌟 Principais Funcionalidades

- **Gestão de Usuários:** Controle de acesso com diferentes níveis de permissão (Administrador, Usuário).
- **Controle de Clientes:** Cadastro completo e busca de clientes.
- **Gerenciamento de Empréstimos:** Registro de empréstimos com cálculo de juros simples e composto.
- **Gestão de Parcelas:** Acompanhamento detalhado de parcelas, incluindo status de pagamento e datas de vencimento.
- **Backup e Restauração:** Funcionalidade integrada para backup e restauração do banco de dados, garantindo a segurança dos dados.
- **Suporte a Múltiplos Bancos de Dados:** Compatível com SQLite, PostgreSQL e MySQL.
- **Assistente de Configuração:** Um assistente gráfico guia o usuário na primeira configuração do banco de dados.
- **Arquitetura Modular:** Sistema projetado de forma escalável, facilitando a adição de novas funcionalidades.

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.10+
- **Interface Gráfica:** PyQt6
- **Banco de Dados (ORM):** SQLAlchemy
- **Drivers de BD:** Psycopg2 (PostgreSQL), PyMySQL (MySQL)
- **Relatórios:** ReportLab
- **Segurança:** Bcrypt para hashing de senhas

## 🚀 Instalação e Execução

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local.

**1. Clone o Repositório**
```bash
git clone https://github.com/Natanaelpvh/CrediGestor.git
cd CrediGestor
```

**2. Crie e Ative um Ambiente Virtual**
```bash
# Crie o ambiente virtual
python -m venv .venv

# Ative o ambiente (Windows)
.venv\Scripts\activate

# Ative o ambiente (Linux/macOS)
source .venv/bin/activate
```

**3. Execute o Script de Inicialização**
O sistema possui um orquestrador que verifica e instala as dependências automaticamente.
```bash
python start.py
```
> **Nota:** Na primeira execução, o script irá verificar as dependências do `requirements.txt` e instalá-las. Se o arquivo de configuração `.env` não for encontrado, um assistente gráfico será aberto para ajudá-lo a configurar a conexão com o banco de dados (SQLite, PostgreSQL ou MySQL).

**4. Login**
Após a configuração, a tela de login será exibida. Se for a primeira vez que o sistema é executado, um usuário administrador padrão será criado:
- **Email:** `admin@example.com`
- **Senha:** `admin`

## 📄 Licença

Este projeto está licenciado sob a Licença MIT.

## 📌 Contato

**Natanael S. de Oliveira**
- GitHub: @Natanaelpvh
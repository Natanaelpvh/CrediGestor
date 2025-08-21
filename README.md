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

---

## 🚀 Instalação e Uso

Existem duas maneiras de instalar o CrediGestor, dependendo se você é um usuário final ou um desenvolvedor.

### Para Usuários (Recomendado)

Esta é a maneira mais fácil de usar o sistema.

1.  **Baixe os arquivos** do projeto e descompacte-os em uma pasta.
2.  Execute o script de inicialização correspondente ao seu sistema operacional:
    -   **No Windows:** Dê um duplo clique no arquivo `run.bat`.
    -   **No Linux:** Abra um terminal, navegue até a pasta e execute os comandos:
        ```bash
        chmod +x run.sh
        ./run.sh
        ```

Na primeira vez que você executar, o sistema irá:
- Instalar todas as dependências necessárias automaticamente.
- Abrir um assistente para você configurar a conexão com o banco de dados.
- Criar um atalho na sua Área de Trabalho para facilitar o acesso futuro.

### Para Desenvolvedores

Se você deseja modificar ou contribuir com o código:

1.  **Clone o Repositório**
    ```bash
    git clone https://github.com/Natanaelpvh/CrediGestor.git
    cd CrediGestor
    ```
2.  **Crie e Ative um Ambiente Virtual**
    ```bash
    # Crie o ambiente
    python -m venv .venv
    # Ative (Windows)
    .venv\Scripts\activate
    # Ative (Linux/macOS)
    source .venv/bin/activate
    ```
3.  **Execute o Script de Inicialização**
    ```bash
    python start.py
    ```

---

## ⚙️ Configuração

A configuração do sistema é armazenada em um arquivo `.env` na raiz do projeto, criado automaticamente pelo assistente na primeira execução. A variável mais importante é a `DATABASE_URL`.

**Exemplos de `DATABASE_URL`:**
- **SQLite:** `DATABASE_URL="sqlite:///database.db"`
- **PostgreSQL:** `DATABASE_URL="postgresql+psycopg2://USER:PASS@HOST:PORT/DB_NAME"`
- **MySQL:** `DATABASE_URL="mysql+pymysql://USER:PASS@HOST:PORT/DB_NAME"`

## 👤 Login Padrão

Na primeira inicialização, um usuário administrador padrão é criado para permitir o acesso:
- **Email:** `admin@example.com`
- **Senha:** `admin`

> É altamente recomendável alterar essa senha após o primeiro login.

## 📦 Backup e Restauração

O sistema possui uma funcionalidade integrada para criar e restaurar backups do banco de dados.

- **Backup**: Cria uma cópia segura do estado atual do banco de dados.
- **Restauração**: Substitui o estado atual do banco de dados pelos dados de um arquivo de backup. **Atenção: esta operação é destrutiva e não pode ser desfeita.**

> Para que a funcionalidade funcione com PostgreSQL ou MySQL, os respectivos utilitários de linha de comando (`pg_dump`, `psql`, `mysqldump`, `mysql`) devem estar instalados.

## 📄 Licença

Este projeto está licenciado sob a Licença MIT.

## 📌 Contato

**Natanael S. de Oliveira**
- GitHub: @Natanaelpvh
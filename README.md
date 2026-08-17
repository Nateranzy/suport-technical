# 🔧 Sistema de Assistência Técnica

Sistema web para gestão de uma assistência técnica: cadastro de clientes, abertura de ordens de serviço, orçamento, controle de peças/estoque, impressão de recibo em PDF e histórico de atendimentos por cliente.

Desenvolvido com **Flask** + **SQLite**, com login de usuários (técnicos).

---

## ✨ Funcionalidades

- **Login de usuários** — múltiplos técnicos podem ter conta no sistema
- **Cadastro de clientes** — nome, telefone, email, endereço
- **Ordens de serviço** — equipamento, defeito relatado, laudo técnico, status (Aberta, Em andamento, Aguardando aprovação, Aprovada, Concluída, Entregue, Cancelada)
- **Orçamento** — adição de peças (do estoque) ou serviços avulsos, com cálculo automático do total
- **Controle de peças/estoque** — abate automático de estoque ao usar uma peça numa ordem
- **Recibo em PDF** — geração automática do recibo da ordem de serviço, pronto pra impressão
- **Histórico** — todas as ordens de serviço de um cliente, com status e valores

---

## 🛠️ Tecnologias

- [Flask](https://flask.palletsprojects.com/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) (ORM)
- [Flask-Login](https://flask-login.readthedocs.io/) (autenticação)
- [ReportLab](https://www.reportlab.com/) (geração de PDF)
- SQLite (banco de dados)
- Bootstrap 5 (interface)

---

## 🚀 Como rodar o projeto

### Pré-requisitos
- Python 3.10+ instalado

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/Nateranzy/sistema-assistencia-tecnica.git
cd sistema-assistencia-tecnica

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode o servidor
python app.py
```

Acesse **http://127.0.0.1:5000** no navegador, clique em **"Criar conta"** e cadastre seu primeiro usuário técnico.

---

## 📁 Estrutura do projeto

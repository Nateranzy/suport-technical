from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Usuario(db.Model, UserMixin):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    endereco = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    ordens = db.relationship("OrdemServico", backref="cliente", lazy=True)


class Peca(db.Model):
    __tablename__ = "pecas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    preco = db.Column(db.Float, nullable=False, default=0)
    estoque = db.Column(db.Integer, nullable=False, default=0)


STATUS_ORDEM = [
    "Aberta",
    "Em andamento",
    "Aguardando aprovacao",
    "Aprovada",
    "Concluida",
    "Entregue",
    "Cancelada",
]


class OrdemServico(db.Model):
    __tablename__ = "ordens_servico"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)

    equipamento = db.Column(db.String(150), nullable=False)
    defeito_relatado = db.Column(db.Text, nullable=False)
    laudo_tecnico = db.Column(db.Text)

    status = db.Column(db.String(30), nullable=False, default="Aberta")

    data_entrada = db.Column(db.DateTime, default=datetime.utcnow)
    data_saida = db.Column(db.DateTime)

    tecnico = db.relationship("Usuario")
    itens = db.relationship(
        "ItemOrdem", backref="ordem", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def total(self):
        return sum(item.valor_total for item in self.itens)


class ItemOrdem(db.Model):
    __tablename__ = "itens_ordem"

    id = db.Column(db.Integer, primary_key=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey("ordens_servico.id"), nullable=False)
    peca_id = db.Column(db.Integer, db.ForeignKey("pecas.id"), nullable=True)

    tipo = db.Column(db.String(20), nullable=False)  # "Peca" ou "Servico"
    descricao = db.Column(db.String(200), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    valor_unitario = db.Column(db.Float, nullable=False, default=0)

    peca = db.relationship("Peca")

    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario

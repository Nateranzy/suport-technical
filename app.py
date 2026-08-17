import io
import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from models import db, Usuario, Cliente, Peca, OrdemServico, ItemOrdem, STATUS_ORDEM

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = "troque-esta-chave-em-producao"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "instance", "assistencia.db")

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_usuario(user_id):
    return Usuario.query.get(int(user_id))


# ---------------------------------------------------------------------------
# AUTENTICACAO
# ---------------------------------------------------------------------------

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        if Usuario.query.filter_by(email=email).first():
            flash("Ja existe um usuario com esse email.", "danger")
            return redirect(url_for("registrar"))

        usuario = Usuario(nome=nome, email=email)
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        flash("Cadastro realizado! Faca login.", "success")
        return redirect(url_for("login"))

    return render_template("registrar.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.checar_senha(senha):
            login_user(usuario)
            return redirect(url_for("dashboard"))

        flash("Email ou senha invalidos.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------

@app.route("/")
@login_required
def dashboard():
    ordens_abertas = OrdemServico.query.filter(
        OrdemServico.status.notin_(["Entregue", "Cancelada"])
    ).order_by(OrdemServico.data_entrada.desc()).all()

    total_clientes = Cliente.query.count()
    total_pecas = Peca.query.count()

    return render_template(
        "dashboard.html",
        ordens_abertas=ordens_abertas,
        total_clientes=total_clientes,
        total_pecas=total_pecas,
    )


# ---------------------------------------------------------------------------
# CLIENTES
# ---------------------------------------------------------------------------

@app.route("/clientes")
@login_required
def listar_clientes():
    termo = request.args.get("q", "")
    query = Cliente.query
    if termo:
        query = query.filter(Cliente.nome.ilike(f"%{termo}%"))
    clientes = query.order_by(Cliente.nome).all()
    return render_template("clientes/listar.html", clientes=clientes, termo=termo)


@app.route("/clientes/novo", methods=["GET", "POST"])
@login_required
def novo_cliente():
    if request.method == "POST":
        cliente = Cliente(
            nome=request.form["nome"],
            telefone=request.form.get("telefone"),
            email=request.form.get("email"),
            endereco=request.form.get("endereco"),
        )
        db.session.add(cliente)
        db.session.commit()
        flash("Cliente cadastrado com sucesso.", "success")
        return redirect(url_for("listar_clientes"))

    return render_template("clientes/form.html", cliente=None)


@app.route("/clientes/<int:cliente_id>/editar", methods=["GET", "POST"])
@login_required
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == "POST":
        cliente.nome = request.form["nome"]
        cliente.telefone = request.form.get("telefone")
        cliente.email = request.form.get("email")
        cliente.endereco = request.form.get("endereco")
        db.session.commit()
        flash("Cliente atualizado.", "success")
        return redirect(url_for("listar_clientes"))

    return render_template("clientes/form.html", cliente=cliente)


@app.route("/clientes/<int:cliente_id>/excluir", methods=["POST"])
@login_required
def excluir_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if cliente.ordens:
        flash("Nao e possivel excluir: cliente possui ordens de servico.", "danger")
        return redirect(url_for("listar_clientes"))
    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente removido.", "success")
    return redirect(url_for("listar_clientes"))


@app.route("/clientes/<int:cliente_id>/historico")
@login_required
def historico_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    ordens = OrdemServico.query.filter_by(cliente_id=cliente.id).order_by(
        OrdemServico.data_entrada.desc()
    ).all()
    return render_template("clientes/historico.html", cliente=cliente, ordens=ordens)


# ---------------------------------------------------------------------------
# PECAS
# ---------------------------------------------------------------------------

@app.route("/pecas")
@login_required
def listar_pecas():
    pecas = Peca.query.order_by(Peca.nome).all()
    return render_template("pecas/listar.html", pecas=pecas)


@app.route("/pecas/nova", methods=["GET", "POST"])
@login_required
def nova_peca():
    if request.method == "POST":
        peca = Peca(
            nome=request.form["nome"],
            preco=float(request.form["preco"]),
            estoque=int(request.form.get("estoque") or 0),
        )
        db.session.add(peca)
        db.session.commit()
        flash("Peca cadastrada.", "success")
        return redirect(url_for("listar_pecas"))

    return render_template("pecas/form.html", peca=None)


@app.route("/pecas/<int:peca_id>/editar", methods=["GET", "POST"])
@login_required
def editar_peca(peca_id):
    peca = Peca.query.get_or_404(peca_id)

    if request.method == "POST":
        peca.nome = request.form["nome"]
        peca.preco = float(request.form["preco"])
        peca.estoque = int(request.form.get("estoque") or 0)
        db.session.commit()
        flash("Peca atualizada.", "success")
        return redirect(url_for("listar_pecas"))

    return render_template("pecas/form.html", peca=peca)


@app.route("/pecas/<int:peca_id>/excluir", methods=["POST"])
@login_required
def excluir_peca(peca_id):
    peca = Peca.query.get_or_404(peca_id)
    db.session.delete(peca)
    db.session.commit()
    flash("Peca removida.", "success")
    return redirect(url_for("listar_pecas"))


# ---------------------------------------------------------------------------
# ORDENS DE SERVICO / ORCAMENTO
# ---------------------------------------------------------------------------

@app.route("/ordens")
@login_required
def listar_ordens():
    status_filtro = request.args.get("status")
    query = OrdemServico.query
    if status_filtro:
        query = query.filter_by(status=status_filtro)
    ordens = query.order_by(OrdemServico.data_entrada.desc()).all()
    return render_template(
        "ordens/listar.html", ordens=ordens, status_list=STATUS_ORDEM, status_filtro=status_filtro
    )


@app.route("/ordens/nova", methods=["GET", "POST"])
@login_required
def nova_ordem():
    if request.method == "POST":
        ordem = OrdemServico(
            cliente_id=int(request.form["cliente_id"]),
            tecnico_id=current_user.id,
            equipamento=request.form["equipamento"],
            defeito_relatado=request.form["defeito_relatado"],
            status="Aberta",
        )
        db.session.add(ordem)
        db.session.commit()
        flash("Ordem de servico criada. Agora adicione os itens do orcamento.", "success")
        return redirect(url_for("detalhe_ordem", ordem_id=ordem.id))

    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template("ordens/form.html", clientes=clientes)


@app.route("/ordens/<int:ordem_id>")
@login_required
def detalhe_ordem(ordem_id):
    ordem = OrdemServico.query.get_or_404(ordem_id)
    pecas = Peca.query.order_by(Peca.nome).all()
    return render_template(
        "ordens/detalhe.html", ordem=ordem, pecas=pecas, status_list=STATUS_ORDEM
    )


@app.route("/ordens/<int:ordem_id>/status", methods=["POST"])
@login_required
def atualizar_status_ordem(ordem_id):
    ordem = OrdemServico.query.get_or_404(ordem_id)
    ordem.status = request.form["status"]
    if ordem.status in ("Entregue", "Cancelada"):
        ordem.data_saida = datetime.utcnow()
    db.session.commit()
    flash("Status atualizado.", "success")
    return redirect(url_for("detalhe_ordem", ordem_id=ordem.id))


@app.route("/ordens/<int:ordem_id>/laudo", methods=["POST"])
@login_required
def atualizar_laudo_ordem(ordem_id):
    ordem = OrdemServico.query.get_or_404(ordem_id)
    ordem.laudo_tecnico = request.form.get("laudo_tecnico")
    db.session.commit()
    flash("Laudo tecnico salvo.", "success")
    return redirect(url_for("detalhe_ordem", ordem_id=ordem.id))


@app.route("/ordens/<int:ordem_id>/itens/adicionar", methods=["POST"])
@login_required
def adicionar_item(ordem_id):
    ordem = OrdemServico.query.get_or_404(ordem_id)
    tipo = request.form["tipo"]
    quantidade = int(request.form.get("quantidade") or 1)

    if tipo == "Peca":
        peca = Peca.query.get(int(request.form["peca_id"]))
        item = ItemOrdem(
            ordem_id=ordem.id,
            peca_id=peca.id,
            tipo="Peca",
            descricao=peca.nome,
            quantidade=quantidade,
            valor_unitario=peca.preco,
        )
        peca.estoque = max(0, peca.estoque - quantidade)
    else:
        item = ItemOrdem(
            ordem_id=ordem.id,
            tipo="Servico",
            descricao=request.form["descricao"],
            quantidade=quantidade,
            valor_unitario=float(request.form["valor_unitario"]),
        )

    db.session.add(item)
    db.session.commit()
    flash("Item adicionado ao orcamento.", "success")
    return redirect(url_for("detalhe_ordem", ordem_id=ordem.id))


@app.route("/ordens/<int:ordem_id>/itens/<int:item_id>/remover", methods=["POST"])
@login_required
def remover_item(ordem_id, item_id):
    item = ItemOrdem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Item removido do orcamento.", "success")
    return redirect(url_for("detalhe_ordem", ordem_id=ordem_id))


# ---------------------------------------------------------------------------
# RECIBO EM PDF
# ---------------------------------------------------------------------------

@app.route("/ordens/<int:ordem_id>/recibo")
@login_required
def recibo_ordem(ordem_id):
    ordem = OrdemServico.query.get_or_404(ordem_id)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4
    y = altura - 2 * cm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, y, "Recibo - Ordem de Servico")
    y -= 0.8 * cm

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"OS #{ordem.id}")
    c.drawRightString(largura - 2 * cm, y, f"Data: {ordem.data_entrada.strftime('%d/%m/%Y')}")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Cliente")
    y -= 0.6 * cm
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Nome: {ordem.cliente.nome}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Telefone: {ordem.cliente.telefone or '-'}")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Equipamento")
    y -= 0.6 * cm
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, ordem.equipamento)
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Defeito relatado: {ordem.defeito_relatado[:90]}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Status: {ordem.status}")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Itens do orcamento")
    y -= 0.7 * cm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(2 * cm, y, "Descricao")
    c.drawString(10 * cm, y, "Qtd")
    c.drawString(12 * cm, y, "Valor unit.")
    c.drawString(15.5 * cm, y, "Total")
    y -= 0.4 * cm
    c.line(2 * cm, y, largura - 2 * cm, y)
    y -= 0.5 * cm

    c.setFont("Helvetica", 9)
    for item in ordem.itens:
        c.drawString(2 * cm, y, item.descricao[:45])
        c.drawString(10 * cm, y, str(item.quantidade))
        c.drawString(12 * cm, y, f"R$ {item.valor_unitario:.2f}")
        c.drawString(15.5 * cm, y, f"R$ {item.valor_total:.2f}")
        y -= 0.5 * cm
        if y < 3 * cm:
            c.showPage()
            y = altura - 2 * cm

    y -= 0.5 * cm
    c.line(2 * cm, y, largura - 2 * cm, y)
    y -= 0.7 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(largura - 2 * cm, y, f"Total: R$ {ordem.total:.2f}")

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"recibo_os_{ordem.id}.pdf",
    )


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Product, Purchase, Sale, StockMovement
from .services import DomainError, dashboard_summary, register_purchase, register_sale


bp = Blueprint("main", __name__)


def parse_money_to_cents(raw: str) -> int:
    normalized = raw.strip().replace("R$", "").replace(" ", "")
    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    try:
        value = Decimal(normalized).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise DomainError("Informe um valor monetário válido.") from exc
    if value < 0:
        raise DomainError("O valor monetário não pode ser negativo.")
    return int(value * 100)


def parse_optional_datetime(raw: str | None) -> datetime:
    if not raw:
        return datetime.now()
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise DomainError("Informe uma data e hora válidas.") from exc


@bp.app_template_filter("money")
def format_money(cents: int) -> str:
    value = Decimal(cents) / Decimal(100)
    formatted = f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"


@bp.route("/")
def dashboard():
    return render_template("dashboard.html", summary=dashboard_summary())


@bp.route("/products", methods=["GET", "POST"])
def products():
    if request.method == "POST":
        try:
            product = Product(
                name=request.form.get("name", "").strip(),
                sku=request.form.get("sku", "").strip().upper(),
                price_cents=parse_money_to_cents(request.form.get("price", "")),
                cost_cents=parse_money_to_cents(request.form.get("cost", "0")),
                current_stock=int(request.form.get("current_stock", "0")),
                minimum_stock=int(request.form.get("minimum_stock", "0")),
            )
            if not product.name or not product.sku:
                raise DomainError("Nome e SKU são obrigatórios.")
            if product.current_stock < 0 or product.minimum_stock < 0:
                raise DomainError("Os valores de estoque não podem ser negativos.")
            db.session.add(product)
            db.session.flush()
            if product.current_stock:
                db.session.add(
                    StockMovement(
                        product_id=product.id,
                        movement_type="opening",
                        quantity_delta=product.current_stock,
                        stock_after=product.current_stock,
                        reference_type="product",
                        reference_id=product.id,
                    )
                )
            db.session.commit()
            flash("Produto cadastrado com sucesso.", "success")
            return redirect(url_for("main.products"))
        except (DomainError, ValueError) as exc:
            db.session.rollback()
            flash(str(exc), "error")
        except IntegrityError:
            db.session.rollback()
            flash("Já existe um produto com esse SKU.", "error")

    product_list = list(db.session.scalars(select(Product).order_by(Product.name)))
    return render_template("products.html", products=product_list)


@bp.route("/purchases", methods=["GET", "POST"])
def purchases():
    if request.method == "POST":
        try:
            register_purchase(
                product_id=int(request.form.get("product_id", "0")),
                quantity=int(request.form.get("quantity", "0")),
                unit_cost_cents=parse_money_to_cents(request.form.get("unit_cost", "")),
                supplier=request.form.get("supplier", ""),
                occurred_at=parse_optional_datetime(request.form.get("occurred_at")),
            )
            flash("Compra registrada e estoque atualizado.", "success")
            return redirect(url_for("main.purchases"))
        except (DomainError, ValueError) as exc:
            flash(str(exc), "error")

    product_list = list(
        db.session.scalars(select(Product).where(Product.active.is_(True)).order_by(Product.name))
    )
    purchase_list = list(
        db.session.scalars(select(Purchase).order_by(Purchase.occurred_at.desc()).limit(30))
    )
    return render_template(
        "purchases.html", products=product_list, purchases=purchase_list
    )


@bp.route("/sales", methods=["GET", "POST"])
def sales():
    product_list = list(
        db.session.scalars(select(Product).where(Product.active.is_(True)).order_by(Product.name))
    )
    if request.method == "POST":
        try:
            lines = [
                (product.id, int(request.form.get(f"quantity_{product.id}", "0") or 0))
                for product in product_list
            ]
            sale = register_sale(
                lines=lines,
                channel=request.form.get("channel", "store"),
                occurred_at=parse_optional_datetime(request.form.get("occurred_at")),
            )
            flash(f"Venda #{sale.id} registrada com sucesso.", "success")
            return redirect(url_for("main.sales"))
        except (DomainError, ValueError) as exc:
            flash(str(exc), "error")

    sale_list = list(
        db.session.scalars(select(Sale).order_by(Sale.occurred_at.desc()).limit(30))
    )
    return render_template("sales.html", products=product_list, sales=sale_list)


@bp.route("/stock")
def stock():
    movements = list(
        db.session.scalars(
            select(StockMovement).order_by(StockMovement.occurred_at.desc()).limit(80)
        )
    )
    return render_template("stock.html", movements=movements)


@bp.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "service": "LojaFlux"})


@bp.route("/api/dashboard")
def api_dashboard():
    summary = dashboard_summary()
    return jsonify(
        {
            "day": summary["day"].isoformat(),
            "sales_count": summary["sales_count"],
            "revenue_cents": summary["revenue_cents"],
            "profit_cents": summary["profit_cents"],
            "ticket_cents": summary["ticket_cents"],
            "low_stock": [
                {
                    "id": product.id,
                    "name": product.name,
                    "current_stock": product.current_stock,
                    "minimum_stock": product.minimum_stock,
                }
                for product in summary["low_stock"]
            ],
            "last_seven_days": [
                {
                    "date": item["date"].isoformat(),
                    "revenue_cents": item["revenue_cents"],
                }
                for item in summary["chart"]
            ],
        }
    )


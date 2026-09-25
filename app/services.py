from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from .extensions import db
from .models import Product, Purchase, PurchaseItem, Sale, SaleItem, StockMovement


class DomainError(ValueError):
    """Erro de regra de negócio que pode ser exibido para a pessoa usuária."""


def register_purchase(
    *,
    product_id: int,
    quantity: int,
    unit_cost_cents: int,
    supplier: str,
    occurred_at: datetime | None = None,
) -> Purchase:
    if quantity <= 0:
        raise DomainError("A quantidade da compra deve ser maior que zero.")
    if unit_cost_cents < 0:
        raise DomainError("O custo unitário não pode ser negativo.")
    if not supplier.strip():
        raise DomainError("Informe o fornecedor.")

    product = db.session.get(Product, product_id)
    if product is None or not product.active:
        raise DomainError("Produto não encontrado ou inativo.")

    moment = occurred_at or datetime.now()
    try:
        total_cents = quantity * unit_cost_cents
        purchase = Purchase(
            supplier=supplier.strip(), total_cents=total_cents, occurred_at=moment
        )
        db.session.add(purchase)
        db.session.flush()

        db.session.add(
            PurchaseItem(
                purchase_id=purchase.id,
                product_id=product.id,
                product_name=product.name,
                quantity=quantity,
                unit_cost_cents=unit_cost_cents,
                total_cents=total_cents,
            )
        )

        product.cost_cents = unit_cost_cents
        product.current_stock += quantity
        db.session.add(
            StockMovement(
                product_id=product.id,
                movement_type="purchase",
                quantity_delta=quantity,
                stock_after=product.current_stock,
                reference_type="purchase",
                reference_id=purchase.id,
                occurred_at=moment,
            )
        )
        db.session.commit()
        return purchase
    except Exception:
        db.session.rollback()
        raise


def register_sale(
    *,
    lines: list[tuple[int, int]],
    channel: str,
    occurred_at: datetime | None = None,
) -> Sale:
    allowed_channels = {"store", "delivery", "social"}
    if channel not in allowed_channels:
        raise DomainError("Canal de venda inválido.")

    consolidated: dict[int, int] = defaultdict(int)
    for product_id, quantity in lines:
        if quantity < 0:
            raise DomainError("A quantidade vendida não pode ser negativa.")
        if quantity > 0:
            consolidated[product_id] += quantity

    if not consolidated:
        raise DomainError("Selecione pelo menos um produto para a venda.")

    products = {
        product.id: product
        for product in db.session.scalars(
            select(Product).where(Product.id.in_(consolidated.keys()))
        )
    }
    if len(products) != len(consolidated):
        raise DomainError("Um dos produtos selecionados não existe.")

    for product_id, quantity in consolidated.items():
        product = products[product_id]
        if not product.active:
            raise DomainError(f"O produto {product.name} está inativo.")
        if product.current_stock < quantity:
            raise DomainError(
                f"Estoque insuficiente para {product.name}: disponível {product.current_stock}."
            )

    moment = occurred_at or datetime.now()
    try:
        total_cents = sum(
            products[product_id].price_cents * quantity
            for product_id, quantity in consolidated.items()
        )
        cost_total_cents = sum(
            products[product_id].cost_cents * quantity
            for product_id, quantity in consolidated.items()
        )
        sale = Sale(
            channel=channel,
            total_cents=total_cents,
            cost_total_cents=cost_total_cents,
            occurred_at=moment,
        )
        db.session.add(sale)
        db.session.flush()

        for product_id, quantity in consolidated.items():
            product = products[product_id]
            line_total = product.price_cents * quantity
            line_cost = product.cost_cents * quantity
            db.session.add(
                SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    product_name=product.name,
                    quantity=quantity,
                    unit_price_cents=product.price_cents,
                    unit_cost_cents=product.cost_cents,
                    total_cents=line_total,
                    cost_total_cents=line_cost,
                )
            )
            product.current_stock -= quantity
            db.session.add(
                StockMovement(
                    product_id=product.id,
                    movement_type="sale",
                    quantity_delta=-quantity,
                    stock_after=product.current_stock,
                    reference_type="sale",
                    reference_id=sale.id,
                    occurred_at=moment,
                )
            )

        db.session.commit()
        return sale
    except Exception:
        db.session.rollback()
        raise


def dashboard_summary(target_day: date | None = None) -> dict:
    target_day = target_day or date.today()
    start = datetime.combine(target_day, time.min)
    end = start + timedelta(days=1)

    sales_today = list(
        db.session.scalars(
            select(Sale)
            .where(Sale.status == "completed")
            .where(Sale.occurred_at >= start, Sale.occurred_at < end)
            .order_by(Sale.occurred_at.desc())
        )
    )
    revenue = sum(sale.total_cents for sale in sales_today)
    profit = sum(sale.estimated_profit_cents for sale in sales_today)
    ticket = revenue // len(sales_today) if sales_today else 0

    low_stock = list(
        db.session.scalars(
            select(Product)
            .where(Product.active.is_(True))
            .where(Product.current_stock <= Product.minimum_stock)
            .order_by(Product.current_stock.asc(), Product.name.asc())
        )
    )

    chart = []
    for offset in range(6, -1, -1):
        current_day = target_day - timedelta(days=offset)
        day_start = datetime.combine(current_day, time.min)
        day_end = day_start + timedelta(days=1)
        daily_sales = list(
            db.session.scalars(
                select(Sale)
                .where(Sale.status == "completed")
                .where(Sale.occurred_at >= day_start, Sale.occurred_at < day_end)
            )
        )
        chart.append(
            {
                "date": current_day,
                "label": current_day.strftime("%d/%m"),
                "revenue_cents": sum(sale.total_cents for sale in daily_sales),
            }
        )

    return {
        "day": target_day,
        "sales_count": len(sales_today),
        "revenue_cents": revenue,
        "profit_cents": profit,
        "ticket_cents": ticket,
        "low_stock": low_stock,
        "recent_sales": sales_today[:8],
        "chart": chart,
    }


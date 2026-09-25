from datetime import datetime

import pytest

from app.extensions import db
from app.models import Product, SaleItem, StockMovement
from app.services import DomainError, dashboard_summary, register_purchase, register_sale


def make_product(**overrides):
    values = {
        "name": "Produto teste",
        "sku": "TEST-1",
        "price_cents": 1500,
        "cost_cents": 500,
        "current_stock": 10,
        "minimum_stock": 3,
    }
    values.update(overrides)
    product = Product(**values)
    db.session.add(product)
    db.session.commit()
    return product


def test_purchase_updates_cost_stock_and_audit_trail(app):
    with app.app_context():
        product = make_product(current_stock=4, cost_cents=300)

        purchase = register_purchase(
            product_id=product.id,
            quantity=6,
            unit_cost_cents=420,
            supplier="Fornecedor teste",
        )

        db.session.refresh(product)
        movement = db.session.query(StockMovement).one()
        assert purchase.total_cents == 2520
        assert product.cost_cents == 420
        assert product.current_stock == 10
        assert movement.quantity_delta == 6
        assert movement.stock_after == 10


def test_sale_is_atomic_and_keeps_price_and_cost_snapshots(app):
    with app.app_context():
        first = make_product(name="Primeiro", sku="P-1", current_stock=5)
        second = make_product(
            name="Segundo",
            sku="P-2",
            price_cents=800,
            cost_cents=200,
            current_stock=8,
        )

        sale = register_sale(
            lines=[(first.id, 2), (second.id, 3)],
            channel="store",
            occurred_at=datetime.now(),
        )

        assert sale.total_cents == 5400
        assert sale.cost_total_cents == 1600
        assert first.current_stock == 3
        assert second.current_stock == 5

        first.price_cents = 9999
        first.cost_cents = 7777
        db.session.commit()
        snapshot = db.session.query(SaleItem).filter_by(product_id=first.id).one()
        assert snapshot.unit_price_cents == 1500
        assert snapshot.unit_cost_cents == 500


def test_sale_rejects_insufficient_stock_without_partial_changes(app):
    with app.app_context():
        first = make_product(name="Primeiro", sku="P-1", current_stock=1)
        second = make_product(name="Segundo", sku="P-2", current_stock=10)

        with pytest.raises(DomainError, match="Estoque insuficiente"):
            register_sale(
                lines=[(first.id, 2), (second.id, 2)],
                channel="delivery",
            )

        assert first.current_stock == 1
        assert second.current_stock == 10
        assert db.session.query(StockMovement).count() == 0


def test_dashboard_calculates_daily_indicators(app):
    with app.app_context():
        product = make_product(current_stock=10, minimum_stock=8)
        register_sale(lines=[(product.id, 2)], channel="social")

        summary = dashboard_summary()

        assert summary["sales_count"] == 1
        assert summary["revenue_cents"] == 3000
        assert summary["profit_cents"] == 2000
        assert summary["ticket_cents"] == 3000
        assert [item.name for item in summary["low_stock"]] == ["Produto teste"]


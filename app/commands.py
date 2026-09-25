from __future__ import annotations

from datetime import datetime, timedelta

import click
from flask import Flask

from .extensions import db
from .models import Product
from .services import register_purchase, register_sale


def register_commands(app: Flask) -> None:
    @app.cli.command("seed-demo")
    def seed_demo() -> None:
        """Cria uma base fictícia para demonstração visual."""
        if db.session.query(Product).count():
            click.echo("A base já possui produtos; nenhuma demonstração foi criada.")
            return

        products = [
            Product(name="Açaí 500 ml", sku="ACAI-500", price_cents=2290, cost_cents=840, minimum_stock=8),
            Product(name="Vitamina de banana", sku="VIT-BAN", price_cents=1490, cost_cents=510, minimum_stock=6),
            Product(name="Pão de queijo", sku="PAO-QJO", price_cents=650, cost_cents=240, minimum_stock=12),
            Product(name="Água mineral", sku="AGUA-500", price_cents=400, cost_cents=160, minimum_stock=10),
        ]
        db.session.add_all(products)
        db.session.commit()

        for product, quantity in zip(products, [60, 40, 80, 48], strict=True):
            register_purchase(
                product_id=product.id,
                quantity=quantity,
                unit_cost_cents=product.cost_cents,
                supplier="Fornecedor demonstração",
                occurred_at=datetime.now() - timedelta(days=8),
            )

        demo_sales = [
            (6, [(0, 2), (2, 3)]),
            (5, [(1, 2), (3, 2)]),
            (4, [(0, 3), (2, 2)]),
            (3, [(0, 1), (1, 2), (3, 1)]),
            (2, [(2, 5), (3, 2)]),
            (1, [(0, 2), (1, 1)]),
            (0, [(0, 3), (2, 4), (3, 2)]),
        ]
        channels = ["store", "delivery", "social"]
        for index, (days_ago, items) in enumerate(demo_sales):
            register_sale(
                lines=[(products[product_index].id, quantity) for product_index, quantity in items],
                channel=channels[index % len(channels)],
                occurred_at=datetime.now() - timedelta(days=days_ago, hours=2),
            )

        click.echo("Base de demonstração criada com dados fictícios.")


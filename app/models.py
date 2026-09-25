from __future__ import annotations

from datetime import datetime

from .extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(40), nullable=False, unique=True, index=True)
    price_cents = db.Column(db.Integer, nullable=False)
    cost_cents = db.Column(db.Integer, nullable=False, default=0)
    current_stock = db.Column(db.Integer, nullable=False, default=0)
    minimum_stock = db.Column(db.Integer, nullable=False, default=0)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)


class Purchase(db.Model):
    __tablename__ = "purchases"

    id = db.Column(db.Integer, primary_key=True)
    supplier = db.Column(db.String(120), nullable=False)
    total_cents = db.Column(db.Integer, nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    items = db.relationship(
        "PurchaseItem", back_populates="purchase", cascade="all, delete-orphan"
    )


class PurchaseItem(db.Model):
    __tablename__ = "purchase_items"

    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey("purchases.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost_cents = db.Column(db.Integer, nullable=False)
    total_cents = db.Column(db.Integer, nullable=False)

    purchase = db.relationship("Purchase", back_populates="items")
    product = db.relationship("Product")


class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    channel = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="completed")
    total_cents = db.Column(db.Integer, nullable=False)
    cost_total_cents = db.Column(db.Integer, nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    @property
    def estimated_profit_cents(self) -> int:
        return self.total_cents - self.cost_total_cents


class SaleItem(db.Model):
    __tablename__ = "sale_items"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price_cents = db.Column(db.Integer, nullable=False)
    unit_cost_cents = db.Column(db.Integer, nullable=False)
    total_cents = db.Column(db.Integer, nullable=False)
    cost_total_cents = db.Column(db.Integer, nullable=False)

    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product")


class StockMovement(db.Model):
    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    movement_type = db.Column(db.String(30), nullable=False)
    quantity_delta = db.Column(db.Integer, nullable=False)
    stock_after = db.Column(db.Integer, nullable=False)
    reference_type = db.Column(db.String(30), nullable=False)
    reference_id = db.Column(db.Integer, nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    product = db.relationship("Product")


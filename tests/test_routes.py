def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"service": "LojaFlux", "status": "ok"}


def test_dashboard_renders_empty_state(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "LojaFlux" in response.text
    assert "O dia ainda não tem vendas" in response.text


def test_product_can_be_created_from_form(client, app):
    response = client.post(
        "/products",
        data={
            "name": "Suco natural",
            "sku": "SUCO-1",
            "price": "12,50",
            "cost": "4,10",
            "current_stock": "7",
            "minimum_stock": "2",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Produto cadastrado com sucesso" in response.text
    assert "Suco natural" in response.text
    with app.app_context():
        from app.models import StockMovement

        movement = StockMovement.query.one()
        assert movement.movement_type == "opening"
        assert movement.quantity_delta == 7
        assert movement.stock_after == 7


def test_dashboard_api_has_stable_contract(client):
    payload = client.get("/api/dashboard").get_json()
    assert set(payload) == {
        "day",
        "sales_count",
        "revenue_cents",
        "profit_cents",
        "ticket_cents",
        "low_stock",
        "last_seven_days",
    }
    assert len(payload["last_seven_days"]) == 7


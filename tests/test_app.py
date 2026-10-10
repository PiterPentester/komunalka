from app import sessions


def test_login_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Login" in response.text or "Вхід" in response.text


def test_login_success(client):
    # Clear sessions before test
    sessions.clear()
    # We need to match the password in .env if it's loaded,
    # but for tests it's better to ensure we know what we are testing.
    # The app.py loads load_dotenv() at the top.
    import os

    user = os.environ.get("APP_USERNAME", "admin")
    pwd = os.environ.get("APP_PASSWORD", "admin")

    response = client.post(
        "/login",
        data={"username": user, "password": pwd},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert sessions.get("is_authenticated") is True


def test_login_failure(client):
    sessions.clear()
    response = client.post(
        "/login", data={"username": "admin", "password": "wrong"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert "Invalid credentials" in response.text


def test_dashboard_unauthorized(client):
    sessions.clear()
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/"


def test_dashboard_authorized(client):
    sessions["is_authenticated"] = True
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Dashboard" in response.text or "Дашборд" in response.text


def test_set_language(client):
    response = client.get("/lang/en", follow_redirects=False)
    assert response.status_code == 307
    assert response.cookies["lang"] == "en"


def test_dashboard_displays_receipts_ordered(client, db_session):
    from datetime import datetime
    from models import Receipt

    sessions["is_authenticated"] = True
    r1 = Receipt(
        receipt_number="OLD-001",
        payment_datetime=datetime(2026, 9, 1, 10, 0),
        total_amount=100.0,
        service_provider="Old Provider",
        service_type="water",
        payment_status="successful",
    )
    r2 = Receipt(
        receipt_number="NEW-001",
        payment_datetime=datetime(2026, 10, 10, 10, 31),
        total_amount=172.06,
        service_provider="New Provider",
        service_type="garbage",
        payment_status="successful",
    )
    db_session.add_all([r1, r2])
    db_session.commit()

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "172.06" in response.text
    assert "New Provider" in response.text
    assert "Old Provider" in response.text


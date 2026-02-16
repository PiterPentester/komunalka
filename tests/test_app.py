from app import sessions


def test_login_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Login" in response.text or "Вхід" in response.text


def test_login_success(client):
    # Clear sessions before test
    sessions.clear()
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert sessions.get("admin") is True


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
    sessions["admin"] = True
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Dashboard" in response.text or "Дашборд" in response.text


def test_set_language(client):
    response = client.get("/lang/en", follow_redirects=False)
    assert response.status_code == 307
    assert response.cookies["lang"] == "en"

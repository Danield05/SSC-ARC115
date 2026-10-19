import secrets


def test_login_ok_and_me(client, make_user):
    _, headers = make_user("admin@example.com", "admin")
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_login_wrong_password(client, make_user):
    make_user("admin@example.com", "admin")
    r = client.post("/auth/login", json={"email": "admin@example.com", "password": "incorrecta"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/auth/login", json={"email": "nadie@example.com", "password": "x"})
    assert r.status_code == 401


def test_protected_route_without_token(client):
    assert client.get("/users").status_code == 401
    assert client.get("/devices").status_code == 401


def test_only_admin_manages_users(client, admin, make_user):
    _, promoter = make_user("promo@example.com", "promoter")
    _, viewer = make_user("viewer@example.com", "viewer")
    body = {"email": "nuevo@example.com", "password": secrets.token_urlsafe(10), "role": "viewer"}
    assert client.post("/users", json=body, headers=promoter).status_code == 403
    assert client.post("/users", json=body, headers=viewer).status_code == 403
    assert client.get("/users", headers=viewer).status_code == 403
    assert client.post("/users", json=body, headers=admin).status_code == 201


def test_create_user_validation_and_duplicates(client, admin):
    ok = {"email": "Nuevo@Example.com", "password": secrets.token_urlsafe(10), "role": "promoter"}
    r = client.post("/users", json=ok, headers=admin)
    assert r.status_code == 201
    assert r.json()["email"] == "nuevo@example.com"
    assert "password" not in r.text
    assert client.post("/users", json=ok, headers=admin).status_code == 409
    corta = {**ok, "email": "otro@example.com", "password": "corta"}
    assert client.post("/users", json=corta, headers=admin).status_code == 422
    rol = {**ok, "email": "otro@example.com", "role": "superuser"}
    assert client.post("/users", json=rol, headers=admin).status_code == 422


def test_deactivated_user_cannot_use_existing_token(client, admin, make_user):
    password, headers = make_user("promo@example.com", "promoter")
    r = client.patch("/users/promo@example.com", json={"active": False}, headers=admin)
    assert r.status_code == 200
    assert client.get("/devices", headers=headers).status_code == 401
    login = client.post("/auth/login", json={"email": "promo@example.com", "password": password})
    assert login.status_code == 401


def test_admin_cannot_deactivate_self(client, admin):
    r = client.patch("/users/admin@example.com", json={"active": False}, headers=admin)
    assert r.status_code == 400


def test_update_unknown_user(client, admin):
    r = client.patch("/users/nadie@example.com", json={"active": False}, headers=admin)
    assert r.status_code == 404

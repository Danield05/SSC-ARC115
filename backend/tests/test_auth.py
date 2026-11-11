import secrets

from app.modules.auth import repository as auth_repository
from app.modules.notifications import service as notifications

# Contraseña generada en cada corrida: no hay credenciales escritas en el código.
NEW_PASSWORD = f"Np-{secrets.token_urlsafe(9)}"


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


def _temp_password(mail: dict) -> str:
    """La contraseña provisional va sola en una línea con sangría dentro del texto del correo."""
    for line in mail["text"].splitlines():
        if line.startswith("    ") and line.strip():
            return line.strip()
    raise AssertionError("el correo no trae contraseña provisional")


def _login(client, email, password):
    return client.post("/auth/login", json={"email": email, "password": password})


def _invite(
    client, admin, outbox, email="nuevo@example.com", role="promoter", name="Nueva Persona"
):
    r = client.post("/users", json={"email": email, "name": name, "role": role}, headers=admin)
    assert r.status_code == 201, r.text
    return r, _temp_password(outbox[-1])


def _headers(client, email, password):
    token = _login(client, email, password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_only_admin_manages_users(client, admin, make_user):
    _, promoter = make_user("promo@example.com", "promoter")
    _, viewer = make_user("viewer@example.com", "viewer")
    body = {"email": "nuevo@example.com", "role": "viewer"}
    assert client.post("/users", json=body, headers=promoter).status_code == 403
    assert client.post("/users", json=body, headers=viewer).status_code == 403
    assert client.get("/users", headers=viewer).status_code == 403
    assert client.post("/users/promo@example.com/resend-invite", headers=viewer).status_code == 403
    assert client.post("/users", json=body, headers=admin).status_code == 201


def test_invite_sends_a_temporary_password_by_email(client, admin, outbox):
    r, temp = _invite(client, admin, outbox, email="Nuevo@Example.com")
    assert r.json()["email"] == "nuevo@example.com"
    assert r.json()["role"] == "promoter"
    assert r.json()["must_change_password"] is True
    assert "password" not in r.text.replace("must_change_password", "")
    [mail] = outbox
    assert mail["to"] == "nuevo@example.com"
    assert "Nueva Persona" in mail["html"]
    assert temp in mail["html"]
    assert len(temp) == 12
    assert _login(client, "nuevo@example.com", temp).status_code == 200


def test_invite_validation_and_duplicates(client, admin, outbox):
    _invite(client, admin, outbox)
    again = {"email": "nuevo@example.com", "role": "viewer"}
    assert client.post("/users", json=again, headers=admin).status_code == 409
    bad_role = {"email": "otro@example.com", "role": "superuser"}
    assert client.post("/users", json=bad_role, headers=admin).status_code == 422
    bad_mail = {"email": "no-es-correo", "role": "viewer"}
    assert client.post("/users", json=bad_mail, headers=admin).status_code == 422
    assert len(outbox) == 1


def test_invite_html_escapes_the_name(client, admin, outbox):
    _invite(client, admin, outbox, name="<script>alert(1)</script>")
    assert "<script>" not in outbox[-1]["html"]
    assert "&lt;script&gt;" in outbox[-1]["html"]


def test_invite_rolls_back_when_the_mail_fails(client, admin, monkeypatch):
    def boom(*args, **kwargs):
        raise notifications.MailError("sin conexión")

    monkeypatch.setattr(notifications, "send_email", boom)
    body = {"email": "nuevo@example.com", "role": "viewer"}
    assert client.post("/users", json=body, headers=admin).status_code == 502
    assert [u["email"] for u in client.get("/users", headers=admin).json()] == ["admin@example.com"]


def test_temporary_password_forces_a_change_before_anything_else(client, admin, outbox):
    _, temp = _invite(client, admin, outbox)
    login = _login(client, "nuevo@example.com", temp)
    assert login.json()["user"]["must_change_password"] is True
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/auth/me", headers=headers).json()["must_change_password"] is True
    assert client.get("/patients", headers=headers).status_code == 403
    assert client.get("/devices", headers=headers).status_code == 403

    wrong = {"current_password": "incorrecta", "new_password": NEW_PASSWORD}
    assert client.post("/auth/change-password", json=wrong, headers=headers).status_code == 400
    same = {"current_password": temp, "new_password": temp}
    assert client.post("/auth/change-password", json=same, headers=headers).status_code == 400
    short = {"current_password": temp, "new_password": "corta"}
    assert client.post("/auth/change-password", json=short, headers=headers).status_code == 422

    ok = {"current_password": temp, "new_password": NEW_PASSWORD}
    r = client.post("/auth/change-password", json=ok, headers=headers)
    assert r.status_code == 200
    assert r.json()["must_change_password"] is False
    assert client.get("/patients", headers=headers).status_code == 200
    assert _login(client, "nuevo@example.com", temp).status_code == 401
    assert _login(client, "nuevo@example.com", NEW_PASSWORD).status_code == 200


def test_resend_invite_replaces_the_password_until_the_account_is_active(client, admin, outbox):
    _, first = _invite(client, admin, outbox)
    r = client.post("/users/nuevo@example.com/resend-invite", headers=admin)
    assert r.status_code == 200
    second = _temp_password(outbox[-1])
    assert second != first
    assert _login(client, "nuevo@example.com", first).status_code == 401
    headers = _headers(client, "nuevo@example.com", second)
    body = {"current_password": second, "new_password": NEW_PASSWORD}
    assert client.post("/auth/change-password", json=body, headers=headers).status_code == 200
    again = client.post("/users/nuevo@example.com/resend-invite", headers=admin)
    assert again.status_code == 409
    missing = client.post("/users/nadie@example.com/resend-invite", headers=admin)
    assert missing.status_code == 404


def test_forgot_password_gives_the_same_answer_for_any_email(client, make_user, outbox):
    make_user("promo@example.com", "promoter")
    known = client.post("/auth/forgot-password", json={"email": "promo@example.com"})
    unknown = client.post("/auth/forgot-password", json={"email": "nadie@example.com"})
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()
    assert [m["to"] for m in outbox] == ["promo@example.com"]


def test_forgot_password_flow_keeps_the_old_password_until_the_new_one_is_set(
    client, make_user, outbox
):
    old, _ = make_user("promo@example.com", "promoter")
    client.post("/auth/forgot-password", json={"email": "promo@example.com"})
    temp = _temp_password(outbox[-1])
    # pedir el reinicio no bloquea la cuenta: la contraseña de siempre sigue valiendo
    assert _login(client, "promo@example.com", old).json()["user"]["must_change_password"] is False

    login = _login(client, "promo@example.com", temp)
    assert login.status_code == 200
    assert login.json()["user"]["must_change_password"] is True
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/patients", headers=headers).status_code == 403
    body = {"current_password": temp, "new_password": NEW_PASSWORD}
    assert client.post("/auth/change-password", json=body, headers=headers).status_code == 200
    assert client.get("/patients", headers=headers).status_code == 200
    assert _login(client, "promo@example.com", old).status_code == 401
    assert _login(client, "promo@example.com", temp).status_code == 401
    assert _login(client, "promo@example.com", NEW_PASSWORD).status_code == 200


def test_forgot_password_has_a_cooldown(client, make_user, outbox):
    make_user("promo@example.com", "promoter")
    for _ in range(3):
        client.post("/auth/forgot-password", json={"email": "promo@example.com"})
    assert len(outbox) == 1


def test_forgot_password_ignores_inactive_users(client, admin, make_user, outbox):
    make_user("promo@example.com", "promoter")
    client.patch("/users/promo@example.com", json={"active": False}, headers=admin)
    client.post("/auth/forgot-password", json={"email": "promo@example.com"})
    assert outbox == []


def test_temporary_password_from_forgot_expires(client, make_user, outbox):
    make_user("promo@example.com", "promoter")
    client.post("/auth/forgot-password", json={"email": "promo@example.com"})
    temp = _temp_password(outbox[-1])
    auth_repository.update_user("promo@example.com", {"reset_expires": "2020-01-01T00:00:00Z"})
    assert _login(client, "promo@example.com", temp).status_code == 401


def test_admin_assigns_and_changes_roles(client, admin, make_user):
    _, promoter = make_user("promo@example.com", "promoter")
    assert client.get("/users", headers=promoter).status_code == 403
    r = client.patch("/users/promo@example.com", json={"role": "admin"}, headers=admin)
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
    # el cambio aplica de inmediato, aunque el token sea anterior
    assert client.get("/users", headers=promoter).status_code == 200
    bad = client.patch("/users/promo@example.com", json={"role": "root"}, headers=admin)
    assert bad.status_code == 422


def test_admin_cannot_change_own_role(client, admin):
    r = client.patch("/users/admin@example.com", json={"role": "viewer"}, headers=admin)
    assert r.status_code == 400


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


def test_only_admin_edits_user_name(client, admin, make_user):
    _, promoter = make_user("promo@example.com", "promoter")
    denied = client.patch("/users/promo@example.com", json={"name": "Otro"}, headers=promoter)
    assert denied.status_code == 403
    r = client.patch("/users/promo@example.com", json={"name": "  Ana Pérez "}, headers=admin)
    assert r.status_code == 200
    assert r.json()["name"] == "Ana Pérez"
    assert r.json()["role"] == "promoter"


def test_admin_changes_user_email_and_reinvites(client, admin, make_user, outbox):
    make_user("promo@example.com", "promoter")
    r = client.patch("/users/promo@example.com", json={"email": "nuevo@example.com"}, headers=admin)
    assert r.status_code == 200
    assert r.json()["email"] == "nuevo@example.com"
    assert r.json()["must_change_password"] is True
    assert outbox[-1]["to"] == "nuevo@example.com"
    emails = [u["email"] for u in client.get("/users", headers=admin).json()]
    assert "promo@example.com" not in emails
    assert "nuevo@example.com" in emails


def test_change_email_conflicts_and_self(client, admin, make_user):
    make_user("a@example.com", "promoter")
    make_user("b@example.com", "viewer")
    dup = client.patch("/users/a@example.com", json={"email": "b@example.com"}, headers=admin)
    assert dup.status_code == 409
    me = client.get("/auth/me", headers=admin).json()["email"]
    own = client.patch(f"/users/{me}", json={"email": "otro@example.com"}, headers=admin)
    assert own.status_code == 400

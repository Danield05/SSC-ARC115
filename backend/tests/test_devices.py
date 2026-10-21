from app.core.security import verify_api_key
from app.modules.devices import repository

NEW = {"device_id": "ESP32-GP03-02", "name": "Segundo", "promoter_email": "promo@example.com"}


def test_create_device_returns_key_once_and_stores_only_hash(client, admin):
    r = client.post("/devices", json=NEW, headers=admin)
    assert r.status_code == 201
    api_key = r.json()["api_key"]
    stored = repository.get_device("ESP32-GP03-02")
    assert api_key not in str(stored)
    assert verify_api_key(api_key, stored["api_key_hash"])
    listed = client.get("/devices", headers=admin)
    assert "api_key" not in listed.text
    assert "api_key_hash" not in listed.text


def test_create_device_duplicate_and_validation(client, admin):
    assert client.post("/devices", json=NEW, headers=admin).status_code == 201
    assert client.post("/devices", json=NEW, headers=admin).status_code == 409
    mala = {**NEW, "device_id": "con espacios"}
    assert client.post("/devices", json=mala, headers=admin).status_code == 422


def test_only_admin_changes_devices(client, admin, make_user):
    client.post("/devices", json=NEW, headers=admin)
    _, viewer = make_user("viewer@example.com", "viewer")
    _, promoter = make_user("promo@example.com", "promoter")
    for headers in (viewer, promoter):
        assert client.post("/devices", json=NEW, headers=headers).status_code == 403
        r = client.patch("/devices/ESP32-GP03-02", json={"active": False}, headers=headers)
        assert r.status_code == 403
        r = client.post("/devices/ESP32-GP03-02/rotate-key", headers=headers)
        assert r.status_code == 403


def test_visibility_by_role(client, admin, make_user):
    client.post("/devices", json=NEW, headers=admin)
    otro = {**NEW, "device_id": "ESP32-GP03-03", "promoter_email": "otro@example.com"}
    client.post("/devices", json=otro, headers=admin)
    _, promoter = make_user("promo@example.com", "promoter")
    _, viewer = make_user("viewer@example.com", "viewer")
    ids = lambda h: [d["device_id"] for d in client.get("/devices", headers=h).json()]  # noqa: E731
    assert ids(admin) == ["ESP32-GP03-02", "ESP32-GP03-03"]
    assert ids(viewer) == ["ESP32-GP03-02", "ESP32-GP03-03"]
    assert ids(promoter) == ["ESP32-GP03-02"]


def test_update_and_rotate(client, admin):
    api_key = client.post("/devices", json=NEW, headers=admin).json()["api_key"]
    r = client.patch(
        "/devices/ESP32-GP03-02", json={"active": False, "name": "Renombrado"}, headers=admin
    )
    assert r.status_code == 200
    assert r.json()["active"] is False
    assert r.json()["name"] == "Renombrado"
    new_key = client.post("/devices/ESP32-GP03-02/rotate-key", headers=admin).json()["api_key"]
    assert new_key != api_key
    stored = repository.get_device("ESP32-GP03-02")
    assert verify_api_key(new_key, stored["api_key_hash"])
    assert not verify_api_key(api_key, stored["api_key_hash"])


def test_unknown_device(client, admin):
    assert client.patch("/devices/NOPE", json={"active": True}, headers=admin).status_code == 404
    assert client.post("/devices/NOPE/rotate-key", headers=admin).status_code == 404

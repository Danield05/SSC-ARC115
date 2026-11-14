"""Borrado por el administrador: pacientes, historial, usuarios, dispositivos y bandeja."""

import boto3
import pytest

from .test_measurements import PATIENT, batch, device, patient_row, record, stored  # noqa: F401
from .test_unassigned import KEY, anon

DEVICE_ID = "ESP32-GP03-01"
PROMOTER = "promo@example.com"


@pytest.fixture
def promoter(make_user):
    return make_user(PROMOTER, "promoter")[1]


@pytest.fixture
def viewer(make_user):
    return make_user("viewer@example.com", "viewer")[1]


@pytest.fixture
def filled(client, device):  # noqa: F811
    """El paciente P-0042 con dos mediciones."""
    client.post("/measurements", json=batch(record(1), record(2)), headers=device)


def patients_table():
    return boto3.resource("dynamodb").Table("patients")


# ---------- historial ----------


def test_delete_history_keeps_the_patient_and_clears_activity(client, admin, filled):
    r = client.delete(f"/patients/{PATIENT}/measurements", headers=admin)
    assert r.status_code == 200
    assert r.json() == {"deleted": 2}
    assert stored() == []
    row = patient_row()
    assert not {"first_seen", "last_seen", "device_ids"} & set(row)


def test_delete_one_measurement(client, admin, filled):
    r = client.delete(f"/patients/{PATIENT}/measurements/2026-10-18T14:32:01Z", headers=admin)
    assert r.status_code == 204
    assert [m["ts"] for m in stored()] == ["2026-10-18T14:32:02Z"]
    again = client.delete(f"/patients/{PATIENT}/measurements/2026-10-18T14:32:01Z", headers=admin)
    assert again.status_code == 404


def test_delete_history_of_unknown_patient_is_404(client, admin):
    assert client.delete("/patients/P-9999/measurements", headers=admin).status_code == 404


@pytest.mark.parametrize("who", ["promoter", "viewer"])
def test_only_admin_deletes_history(client, filled, who, request):
    headers = request.getfixturevalue(who)
    assert client.delete(f"/patients/{PATIENT}/measurements", headers=headers).status_code == 403
    path = f"/patients/{PATIENT}/measurements/2026-10-18T14:32:01Z"
    assert client.delete(path, headers=headers).status_code == 403
    assert len(stored()) == 2


def test_delete_requires_login(client, filled):
    assert client.delete(f"/patients/{PATIENT}/measurements").status_code == 401
    assert client.delete(f"/patients/{PATIENT}").status_code == 401


# ---------- paciente ----------


def test_delete_patient_removes_card_and_measurements(client, admin, filled):
    r = client.delete(f"/patients/{PATIENT}", headers=admin)
    assert r.json() == {"deleted": 2}
    assert stored() == []
    assert "Item" not in patients_table().get_item(Key={"patient_code": PATIENT})
    assert client.get(f"/patients/{PATIENT}", headers=admin).status_code == 404


def test_deleted_code_is_not_reused(client, admin):
    first = client.post("/patients", json={"name": "A", "age": 30, "sex": "F"}, headers=admin)
    code = first.json()["patient_code"]
    client.delete(f"/patients/{code}", headers=admin)
    second = client.post("/patients", json={"name": "B", "age": 30, "sex": "M"}, headers=admin)
    assert second.json()["patient_code"] != code


def test_delete_patient_cancels_its_open_order(client, admin, device, filled):  # noqa: F811
    client.post(f"/devices/{DEVICE_ID}/measure", json={"patient_code": PATIENT}, headers=admin)
    client.delete(f"/patients/{PATIENT}", headers=admin)
    order = client.get(f"/devices/{DEVICE_ID}/measure", headers=admin).json()
    assert order["status"] == "cancelada"


def test_delete_patient_keeps_tray_original_so_resend_is_duplicate(client, admin, device):  # noqa: F811
    client.post("/patients", json={"name": "Ana", "age": 30, "sex": "F"}, headers=admin)
    client.post("/measurements", json=batch(anon(1)), headers=device)
    ref = {"device_id": DEVICE_ID, "ts": "2026-10-18T14:32:01Z"}
    client.post(
        "/measurements/unassigned/assign",
        json={"patient_code": "P-0001", "items": [ref]},
        headers=admin,
    )
    client.delete("/patients/P-0001", headers=admin)
    r = client.post("/measurements", json=batch(anon(1)), headers=device)
    assert r.json()["duplicates"] == ["ESP32-GP03-01-000001"]
    assert client.get("/measurements/unassigned", headers=admin).json() == []


@pytest.mark.parametrize("who", ["promoter", "viewer"])
def test_only_admin_deletes_patient(client, filled, who, request):
    headers = request.getfixturevalue(who)
    assert client.delete(f"/patients/{PATIENT}", headers=headers).status_code == 403
    assert len(stored()) == 2


# ---------- bandeja ----------


def test_delete_unassigned_rows(client, admin, device):  # noqa: F811
    client.post("/measurements", json=batch(anon(1), anon(2)), headers=device)
    items = [
        {"device_id": DEVICE_ID, "ts": "2026-10-18T14:32:01Z"},
        {"device_id": DEVICE_ID, "ts": "2026-10-18T14:32:09Z"},
    ]
    r = client.post("/measurements/unassigned/delete", json={"items": items}, headers=admin)
    assert r.json() == {
        "deleted": ["2026-10-18T14:32:01Z"],
        "not_found": ["2026-10-18T14:32:09Z"],
    }
    assert [m["ts"] for m in stored(KEY)] == ["2026-10-18T14:32:02Z"]


def test_delete_unassigned_skips_already_assigned(client, admin, device):  # noqa: F811
    client.post("/patients", json={"name": "Ana", "age": 30, "sex": "F"}, headers=admin)
    client.post("/measurements", json=batch(anon(1)), headers=device)
    ref = {"device_id": DEVICE_ID, "ts": "2026-10-18T14:32:01Z"}
    client.post(
        "/measurements/unassigned/assign",
        json={"patient_code": "P-0001", "items": [ref]},
        headers=admin,
    )
    r = client.post("/measurements/unassigned/delete", json={"items": [ref]}, headers=admin)
    assert r.json()["deleted"] == []
    assert len(stored(KEY)) == 1  # el original sigue, para que un reenvío sea duplicado


@pytest.mark.parametrize("who", ["promoter", "viewer"])
def test_only_admin_deletes_unassigned(client, device, who, request):  # noqa: F811
    headers = request.getfixturevalue(who)
    client.post("/measurements", json=batch(anon(1)), headers=device)
    body = {"items": [{"device_id": DEVICE_ID, "ts": "2026-10-18T14:32:01Z"}]}
    r = client.post("/measurements/unassigned/delete", json=body, headers=headers)
    assert r.status_code == 403
    assert len(stored(KEY)) == 1


# ---------- dispositivo ----------


def test_delete_device_removes_it_and_its_tray_but_not_patient_data(client, admin, device):  # noqa: F811
    client.post("/measurements", json=batch(record(1), anon(2)), headers=device)
    assert client.delete(f"/devices/{DEVICE_ID}", headers=admin).status_code == 204
    assert client.get("/devices", headers=admin).json() == []
    assert stored(KEY) == []
    assert len(stored()) == 1
    # Su clave ya no sirve.
    assert client.post("/measurements", json=batch(record(3)), headers=device).status_code == 401


def test_delete_unknown_device_is_404(client, admin):
    assert client.delete("/devices/ESP32-GP03-99", headers=admin).status_code == 404


@pytest.mark.parametrize("who", ["promoter", "viewer"])
def test_only_admin_deletes_device(client, device, who, request):  # noqa: F811
    headers = request.getfixturevalue(who)
    assert client.delete(f"/devices/{DEVICE_ID}", headers=headers).status_code == 403


# ---------- usuario ----------


def test_delete_user(client, admin, make_user):
    password, _ = make_user("otro@example.com", "viewer")
    assert client.delete("/users/otro@example.com", headers=admin).status_code == 204
    emails = [u["email"] for u in client.get("/users", headers=admin).json()]
    assert emails == ["admin@example.com"]
    login = client.post("/auth/login", json={"email": "otro@example.com", "password": password})
    assert login.status_code == 401


def test_deleted_user_token_stops_working(client, admin, make_user):
    _, headers = make_user("otro@example.com", "viewer")
    assert client.get("/patients", headers=headers).status_code == 200
    client.delete("/users/otro@example.com", headers=admin)
    assert client.get("/patients", headers=headers).status_code == 401


def test_admin_cannot_delete_self(client, admin):
    r = client.delete("/users/admin@example.com", headers=admin)
    assert r.status_code == 400
    assert len(client.get("/users", headers=admin).json()) == 1


def test_unknown_user_is_404(client, admin):
    assert client.delete("/users/nadie@example.com", headers=admin).status_code == 404


def test_user_with_devices_is_blocked(client, admin, promoter, device):  # noqa: F811
    r = client.delete(f"/users/{PROMOTER}", headers=admin)
    assert r.status_code == 409
    assert DEVICE_ID in r.json()["detail"]
    client.delete(f"/devices/{DEVICE_ID}", headers=admin)
    assert client.delete(f"/users/{PROMOTER}", headers=admin).status_code == 204


@pytest.mark.parametrize("who", ["promoter", "viewer"])
def test_only_admin_deletes_users(client, who, request):
    headers = request.getfixturevalue(who)
    assert client.delete("/users/admin@example.com", headers=headers).status_code == 403

"""Orden «Medir a este paciente»: la web la crea, el ESP32 la consulta y la medición la cierra."""

from datetime import UTC, datetime, timedelta

import pytest

from app.modules.devices import service as devices_service

from .test_measurements import batch, device, record, stored  # noqa: F401

DEVICE_ID = "ESP32-GP03-01"
PROMOTER = "promo@example.com"
STAGE_KEY = f"SIN-ASIGNAR#{DEVICE_ID}"


@pytest.fixture
def promoter(make_user):
    return make_user(PROMOTER, "promoter")[1]


@pytest.fixture
def patient(client, promoter):
    r = client.post("/patients", json={"name": "Ana", "age": 30, "sex": "F"}, headers=promoter)
    return r.json()["patient_code"]


@pytest.fixture
def clock(monkeypatch):
    """Reloj controlable de las órdenes: `clock.advance(minutes=3)` adelanta el tiempo."""

    class Clock:
        now = datetime(2026, 11, 12, 19, 0, 0, tzinfo=UTC)

        def advance(self, **kw):
            self.now += timedelta(**kw)

    c = Clock()
    monkeypatch.setattr(devices_service, "_now", lambda: c.now)
    return c


def order(client, headers, patient, device_id=DEVICE_ID):
    return client.post(
        f"/devices/{device_id}/measure", json={"patient_code": patient}, headers=headers
    )


def status_of(client, headers):
    return client.get(f"/devices/{DEVICE_ID}/measure", headers=headers).json()["status"]


def anon(n, **over):
    row = record(n, **over)
    row.pop("patient_code", None)
    return row


def test_create_order_is_pending_with_two_minutes(client, promoter, patient, device, clock):  # noqa: F811
    r = order(client, promoter, patient)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pendiente"
    assert body["patient_code"] == patient
    assert body["command_id"].startswith("CMD-")
    assert body["created_at"] == "2026-11-12T19:00:00Z"
    assert body["expires_at"] == "2026-11-12T19:02:00Z"


def test_device_receives_the_order_and_it_becomes_taken(client, promoter, patient, device, clock):  # noqa: F811
    created = order(client, promoter, patient).json()
    r = client.get(f"/devices/{DEVICE_ID}/command", headers=device)
    assert r.status_code == 200
    assert r.json()["command"] == {"command_id": created["command_id"], "patient_code": patient}
    assert status_of(client, promoter) == "tomada"
    # Si el aparato la pide otra vez (perdió la respuesta), recibe la misma.
    again = client.get(f"/devices/{DEVICE_ID}/command", headers=device).json()["command"]
    assert again["command_id"] == created["command_id"]


def test_poll_without_order_returns_null(client, device):  # noqa: F811
    r = client.get(f"/devices/{DEVICE_ID}/command", headers=device)
    assert r.status_code == 200
    assert r.json() == {"device_id": DEVICE_ID, "command": None}


def test_poll_requires_a_valid_device_key(client, device):  # noqa: F811
    assert client.get(f"/devices/{DEVICE_ID}/command").status_code == 401
    bad = {"x-api-key": "mala"}
    assert client.get(f"/devices/{DEVICE_ID}/command", headers=bad).status_code == 401


def test_pending_order_expires_after_two_minutes(client, promoter, patient, device, clock):  # noqa: F811
    order(client, promoter, patient)
    clock.advance(minutes=2, seconds=1)
    assert status_of(client, promoter) == "expirada"
    # Un aparato que enciende tarde no mide a nadie por equivocación.
    assert client.get(f"/devices/{DEVICE_ID}/command", headers=device).json()["command"] is None


def test_taken_order_has_five_minutes_to_measure(client, promoter, patient, device, clock):  # noqa: F811
    order(client, promoter, patient)
    clock.advance(minutes=1, seconds=50)
    client.get(f"/devices/{DEVICE_ID}/command", headers=device)  # la toma a punto de vencer
    clock.advance(minutes=4)  # 4 min después de tomarla: sigue vigente
    assert status_of(client, promoter) == "tomada"
    assert client.get(f"/devices/{DEVICE_ID}/command", headers=device).json()["command"]
    clock.advance(minutes=1, seconds=1)
    assert status_of(client, promoter) == "expirada"


def test_measurement_with_command_id_lands_on_the_patient_and_completes(
    client,
    promoter,
    patient,
    device,  # noqa: F811
    clock,
):
    created = order(client, promoter, patient).json()
    client.get(f"/devices/{DEVICE_ID}/command", headers=device)
    row = anon(1, command_id=created["command_id"])
    r = client.post("/measurements", json=batch(row), headers=device)
    assert r.json()["saved"] == ["ESP32-GP03-01-000001"]
    assert len(stored(patient)) == 1
    assert stored(STAGE_KEY) == []
    done = client.get(f"/devices/{DEVICE_ID}/measure", headers=promoter).json()
    assert done["status"] == "completada"
    assert done["ts"] == "2026-10-18T14:32:01Z"
    assert done["completed_at"] == "2026-11-12T19:00:00Z"
    # Terminada la orden, el aparato ya no recibe nada.
    assert client.get(f"/devices/{DEVICE_ID}/command", headers=device).json()["command"] is None


def test_explicit_patient_in_record_wins_over_the_order(client, promoter, patient, device, clock):  # noqa: F811
    created = order(client, promoter, patient).json()
    row = record(1, patient_code="P-0777", command_id=created["command_id"])
    client.post("/measurements", json=batch(row), headers=device)
    assert len(stored("P-0777")) == 1
    assert stored(patient) == []


def test_unknown_or_expired_command_id_goes_to_the_tray(client, promoter, patient, device, clock):  # noqa: F811
    created = order(client, promoter, patient).json()
    clock.advance(minutes=3)  # la orden se venció sin que el aparato la tomara
    client.post(
        "/measurements",
        json=batch(anon(1, command_id=created["command_id"]), anon(2, command_id="CMD-inventada")),
        headers=device,
    )
    assert len(stored(STAGE_KEY)) == 2
    assert stored(patient) == []


def test_cancel_order(client, promoter, patient, device, clock):  # noqa: F811
    order(client, promoter, patient)
    r = client.delete(f"/devices/{DEVICE_ID}/measure", headers=promoter)
    assert r.status_code == 200
    assert r.json()["status"] == "cancelada"
    assert client.get(f"/devices/{DEVICE_ID}/command", headers=device).json()["command"] is None


def test_cannot_start_another_order_while_measuring(client, promoter, patient, device, clock):  # noqa: F811
    order(client, promoter, patient)
    client.get(f"/devices/{DEVICE_ID}/command", headers=device)
    assert order(client, promoter, patient).status_code == 409
    # Si todavía está pendiente, la nueva la reemplaza.
    client.delete(f"/devices/{DEVICE_ID}/measure", headers=promoter)
    first = order(client, promoter, patient).json()
    second = order(client, promoter, patient).json()
    assert second["command_id"] != first["command_id"]


def test_expired_taken_order_does_not_block_a_new_one(client, promoter, patient, device, clock):  # noqa: F811
    order(client, promoter, patient)
    client.get(f"/devices/{DEVICE_ID}/command", headers=device)
    clock.advance(minutes=6)
    assert order(client, promoter, patient).status_code == 201


def test_status_is_null_when_there_was_never_an_order(client, promoter, device):  # noqa: F811
    r = client.get(f"/devices/{DEVICE_ID}/measure", headers=promoter)
    assert r.status_code == 200
    assert r.json() is None


def test_viewer_cannot_order_but_can_read(client, make_user, promoter, patient, device, clock):  # noqa: F811
    viewer = make_user("eval@example.com", "viewer")[1]
    assert order(client, viewer, patient).status_code == 403
    assert client.delete(f"/devices/{DEVICE_ID}/measure", headers=viewer).status_code == 403
    assert client.get(f"/devices/{DEVICE_ID}/measure", headers=viewer).status_code == 200


def test_promoter_only_orders_on_own_devices_and_visible_patients(
    client,
    make_user,
    admin,
    promoter,
    patient,
    device,  # noqa: F811
    clock,
):
    other = make_user("otro@example.com", "promoter")[1]
    assert order(client, other, patient).status_code == 404  # no es su dispositivo
    assert client.get(f"/devices/{DEVICE_ID}/measure", headers=other).status_code == 404
    assert order(client, promoter, "P-9999").status_code == 404  # paciente inexistente
    # Un paciente que registró el admin no lo ve el promotor; el admin sí puede medirlo.
    code = client.post(
        "/patients", json={"name": "C", "age": 40, "sex": "M"}, headers=admin
    ).json()["patient_code"]
    assert order(client, promoter, code).status_code == 404
    assert order(client, admin, code).status_code == 201


def test_order_for_unknown_device_is_404(client, admin, patient):
    assert order(client, admin, patient, device_id="ESP32-GP03-99").status_code == 404


def test_order_requires_login(client):
    r = client.post(f"/devices/{DEVICE_ID}/measure", json={"patient_code": "P-0001"})
    assert r.status_code == 401

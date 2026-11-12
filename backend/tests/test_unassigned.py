"""Bandeja «Sin asignar»: mediciones sin paciente que se asignan después desde la web."""

import boto3
import pytest

from .test_measurements import batch, device, record, stored  # noqa: F401

DEVICE_ID = "ESP32-GP03-01"
KEY = f"SIN-ASIGNAR#{DEVICE_ID}"
PROMOTER = "promo@example.com"


def anon(n: int, **over):
    """Un registro sin paciente, como lo manda el ESP32 sin orden."""
    row = record(n, **over)
    row.pop("patient_code", None)
    return row


@pytest.fixture
def promoter(make_user):
    return make_user(PROMOTER, "promoter")[1]


@pytest.fixture
def patient(client, promoter):
    """Un paciente creado por el promotor del dispositivo (así lo ve)."""
    r = client.post("/patients", json={"name": "Ana", "age": 30, "sex": "F"}, headers=promoter)
    return r.json()["patient_code"]


def patients_table():
    return boto3.resource("dynamodb").Table("patients")


def test_record_without_patient_goes_to_tray_and_creates_no_patient(client, device):  # noqa: F811
    r = client.post("/measurements", json=batch(anon(1)), headers=device)
    assert r.json() == {"saved": ["ESP32-GP03-01-000001"], "duplicates": []}
    items = stored(KEY)
    assert len(items) == 1
    assert items[0]["device_id"] == DEVICE_ID
    # No se inventó un paciente «SIN-ASIGNAR» ni se tocó ninguno.
    assert patients_table().scan()["Items"] == []


@pytest.mark.parametrize("value", [None, "", "  ", "SIN-ASIGNAR", "sin-asignar"])
def test_blank_or_placeholder_patient_is_unassigned(client, device, value):  # noqa: F811
    row = record(1, patient_code=value)
    r = client.post("/measurements", json=batch(row), headers=device)
    assert r.status_code == 200
    assert len(stored(KEY)) == 1


def test_resend_of_unassigned_is_duplicate(client, device):  # noqa: F811
    client.post("/measurements", json=batch(anon(1)), headers=device)
    r = client.post("/measurements", json=batch(anon(1), anon(2)), headers=device)
    assert r.json() == {"saved": ["ESP32-GP03-01-000002"], "duplicates": ["ESP32-GP03-01-000001"]}
    assert len(stored(KEY)) == 2


def test_tray_is_listed_newest_first_for_admin_and_owner(client, admin, promoter, device):  # noqa: F811
    client.post("/measurements", json=batch(anon(1), anon(2)), headers=device)
    for headers in (admin, promoter):
        rows = client.get("/measurements/unassigned", headers=headers).json()
        assert [m["ts"] for m in rows] == ["2026-10-18T14:32:02Z", "2026-10-18T14:32:01Z"]
        assert rows[0]["device_id"] == DEVICE_ID
        assert rows[0]["device_name"] == "Uno"
        assert rows[0]["weight_kg"] == 71.4


def test_other_promoter_does_not_see_the_tray(client, make_user, device):  # noqa: F811
    client.post("/measurements", json=batch(anon(1)), headers=device)
    other = make_user("otro@example.com", "promoter")[1]
    assert client.get("/measurements/unassigned", headers=other).json() == []


def test_viewer_can_read_but_not_assign(client, make_user, device, patient):  # noqa: F811
    client.post("/measurements", json=batch(anon(1)), headers=device)
    viewer = make_user("eval@example.com", "viewer")[1]
    assert len(client.get("/measurements/unassigned", headers=viewer).json()) == 1
    body = {
        "patient_code": patient,
        "items": [{"device_id": DEVICE_ID, "ts": "2026-10-18T14:32:01Z"}],
    }
    assert (
        client.post("/measurements/unassigned/assign", json=body, headers=viewer).status_code == 403
    )


def test_tray_requires_login(client):
    assert client.get("/measurements/unassigned").status_code == 401


def assign_body(patient, *seconds):
    return {
        "patient_code": patient,
        "items": [{"device_id": DEVICE_ID, "ts": f"2026-10-18T14:32:{s:02d}Z"} for s in seconds],
    }


def test_assign_moves_measurements_to_the_patient(client, promoter, patient, device):  # noqa: F811
    client.post("/measurements", json=batch(anon(1), anon(2), anon(3)), headers=device)
    r = client.post(
        "/measurements/unassigned/assign", json=assign_body(patient, 1, 2), headers=promoter
    )
    assert r.status_code == 200
    assert r.json() == {
        "assigned": ["2026-10-18T14:32:01Z", "2026-10-18T14:32:02Z"],
        "conflicts": [],
        "not_found": [],
    }
    # Quedan en el historial del paciente, con quién las asignó...
    history = client.get(f"/patients/{patient}/measurements", headers=promoter).json()["items"]
    assert [m["ts"] for m in history] == ["2026-10-18T14:32:01Z", "2026-10-18T14:32:02Z"]
    assert stored(patient)[0]["assigned_by"] == PROMOTER
    # ...y la bandeja solo conserva la que falta.
    pending = client.get("/measurements/unassigned", headers=promoter).json()
    assert [m["ts"] for m in pending] == ["2026-10-18T14:32:03Z"]
    # El paciente ya sabe de qué dispositivo y desde cuándo hay mediciones.
    row = patients_table().get_item(Key={"patient_code": patient})["Item"]
    assert row["first_seen"] == "2026-10-18T14:32:01Z"
    assert row["last_seen"] == "2026-10-18T14:32:02Z"
    assert DEVICE_ID in row["device_ids"]


def test_resend_after_assigning_is_still_a_duplicate(client, promoter, patient, device):  # noqa: F811
    client.post("/measurements", json=batch(anon(1)), headers=device)
    client.post("/measurements/unassigned/assign", json=assign_body(patient, 1), headers=promoter)
    r = client.post("/measurements", json=batch(anon(1)), headers=device)
    assert r.json() == {"saved": [], "duplicates": ["ESP32-GP03-01-000001"]}
    # No reaparece en la bandeja ni se duplica en el historial.
    assert client.get("/measurements/unassigned", headers=promoter).json() == []
    assert len(stored(patient)) == 1


def test_assigning_twice_reports_not_found(client, promoter, patient, device):  # noqa: F811
    client.post("/measurements", json=batch(anon(1)), headers=device)
    body = assign_body(patient, 1)
    client.post("/measurements/unassigned/assign", json=body, headers=promoter)
    again = client.post("/measurements/unassigned/assign", json=body, headers=promoter).json()
    assert again == {"assigned": [], "conflicts": [], "not_found": ["2026-10-18T14:32:01Z"]}


def test_same_timestamp_in_patient_is_a_conflict_and_stays_in_tray(
    client,
    promoter,
    patient,
    device,  # noqa: F811
):
    client.post("/measurements", json=batch(record(1, patient_code=patient)), headers=device)
    client.post("/measurements", json=batch(anon(1, record_id="otro-1"), anon(2)), headers=device)
    r = client.post(
        "/measurements/unassigned/assign", json=assign_body(patient, 1, 2), headers=promoter
    )
    assert r.json() == {
        "assigned": ["2026-10-18T14:32:02Z"],
        "conflicts": ["2026-10-18T14:32:01Z"],
        "not_found": [],
    }
    # La que chocó sigue en la bandeja, sin marca de asignada, para decidir qué hacer.
    pending = client.get("/measurements/unassigned", headers=promoter).json()
    assert [m["ts"] for m in pending] == ["2026-10-18T14:32:01Z"]


def test_other_promoter_cannot_assign_foreign_measurements(client, make_user, admin, device):  # noqa: F811
    client.post("/measurements", json=batch(anon(1)), headers=device)
    other = make_user("otro@example.com", "promoter")[1]
    mine = client.post("/patients", json={"name": "B", "age": 30, "sex": "M"}, headers=other)
    code = mine.json()["patient_code"]
    r = client.post("/measurements/unassigned/assign", json=assign_body(code, 1), headers=other)
    assert r.json()["not_found"] == ["2026-10-18T14:32:01Z"]
    assert r.json()["assigned"] == []
    assert len(client.get("/measurements/unassigned", headers=admin).json()) == 1


def test_assign_to_unknown_or_invisible_patient_is_404(client, admin, promoter, device):  # noqa: F811
    client.post("/measurements", json=batch(anon(1)), headers=device)
    r = client.post("/measurements/unassigned/assign", json=assign_body("P-9999", 1), headers=admin)
    assert r.status_code == 404
    # Un paciente que registró un admin no lo ve el promotor hasta que su equipo lo mida.
    code = client.post(
        "/patients", json={"name": "C", "age": 40, "sex": "M"}, headers=admin
    ).json()["patient_code"]
    r = client.post("/measurements/unassigned/assign", json=assign_body(code, 1), headers=promoter)
    assert r.status_code == 404
    # El admin sí puede asignarle.
    r = client.post("/measurements/unassigned/assign", json=assign_body(code, 1), headers=admin)
    assert r.json()["assigned"] == ["2026-10-18T14:32:01Z"]


def test_batch_mail_labels_unassigned_and_links_to_tray(client, device, outbox):  # noqa: F811
    client.post("/measurements", json=batch(anon(1, temp_c=38.6)), headers=device)
    mail = outbox[0]
    assert mail["subject"].startswith("Alerta en 1 medición")
    assert f"Sin asignar ({DEVICE_ID})" in mail["text"]
    assert "SIN-ASIGNAR#" not in mail["text"] + mail["html"]
    assert "/sin-asignar" in mail["html"]

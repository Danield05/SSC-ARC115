import boto3
import pytest

DEVICE = {"device_id": "ESP32-GP03-01", "name": "Uno", "promoter_email": "promo@example.com"}


def _batch(code="P-0001", n=1):
    return {
        "device_id": "ESP32-GP03-01",
        "records": [
            {
                "record_id": f"R-{code}-{n}",
                "patient_code": code,
                "ts": f"2026-10-18T14:32:{n:02d}Z",
                "weight_kg": 70.0,
                "temp_c": 36.5,
                "spo2": 97,
                "bpm": 75,
                "alert": False,
            }
        ],
    }


@pytest.fixture
def device_key(client, admin):
    r = client.post("/devices", json=DEVICE, headers=admin)
    return {"x-api-key": r.json()["api_key"]}


def test_create_and_list_with_name(client, admin):
    r = client.post(
        "/patients", json={"patient_code": "P-0001", "name": "  Daniel  "}, headers=admin
    )
    assert r.status_code == 201
    assert r.json()["name"] == "Daniel"
    listed = client.get("/patients", headers=admin).json()
    assert [(p["patient_code"], p["name"]) for p in listed] == [("P-0001", "Daniel")]


def test_duplicate_code_and_validation(client, admin):
    body = {"patient_code": "P-0001", "name": "Daniel"}
    assert client.post("/patients", json=body, headers=admin).status_code == 201
    assert client.post("/patients", json=body, headers=admin).status_code == 409
    for bad in (
        {"patient_code": "con espacios", "name": "X"},
        {"patient_code": "P-0002", "name": "   "},
        {"patient_code": "P-0002", "name": "x" * 81},
    ):
        assert client.post("/patients", json=bad, headers=admin).status_code == 422


def test_measurement_creates_patient_without_name_then_name_is_added(client, admin, device_key):
    client.post("/measurements", json=_batch("P-0002"), headers=device_key)
    [p] = client.get("/patients", headers=admin).json()
    assert p["patient_code"] == "P-0002"
    assert p["name"] == ""
    assert p["device_ids"] == ["ESP32-GP03-01"]
    assert p["first_seen"] == "2026-10-18T14:32:01Z"
    r = client.patch("/patients/P-0002", json={"name": "Magali"}, headers=admin)
    assert r.status_code == 200
    assert r.json()["name"] == "Magali"
    assert r.json()["first_seen"] == "2026-10-18T14:32:01Z"


def test_name_survives_later_measurements(client, admin, device_key):
    client.post("/patients", json={"patient_code": "P-0003", "name": "Alexandra"}, headers=admin)
    client.post("/measurements", json=_batch("P-0003"), headers=device_key)
    [p] = client.get("/patients", headers=admin).json()
    assert p["name"] == "Alexandra"
    assert p["last_seen"] == "2026-10-18T14:32:01Z"


def test_patch_unknown_patient_is_404(client, admin):
    r = client.patch("/patients/NO-EXISTE", json={"name": "X"}, headers=admin)
    assert r.status_code == 404


def test_viewer_reads_but_cannot_write(client, admin, make_user):
    client.post("/patients", json={"patient_code": "P-0001", "name": "Daniel"}, headers=admin)
    _, viewer = make_user("viewer@example.com", "viewer")
    assert client.get("/patients", headers=viewer).status_code == 200
    body = {"patient_code": "P-0009", "name": "X"}
    assert client.post("/patients", json=body, headers=viewer).status_code == 403
    assert client.patch("/patients/P-0001", json={"name": "Y"}, headers=viewer).status_code == 403


def test_requires_login(client):
    assert client.get("/patients").status_code == 401


def test_promoter_sees_only_own_patients(client, admin, make_user, device_key):
    _, promo = make_user("promo@example.com", "promoter")
    _, otro = make_user("otro@example.com", "promoter")
    client.post("/measurements", json=_batch("P-0001"), headers=device_key)  # equipo de promo
    client.post("/patients", json={"patient_code": "P-0050", "name": "Del otro"}, headers=otro)
    client.post("/patients", json={"patient_code": "P-0060", "name": "Ajeno"}, headers=admin)
    assert [p["patient_code"] for p in client.get("/patients", headers=promo).json()] == ["P-0001"]
    assert [p["patient_code"] for p in client.get("/patients", headers=otro).json()] == ["P-0050"]
    assert len(client.get("/patients", headers=admin).json()) == 3
    # el promotor tampoco puede renombrar pacientes ajenos
    r = client.patch("/patients/P-0060", json={"name": "Hack"}, headers=promo)
    assert r.status_code == 404
    r = client.patch("/patients/P-0001", json={"name": "Mio"}, headers=promo)
    assert r.status_code == 200


def test_touch_keeps_device_set(client, device_key):
    client.post("/measurements", json=_batch("P-0001", 1), headers=device_key)
    client.post("/measurements", json=_batch("P-0001", 2), headers=device_key)
    item = boto3.resource("dynamodb").Table("patients").get_item(Key={"patient_code": "P-0001"})
    assert item["Item"]["device_ids"] == {"ESP32-GP03-01"}

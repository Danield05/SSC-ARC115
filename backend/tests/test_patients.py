import boto3
import pytest

from app.modules.patients import repository

DEVICE = {"name": "Uno", "promoter_email": "promo@example.com"}  # recibe el id ESP32-GP03-01


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


def test_codes_are_generated_in_sequence(client, admin):
    codes = [
        client.post("/patients", json={"name": n}, headers=admin).json()["patient_code"]
        for n in ("Ana", "Beto", "Carla")
    ]
    assert codes == ["P-0001", "P-0002", "P-0003"]
    listed = client.get("/patients", headers=admin).json()
    assert [p["patient_code"] for p in listed] == codes  # el contador no aparece en la lista
    assert repository.get_patient("#counter") is None


def test_a_code_in_the_request_is_ignored(client, admin):
    r = client.post("/patients", json={"patient_code": "X-9", "name": "  Daniel  "}, headers=admin)
    assert r.status_code == 201
    assert r.json()["patient_code"] == "P-0001"
    assert r.json()["name"] == "Daniel"


def test_full_profile_is_saved_and_returned(client, admin):
    body = {
        "name": "Magali Pérez",
        "dui": "01234567-8",
        "age": 42,
        "email": "Magali@Example.com",
        "phone": "+503 7000-1234",
        "address": "Cantón El Rosario, Santa Ana",
    }
    r = client.post("/patients", json=body, headers=admin)
    assert r.status_code == 201
    p = r.json()
    assert (p["dui"], p["age"], p["email"], p["phone"]) == (
        "01234567-8",
        42,
        "magali@example.com",
        "+503 7000-1234",
    )
    assert p["address"] == "Cantón El Rosario, Santa Ana"


def test_only_the_name_is_required(client, admin):
    r = client.post("/patients", json={"name": "Solo nombre"}, headers=admin)
    assert r.status_code == 201
    p = r.json()
    assert (p["dui"], p["age"], p["email"], p["phone"], p["address"]) == ("", None, "", "", "")


def test_validation(client, admin):
    for bad in (
        {"name": "   "},
        {"name": "x" * 81},
        {"name": "A", "dui": "123"},
        {"name": "A", "age": -1},
        {"name": "A", "age": 121},
        {"name": "A", "email": "no-es-correo"},
        {"name": "A", "phone": "abc"},
        {"name": "A", "address": "x" * 201},
    ):
        assert client.post("/patients", json=bad, headers=admin).status_code == 422, bad


def test_patch_changes_only_sent_fields_and_clears_with_empty(client, admin):
    code = client.post(
        "/patients", json={"name": "Ana", "phone": "7000-0000", "age": 30}, headers=admin
    ).json()["patient_code"]
    r = client.patch(f"/patients/{code}", json={"address": "Calle 1"}, headers=admin)
    assert (r.json()["name"], r.json()["phone"], r.json()["age"]) == ("Ana", "7000-0000", 30)
    assert r.json()["address"] == "Calle 1"
    r = client.patch(f"/patients/{code}", json={"phone": "", "age": None}, headers=admin)
    assert r.json()["phone"] == ""
    assert r.json()["age"] is None
    assert r.json()["name"] == "Ana"
    assert client.patch(f"/patients/{code}", json={"name": ""}, headers=admin).status_code == 422


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


def test_generated_code_skips_one_the_device_already_created(client, admin, device_key):
    client.post("/measurements", json=_batch("P-0001"), headers=device_key)
    r = client.post("/patients", json={"name": "Nueva"}, headers=admin)
    assert r.json()["patient_code"] == "P-0002"


def test_name_survives_later_measurements(client, admin, device_key):
    code = client.post("/patients", json={"name": "Alexandra"}, headers=admin).json()[
        "patient_code"
    ]
    client.post("/measurements", json=_batch(code), headers=device_key)
    [p] = client.get("/patients", headers=admin).json()
    assert p["name"] == "Alexandra"
    assert p["last_seen"] == "2026-10-18T14:32:01Z"


def test_patch_unknown_patient_is_404(client, admin):
    r = client.patch("/patients/NO-EXISTE", json={"name": "X"}, headers=admin)
    assert r.status_code == 404
    r = client.patch("/patients/%23counter", json={"name": "X"}, headers=admin)
    assert r.status_code == 404


def test_viewer_reads_but_cannot_write(client, admin, make_user):
    client.post("/patients", json={"name": "Daniel"}, headers=admin)
    _, viewer = make_user("viewer@example.com", "viewer")
    assert client.get("/patients", headers=viewer).status_code == 200
    assert client.post("/patients", json={"name": "X"}, headers=viewer).status_code == 403
    assert client.patch("/patients/P-0001", json={"name": "Y"}, headers=viewer).status_code == 403


def test_requires_login(client):
    assert client.get("/patients").status_code == 401


def test_promoter_sees_only_own_patients(client, admin, make_user, device_key):
    _, promo = make_user("promo@example.com", "promoter")
    _, otro = make_user("otro@example.com", "promoter")
    client.post("/measurements", json=_batch("P-0001"), headers=device_key)  # equipo de promo
    del_otro = client.post("/patients", json={"name": "Del otro"}, headers=otro).json()
    ajeno = client.post("/patients", json={"name": "Ajeno"}, headers=admin).json()
    assert [p["patient_code"] for p in client.get("/patients", headers=promo).json()] == ["P-0001"]
    assert [p["patient_code"] for p in client.get("/patients", headers=otro).json()] == [
        del_otro["patient_code"]
    ]
    assert len(client.get("/patients", headers=admin).json()) == 3
    # el promotor tampoco puede editar pacientes ajenos
    r = client.patch(f"/patients/{ajeno['patient_code']}", json={"name": "Hack"}, headers=promo)
    assert r.status_code == 404
    r = client.patch("/patients/P-0001", json={"name": "Mio"}, headers=promo)
    assert r.status_code == 200


def test_touch_keeps_device_set(client, device_key):
    client.post("/measurements", json=_batch("P-0001", 1), headers=device_key)
    client.post("/measurements", json=_batch("P-0001", 2), headers=device_key)
    item = boto3.resource("dynamodb").Table("patients").get_item(Key={"patient_code": "P-0001"})
    assert item["Item"]["device_ids"] == {"ESP32-GP03-01"}

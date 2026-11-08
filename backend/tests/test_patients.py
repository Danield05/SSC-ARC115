from decimal import Decimal

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
        client.post("/patients", json={"name": n, "age": 30, "sex": "F"}, headers=admin).json()[
            "patient_code"
        ]
        for n in ("Ana", "Beto", "Carla")
    ]
    assert codes == ["P-0001", "P-0002", "P-0003"]
    listed = client.get("/patients", headers=admin).json()
    assert [p["patient_code"] for p in listed] == codes  # el contador no aparece en la lista
    assert repository.get_patient("#counter") is None


def test_a_code_in_the_request_is_ignored(client, admin):
    r = client.post(
        "/patients",
        json={"patient_code": "X-9", "name": "  Daniel  ", "age": 30, "sex": "M"},
        headers=admin,
    )
    assert r.status_code == 201
    assert r.json()["patient_code"] == "P-0001"
    assert r.json()["name"] == "Daniel"


def test_full_profile_is_saved_and_returned(client, admin):
    body = {
        "name": "Magali Pérez",
        "dui": "01234567-8",
        "age": 42,
        "sex": "F",
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


def test_name_age_and_sex_are_required(client, admin):
    r = client.post("/patients", json={"name": "Solo esto", "age": 30, "sex": "F"}, headers=admin)
    assert r.status_code == 201
    p = r.json()
    assert (p["dui"], p["email"], p["phone"], p["address"], p["height_cm"]) == (
        "",
        "",
        "",
        "",
        None,
    )
    for missing in ({"name": "A", "age": 30}, {"name": "A", "sex": "M"}, {"age": 30, "sex": "M"}):
        assert client.post("/patients", json=missing, headers=admin).status_code == 422, missing


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
        bad = {"age": 30, "sex": "F", **bad}
        assert client.post("/patients", json=bad, headers=admin).status_code == 422, bad


def test_patch_changes_only_sent_fields_and_clears_with_empty(client, admin):
    code = client.post(
        "/patients",
        json={"name": "Ana", "phone": "7000-0000", "age": 30, "sex": "F"},
        headers=admin,
    ).json()["patient_code"]
    r = client.patch(f"/patients/{code}", json={"address": "Calle 1"}, headers=admin)
    assert (r.json()["name"], r.json()["phone"], r.json()["age"]) == ("Ana", "7000-0000", 30)
    assert r.json()["address"] == "Calle 1"
    r = client.patch(f"/patients/{code}", json={"phone": ""}, headers=admin)
    assert r.json()["phone"] == ""
    assert r.json()["age"] == 30
    assert r.json()["name"] == "Ana"
    # la edad y el sexo se pueden cambiar, pero no borrar
    assert client.patch(f"/patients/{code}", json={"age": 31}, headers=admin).json()["age"] == 31
    for body in ({"age": None}, {"sex": ""}, {"sex": None}, {"sex": "X"}):
        assert client.patch(f"/patients/{code}", json=body, headers=admin).status_code == 422, body
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
    r = client.post("/patients", json={"name": "Nueva", "age": 30, "sex": "F"}, headers=admin)
    assert r.json()["patient_code"] == "P-0002"


def test_name_survives_later_measurements(client, admin, device_key):
    code = client.post(
        "/patients", json={"name": "Alexandra", "age": 30, "sex": "F"}, headers=admin
    ).json()["patient_code"]
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
    client.post("/patients", json={"name": "Daniel", "age": 30, "sex": "F"}, headers=admin)
    _, viewer = make_user("viewer@example.com", "viewer")
    assert client.get("/patients", headers=viewer).status_code == 200
    assert (
        client.post(
            "/patients", json={"name": "X", "age": 30, "sex": "F"}, headers=viewer
        ).status_code
        == 403
    )
    assert client.patch("/patients/P-0001", json={"name": "Y"}, headers=viewer).status_code == 403


def test_requires_login(client):
    assert client.get("/patients").status_code == 401


def test_promoter_sees_only_own_patients(client, admin, make_user, device_key):
    _, promo = make_user("promo@example.com", "promoter")
    _, otro = make_user("otro@example.com", "promoter")
    client.post("/measurements", json=_batch("P-0001"), headers=device_key)  # equipo de promo
    del_otro = client.post(
        "/patients", json={"name": "Del otro", "age": 30, "sex": "F"}, headers=otro
    ).json()
    ajeno = client.post(
        "/patients", json={"name": "Ajeno", "age": 30, "sex": "F"}, headers=admin
    ).json()
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


def test_create_with_sex_and_height_stores_decimal(client, admin):
    r = client.post(
        "/patients",
        json={"name": "Ana", "age": 30, "sex": "F", "height_cm": 162.46},
        headers=admin,
    )
    assert r.status_code == 201
    assert r.json()["sex"] == "F"
    assert r.json()["height_cm"] == 162.5
    stored = boto3.resource("dynamodb").Table("patients").get_item(Key={"patient_code": "P-0001"})
    assert isinstance(stored["Item"]["height_cm"], Decimal)


@pytest.mark.parametrize("body", [{"sex": "X"}, {"height_cm": 30}, {"height_cm": 300}])
def test_invalid_sex_or_height_is_422(client, admin, body):
    full = {"name": "Ana", "age": 30, "sex": "F", **body}
    assert client.post("/patients", json=full, headers=admin).status_code == 422


def test_update_and_clear_height(client, admin):
    body = {"name": "Ana", "age": 30, "sex": "F", "height_cm": 160}
    client.post("/patients", json=body, headers=admin)
    r = client.patch("/patients/P-0001", json={"height_cm": 165.5}, headers=admin)
    assert r.json()["height_cm"] == 165.5
    r = client.patch("/patients/P-0001", json={"height_cm": None}, headers=admin)
    assert r.json()["height_cm"] is None
    assert r.json()["sex"] == "F"


def test_patient_created_by_device_has_no_age_or_sex(client, admin, device_key):
    client.post("/measurements", json=_batch("P-0002"), headers=device_key)
    r = client.get("/patients/P-0002", headers=admin).json()
    assert (r["sex"], r["age"], r["height_cm"]) == ("", None, None)
    # se puede editar otro dato sin tener que mandar la edad ni el sexo
    assert client.patch("/patients/P-0002", json={"name": "Ana"}, headers=admin).status_code == 200


def test_patch_age_switches_between_dui_and_guardian(client, admin):
    code = client.post(
        "/patients",
        json={"name": "Luis", "age": 30, "sex": "M", "dui": "01234567-8"},
        headers=admin,
    ).json()["patient_code"]
    # adulto -> menor: exige responsable y borra el DUI propio
    assert client.patch(f"/patients/{code}", json={"age": 10}, headers=admin).status_code == 422
    r = client.patch(
        f"/patients/{code}",
        json={"age": 10, "guardian_name": "Ana", "guardian_dui": "76543210-1"},
        headers=admin,
    )
    assert r.status_code == 200, r.text
    assert (r.json()["dui"], r.json()["guardian_name"]) == ("", "Ana")
    # menor -> adulto: borra los datos del responsable
    r = client.patch(f"/patients/{code}", json={"age": 20}, headers=admin)
    assert r.status_code == 200, r.text
    assert (r.json()["guardian_name"], r.json()["guardian_dui"]) == ("", "")


def test_minor_requires_guardian_and_has_no_own_dui(client, admin):
    base = {"name": "Nina", "age": 9, "sex": "F"}
    assert client.post("/patients", json=base, headers=admin).status_code == 422
    r = client.post(
        "/patients",
        json={**base, "dui": "01234567-8", "guardian_name": "Ana", "guardian_dui": "76543210-1"},
        headers=admin,
    )
    assert r.status_code == 201, r.text
    p = r.json()
    assert (p["dui"], p["guardian_name"], p["guardian_dui"]) == ("", "Ana", "76543210-1")

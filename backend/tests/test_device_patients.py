import pytest

PROMO = "promo@example.com"
PATIENT = {"age": 30, "sex": "F"}


@pytest.fixture
def setup(client, admin, make_user):
    """Dos dispositivos (de dos promotores) y un paciente de cada uno."""
    promo = make_user(PROMO, "promoter")[1]
    otro = make_user("otro@example.com", "promoter")[1]
    keys = {}
    for who in (PROMO, "otro@example.com"):
        r = client.post("/devices", json={"name": who, "promoter_email": who}, headers=admin)
        keys[r.json()["device_id"]] = r.json()["api_key"]
    mine = client.post("/patients", json={"name": "Zacarías Mío", **PATIENT}, headers=promo)
    theirs = client.post("/patients", json={"name": "Beatriz Ajena", **PATIENT}, headers=otro)
    # un paciente de otro registrado por el admin tampoco debe salir
    client.post("/patients", json={"name": "Carlos Admin", **PATIENT}, headers=admin)
    return keys, mine.json()["patient_code"], theirs.json()["patient_code"]


def get(client, device_id, key):
    headers = {"x-api-key": key} if key is not None else {}
    return client.get(f"/devices/{device_id}/patients", headers=headers)


def test_returns_only_the_promoter_patients_sorted_with_server_time(client, admin, make_user):
    promo = make_user(PROMO, "promoter")[1]
    key = client.post("/devices", json={"name": "Uno", "promoter_email": PROMO}, headers=admin)
    key = key.json()["api_key"]
    for name in ("Ana", "Beto", "Carla"):
        client.post("/patients", json={"name": name, **PATIENT}, headers=promo)
    client.post("/patients", json={"name": "Del admin", **PATIENT}, headers=admin)
    r = get(client, "ESP32-GP03-01", key)
    assert r.status_code == 200
    body = r.json()
    assert body["device_id"] == "ESP32-GP03-01"
    assert body["patients"] == ["P-0001", "P-0002", "P-0003"]
    assert body["server_time"].endswith("Z") and len(body["server_time"]) == 20


def test_other_promoters_patients_are_not_listed(client, setup):
    keys, mine, theirs = setup
    first, second = sorted(keys)
    assert get(client, first, keys[first]).json()["patients"] == [mine]
    assert get(client, second, keys[second]).json()["patients"] == [theirs]


def test_response_has_no_personal_data(client, setup):
    keys, _, _ = setup
    first = sorted(keys)[0]
    text = get(client, first, keys[first]).text
    for private in ("Zacar", "Mío", "Beatriz", "Carlos", PROMO):
        assert private not in text


def test_missing_wrong_or_foreign_key_is_401(client, setup):
    keys, _, _ = setup
    first, second = sorted(keys)
    assert get(client, first, None).status_code == 401
    assert get(client, first, "clave-mala").status_code == 401
    assert get(client, first, keys[second]).status_code == 401
    assert get(client, "ESP32-GP03-99", keys[first]).status_code == 401


def test_inactive_device_is_401(client, admin, setup):
    keys, _, _ = setup
    first = sorted(keys)[0]
    client.patch(f"/devices/{first}", json={"active": False}, headers=admin)
    assert get(client, first, keys[first]).status_code == 401


def test_jwt_is_not_a_substitute_for_the_device_key(client, admin, setup):
    keys, _, _ = setup
    first = sorted(keys)[0]
    r = client.get(f"/devices/{first}/patients", headers=admin)
    assert r.status_code == 401

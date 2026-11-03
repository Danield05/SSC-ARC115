import pytest

DEVICE = {"name": "Uno", "promoter_email": "promo@example.com"}  # recibe ESP32-GP03-01


def _record(code, n, temp=36.5, spo2=97, ts=None):
    return {
        "record_id": f"R-{code}-{n}",
        "patient_code": code,
        "ts": ts or f"2026-10-{n:02d}T14:00:00Z",
        "weight_kg": 70.0 + n,
        "temp_c": temp,
        "spo2": spo2,
        "bpm": 70 + n,
        "alert": False,
    }


@pytest.fixture
def send(client, admin):
    key = client.post("/devices", json=DEVICE, headers=admin).json()["api_key"]

    def _send(*records):
        body = {"device_id": "ESP32-GP03-01", "records": list(records)}
        return client.post("/measurements", json=body, headers={"x-api-key": key})

    return _send


def _history(client, headers, code="P-0001", **params):
    return client.get(f"/patients/{code}/measurements", params=params, headers=headers)


def test_history_is_sorted_oldest_first_with_thresholds(client, admin, send):
    send(_record("P-0001", 3), _record("P-0001", 1), _record("P-0001", 2))
    r = _history(client, admin)
    assert r.status_code == 200
    body = r.json()
    assert body["patient_code"] == "P-0001"
    assert [i["ts"] for i in body["items"]] == [
        "2026-10-01T14:00:00Z",
        "2026-10-02T14:00:00Z",
        "2026-10-03T14:00:00Z",
    ]
    assert body["thresholds"] == {"temp_low_c": 35.0, "temp_high_c": 38.0, "spo2_min": 92}
    first = body["items"][0]
    assert (first["temp_c"], first["spo2"], first["bpm"], first["weight_kg"]) == (
        36.5,
        97,
        71,
        71.0,
    )


def test_history_filters_by_range(client, admin, send):
    send(*[_record("P-0001", n) for n in range(1, 8)])
    r = _history(client, admin, **{"from": "2026-10-03T00:00:00Z", "to": "2026-10-05T23:59:59Z"})
    assert [i["ts"][:10] for i in r.json()["items"]] == [
        "2026-10-03",
        "2026-10-04",
        "2026-10-05",
    ]
    only_from = _history(client, admin, **{"from": "2026-10-06T00:00:00Z"})
    assert len(only_from.json()["items"]) == 2
    only_to = _history(client, admin, to="2026-10-02T23:59:59Z")
    assert len(only_to.json()["items"]) == 2


def test_history_only_returns_that_patient(client, admin, send):
    send(_record("P-0001", 1), _record("P-0002", 2))
    items = _history(client, admin, code="P-0002").json()["items"]
    assert [i["record_id"] for i in items] == ["R-P-0002-2"]


def test_alert_is_recalculated_by_the_server(client, admin, send):
    send(_record("P-0001", 1, temp=39.0), _record("P-0001", 2, spo2=90), _record("P-0001", 3))
    alerts = [i["alert"] for i in _history(client, admin).json()["items"]]
    assert alerts == [True, True, False]


def test_empty_history_for_a_patient_without_measurements(client, admin):
    client.post("/patients", json={"name": "Sin datos", "age": 30, "sex": "F"}, headers=admin)
    r = _history(client, admin)
    assert r.status_code == 200
    assert r.json()["items"] == []


def test_unknown_patient_and_bad_ranges(client, admin, send):
    assert _history(client, admin, code="NO-EXISTE").status_code == 404
    send(_record("P-0001", 1))
    swapped = _history(
        client, admin, **{"from": "2026-10-09T00:00:00Z", "to": "2026-10-01T00:00:00Z"}
    )
    assert swapped.status_code == 422
    assert _history(client, admin, **{"from": "no-es-fecha"}).status_code == 422


def test_requires_login(client, send):
    send(_record("P-0001", 1))
    assert client.get("/patients/P-0001/measurements").status_code == 401


def test_viewer_can_read_history(client, admin, make_user, send):
    send(_record("P-0001", 1))
    _, viewer = make_user("viewer@example.com", "viewer")
    assert len(_history(client, viewer).json()["items"]) == 1


def test_promoter_only_sees_history_of_own_patients(client, admin, make_user, send):
    _, promo = make_user("promo@example.com", "promoter")
    _, otro = make_user("otro@example.com", "promoter")
    send(_record("P-0001", 1))  # lo midió el equipo de promo
    assert len(_history(client, promo).json()["items"]) == 1
    # otro promotor no puede ver ese historial: responde como si no existiera
    assert _history(client, otro).status_code == 404
    # un paciente que el otro promotor registró es suyo
    mine = client.post(
        "/patients", json={"name": "Mio", "age": 30, "sex": "F"}, headers=otro
    ).json()["patient_code"]
    assert _history(client, otro, code=mine).status_code == 200
    assert _history(client, promo, code=mine).status_code == 404


def test_get_single_patient_respects_visibility(client, admin, make_user, send):
    send(_record("P-0001", 1))
    _, promo = make_user("promo@example.com", "promoter")
    _, otro = make_user("otro@example.com", "promoter")
    assert client.get("/patients/P-0001", headers=promo).json()["patient_code"] == "P-0001"
    assert client.get("/patients/P-0001", headers=otro).status_code == 404
    assert client.get("/patients/%23counter", headers=admin).status_code == 404


def test_history_includes_bmi_per_measurement(client, admin, send):
    client.post(
        "/patients",
        json={"name": "Ana", "age": 40, "sex": "F", "height_cm": 170},
        headers=admin,
    )
    send(_record("P-0001", 1), _record("P-0001", 20))  # 71 kg y 90 kg
    body = _history(client, admin).json()
    assert (body["height_cm"], body["sex"], body["age"]) == (170, "F", 40)
    assert [i["bmi"] for i in body["items"]] == [24.6, 31.1]


def test_history_without_height_has_no_bmi(client, admin, send):
    client.post("/patients", json={"name": "Ana", "age": 30, "sex": "F"}, headers=admin)
    send(_record("P-0001", 1))
    body = _history(client, admin).json()
    assert body["height_cm"] is None
    assert body["items"][0]["bmi"] is None


def test_history_bmi_category_for_a_child_uses_who_tables(client, admin, send):
    client.post(
        "/patients",
        json={"name": "Nino", "age": 10, "sex": "M", "height_cm": 140},
        headers=admin,
    )
    send(_record("P-0001", 1))  # 71 kg y 140 cm -> IMC 36.2
    item = _history(client, admin).json()["items"][0]
    assert item["bmi"] == 36.2
    assert item["bmi_category"] == "Obesidad"


def test_history_adult_category_and_missing_data(client, admin, send):
    client.post(
        "/patients", json={"name": "Ana", "age": 40, "sex": "F", "height_cm": 170}, headers=admin
    )
    send(_record("P-0001", 1))
    assert _history(client, admin).json()["items"][0]["bmi_category"] == "Normal"

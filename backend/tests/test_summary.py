import pytest

PROMO = "promo@example.com"
PATIENT = {"age": 40, "sex": "F", "height_cm": 170}


@pytest.fixture
def send(client, admin):
    key = client.post("/devices", json={"name": "Uno", "promoter_email": PROMO}, headers=admin)

    def _send(*records):
        body = {"device_id": "ESP32-GP03-01", "records": list(records)}
        return client.post("/measurements", json=body, headers={"x-api-key": key.json()["api_key"]})

    return _send


def rec(day, weight=70.0, temp=36.5, spo2=97, bpm=70, hour=12):
    return {
        "record_id": f"R-{day}-{hour}",
        "patient_code": "P-0001",
        "ts": f"2026-10-{day:02d}T{hour:02d}:00:00Z",
        "weight_kg": weight,
        "temp_c": temp,
        "spo2": spo2,
        "bpm": bpm,
        "alert": False,
    }


def summary(client, headers, code="P-0001"):
    return client.get(f"/patients/{code}/summary", headers=headers)


def test_summary_of_a_patient_with_data(client, admin, send):
    client.post("/patients", json={"name": "Ana", **PATIENT}, headers=admin)
    # peso 72, 71, 70 en días seguidos; la última tiene temperatura de alerta
    send(rec(1, 72.0), rec(2, 71.0), rec(3, 70.0, temp=38.5))
    r = summary(client, admin)
    assert r.status_code == 200
    s = r.json()
    assert s["count"] == 3
    assert (s["first_ts"], s["last_ts"]) == ("2026-10-01T12:00:00Z", "2026-10-03T12:00:00Z")
    assert s["latest"] == {
        "ts": "2026-10-03T12:00:00Z",
        "weight_kg": 70.0,
        "temp_c": 38.5,
        "spo2": 97,
        "bpm": 70,
    }
    assert s["bmi"] == {"value": 24.2, "category": "Normal", "height_cm": 170.0}
    assert s["weight_change"] == {"vs_first_kg": -2.0, "vs_first_pct": -2.8, "vs_previous_kg": -1.0}
    assert s["trend"]["weight_kg"] == {"per_day": -1.0, "label": "baja"}
    assert s["windows"]["7"]["n"] == 3
    assert s["windows"]["7"]["weight_kg"] == {"avg": 71.0, "min": 70.0, "max": 72.0}
    assert set(s["windows"]) == {"7", "30", "90"}
    assert s["alert_pct"] == pytest.approx(33.3)
    assert s["correlation"]["temp_bpm"] is None  # menos de 10 mediciones


def test_windows_end_at_the_last_measurement(client, admin, send):
    client.post("/patients", json={"name": "Ana", **PATIENT}, headers=admin)
    send(rec(1), rec(10), rec(14), rec(20))
    windows = summary(client, admin).json()["windows"]
    assert (windows["7"]["n"], windows["30"]["n"], windows["90"]["n"]) == (2, 4, 4)


def test_correlation_with_ten_or_more_measurements(client, admin, send):
    client.post("/patients", json={"name": "Ana", **PATIENT}, headers=admin)
    send(*[rec(d, temp=36 + d * 0.1, bpm=60 + d * 2) for d in range(1, 13)])
    c = summary(client, admin).json()["correlation"]["temp_bpm"]
    assert c == {"r": 1.0, "n": 12}


def test_summary_without_height_keeps_the_rest(client, admin, send):
    client.post("/patients", json={"name": "Ana", "age": 40, "sex": "F"}, headers=admin)
    send(rec(1))
    s = summary(client, admin).json()
    assert s["bmi"] is None
    assert s["count"] == 1
    assert s["weight_change"] == {"vs_first_kg": None, "vs_first_pct": None, "vs_previous_kg": None}
    assert s["trend"]["weight_kg"] is None


def test_summary_of_a_patient_without_measurements(client, admin):
    client.post("/patients", json={"name": "Ana", **PATIENT}, headers=admin)
    s = summary(client, admin).json()
    assert s["count"] == 0
    assert all(s[k] is None for k in ("latest", "bmi", "windows", "trend", "alert_pct"))
    assert "NaN" not in summary(client, admin).text


def test_roles_and_missing_patient(client, admin, make_user, send):
    promo = make_user(PROMO, "promoter")[1]
    otro = make_user("otro@example.com", "promoter")[1]
    viewer = make_user("viewer@example.com", "viewer")[1]
    client.post("/patients", json={"name": "Ana", **PATIENT}, headers=promo)
    send(rec(1))
    assert summary(client, promo).status_code == 200
    assert summary(client, viewer).status_code == 200
    assert summary(client, otro).status_code == 404
    assert summary(client, admin, "P-9999").status_code == 404
    assert client.get("/patients/P-0001/summary").status_code in (401, 403)

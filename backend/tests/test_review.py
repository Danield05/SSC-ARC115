import io

import pytest
from openpyxl import load_workbook

DEVICE = {"name": "Uno", "promoter_email": "promo@example.com"}  # recibe ESP32-GP03-01
ALERT_TS = "2026-10-02T14:00:00Z"
NORMAL_TS = "2026-10-01T14:00:00Z"


def _record(n, temp=36.5, spo2=97):
    return {
        "record_id": f"R-{n}",
        "patient_code": "P-0001",
        "ts": f"2026-10-{n:02d}T14:00:00Z",
        "weight_kg": 70.0,
        "temp_c": temp,
        "spo2": spo2,
        "bpm": 72,
        "alert": False,
    }


@pytest.fixture
def send(client, admin):
    key = client.post("/devices", json=DEVICE, headers=admin).json()["api_key"]

    def _send(*records):
        body = {"device_id": "ESP32-GP03-01", "records": list(records)}
        return client.post("/measurements", json=body, headers={"x-api-key": key})

    return _send


@pytest.fixture
def data(send):
    # el día 2 tiene fiebre (alerta); el día 1 es normal
    send(_record(1), _record(2, temp=39.0))


def review(client, headers, ts=ALERT_TS, code="P-0001", **body):
    body = {"status": "confirmada", **body}
    return client.patch(f"/patients/{code}/measurements/{ts}/review", json=body, headers=headers)


def history_items(client, headers):
    return client.get("/patients/P-0001/measurements", headers=headers).json()["items"]


def test_review_is_saved_and_shown_in_history(client, admin, data):
    r = review(client, admin, status="falso_positivo", note="  Sensor mal puesto  ")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "falso_positivo"
    assert body["note"] == "Sensor mal puesto"
    assert body["reviewed_by"] == "admin@example.com"
    assert body["reviewed_at"].endswith("Z")
    items = history_items(client, admin)
    assert items[0]["review"] is None
    assert items[1]["review"] == body


def test_review_can_be_changed(client, admin, data):
    review(client, admin, status="confirmada")
    review(client, admin, status="artefacto", note="Lectura aislada")
    saved = history_items(client, admin)[1]["review"]
    assert (saved["status"], saved["note"]) == ("artefacto", "Lectura aislada")


def test_note_is_optional_and_limited_to_200_characters(client, admin, data):
    assert review(client, admin).json()["note"] == ""
    assert review(client, admin, note="x" * 200).status_code == 200
    assert review(client, admin, note="x" * 201).status_code == 422


def test_unknown_status_and_bad_timestamp_are_rejected(client, admin, data):
    assert review(client, admin, status="dudosa").status_code == 422
    assert review(client, admin, ts="no-es-fecha").status_code == 422


def test_only_alerts_can_be_reviewed(client, admin, data):
    assert review(client, admin, ts=NORMAL_TS).status_code == 409
    assert history_items(client, admin)[0]["review"] is None


def test_unknown_measurement_and_patient(client, admin, data):
    assert review(client, admin, ts="2026-10-09T14:00:00Z").status_code == 404
    assert review(client, admin, code="NO-EXISTE").status_code == 404


def test_requires_login(client, data):
    r = client.patch(
        f"/patients/P-0001/measurements/{ALERT_TS}/review", json={"status": "confirmada"}
    )
    assert r.status_code == 401


def test_viewer_can_read_but_not_review(client, admin, make_user, data):
    review(client, admin, status="confirmada")
    viewer = make_user("viewer@example.com", "viewer")[1]
    assert review(client, viewer).status_code == 403
    assert history_items(client, viewer)[1]["review"]["status"] == "confirmada"


def test_promoter_reviews_only_own_patients(client, admin, make_user, data):
    promo = make_user("promo@example.com", "promoter")[1]
    otro = make_user("otro@example.com", "promoter")[1]
    ok = review(client, promo, status="artefacto")
    assert ok.status_code == 200
    assert ok.json()["reviewed_by"] == "promo@example.com"
    assert review(client, otro).status_code == 404
    assert history_items(client, admin)[1]["review"]["status"] == "artefacto"


def test_exports_include_only_the_label(client, admin, data):
    review(client, admin, status="falso_positivo", note="Dato privado de la nota")
    csv = client.get("/patients/P-0001/export", params={"format": "csv"}, headers=admin)
    rows = csv.content.decode("utf-8-sig").strip().split("\r\n")
    assert [r.split(",")[-1] for r in rows] == ["Revisión", "", "Falso positivo"]
    assert "Dato privado" not in csv.text
    assert "admin@example.com" not in csv.text

    xlsx = client.get("/patients/P-0001/export", headers=admin)
    sheet = load_workbook(io.BytesIO(xlsx.content))["Mediciones"]
    assert sheet["I1"].value == "Revisión"
    assert sheet["I2"].value in (None, "")
    assert sheet["I3"].value == "Falso positivo"

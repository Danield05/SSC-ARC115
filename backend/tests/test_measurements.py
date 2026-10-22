import boto3
import pytest
from boto3.dynamodb.conditions import Key

PATIENT = "P-0042"


@pytest.fixture
def device(client, admin):
    r = client.post(
        "/devices",
        json={"name": "Uno", "promoter_email": "promo@example.com"},
        headers=admin,
    )
    return {"x-api-key": r.json()["api_key"]}


def record(n: int, **over):
    base = {
        "record_id": f"ESP32-GP03-01-{n:06d}",
        "patient_code": PATIENT,
        "ts": f"2026-10-18T14:32:{n:02d}Z",
        "weight_kg": 71.4,
        "temp_c": 36.8,
        "spo2": 97,
        "bpm": 78,
        "alert": False,
    }
    return {**base, **over}


def batch(*records):
    return {"device_id": "ESP32-GP03-01", "records": list(records)}


def stored(patient=PATIENT):
    table = boto3.resource("dynamodb").Table("measurements")
    return table.query(KeyConditionExpression=Key("patient_code").eq(patient))["Items"]


def patient_row():
    table = boto3.resource("dynamodb").Table("patients")
    return table.get_item(Key={"patient_code": PATIENT})["Item"]


def test_saves_batch_and_registers_patient(client, device):
    r = client.post("/measurements", json=batch(record(1), record(2)), headers=device)
    assert r.status_code == 200
    assert r.json() == {
        "saved": ["ESP32-GP03-01-000001", "ESP32-GP03-01-000002"],
        "duplicates": [],
    }
    items = stored()
    assert len(items) == 2
    assert items[0]["device_id"] == "ESP32-GP03-01"
    assert items[0]["ts"] == "2026-10-18T14:32:01Z"
    assert patient_row()["first_seen"] == "2026-10-18T14:32:01Z"
    assert patient_row()["last_seen"] == "2026-10-18T14:32:02Z"


def test_resend_is_reported_as_duplicate(client, device):
    client.post("/measurements", json=batch(record(1)), headers=device)
    r = client.post("/measurements", json=batch(record(1), record(2)), headers=device)
    assert r.json() == {
        "saved": ["ESP32-GP03-01-000002"],
        "duplicates": ["ESP32-GP03-01-000001"],
    }
    assert len(stored()) == 2


def test_out_of_order_batch_keeps_first_and_last_seen(client, device):
    client.post("/measurements", json=batch(record(5)), headers=device)
    client.post("/measurements", json=batch(record(9), record(1)), headers=device)
    assert patient_row()["first_seen"] == "2026-10-18T14:32:01Z"
    assert patient_row()["last_seen"] == "2026-10-18T14:32:09Z"


def test_alert_is_computed_from_thresholds(client, device):
    rows = [record(1, temp_c=38.0), record(2, temp_c=35.0), record(3, spo2=91), record(4)]
    client.post("/measurements", json=batch(*rows), headers=device)
    alerts = {i["record_id"][-1]: i["alert"] for i in stored()}
    assert alerts == {"1": True, "2": True, "3": True, "4": False}


def test_rejects_missing_wrong_or_inactive_key(client, admin, device):
    body = batch(record(1))
    assert client.post("/measurements", json=body).status_code == 401
    assert client.post("/measurements", json=body, headers={"x-api-key": "mala"}).status_code == 401
    otro = {**body, "device_id": "NO-EXISTE"}
    assert client.post("/measurements", json=otro, headers=device).status_code == 401
    client.patch("/devices/ESP32-GP03-01", json={"active": False}, headers=admin)
    assert client.post("/measurements", json=body, headers=device).status_code == 401
    assert stored() == []


def test_rotated_key_invalidates_the_old_one(client, admin, device):
    client.post("/devices/ESP32-GP03-01/rotate-key", headers=admin)
    r = client.post("/measurements", json=batch(record(1)), headers=device)
    assert r.status_code == 401


@pytest.mark.parametrize(
    "bad",
    [
        {"records": []},
        {"records": [record(1, spo2=101)]},
        {"records": [record(1, patient_code="Juan Perez")]},
        {"records": [record(1, ts="ayer")]},
        {"records": [record(1, weight_kg=-1)]},
    ],
)
def test_invalid_payload_is_422(client, device, bad):
    r = client.post("/measurements", json={"device_id": "ESP32-GP03-01", **bad}, headers=device)
    assert r.status_code == 422
    assert stored() == []

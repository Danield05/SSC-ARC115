import pytest

from app.modules.notifications import service as notifications

from .test_measurements import PATIENT, batch, device, record, stored  # noqa: F401


def test_batch_with_alert_sends_one_mail_alert_first(client, device, outbox):  # noqa: F811
    rows = [record(1), record(2, temp_c=38.6)]
    r = client.post("/measurements", json=batch(*rows), headers=device)
    assert r.status_code == 200
    assert len(outbox) == 1
    mail = outbox[0]
    assert mail["to"] == "promo@example.com"
    assert mail["subject"].startswith("Alerta en 1 mediciones")
    assert "temperatura alta" in mail["text"]
    assert mail["text"].index("ALERTAS") < mail["text"].index(f"{PATIENT}\n")
    # 14:32 UTC es 08:32 en El Salvador
    assert "18/10/2026 08:32" in mail["text"]
    assert f"/patients/{PATIENT}" in mail["html"]


def test_batch_without_alert_has_plain_subject(client, device, outbox):  # noqa: F811
    client.post("/measurements", json=batch(record(1), record(2)), headers=device)
    assert outbox[0]["subject"].startswith("Lote de ")
    assert "ALERTAS" not in outbox[0]["text"]


def test_duplicate_batch_sends_no_mail(client, device, outbox):  # noqa: F811
    client.post("/measurements", json=batch(record(1)), headers=device)
    outbox.clear()
    client.post("/measurements", json=batch(record(1)), headers=device)
    assert outbox == []


def test_mail_never_contains_patient_name(client, admin, device, outbox):  # noqa: F811
    client.post("/patients", json={"name": "Zacarías Fantasma", "dui": "01234567-8"}, headers=admin)
    code = "P-0001"
    client.post("/measurements", json=batch(record(1, patient_code=code, spo2=90)), headers=device)
    mail = outbox[0]
    for part in (mail["text"], mail["html"], mail["subject"]):
        assert "Zacar" not in part
        assert "01234567" not in part
    assert "SpO₂ baja" in mail["text"]


def test_device_flag_without_threshold_has_generic_cause(client, device, outbox):  # noqa: F811
    client.post("/measurements", json=batch(record(1, alert=True)), headers=device)
    assert "alerta del dispositivo" in outbox[0]["text"]


def test_mail_failure_still_returns_200(client, device, monkeypatch):  # noqa: F811
    def boom(*a, **k):
        raise notifications.MailError("smtp caído")

    monkeypatch.setattr(notifications, "send_email", boom)
    r = client.post("/measurements", json=batch(record(1)), headers=device)
    assert r.status_code == 200
    assert r.json()["saved"] == ["ESP32-GP03-01-000001"]
    assert len(stored()) == 1


def test_large_batch_summarizes(client, device, outbox):  # noqa: F811
    rows = [record(i % 60, ts=f"2026-10-{1 + i // 24:02d}T{i % 24:02d}:00:00Z") for i in range(60)]
    for i, row in enumerate(rows):
        row["record_id"] = f"ESP32-GP03-01-{i:06d}"
    rows[3]["temp_c"] = 39.0
    client.post("/measurements", json=batch(*rows), headers=device)
    mail = outbox[0]
    assert "60 mediciones" in mail["text"]
    assert "y 59 más" in mail["text"]
    assert "temperatura alta" in mail["text"]
    assert " kg" not in mail["text"]


@pytest.mark.parametrize(
    "codes,suffix", [(["P-0001"], "/patients/P-0001"), (["A", "B"], "/patients")]
)
def test_link_depends_on_patient_count(client, device, outbox, codes, suffix):  # noqa: F811
    rows = [record(i + 1, patient_code=c) for i, c in enumerate(codes)]
    client.post("/measurements", json=batch(*rows), headers=device)
    assert f'href="http://localhost:5173{suffix}"' in outbox[0]["html"]

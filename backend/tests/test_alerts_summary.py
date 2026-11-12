"""Resumen de alertas de los últimos 7 días para la tarjeta del dashboard."""

from datetime import UTC, datetime, timedelta

import pytest

from .test_measurements import batch, device, record  # noqa: F401

DEVICE_ID = "ESP32-GP03-01"


def when(days_ago: float) -> str:
    return (datetime.now(UTC) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def send(client, headers, *rows):
    return client.post("/measurements", json=batch(*rows), headers=headers)


def row(n, days_ago, patient="P-0001", **over):
    base = record(n, patient_code=patient, ts=when(days_ago))
    return {**base, **over}


@pytest.fixture
def promoter(make_user):
    return make_user("promo@example.com", "promoter")[1]


def summary(client, headers):
    r = client.get("/measurements/alerts-summary", headers=headers)
    assert r.status_code == 200
    return r.json()


def test_counts_alerts_and_measurements_of_the_last_week(client, admin, device):  # noqa: F811
    rows = [
        row(1, 1),
        row(2, 2, temp_c=38.6),  # alerta
        row(3, 3, spo2=90),  # alerta
        row(4, 10, temp_c=39.0),  # alerta, pero fuera de la ventana de 7 días
    ]
    send(client, device, *rows)
    s = summary(client, admin)
    assert s["days"] == 7
    assert s["measurements"] == 3
    assert s["alerts"] == 2
    assert s["unassigned_alerts"] == 0
    assert s["latest"] == {"patient_code": "P-0001", "ts": rows[1]["ts"]}


def test_latest_is_the_most_recent_alert(client, admin, device):  # noqa: F811
    send(
        client,
        device,
        row(1, 3, patient="P-0001", temp_c=38.6),
        row(2, 1, patient="P-0002", spo2=88),
    )
    latest = summary(client, admin)["latest"]
    assert latest["patient_code"] == "P-0002"


def test_unassigned_alerts_are_counted_apart(client, admin, device):  # noqa: F811
    anon = row(1, 1, temp_c=38.6)
    anon.pop("patient_code")
    send(client, device, anon, row(2, 1))
    s = summary(client, admin)
    assert s["alerts"] == 0
    assert s["unassigned_alerts"] == 1
    assert s["measurements"] == 2
    assert s["latest"] is None


def test_empty_system(client, admin):
    assert summary(client, admin) == {
        "days": 7,
        "measurements": 0,
        "alerts": 0,
        "unassigned_alerts": 0,
        "latest": None,
    }


def test_promoter_only_counts_what_they_can_see(client, make_user, admin, promoter, device):  # noqa: F811
    send(client, device, row(1, 1, temp_c=38.6))  # el dispositivo es de promo@example.com
    mine = summary(client, promoter)
    assert (mine["measurements"], mine["alerts"]) == (1, 1)
    other = make_user("otro@example.com", "promoter")[1]
    theirs = summary(client, other)
    assert (theirs["measurements"], theirs["alerts"], theirs["unassigned_alerts"]) == (0, 0, 0)


def test_viewer_sees_everything_and_login_is_required(client, make_user, admin, device):  # noqa: F811
    send(client, device, row(1, 1, temp_c=38.6))
    viewer = make_user("eval@example.com", "viewer")[1]
    assert summary(client, viewer)["alerts"] == 1
    assert client.get("/measurements/alerts-summary").status_code == 401

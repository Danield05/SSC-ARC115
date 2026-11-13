"""CORS: el navegador pregunta (preflight) antes de cada método que no es GET/POST simple.

TestClient no aplica las reglas del navegador, así que estas pruebas piden el preflight a mano.
Si un método que la web usa falta en la lista, el botón correspondiente falla en producción.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

ORIGIN = "http://localhost:5173"


@pytest.mark.parametrize("method", ["GET", "POST", "PATCH", "DELETE"])
def test_preflight_permite_los_metodos_que_usa_la_web(method):
    r = TestClient(app).options(
        "/devices/ESP32-GP03-01/measure",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert r.status_code == 200
    assert method in r.headers["access-control-allow-methods"]


def test_preflight_rechaza_otro_origen():
    r = TestClient(app).options(
        "/devices/ESP32-GP03-01/measure",
        headers={
            "Origin": "https://sitio-ajeno.example",
            "Access-Control-Request-Method": "DELETE",
        },
    )
    assert r.status_code == 400

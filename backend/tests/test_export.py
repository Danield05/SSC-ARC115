import io

import pytest
from openpyxl import load_workbook

PROMO = "promo@example.com"
NAME = "Zacarías Fantasma"
PATIENT = {"name": NAME, "age": 40, "sex": "F", "height_cm": 170, "dui": "01234567-8"}


@pytest.fixture
def send(client, admin):
    key = client.post("/devices", json={"name": "Uno", "promoter_email": PROMO}, headers=admin)

    def _send(*records):
        body = {"device_id": "ESP32-GP03-01", "records": list(records)}
        return client.post("/measurements", json=body, headers={"x-api-key": key.json()["api_key"]})

    return _send


def rec(day, weight=70.0, temp=36.5, spo2=97, bpm=70):
    return {
        "record_id": f"R-{day}",
        "patient_code": "P-0001",
        "ts": f"2026-10-{day:02d}T14:00:00Z",
        "weight_kg": weight,
        "temp_c": temp,
        "spo2": spo2,
        "bpm": bpm,
        "alert": False,
    }


@pytest.fixture
def data(client, admin, send):
    client.post("/patients", json=PATIENT, headers=admin)
    # 12 mediciones: peso baja 0,1 kg por día, temperatura y pulso suben juntos; la última, alerta
    rows = [rec(d, 72.0 - d * 0.1, 36.0 + d * 0.05, 97, 60 + d) for d in range(1, 13)]
    rows[-1]["temp_c"] = 38.6
    send(*rows)


def export(client, headers, **params):
    return client.get("/patients/P-0001/export", params=params, headers=headers)


def workbook(response, data_only=False):
    return load_workbook(io.BytesIO(response.content), data_only=data_only)


def all_text(wb):
    return " ".join(
        str(c.value) for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value
    )


def test_xlsx_has_sheets_headers_and_download_name(client, admin, data):
    r = export(client, admin)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert r.headers["content-disposition"].startswith('attachment; filename="P-0001_')
    assert r.headers["content-disposition"].endswith('.xlsx"')
    wb = workbook(r)
    assert wb.sheetnames == ["Mediciones", "Resumen", "Correlaciones", "Gráficas", "Diccionario"]
    ws = wb["Mediciones"]
    assert ws["C1"].value == "Peso (kg)"
    assert ws.max_row == 13  # encabezado + 12 mediciones
    # 14:00 UTC es 08:00 en El Salvador
    assert ws["A2"].value.hour == 8


def test_formulas_exist_and_point_to_measurements(client, admin, data):
    wb = workbook(export(client, admin))
    resumen = wb["Resumen"]
    formulas = " ".join(str(c.value) for row in resumen.iter_rows() for c in row if c.value)
    for name in ("AVERAGEIFS", "MINIFS", "MAXIFS", "SLOPE", "COUNTIFS", "INDEX"):
        assert name in formulas, name
    assert "Mediciones!$C$2:$C$13" in formulas
    assert "CORREL" in all_text(wb)
    assert wb["Mediciones"]["H2"].value.startswith("=IF(ISNUMBER(Resumen!$B$4)")


def test_cached_values_match_the_summary_panel(client, admin, data):
    summary = client.get("/patients/P-0001/summary", headers=admin).json()
    wb = workbook(export(client, admin), data_only=True)
    s = wb["Resumen"]
    assert s["B9"].value == summary["count"]
    assert s["B12"].value == summary["bmi"]["value"]
    assert s["B13"].value == summary["bmi"]["category"]
    assert s["B14"].value == summary["weight_change"]["vs_first_kg"]
    assert s["B15"].value == summary["weight_change"]["vs_first_pct"]
    assert s["B16"].value == summary["weight_change"]["vs_previous_kg"]
    assert s["B17"].value == summary["alert_pct"]
    # ventana de 7 días del peso: filas 20 (7), 21 (30), 22 (90)
    w7 = summary["windows"]["7"]
    assert s["C20"].value == w7["n"]
    assert s["D20"].value == pytest.approx(w7["weight_kg"]["avg"])
    assert s["E20"].value == pytest.approx(w7["weight_kg"]["min"])
    assert s["F20"].value == pytest.approx(w7["weight_kg"]["max"])
    # tendencia del peso
    assert s["B34"].value == pytest.approx(summary["trend"]["weight_kg"]["per_day"])
    assert s["C34"].value == summary["trend"]["weight_kg"]["label"]
    # correlación temperatura-pulso
    corr = wb["Correlaciones"]
    assert corr["E6"].value == summary["correlation"]["temp_bpm"]["r"]


def test_no_personal_data_by_default(client, admin, data):
    r = export(client, admin)
    wb = workbook(r)
    text = all_text(wb)
    for private in ("Zacar", "Fantasma", "01234567"):
        assert private not in text
    assert wb.properties.creator == "SSC-ARC115"
    assert NAME.encode() not in r.content


def test_identified_export_is_admin_only_and_includes_the_name(client, admin, make_user, data):
    wb = workbook(export(client, admin, identified="true"))
    text = all_text(wb)
    assert NAME in text and "01234567-8" in text
    promo = make_user(PROMO, "promoter")[1]
    viewer = make_user("viewer@example.com", "viewer")[1]
    for headers in (promo, viewer):
        assert export(client, headers, identified="true").status_code in (403, 404)
    assert export(client, viewer, identified="true").status_code == 403


def test_csv_has_bom_header_and_rows(client, admin, data):
    r = export(client, admin, format="csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert r.headers["content-disposition"].endswith('.csv"')
    assert r.content.startswith(b"\xef\xbb\xbf")
    lines = r.content.decode("utf-8-sig").strip().split("\r\n")
    assert lines[0] == (
        "Fecha y hora (El Salvador),Código,Peso (kg),Temperatura (°C),SpO₂ (%),"
        "Pulso (lpm),Alerta,IMC"
    )
    assert len(lines) == 13
    assert lines[-1].split(",")[6] == "Sí"
    assert NAME not in r.text


def test_roles_range_and_missing_patient(client, admin, make_user, data):
    promo = make_user(PROMO, "promoter")[1]
    otro = make_user("otro@example.com", "promoter")[1]
    # el promotor del dispositivo ve al paciente porque su equipo lo midió
    assert export(client, promo).status_code == 200
    assert export(client, otro).status_code == 404
    assert client.get("/patients/P-9999/export", headers=admin).status_code == 404
    bad = export(client, admin, **{"from": "2026-11-01T00:00:00Z", "to": "2026-10-01T00:00:00Z"})
    assert bad.status_code == 422
    assert client.get("/patients/P-0001/export").status_code in (401, 403)


def test_range_filters_the_rows(client, admin, data):
    r = export(client, admin, **{"from": "2026-10-10T00:00:00Z"})
    assert workbook(r)["Mediciones"].max_row == 4  # días 10, 11 y 12


def test_empty_patient_still_produces_a_valid_workbook(client, admin):
    client.post("/patients", json=PATIENT, headers=admin)
    r = export(client, admin)
    assert r.status_code == 200
    s = workbook(r, data_only=True)["Resumen"]
    assert s["B9"].value == 0
    assert s["B12"].value == "n/d"
    assert export(client, admin, format="csv").content.decode("utf-8-sig").count("\r\n") == 1


def test_dictionary_has_the_four_variables_and_thresholds(client, admin, data):
    d = workbook(export(client, admin))["Diccionario"]
    names = [d.cell(row=i, column=1).value for i in range(2, 6)]
    assert names == ["Peso", "Temperatura", "SpO₂", "Pulso"]
    assert "35" in d["F3"].value and "38" in d["F3"].value
    assert "92" in d["F4"].value


def test_child_category_is_written_as_text(client, admin, send):
    body = {"name": "Nino", "age": 10, "sex": "M", "height_cm": 140}
    client.post("/patients", json=body, headers=admin)
    send(rec(1, weight=71.0))
    s = workbook(export(client, admin))["Resumen"]
    assert s["B13"].value == "Obesidad"
    assert not str(s["B13"].value).startswith("=")

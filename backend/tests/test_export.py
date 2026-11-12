import csv
import io
import re
import zipfile

import pytest
from openpyxl import load_workbook

from app.core.config import get_settings
from app.modules.measurements.export import HEADERS, pseudonym

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
        "Pulso (lpm),Alerta,IMC,Revisión"
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
    body = {
        "name": "Nino",
        "age": 10,
        "sex": "M",
        "height_cm": 140,
        "guardian_name": "Madre",
        "guardian_dui": "01234567-8",
    }
    client.post("/patients", json=body, headers=admin)
    send(rec(1, weight=71.0))
    s = workbook(export(client, admin))["Resumen"]
    assert s["B13"].value == "Obesidad"
    assert not str(s["B13"].value).startswith("=")


# --- Exportación anonimizada: ID sustituto y días desde la primera medición -------------------

ALIAS = r"ANON-[0-9A-F]{8}"
DAYS = "Días desde la primera medición"


def xl_parts(response):
    """Texto de las partes del libro (hojas, gráficas, cadenas), sin las propiedades del archivo,
    que llevan la fecha de creación del archivo y no la de las mediciones."""
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        return {n: z.read(n).decode("utf-8") for n in z.namelist() if n.startswith("xl/")}


def test_pseudonym_is_stable_keyed_and_not_the_code():
    a = pseudonym("P-0001", "secreto")
    assert re.fullmatch(ALIAS, a)
    assert a == pseudonym("P-0001", "secreto")
    assert a != pseudonym("P-0002", "secreto")
    assert a != pseudonym("P-0001", "otro-secreto")
    assert "0001" not in a


def test_anonymized_xlsx_has_no_real_code_or_dates(client, admin, data):
    r = export(client, admin, anonymize="true")
    assert r.status_code == 200
    alias = pseudonym("P-0001", get_settings().jwt_secret)
    disposition = r.headers["content-disposition"]
    assert disposition == f'attachment; filename="{alias}_anonimo.xlsx"'
    wb = workbook(r)
    text = all_text(wb)
    for private in ("P-0001", "2026", "Zacar", "Fantasma", "01234567"):
        assert private not in text
    for name, content in xl_parts(r).items():
        assert "P-0001" not in content, name
        assert "2026-10" not in content, name
    assert "P-0001" not in wb.properties.title and alias in wb.properties.title
    ws = wb["Mediciones"]
    assert ws["A1"].value == DAYS
    assert ws.max_row == 13  # las mismas 12 mediciones
    assert all(ws.cell(row=i, column=2).value == alias for i in range(2, 14))
    assert ws["A2"].value == 0
    assert ws["A3"].value == pytest.approx(1)  # un día después, a la misma hora
    assert ws["A13"].value == pytest.approx(11)
    assert ws["A2"].number_format == "0.00"
    assert wb["Resumen"]["B3"].value == alias


def test_anonymized_xlsx_keeps_the_formulas_and_the_same_numbers(client, admin, data):
    plain = workbook(export(client, admin), data_only=True)
    r = export(client, admin, anonymize="true")
    anon = workbook(r, data_only=True)
    # Desde la fila 9 (mediciones, IMC, ventanas, tendencias) y en Correlaciones nada cambia.
    for sheet in ("Resumen", "Correlaciones"):
        for row_a, row_b in zip(plain[sheet].iter_rows(), anon[sheet].iter_rows(), strict=True):
            if sheet == "Resumen" and row_a[0].row < 9:
                continue
            assert [c.value for c in row_a] == [c.value for c in row_b], (sheet, row_a[0].row)
    s = anon["Resumen"]
    assert (s["A7"].value, s["B7"].value) == ("Primera medición (día)", 0)
    assert s["A8"].value == "Última medición (día)"
    assert s["B8"].value == pytest.approx(11)
    formulas = workbook(r)["Resumen"]
    assert "MIN(Mediciones!$A$2:$A$13)" in formulas["B7"].value
    text = " ".join(str(c.value) for row in formulas.iter_rows() for c in row if c.value)
    for name in ("AVERAGEIFS", "MINIFS", "MAXIFS", "SLOPE", "COUNTIFS", "INDEX"):
        assert name in text, name
    # el IMC de la hoja Mediciones sigue siendo fórmula
    assert workbook(r)["Mediciones"]["H2"].value.startswith("=IF(ISNUMBER(Resumen!$B$4)")


def test_anonymized_csv(client, admin, data):
    r = export(client, admin, format="csv", anonymize="true")
    alias = pseudonym("P-0001", get_settings().jwt_secret)
    assert r.headers["content-disposition"] == f'attachment; filename="{alias}_anonimo.csv"'
    text = r.content.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    assert len(rows) == 13
    assert rows[0][0] == DAYS
    assert rows[0][1:] == HEADERS[1:]
    assert [rows[1][0], rows[2][0], rows[12][0]] == ["0.0", "1.0", "11.0"]
    assert {row[1] for row in rows[1:]} == {alias}
    assert "P-0001" not in text and "2026" not in text


def test_anonymized_range_starts_at_day_zero_of_the_range(client, admin, data):
    r = export(client, admin, anonymize="true", **{"from": "2026-10-10T00:00:00Z"})
    ws = workbook(r)["Mediciones"]
    assert [ws.cell(row=i, column=1).value for i in (2, 3, 4)] == [0, 1, 2]
    assert workbook(r, data_only=True)["Resumen"]["B8"].value == pytest.approx(2)


def test_anonymized_empty_patient(client, admin):
    client.post("/patients", json=PATIENT, headers=admin)
    r = export(client, admin, anonymize="true")
    assert r.status_code == 200
    s = workbook(r, data_only=True)["Resumen"]
    assert (s["B7"].value, s["B8"].value, s["B9"].value) == ("n/d", "n/d", 0)
    csv_text = export(client, admin, format="csv", anonymize="true").content.decode("utf-8-sig")
    assert csv_text.count("\r\n") == 1


def test_anonymize_cannot_be_combined_with_identified(client, admin, make_user, data):
    both = export(client, admin, identified="true", anonymize="true")
    assert both.status_code == 422
    promo = make_user(PROMO, "promoter")[1]
    # un promotor ni siquiera puede pedir la identificada: 403 antes que el choque de opciones
    assert export(client, promo, identified="true", anonymize="true").status_code == 403


def test_every_role_that_sees_the_patient_can_anonymize(client, admin, make_user, data):
    promo = make_user(PROMO, "promoter")[1]
    viewer = make_user("viewer@example.com", "viewer")[1]
    otro = make_user("otro@example.com", "promoter")[1]
    for headers in (admin, promo, viewer):
        r = export(client, headers, anonymize="true")
        assert r.status_code == 200
        assert NAME.encode() not in r.content
    assert export(client, otro, anonymize="true").status_code == 404


# --- Compatibilidad con Excel, texto del paciente y gráficas ---------------------------------


def test_minifs_and_maxifs_carry_the_xlfn_prefix(client, admin, data):
    """Sin `_xlfn.` Excel da #NAME? y el IFERROR lo esconde detrás de «n/d»: la prueba lee la
    fórmula, no el valor guardado (que está bien aunque falte el prefijo)."""
    for params in ({}, {"anonymize": "true"}):
        ws = workbook(export(client, admin, **params))["Resumen"]
        assert "_xlfn.MINIFS(" in ws["E20"].value
        assert "_xlfn.MAXIFS(" in ws["F20"].value
        for row in ws.iter_rows():
            for cell in row:
                value = str(cell.value)
                for name in ("MINIFS", "MAXIFS"):
                    assert name not in value.replace(f"_xlfn.{name}", ""), cell.coordinate


def test_identified_text_is_written_as_text_never_as_a_formula(client, admin, send):
    body = {**PATIENT, "name": "=1+1", "address": '=HYPERLINK("http://example.com","clic")'}
    assert client.post("/patients", json=body, headers=admin).status_code == 201
    send(rec(1))
    s = workbook(export(client, admin, identified="true"))["Resumen"]
    wanted = ("Nombre", "Dirección")
    rows = {row[0].value: row[1] for row in s.iter_rows() if row[0].value in wanted}
    assert rows["Nombre"].value == "=1+1" and rows["Nombre"].data_type == "s"
    assert rows["Dirección"].data_type == "s"


def test_graphs_sheet_has_one_chart_per_parameter_and_the_scatter(client, admin, data):
    for params, date_axis in (({}, True), ({"anonymize": "true"}, False)):
        parts = xl_parts(export(client, admin, **params))
        charts = {n: c for n, c in parts.items() if n.startswith("xl/charts/chart")}
        assert len(charts) == 5
        titles = " ".join(charts.values())
        for expected in ("Peso en el tiempo", "Temperatura en el tiempo", "SpO₂ en el tiempo"):
            assert expected in titles
        assert "Pulso en el tiempo" in titles and "Temperatura contra pulso" in titles
        assert ("c:dateAx" in titles) is date_axis
        # Con días relativos las de líneas pasan a dispersión: el eje es numérico y proporcional
        assert titles.count("<c:lineChart>") == (4 if date_axis else 0)
        assert titles.count("<c:scatterChart>") == (1 if date_axis else 5)

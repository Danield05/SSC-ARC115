"""Exportación del historial de un paciente a Excel (.xlsx con fórmulas reales) y a CSV.

El libro se arma en memoria con XlsxWriter. Las hojas `Resumen` y `Correlaciones` usan fórmulas de
Excel (AVERAGEIFS, MINIFS, MAXIFS, SLOPE, CORREL, IMC…) que apuntan a la hoja `Mediciones`.
XlsxWriter no calcula fórmulas, así que cada una se escribe con su valor ya calculado en Python
(con las funciones de `metrics.py`, las mismas del panel de resumen): un visor que no recalcula
muestra números y no ceros. Por defecto solo lleva el código del paciente; los datos personales
entran únicamente con `identified`.
"""

import csv
import io
from datetime import datetime, timedelta

import xlsxwriter

from app.modules.measurements import metrics
from app.modules.patients.bmi import bmi_category

SV_OFFSET = timedelta(hours=-6)  # El Salvador: UTC-6, sin horario de verano
AUTHOR = "SSC-ARC115"
NA = "n/d"
YES, NO = "Sí", "No"

HEADERS = [
    "Fecha y hora (El Salvador)",
    "Código",
    "Peso (kg)",
    "Temperatura (°C)",
    "SpO₂ (%)",
    "Pulso (lpm)",
    "Alerta",
    "IMC",
]
# Columna de cada variable en la hoja Mediciones.
COLUMN = {"weight_kg": "C", "temp_c": "D", "spo2": "E", "bpm": "F"}
LABEL = {"weight_kg": "Peso", "temp_c": "Temperatura", "spo2": "SpO₂", "bpm": "Pulso"}
UNIT = {"weight_kg": "kg", "temp_c": "°C", "spo2": "%", "bpm": "lpm"}


def local_time(ts: str) -> datetime:
    """'2026-10-18T14:32:10Z' (UTC) -> hora de El Salvador, sin zona (como la guarda Excel)."""
    return metrics.parse_ts(ts) + SV_OFFSET


def excel_serial(moment: datetime | None) -> float | str:
    """Número de serie de Excel (días desde 1899-12-30) para el valor en caché de una fórmula."""
    if moment is None:
        return NA
    return (moment - datetime(1899, 12, 30)).total_seconds() / 86400


def filename(code: str, extension: str, today: datetime) -> str:
    return f"{code}_{(today + SV_OFFSET).strftime('%Y-%m-%d')}.{extension}"


def _yes_no(alert: bool) -> str:
    return YES if alert else NO


def build_csv(items: list[dict]) -> bytes:
    """CSV con las mismas columnas de la hoja Mediciones, en UTF-8 con BOM (para las tildes)."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(HEADERS)
    for m in items:
        writer.writerow(
            [
                local_time(m["ts"]).strftime("%Y-%m-%d %H:%M:%S"),
                m["patient_code"],
                float(m["weight_kg"]),
                float(m["temp_c"]),
                int(m["spo2"]),
                int(m["bpm"]),
                _yes_no(m["alert"]),
                "" if m.get("bmi") is None else m["bmi"],
            ]
        )
    return b"\xef\xbb\xbf" + out.getvalue().encode("utf-8")


def build_xlsx(
    *,
    code: str,
    age: int | None,
    sex: str,
    height_cm: float | None,
    items: list[dict],
    thresholds: dict,
    identified: dict | None = None,
) -> bytes:
    """Libro de Excel. `identified` (nombre y contacto del paciente) solo lo pasa un admin."""
    out = io.BytesIO()
    wb = xlsxwriter.Workbook(out, {"in_memory": True})
    wb.set_properties({"author": AUTHOR, "title": f"Historial de {code}", "company": AUTHOR})

    f = _formats(wb)
    n = len(items)
    last = max(n + 1, 2)  # última fila de datos (los rangos nunca quedan invertidos)

    def rng(col: str) -> str:
        return f"Mediciones!${col}$2:${col}${last}"

    dates = rng("A")

    # --- Mediciones -------------------------------------------------------------------------
    sheet = wb.add_worksheet("Mediciones")
    sheet.write_row(0, 0, HEADERS, f["header"])
    sheet.freeze_panes(1, 0)
    sheet.set_column("A:A", 24, f["datetime"])
    sheet.set_column("B:B", 12)
    sheet.set_column("C:F", 16)
    sheet.set_column("G:H", 10)
    for i, m in enumerate(items, start=1):
        sheet.write_datetime(i, 0, local_time(m["ts"]), f["datetime"])
        sheet.write(i, 1, m["patient_code"])
        sheet.write_number(i, 2, float(m["weight_kg"]), f["one"])
        sheet.write_number(i, 3, float(m["temp_c"]), f["one"])
        sheet.write_number(i, 4, int(m["spo2"]))
        sheet.write_number(i, 5, int(m["bpm"]))
        sheet.write(i, 6, _yes_no(m["alert"]))
        bmi_value = m.get("bmi")
        sheet.write_formula(
            i,
            7,
            f'=IF(ISNUMBER(Resumen!$B$4),ROUND(C{i + 1}/(Resumen!$B$4/100)^2,1),"")',
            f["one"],
            "" if bmi_value is None else bmi_value,
        )
    if n:
        sheet.conditional_format(
            1, 0, n, 7, {"type": "formula", "criteria": '=$G2="Sí"', "format": f["alert"]}
        )

    # --- Resumen ----------------------------------------------------------------------------
    s = wb.add_worksheet("Resumen")
    s.set_column("A:A", 38)
    s.set_column("B:F", 16)
    s.write("A1", f"Resumen de {code}", f["title"])
    s.write("A2", "Informativo: este sistema registra y da seguimiento; no emite diagnósticos.")

    last_weight = float(items[-1]["weight_kg"]) if items else None
    bmi_value = items[-1].get("bmi") if items else None
    s.write("A3", "Paciente")
    s.write("B3", code)
    s.write("A4", "Estatura (cm)")
    s.write("A5", "Edad (años)")
    s.write("A6", "Sexo")
    if height_cm is not None:
        s.write_number("B4", float(height_cm))
    if age is not None:
        s.write_number("B5", age)
    s.write("B6", sex)
    s.write("A7", "Primera medición")
    s.write("A8", "Última medición")
    s.write("A9", "Mediciones")
    first_dt = local_time(items[0]["ts"]) if items else None
    last_dt = local_time(items[-1]["ts"]) if items else None
    s.write_formula("B7", f'=IF(B9>0,MIN({dates}),"{NA}")', f["datetime"], excel_serial(first_dt))
    s.write_formula("B8", f'=IF(B9>0,MAX({dates}),"{NA}")', f["datetime"], excel_serial(last_dt))
    s.write_formula("B9", f"=COUNT({dates})", None, n)

    s.write("A11", "Peso más reciente (kg)")
    s.write_formula(
        "B11",
        f'=IF(B9>0,INDEX({rng("C")},B9),"{NA}")',
        f["one"],
        NA if last_weight is None else last_weight,
    )
    s.write("A12", "IMC (kg/m²)")
    s.write_formula(
        "B12",
        f'=IF(AND(ISNUMBER(B4),ISNUMBER(B11)),ROUND(B11/(B4/100)^2,1),"{NA}")',
        f["one"],
        NA if bmi_value is None else bmi_value,
    )
    s.write("A13", "Categoría del IMC")
    category = bmi_category(bmi_value, age, sex)
    if age is not None and age < 18:
        # Menores: la categoría sale de las tablas z de la OMS por edad y sexo (no de una fórmula).
        s.write("B13", category or NA)
        s.write("C13", "Tablas de la OMS (5 a 17 años), calculada por el sistema")
    else:
        s.write_formula(
            "B13",
            '=IF(AND(ISNUMBER(B12),ISNUMBER(B5),B5>=18),IF(B12<18.5,"Bajo peso",IF(B12<25,"Normal",'
            'IF(B12<30,"Sobrepeso",IF(B12<35,"Obesidad grado I",IF(B12<40,"Obesidad grado II",'
            f'"Obesidad grado III"))))),"{NA}")',
            None,
            category or NA,
        )

    change = metrics.weight_change(items) or {}

    def or_na(value):
        return NA if value is None else value

    s.write("A14", "Variación de peso vs la primera (kg)")
    s.write_formula(
        "B14",
        f'=IF(AND(ISNUMBER(B11),B9>1),ROUND(B11-INDEX({rng("C")},1),1),"{NA}")',
        f["one"],
        or_na(change.get("vs_first_kg")),
    )
    s.write("A15", "Variación de peso vs la primera (%)")
    s.write_formula(
        "B15",
        f'=IF(AND(ISNUMBER(B11),B9>1),ROUND((B11-INDEX({rng("C")},1))/INDEX({rng("C")},1)*100,1),'
        f'"{NA}")',
        f["one"],
        or_na(change.get("vs_first_pct")),
    )
    s.write("A16", "Variación de peso vs la anterior (kg)")
    s.write_formula(
        "B16",
        f'=IF(AND(ISNUMBER(B11),B9>1),ROUND(B11-INDEX({rng("C")},B9-1),1),"{NA}")',
        f["one"],
        or_na(change.get("vs_previous_kg")),
    )
    s.write("A17", "Mediciones con alerta (%)")
    s.write_formula(
        "B17",
        f'=IF(B9>0,ROUND(COUNTIF({rng("G")},"Sí")/B9*100,1),"{NA}")',
        f["one"],
        or_na(metrics.alert_percentage(items)),
    )

    s.write_row(
        "A19",
        ["Parámetro", "Ventana (días)", "Mediciones", "Promedio", "Mínimo", "Máximo"],
        f["header"],
    )
    row = 20  # fila de Excel (1-based) de la primera ventana
    for variable in metrics.VARIABLES:
        col = rng(COLUMN[variable])
        for days in metrics.WINDOW_DAYS:
            chosen = metrics.window(items, days)
            st = metrics.stats([m[variable] for m in chosen])
            criteria = f'{dates},">="&($B$8-$B{row})'
            s.write(f"A{row}", f"{LABEL[variable]} ({UNIT[variable]})")
            s.write_number(f"B{row}", days)
            s.write_formula(f"C{row}", f"=COUNTIFS({criteria})", None, len(chosen))
            for letter, func, key in (
                ("D", "AVERAGEIFS", "avg"),
                ("E", "MINIFS", "min"),
                ("F", "MAXIFS", "max"),
            ):
                inner = f"{func}({col},{criteria})"
                formula = (
                    f'=IFERROR(ROUND({inner},2),"{NA}")'
                    if key == "avg"
                    else f'=IFERROR({inner},"{NA}")'
                )
                s.write_formula(f"{letter}{row}", formula, f["two"], NA if st is None else st[key])
            row += 1

    row += 1
    s.write_row(
        f"A{row}", ["Tendencia (todo el historial)", "Pendiente por día", "Tendencia"], f["header"]
    )
    row += 1
    for variable in metrics.VARIABLES:
        points = [(metrics.parse_ts(m["ts"]), m[variable]) for m in items]
        slope = metrics.slope_per_day(points)
        rounded = None if slope is None else round(slope, 3)
        tol = metrics.TREND_TOLERANCE_PER_DAY[variable]
        s.write(f"A{row}", f"{LABEL[variable]} ({UNIT[variable]}/día)")
        s.write_formula(
            f"B{row}",
            f'=IFERROR(ROUND(SLOPE({rng(COLUMN[variable])},{dates}),3),"{NA}")',
            f["three"],
            or_na(rounded),
        )
        s.write_formula(
            f"C{row}",
            f'=IF(ISNUMBER(B{row}),IF(B{row}>{tol},"sube",IF(B{row}<-{tol},"baja","estable")),"{NA}")',
            None,
            or_na(metrics.trend_label(variable, rounded)),
        )
        row += 1

    if identified:
        row += 1
        s.write(f"A{row}", "Datos del paciente (exportación identificada)", f["header"])
        for label, key in (
            ("Nombre", "name"),
            ("DUI", "dui"),
            ("Correo", "email"),
            ("Teléfono", "phone"),
            ("Dirección", "address"),
        ):
            row += 1
            s.write(f"A{row}", label)
            s.write(f"B{row}", identified.get(key, ""))

    # --- Correlaciones ----------------------------------------------------------------------
    c = wb.add_worksheet("Correlaciones")
    c.set_column("A:A", 24)
    c.set_column("B:E", 16)
    c.write("A1", "Correlación de Pearson entre parámetros", f["title"])
    c.write("A2", f"Se calcula solo con {metrics.MIN_CORRELATION_PAIRS} o más mediciones.")
    c.write_row("A4", ["", *(LABEL[v] for v in metrics.VARIABLES)], f["header"])
    series = {v: [float(m[v]) for m in items] for v in metrics.VARIABLES}
    for i, row_var in enumerate(metrics.VARIABLES):
        r = 5 + i
        c.write(f"A{r}", LABEL[row_var], f["header"])
        for j, col_var in enumerate(metrics.VARIABLES):
            value = metrics.pearson(series[row_var], series[col_var])
            formula = (
                f"=IF(COUNT({dates})>={metrics.MIN_CORRELATION_PAIRS},"
                f'IFERROR(ROUND(CORREL({rng(COLUMN[row_var])},{rng(COLUMN[col_var])}),2),"{NA}"),"{NA}")'
            )
            c.write_formula(
                r - 1, 1 + j, formula, f["two"], NA if value is None else round(value, 2)
            )
    c.write("A10", "La correlación no implica causalidad.")

    # --- Gráficas ---------------------------------------------------------------------------
    g = wb.add_worksheet("Gráficas")
    weight_chart = wb.add_chart({"type": "line"})
    weight_chart.add_series(
        {
            "name": "Peso (kg)",
            "categories": f"=Mediciones!$A$2:$A${last}",
            "values": f"=Mediciones!$C$2:$C${last}",
        }
    )
    weight_chart.set_title({"name": f"Peso en el tiempo · {code}"})
    weight_chart.set_x_axis({"name": "Fecha", "date_axis": True, "num_format": "dd/mm"})
    weight_chart.set_y_axis({"name": "kg"})
    weight_chart.set_legend({"none": True})
    g.insert_chart("A1", weight_chart, {"x_scale": 1.6, "y_scale": 1.2})
    scatter = wb.add_chart({"type": "scatter"})
    scatter.add_series(
        {
            "name": "Mediciones",
            "categories": f"=Mediciones!$D$2:$D${last}",
            "values": f"=Mediciones!$F$2:$F${last}",
            "marker": {"type": "circle", "size": 6},
            "trendline": {"type": "linear"},
        }
    )
    scatter.set_title({"name": "Temperatura contra pulso"})
    scatter.set_x_axis({"name": "Temperatura (°C)"})
    scatter.set_y_axis({"name": "Pulso (lpm)"})
    scatter.set_legend({"none": True})
    g.insert_chart("A26", scatter, {"x_scale": 1.6, "y_scale": 1.2})

    # --- Diccionario ------------------------------------------------------------------------
    d = wb.add_worksheet("Diccionario")
    d.set_column("A:A", 16)
    d.set_column("B:B", 8)
    d.set_column("C:C", 14)
    d.set_column("D:D", 34)
    d.set_column("E:E", 18)
    d.set_column("F:F", 34)
    d.write_row(
        "A1",
        ["Variable", "Unidad", "Rango válido", "Sensor", "Resolución", "Umbral de alerta"],
        f["header"],
    )
    t = thresholds
    rows = [
        ("Peso", "kg", "0 a 500", "Celdas de carga + HX711", "0,1 kg", "Sin umbral"),
        (
            "Temperatura",
            "°C",
            "0 a 60",
            "MLX90614 (infrarrojo, sin contacto)",
            "0,02 °C",
            f"≤ {t['temp_low_c']:g} °C o ≥ {t['temp_high_c']:g} °C",
        ),
        ("SpO₂", "%", "0 a 100", "MAX30102 (oximetría)", "1 %", f"< {t['spo2_min']} %"),
        ("Pulso", "lpm", "0 a 300", "MAX30102 (oximetría)", "1 lpm", "Sin umbral"),
    ]
    for i, values in enumerate(rows, start=1):
        d.write_row(i, 0, values)

    wb.close()
    return out.getvalue()


def _formats(wb: xlsxwriter.Workbook) -> dict:
    return {
        "header": wb.add_format(
            {"bold": True, "bg_color": "#0F766E", "font_color": "#FFFFFF", "border": 1}
        ),
        "title": wb.add_format({"bold": True, "font_size": 14}),
        "datetime": wb.add_format({"num_format": "dd/mm/yyyy hh:mm", "align": "left"}),
        "one": wb.add_format({"num_format": "0.0"}),
        "two": wb.add_format({"num_format": "0.00"}),
        "three": wb.add_format({"num_format": "0.000"}),
        "alert": wb.add_format({"bg_color": "#FEE2E2", "font_color": "#9C0006"}),
    }

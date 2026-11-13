"""Plantillas de correo del proyecto: un marco común y un cuerpo por tipo de mensaje.

El HTML usa estilos en línea y tablas porque los clientes de correo (Gmail, Outlook) ignoran
casi todo el CSS externo. Cada plantilla devuelve (asunto, texto plano, html).
"""

from datetime import datetime, timedelta
from html import escape

from app.core.constants import UNASSIGNED_PREFIX, is_unassigned

BRAND = "#0f766e"
BRAND_DARK = "#115e59"
INK = "#1f2937"
MUTED = "#6b7280"
SOFT = "#f0fdfa"
WARN_BG = "#fef3c7"
WARN_INK = "#92400e"

FOOTER = (
    "SSC-ARC115 · Dispositivo de monitoreo de salud comunitario (GP03). Proyecto académico de "
    "ARC115, Universidad de El Salvador en Línea. Este sistema registra y da seguimiento; no "
    "emite diagnósticos médicos."
)


def _layout(preheader: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>SSC-ARC115</title></head>
<body style="margin:0;padding:0;background:#f3f4f6;
font-family:Segoe UI,Helvetica,Arial,sans-serif;">
<span style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(preheader)}</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="560" cellpadding="0" cellspacing="0"
 style="max-width:560px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;">
<tr><td style="background:{BRAND};padding:20px 28px;color:#ffffff;">
<div style="font-size:20px;font-weight:700;letter-spacing:.3px;">&#9829; SSC-ARC115</div>
<div style="font-size:13px;opacity:.9;margin-top:2px;">Salud comunitaria</div>
</td></tr>
<tr><td style="padding:28px;color:{INK};font-size:15px;line-height:1.55;">{body}</td></tr>
<tr><td style="padding:16px 28px 24px;border-top:1px solid #e5e7eb;color:{MUTED};
 font-size:12px;line-height:1.5;">{escape(FOOTER)}</td></tr>
</table></td></tr></table></body></html>"""


def _title(text: str) -> str:
    return f'<h1 style="margin:0 0 12px;font-size:22px;color:{BRAND_DARK};">{text}</h1>'


def _code_box(value: str) -> str:
    return (
        f'<div style="margin:18px 0;padding:14px 18px;background:{SOFT};border:1px dashed {BRAND};'
        "border-radius:8px;text-align:center;font-family:Consolas,Menlo,monospace;"
        f'font-size:22px;font-weight:700;letter-spacing:2px;color:{BRAND_DARK};">'
        f"{escape(value)}</div>"
    )


def _button(url: str, label: str) -> str:
    return (
        f'<p style="text-align:center;margin:22px 0;"><a href="{escape(url, quote=True)}" '
        f'style="background:{BRAND};color:#ffffff;text-decoration:none;padding:12px 26px;'
        f'border-radius:8px;font-weight:600;display:inline-block;">{escape(label)}</a></p>'
    )


def _notice(message: str) -> str:
    return (
        f'<div style="margin:18px 0;padding:12px 16px;background:{WARN_BG};color:{WARN_INK};'
        f'border-radius:8px;font-size:13px;">{escape(message)}</div>'
    )


def _small(message: str) -> str:
    return f'<p style="color:{MUTED};font-size:13px;">{escape(message)}</p>'


def invitation(
    name: str, email: str, role_label: str, temp_password: str, app_url: str
) -> tuple[str, str, str]:
    who = name.strip() or email
    login_url = f"{app_url.rstrip('/')}/login"
    text = (
        f"Hola {who},\n\n"
        f"El equipo de SSC-ARC115 te dio acceso al sistema con el rol: {role_label}.\n\n"
        f"Entra en {login_url} con tu correo y esta contraseña provisional:\n\n"
        f"    {temp_password}\n\n"
        "Al entrar, el sistema te pedirá crear tu propia contraseña. Con ese primer ingreso "
        "queda verificado tu correo.\n\n"
        "Si no esperabas este mensaje, ignóralo.\n\n" + FOOTER
    )
    body = (
        _title(f"¡Bienvenido, {escape(who)}!")
        + f"<p>El equipo de SSC-ARC115 te dio acceso al sistema con el rol "
        f"<strong>{escape(role_label)}</strong>.</p>"
        "<p>Para entrar usa tu correo y esta contraseña provisional:</p>"
        + _code_box(temp_password)
        + _button(login_url, "Entrar al sistema")
        + _notice(
            "Al entrar tendrás que crear tu propia contraseña. "
            "Ese primer ingreso verifica tu correo."
        )
        + _small("Si no esperabas este mensaje, puedes ignorarlo.")
    )
    return "Tu acceso a SSC-ARC115", text, _layout("Tu contraseña provisional de SSC-ARC115", body)


def password_reset(
    name: str, temp_password: str, minutes: int, app_url: str
) -> tuple[str, str, str]:
    who = name.strip() or "de nuevo"
    login_url = f"{app_url.rstrip('/')}/login"
    text = (
        f"Hola {who},\n\n"
        "Pediste recuperar tu contraseña. Esta es tu contraseña provisional:\n\n"
        f"    {temp_password}\n\n"
        f"Es válida por {minutes} minutos. Entra en {login_url} y el sistema te pedirá crear "
        "una contraseña nueva.\n\n"
        "Si no fuiste tú, ignora este mensaje: tu contraseña de siempre sigue funcionando.\n\n"
        + FOOTER
    )
    body = (
        _title("Recupera tu contraseña")
        + "<p>Pediste una contraseña nueva. Usa esta provisional para entrar:</p>"
        + _code_box(temp_password)
        + _button(login_url, "Ir a iniciar sesión")
        + _notice(
            f"Es válida por {minutes} minutos. Al entrar tendrás que crear una contraseña nueva."
        )
        + _small(
            "Si no fuiste tú, ignora este mensaje: tu contraseña de siempre sigue funcionando."
        )
    )
    return (
        "Contraseña provisional de SSC-ARC115",
        text,
        _layout("Tu contraseña provisional (válida por tiempo limitado)", body),
    )


MAX_LISTED = 50
_SV_OFFSET = timedelta(hours=-6)  # El Salvador: UTC-6, sin horario de verano


def _sv_time(ts: str) -> str:
    """'2026-10-18T14:32:10Z' (UTC) -> '18/10/2026 08:32' (hora de El Salvador)."""
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ") + _SV_OFFSET
    return dt.strftime("%d/%m/%Y %H:%M")


def alert_causes(item: dict, thresholds: dict) -> list[str]:
    causes = []
    if item["temp_c"] <= thresholds["temp_low_c"]:
        causes.append("temperatura baja")
    if item["temp_c"] >= thresholds["temp_high_c"]:
        causes.append("temperatura alta")
    if item["spo2"] < thresholds["spo2_min"]:
        causes.append("SpO₂ baja")
    # La bandera vino del ESP32 pero ningún umbral del servidor se cumple.
    return causes or ["alerta del dispositivo"]


def _alert_value(item: dict, cause: str) -> str:
    if "temperatura" in cause:
        return f"{item['temp_c']} °C"
    if "SpO₂" in cause:
        return f"{item['spo2']} %"
    return f"{item['temp_c']} °C · SpO₂ {item['spo2']} %"


def _label(patient_code: str) -> str:
    """Cómo se nombra al paciente en el correo: su código, o «Sin asignar» (y de qué aparato)
    si la medición aún no tiene paciente. Nunca el nombre."""
    if is_unassigned(patient_code):
        return f"Sin asignar ({patient_code.removeprefix(UNASSIGNED_PREFIX)})"
    return patient_code


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _history_link(app_url: str, codes: list[str]) -> tuple[str, str]:
    """Enlace y texto del botón: el historial del paciente si el lote es de uno solo, la bandeja
    «Sin asignar» si todo está sin asignar, o la lista de pacientes."""
    base = app_url.rstrip("/")
    if len(codes) == 1 and is_unassigned(codes[0]):
        return f"{base}/sin-asignar", "Abrir bandeja sin asignar"
    if len(codes) == 1:
        return f"{base}/patients/{codes[0]}", "Abrir historial"
    return f"{base}/patients", "Abrir historial"


def _alert_lines(alerts: list[dict], thresholds: dict) -> list[str]:
    return [
        f"{_label(item['patient_code'])} · {_sv_time(item['ts'])} · "
        f"{_alert_value(item, cause)} · {cause}"
        for item in alerts
        for cause in alert_causes(item, thresholds)
    ]


def _row(cells: list[str], header: bool = False) -> str:
    tag, weight = ("th", "700") if header else ("td", "400")
    style = (
        "padding:6px 8px;border-bottom:1px solid #e5e7eb;text-align:left;"
        f"font-size:13px;font-weight:{weight};"
    )
    return "<tr>" + "".join(f'<{tag} style="{style}">{escape(c)}</{tag}>' for c in cells) + "</tr>"


def _measure_cells(item: dict) -> list[str]:
    return [
        _sv_time(item["ts"]),
        f"{item['weight_kg']} kg",
        f"{item['temp_c']} °C",
        f"{item['spo2']} %",
        f"{item['bpm']} lpm",
    ]


def measurement_batch(
    device_name: str, items: list[dict], thresholds: dict, app_url: str
) -> tuple[str, str, str]:
    """Correo por lote: alertas arriba y, debajo, las mediciones nuevas agrupadas por paciente.

    Solo lleva el código del paciente, nunca el nombre. Con más de MAX_LISTED mediciones se
    listan solo las alertas y un resumen por paciente.
    """
    items = sorted(items, key=lambda i: (i["patient_code"], i["ts"]))
    n = len(items)
    alerts = [i for i in items if i.get("alert")]
    by_patient: dict[str, list[dict]] = {}
    for item in items:
        by_patient.setdefault(item["patient_code"], []).append(item)

    if alerts:
        subject = f"Alerta en {_plural(len(alerts), 'medición', 'mediciones')} · {device_name}"
    else:
        subject = f"Lote de {device_name}: {_plural(n, 'medición', 'mediciones')}"

    link, button_label = _history_link(app_url, list(by_patient))
    summarize = n > MAX_LISTED
    header = ["Hora (El Salvador)", "Peso", "Temperatura", "SpO₂", "Pulso"]
    more = f"Solo se muestran las alertas y un resumen por paciente (y {n - len(alerts)} más)."
    alert_lines = _alert_lines(alerts, thresholds)

    text_parts = [f"Dispositivo {device_name}: {n} mediciones nuevas.\n"]
    if alert_lines:
        text_parts.append("ALERTAS:\n" + "\n".join(f"  - {line}" for line in alert_lines) + "\n")
    for code, rows in by_patient.items():
        if summarize:
            text_parts.append(f"{_label(code)}: {len(rows)} mediciones")
        else:
            text_parts.append(_label(code))
            text_parts.extend("  " + " · ".join(_measure_cells(r)) for r in rows)
    if summarize:
        text_parts.append(f"\n{more}")
    text_parts.append(f"\n{button_label}: {link}\n\n{FOOTER}")

    body = _title(escape(subject))
    body += f"<p>Se recibieron <strong>{n}</strong> mediciones nuevas de {escape(device_name)}.</p>"
    if alert_lines:
        body += _notice("Alertas: " + " | ".join(alert_lines))
    for code, rows in by_patient.items():
        if summarize:
            body += f"<p><strong>{escape(_label(code))}</strong>: {len(rows)} mediciones</p>"
            continue
        body += f'<p style="margin:16px 0 4px;"><strong>{escape(_label(code))}</strong></p>'
        body += '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
        body += _row(header, header=True) + "".join(_row(_measure_cells(r)) for r in rows)
        body += "</table>"
    if summarize:
        body += _small(more)
    body += _button(link, button_label)
    return subject, "\n".join(text_parts), _layout(subject, body)

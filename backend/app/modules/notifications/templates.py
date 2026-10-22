"""Plantillas de correo del proyecto: un marco común y un cuerpo por tipo de mensaje.

El HTML usa estilos en línea y tablas porque los clientes de correo (Gmail, Outlook) ignoran
casi todo el CSS externo. Cada plantilla devuelve (asunto, texto plano, html).
"""

from html import escape

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

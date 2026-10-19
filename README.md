# SSC-ARC115 · Dispositivo de monitoreo de salud comunitario

Proyecto de ARC115 (Arquitectura de Computadoras), Universidad de El Salvador en Línea, ciclo II-2026, grupo GP03. Tutor: Mg. Luis Kelman Belloso Huezo.

Prototipo que mide **temperatura corporal, oximetría y pulso, y peso**, guarda cada medición y la envía a una API en la nube. La persona que toma los signos recibe un correo con el resultado (y las alertas) y puede consultar el historial de cada paciente en una página web.

> El sistema registra y da seguimiento. No emite diagnósticos médicos.

## Cómo funciona

```
ESP32 (sensores) → microSD (cola local) → HTTPS + JSON → API Gateway + Lambda → DynamoDB
                                                                    └→ correo al promotor
Frontend web ── consulta ──► la misma API (historial y gráficas por paciente)
```

El dispositivo trabaja sin internet: guarda todo en la microSD y sincroniza el lote pendiente cuando vuelve el Wi-Fi, sin duplicar registros.

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `firmware/` | Código del ESP32 (C++, Arduino) |
| `backend/` | API en Python (FastAPI) desplegada en AWS Lambda con SAM |
| `frontend/` | Aplicación web en React + Vite + TypeScript |
| `docs/` | Plan, manuales, bitácora y referencias |
| `.github/workflows/` | Pipelines de GitHub Actions (CI y despliegue) |

Cada módulo del backend y del frontend se organiza por funcionalidad (dispositivos, pacientes, mediciones, notificaciones, autenticación).

## Tecnologías

ESP32 · MAX30205 (temperatura) · MAX30102 (SpO₂ y pulso) · celdas de carga + HX711 (peso) · microSD · Python + FastAPI · AWS (API Gateway, Lambda, DynamoDB) · SMTP de Gmail · React + Vite · GitHub Actions.

## Estado

En desarrollo, Etapa 2. Entrega: 15 de noviembre de 2026. El plan, la rúbrica y el calendario están en [`docs/PLAN.md`](docs/PLAN.md).

## Configuración y secretos

Este repositorio **no contiene secretos**. Las claves, contraseñas y direcciones se leen de variables de entorno:
- Backend: variables de la función Lambda (se definen en el despliegue).
- Frontend: `VITE_API_URL`.
- Firmware: archivo `secrets.h` local (hay un `secrets.example.h` de ejemplo).
- Pipelines: GitHub Secrets.

El detalle de cada variable se documenta en el manual técnico (`docs/`) a medida que se implementa cada módulo.

## Flujo de trabajo con Git

- `main` es la rama estable y está protegida.
- Cada cambio se hace en una rama `feature/<módulo>-<descripción>` y entra por pull request con el CI en verde.
- Commits cortos en español con el formato `tipo(módulo): descripción`, por ejemplo `feat(mediciones): validar lote del ESP32`.

## Equipo

| Integrante | Carnet |
|---|---|
| Aquino Cortez, José Daniel | AC21051 |
| Gálvez Rodas, Jennyfer Alexandra | GR22078 |
| Méndez Sosa, José Roberto | MS24030 |
| Ramírez Hernández, Jakelin Johana | RH21014 |

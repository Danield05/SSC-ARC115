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
| `.github/workflows/` | Pipelines de GitHub Actions (CI y despliegue) |

Cada módulo del backend y del frontend se organiza por funcionalidad (dispositivos, pacientes, mediciones, notificaciones, autenticación).

## Tecnologías

ESP32 · MAX30205 (temperatura) · MAX30102 (SpO₂ y pulso) · celdas de carga + HX711 (peso) · microSD · Python + FastAPI · AWS (API Gateway, Lambda, DynamoDB) · SMTP de Gmail · React + Vite + Tailwind CSS (shadcn/ui) · GitHub Actions.

## Estado

En desarrollo, Etapa 2. Hecho: base del backend y del frontend, inicio de sesión con roles, administración de dispositivos y usuarios, CI. En curso: recepción de mediciones (`POST /measurements`), correo al promotor, gráficas por paciente y firmware. Entrega: 15 de noviembre de 2026.

## Configuración y secretos

Este repositorio **no contiene secretos**. Las claves, contraseñas y direcciones se leen de variables de entorno:
- Backend: variables de la función Lambda (se definen en el despliegue).
- Frontend: `VITE_API_URL`.
- Firmware: archivo `secrets.h` local (hay un `secrets.example.h` de ejemplo).
- Pipelines: GitHub Secrets.

Las variables del backend y del frontend, con valores de ejemplo, están en [`.env.example`](.env.example).

## Ejecutar el proyecto en local

Requisitos: Docker Desktop, Python 3.12 o superior y Node.js 22.

### 1. Base de datos (DynamoDB Local en Docker)

```powershell
docker compose up -d        # raíz del repo: base en el puerto 8001
```

Los datos **persisten** en un volumen de Docker: sobreviven a `docker compose down` y a reiniciar la PC. Para borrar todo y empezar de cero: `docker compose down -v`.

### 2. Backend (primera vez)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python scripts/create_tables.py                              # crea las 4 tablas y un dispositivo de prueba
python scripts/create_admin.py --local admin@example.com     # primer administrador (pide la contraseña)
python scripts/seed_demo_users.py --local                    # opcional: promotor y evaluador de ejemplo (pide una contraseña)
```

Las contraseñas se piden por teclado y nunca se guardan en archivos. Los scripts son repetibles: si algo ya existe, lo omiten.

### 3. Levantar la API

```powershell
cd backend
.venv\Scripts\Activate.ps1
$env:DYNAMODB_ENDPOINT="http://localhost:8001"; $env:AWS_ACCESS_KEY_ID="local"; $env:AWS_SECRET_ACCESS_KEY="local"; $env:AWS_DEFAULT_REGION="us-east-1"
$env:JWT_SECRET = python -c "import secrets; print(secrets.token_hex(32))"
uvicorn app.main:app --reload
```

API en <http://localhost:8000> y documentación interactiva en <http://localhost:8000/docs>. Sin `JWT_SECRET` el inicio de sesión responde `503`. Las variables `$env:` valen solo para esa terminal. Con un `JWT_SECRET` nuevo, las sesiones abiertas dejan de ser válidas.

### 4. Levantar el frontend

```powershell
cd frontend
npm install        # solo la primera vez
npm run dev
```

Abre <http://localhost:5173> e inicia sesión con alguno de los usuarios creados.

### Roles

| Rol | Qué puede hacer |
|---|---|
| Administrador | Gestiona dispositivos y usuarios; ve todo |
| Promotor | Ve solo los dispositivos que tienen su correo como promotor |
| Evaluador | Solo lectura de dispositivos; sin edición |

### Consultar los datos

- **Interfaz web (recomendada):** `dynamodb-admin`. En otra terminal:
  ```powershell
  $env:DYNAMO_ENDPOINT="http://localhost:8001"; $env:AWS_REGION="us-east-1"; $env:AWS_ACCESS_KEY_ID="local"; $env:AWS_SECRET_ACCESS_KEY="local"; $env:PORT="8002"
  npx dynamodb-admin
  ```
  Luego abre <http://localhost:8002>. El `PORT=8002` es necesario porque la base ya usa el 8001.
- **Por terminal:** desde `backend/` con el entorno activado, `python scripts/show_tables.py` imprime el contenido de las tablas (sin hashes).
- **Aplicación de escritorio:** [NoSQL Workbench](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.html) de AWS: *Add connection* → *DynamoDB local* → host `localhost`, puerto `8001`.

DataGrip y otros clientes SQL no sirven para esto: DynamoDB no es una base SQL.

### Pruebas y calidad

```powershell
cd backend;  ruff check .; ruff format --check .; pytest      # entorno activado
cd frontend; npm run lint; npm run build
```

Si `docker compose` falla en Windows con `docker-credential-desktop`, agrega `C:\Program Files\Docker\Docker\resources\bin` al PATH.

## Flujo de trabajo con Git

- `main` es la rama estable y está protegida; `development` es la rama de integración.
- Cada cambio se hace en una rama `feature/<módulo>-<descripción>` que sale de `development` y entra a ella por pull request con el CI en verde. Cuando `development` está estable, se fusiona a `main` por pull request.
- Commits cortos en español con el formato `tipo(módulo): descripción`, por ejemplo `feat(mediciones): validar lote del ESP32`.

## Créditos y licencias

La interfaz adapta componentes de una plantilla con licencia MIT y usa fotos de dominio público y CC0. El detalle de autoría y licencias está en [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Equipo

| Integrante | Carnet |
|---|---|
| Aquino Cortez, José Daniel | AC21051 |
| Gálvez Rodas, Jennyfer Alexandra | GR22078 |
| Méndez Sosa, José Roberto | MS24030 |
| Ramírez Hernández, Jakelin Johana | RH21014 |

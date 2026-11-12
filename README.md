# 🩺 SSC-ARC115 · Dispositivo de monitoreo de salud comunitario

Proyecto de ARC115 (Arquitectura de Computadoras), Universidad de El Salvador en Línea, ciclo II-2026, grupo GP03. Tutor: Mg. Luis Kelman Belloso Huezo.

Prototipo que mide **temperatura corporal, oximetría y pulso, y peso**, guarda cada medición y la envía a una API en la nube. La persona que toma los signos recibe un correo con el resultado (y las alertas) y puede consultar el historial de cada paciente en una página web.

> El sistema registra y da seguimiento. No emite diagnósticos médicos.

## ⚙️ Cómo funciona

```
ESP32 (sensores) → memoria flash interna (cola local) → HTTPS + JSON → API Gateway + Lambda → DynamoDB
                                                                    └→ correo al promotor
Frontend web ── consulta ──► la misma API (historial y gráficas por paciente)
```

El dispositivo trabaja sin internet: guarda todo en su memoria interna y sincroniza el lote pendiente cuando vuelve el Wi-Fi, sin duplicar registros.

## 🗂️ Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `firmware/` | Código del ESP32 (C++, Arduino) |
| `backend/` | API en Python (FastAPI) desplegada en AWS Lambda con SAM |
| `frontend/` | Aplicación web en React + Vite + TypeScript |
| `.github/workflows/` | Pipelines de GitHub Actions (CI y despliegue) |

Cada módulo del backend y del frontend se organiza por funcionalidad (dispositivos, pacientes, mediciones, notificaciones, autenticación).

## 🧰 Tecnologías

ESP32 · MLX90614 (temperatura infrarroja) · MAX30102 (SpO₂ y pulso) · celdas de carga + HX711 (peso) · Python + FastAPI · AWS (API Gateway, Lambda, DynamoDB) · SMTP de Gmail · React + Vite + Tailwind CSS (shadcn/ui) · GitHub Actions y GitHub Pages.

## 📊 Estado

En desarrollo, Etapa 2. Hecho: base del backend y del frontend, inicio de sesión con roles, alta de usuarios por invitación con contraseña provisional por correo y recuperación de contraseña, portada pública, códigos automáticos de pacientes y dispositivos, administración de dispositivos y usuarios, recepción de mediciones (`POST /measurements`), CI y despliegue automático (API en AWS y frontend en GitHub Pages con dominio propio). En curso: correo al promotor, gráficas por paciente y firmware. Entrega: 15 de noviembre de 2026.

## ☁️ Despliegue

El sistema ya está publicado:

| Parte | Dónde |
|---|---|
| Frontend | <https://app.sistemasalud.app> (GitHub Pages, dominio propio) |
| API | AWS: API Gateway (HTTP API) + Lambda + DynamoDB, región `us-east-1`, stack `ssc-arc115` |

El despliegue es automático: cada vez que se fusiona un cambio en `main`, el workflow [`deploy.yml`](.github/workflows/deploy.yml) compila y despliega el backend con AWS SAM, prueba `GET /health` y publica el frontend. El CI (`ci.yml`) corre en cada pull request y en cada push.

Secretos del repositorio (Settings → Secrets and variables → Actions): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `JWT_SECRET` y `ALLOWED_ORIGIN`. Para el frontend, Pages debe tener *Source = GitHub Actions* y el dominio personalizado configurado.

El stack de AWS es único (hace de pruebas y de producción) y se elimina al terminar el curso con `sam delete`. Mientras exista, no se usan servicios fuera de Lambda, API Gateway, DynamoDB y lo que crea SAM.

Para recibir mediciones, cada dispositivo se da de alta desde la página de administración; su clave `x-api-key` se muestra una sola vez.

## 🔐 Configuración y secretos

Este repositorio **no contiene secretos**. Las claves, contraseñas y direcciones se leen de variables de entorno:
- Backend: variables de la función Lambda (se definen en el despliegue).
- Frontend: `VITE_API_URL`.
- Firmware: archivo `secrets.h` local (hay un `secrets.example.h` de ejemplo).
- Pipelines: GitHub Secrets.

Las variables del backend y del frontend, con valores de ejemplo, están en [`.env.example`](.env.example).

## 💻 Ejecutar el proyecto en local

### 🐳 Opción A: todo con Docker (la más fácil)

Solo necesitas **Docker Desktop abierto** (no hace falta instalar Python ni Node). Desde la raíz del repo:

```powershell
docker compose up --build
```

La primera vez tarda unos minutos (descarga las imágenes e instala las dependencias); después basta `docker compose up`. Levanta cuatro cosas: la base de datos (DynamoDB Local), un paso que crea las tablas y un dispositivo de prueba, la API y el frontend. Cuando termine de arrancar, abre <http://localhost:5173>; la documentación de la API está en <http://localhost:8000/docs>.

Crear el primer administrador (en **otra terminal**, mientras lo anterior sigue corriendo; pide la contraseña por teclado):

```powershell
docker compose run --rm backend python scripts/create_admin.py admin@example.com
```

Opcional, para ver datos de ejemplo:

```powershell
docker compose run --rm backend python scripts/seed_demo_users.py --local          # promotor y evaluador (pide una contraseña)
docker compose run --rm backend python scripts/seed_demo_measurements.py --local   # dos pacientes con ~30 días de mediciones
```

Cosas que conviene saber:
- **Cambios en el código:** lo que edites en `backend/app/` y en `frontend/src/` se refleja solo (la API y Vite se recargan). Si cambias dependencias (`requirements.txt` o `package.json`), vuelve a correr `docker compose up --build`.
- **Correos:** las invitaciones y la recuperación de contraseña no se envían: se imprimen, con la contraseña provisional, en los registros de la API (`docker compose logs -f backend`).
- **Datos:** persisten aunque apagues todo (`docker compose down`). Para empezar de cero: `docker compose down -v`.
- **Puertos:** usa el 5173 (frontend), el 8000 (API) y el 8001 (base). Si alguno está ocupado, ciérralo antes de levantar.
- **Pruebas y lint:** `pytest`, `ruff` y `npm run lint` se siguen corriendo con Python y Node en tu PC (ver «Pruebas y calidad» más abajo).
- **Solo la base:** `docker compose up -d dynamodb` levanta únicamente la base de datos, para correr la API y el frontend a mano (Opción B).

### 🧰 Opción B: a mano (Python y Node en tu PC)

Requisitos: Docker Desktop (solo para la base de datos), Python 3.12 o superior y Node.js 22.

**Atajo:** el script `setup-local.ps1` hace los pasos de instalación de una vez (revisa las herramientas, instala Python y npm, levanta la base y crea las tablas) y al final imprime los comandos para crear el administrador y arrancar la API y el frontend:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup-local.ps1
```

Sin Docker, `setup-local.ps1` indica cómo usar `moto_server`. El archivo `requirements-local.txt` (con comentarios) instala solo lo de Python: `pip install -r requirements-local.txt`. Si prefieres hacerlo a mano, los pasos siguen abajo.

### 🗄️ 1. Base de datos (DynamoDB Local en Docker)

```powershell
docker compose up -d dynamodb   # raíz del repo: base en el puerto 8001
```

Los datos **persisten** en un volumen de Docker: sobreviven a `docker compose down` y a reiniciar la PC. Para borrar todo y empezar de cero: `docker compose down -v`.

### 🐍 2. Backend (primera vez)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python scripts/create_tables.py                              # crea las 4 tablas y un dispositivo de prueba
python scripts/create_admin.py --local admin@example.com     # primer administrador (pide la contraseña)
python scripts/seed_demo_users.py --local                    # opcional: promotor y evaluador de ejemplo (pide una contraseña)
python scripts/seed_demo_measurements.py --local             # opcional: paciente de ejemplo con 30 días de mediciones (para ver las gráficas)
```

Las contraseñas se piden por teclado y nunca se guardan en archivos. Los scripts son repetibles: si algo ya existe, lo omiten.

### 🚀 3. Levantar la API

```powershell
cd backend
.venv\Scripts\Activate.ps1
$env:DYNAMODB_ENDPOINT="http://localhost:8001"; $env:AWS_ACCESS_KEY_ID="local"; $env:AWS_SECRET_ACCESS_KEY="local"; $env:AWS_DEFAULT_REGION="us-east-1"
$env:JWT_SECRET = python -c "import secrets; print(secrets.token_hex(32))"
uvicorn app.main:app --reload
```

API en <http://localhost:8000> y documentación interactiva en <http://localhost:8000/docs>. Sin `JWT_SECRET` el inicio de sesión responde `503`. Las variables `$env:` valen solo para esa terminal. Con un `JWT_SECRET` nuevo, las sesiones abiertas dejan de ser válidas.

### 🖥️ 4. Levantar el frontend

```powershell
cd frontend
npm install        # solo la primera vez
npm run dev
```

Abre <http://localhost:5173>: verás la portada del proyecto; el botón *Ingresar* lleva al login. Inicia sesión con alguno de los usuarios creados.

**Correo en local:** sin cuenta de Gmail configurada, con `MAIL_CONSOLE=1` los correos (invitaciones y recuperación de contraseña) no se envían: se imprimen en la consola donde corre `uvicorn`, con la contraseña provisional. En AWS se usa `GMAIL_USER` y `GMAIL_APP_PASSWORD`.

### 👥 Roles

| Rol | Qué puede hacer |
|---|---|
| Administrador | Gestiona dispositivos y usuarios; ve todo |
| Promotor | Ve solo los dispositivos que tienen su correo como promotor |
| Evaluador | Solo lectura de dispositivos; sin edición |

### ✉️ Cómo se agrega a una persona del equipo

1. El administrador entra a *Usuarios* → *Invitar usuario*, escribe el correo y el nombre y **elige el rol**.
2. El sistema genera una contraseña provisional aleatoria y se la envía por correo (plantilla del proyecto).
3. La persona entra con esa contraseña; el sistema le pide crear la suya. Con ese primer ingreso queda verificado su correo (hasta entonces aparece como *Pendiente de verificar* y el administrador puede *Reenviar*).
4. Si olvida la contraseña, en el login pulsa *¿Olvidaste tu contraseña?* y recibe otra provisional (válida 30 minutos); la de siempre sigue funcionando hasta que use la provisional.

### 📈 Historial y gráficas

En *Pacientes*, el botón *Historial* abre las mediciones de esa persona: filtro de 7, 30 o 90 días (o todo), la última medición de cada parámetro, una gráfica por parámetro (temperatura y SpO₂ con su rango normal sombreado; los valores fuera de rango van en rojo) y una tabla con todas las mediciones. El promotor solo ve a sus propios pacientes.

La barra superior muestra un reloj con la hora de El Salvador, la misma con la que el historial y los archivos exportados muestran las mediciones.

En la lista de *Pacientes* hay una caja de búsqueda: escribe el nombre, o el apellido, o el código del paciente (por ejemplo «Juan», «Orellana» o `P-0003`, también solo `0003`) y la tabla muestra a quienes coinciden, sin importar mayúsculas ni tildes. La búsqueda queda en la dirección de la página, así que sigue puesta al volver desde el historial de alguien. No hay filtro de fechas en la lista: el rango (7, 30, 90 días o todo) está dentro de cada paciente.

El Excel trae las hojas *Mediciones*, *Resumen* (con fórmulas de Excel reales: promedios, mínimos, máximos, tendencia, IMC), *Correlaciones*, *Gráficas* (una por parámetro y la dispersión temperatura–pulso) y *Diccionario*. El interruptor *Anonimizar*, junto a *Descargar Excel* y *CSV*, cambia el código del paciente por un ID sustituto (`ANON-` y 8 caracteres, siempre el mismo para la misma persona) y las fechas por los días desde la primera medición del archivo. Sin él, el archivo ya va sin nombre, DUI ni contactos, pero con el código real y las fechas.

El historial de cada paciente tiene seis pestañas, cada una con su propia ruta: *Historial*, *Monitor*, *Análisis*, *Trazabilidad*, *Episodios* y *Alertas*. En *Historial* las cuatro gráficas comparten el cursor: al pasar sobre una se ve la misma medición en todas, y la tabla muestra la etiqueta de revisión de las alertas.

**Monitor** (pestaña *Monitor*, ruta `/patients/:code/monitor`): los cuatro valores de la medición elegida en grande y una línea de tiempo para recorrer las mediciones (con las flechas del teclado, o con los botones anterior, siguiente y reproducir), con marcas rojas en las que tuvieron alerta y una traza pequeña por parámetro. El fondo y la flecha de cada valor indican cuánto se aleja de las 10 mediciones anteriores de esa persona (ámbar: algo; rojo: mucho; a partir de la cuarta medición); es informativo, no un umbral clínico. 

**Análisis** (`/patients/:code/analisis`): el resumen del paciente (IMC, variación de peso, promedios, mínimos y máximos por ventana), la *franja de desviación* (una celda por medición y una fila por parámetro: el color y la flecha dicen cuánto y hacia dónde se aleja cada valor de las 10 mediciones anteriores de esa persona), la gráfica de temperatura contra pulso con su recta de regresión y el coeficiente r, y el *mapa de retardo*: cada valor contra el siguiente (pulso, temperatura, SpO₂ o peso), con una diagonal de «sin cambio». Los puntos lejos de la diagonal son saltos entre una visita y la siguiente. Con menos de 10 mediciones muestra «n/d».

**Trazabilidad** (`/patients/:code/trazabilidad`): por cada medición, cuándo se midió y cuándo llegó a la nube, el retraso, si el dispositivo la guardó sin conexión (más de 5 minutos entre medir y llegar) y con cuántas otras llegó en el mismo lote.

**Episodios** (`/patients/:code/episodios`): agrupa las alertas seguidas en episodios y los muestra en una línea de tiempo a escala real, con el estado de su revisión (sin revisar, confirmada, falso positivo o artefacto), y en una lista con la duración, el valor más extremo y cuándo volvió a rango.

**Alertas** (`/patients/:code/alertas`): las alertas del rango con sus valores, la medición anterior y la siguiente, y el motivo. El administrador y el promotor marcan cada una como *Confirmada*, *Falso positivo* o *Artefacto* (lectura mala del sensor), con una nota de hasta 200 caracteres; el evaluador la ve en solo lectura. Arriba se ve cuántas están revisadas y el porcentaje de falsas alarmas. El Excel y el CSV agregan la columna «Revisión» (solo la etiqueta, sin la nota ni quién la puso).

Para verlo con datos: `python scripts/seed_demo_measurements.py --local` crea dos pacientes de ejemplo (un adulto con un episodio febril, un episodio de desaturación, una bradicardia, una lectura mala de SpO₂ y un día con varias mediciones, y un niño de 9 años con otra línea base). Cada uno tiene un periodo sin conexión (sus mediciones llegan en un solo lote) y tres alertas de la adulta ya vienen revisadas. Los valores llevan una pequeña variación natural, la misma en cada carga.

### 🔢 Códigos automáticos

- **Pacientes:** el sistema asigna el código (`P-0001`, `P-0002`…). Al registrar son obligatorios el nombre, la edad y el sexo (M/F, para calcular la categoría del IMC); también se pueden guardar estatura, teléfono, correo y dirección. El DUI solo se pide a mayores de 18 años; para un menor de edad son obligatorios el nombre y el DUI de su responsable. El dispositivo solo guarda el código.
- **Dispositivos:** el sistema asigna el identificador (`ESP32-GP03-01`, `-02`…) y genera la clave; el identificador se copia al `secrets.h` del firmware junto con la clave.

### 🔍 Consultar los datos

- **Interfaz web (recomendada):** `dynamodb-admin`. En otra terminal:
  ```powershell
  $env:DYNAMO_ENDPOINT="http://localhost:8001"; $env:AWS_REGION="us-east-1"; $env:AWS_ACCESS_KEY_ID="local"; $env:AWS_SECRET_ACCESS_KEY="local"; $env:PORT="8002"
  npx dynamodb-admin
  ```
  Luego abre <http://localhost:8002>. El `PORT=8002` es necesario porque la base ya usa el 8001.
- **Por terminal:** desde `backend/` con el entorno activado, `python scripts/show_tables.py` imprime el contenido de las tablas (sin hashes).
- **Aplicación de escritorio:** [NoSQL Workbench](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.html) de AWS: *Add connection* → *DynamoDB local* → host `localhost`, puerto `8001`.

DataGrip y otros clientes SQL no sirven para esto: DynamoDB no es una base SQL.

### ✅ Pruebas y calidad

```powershell
cd backend;  ruff check .; ruff format --check .; pytest      # entorno activado
cd frontend; npm run lint; npm run build
```

Si `docker compose` falla en Windows con `docker-credential-desktop`, agrega `C:\Program Files\Docker\Docker\resources\bin` al PATH.

## 🔧 Firmware (ESP32)

El código está en `firmware/gp03_monitor/` (C++, Arduino framework). Mide peso, temperatura y SpO₂/pulso, muestra el resultado en la OLED, lo guarda en la flash interna (LittleFS) y lo sincroniza por lotes cuando hay Wi-Fi. Sin internet funciona igual, con una salvedad: la hora sale de NTP, así que el equipo necesita Wi-Fi al menos una vez después de encenderse (sin hora muestra «Sin hora» y no mide).

**Preparar el IDE (una vez):** Arduino IDE → núcleo *esp32 de Espressif* (probado con 3.3.12) y placa *ESP32 Dev Module*. Librerías (Gestor de bibliotecas): ArduinoJson 7.4.3, HX711 0.6.6 (Bogdan Necula), SparkFun MAX3010x Pulse and Proximity Sensor Library 1.1.2, Adafruit MLX90614 Library 2.1.7, Adafruit SSD1306 2.5.17 y Adafruit GFX Library 1.13.0.

**Credenciales:** copiar `secrets.example.h` como `secrets.h` (junto al `.ino`; no se sube a git) y llenar `WIFI_SSID`, `WIFI_PASSWORD`, `API_URL` (dirección base de la API, sin ruta), `DEVICE_ID` y `API_KEY` (la clave se muestra una sola vez al dar de alta el dispositivo en la página).

**Pines, umbrales y calibración:** todo en `config.h`. Los pines son una propuesta y hay que confirmarlos con la placa perforada. Para subir el programa conviene elegir la partición *No OTA (2MB APP/2MB SPIFFS)*; con la partición por defecto el programa ocupa el 88 % de su espacio. Subir con «borrar toda la flash» borra los registros guardados.

**Uso:** el botón 1 recorre los pacientes (en reposo, pulsación larga = tara de la báscula) y el botón 2 acepta (pulsación larga = cancelar). LED verde = todo bien, amarillo = aviso (pendientes por enviar, memoria al 80 %, sin hora o un sensor sin responder), rojo con buzzer = valor fuera de umbral.

**Pruebas por separado** (`firmware/pruebas/`, una por sensor): escáner I2C, calibración del HX711, MAX30102, MLX90614, OLED y LittleFS. Se hacen antes de probar el programa completo y sus capturas sirven de evidencia para el documento.

**Compilar sin el IDE:** `arduino-cli compile --fqbn esp32:esp32:esp32 firmware/gp03_monitor` (con `secrets.h` creado). El CI hace lo mismo con `secrets.example.h`.

## 🌿 Flujo de trabajo con Git

Las dependencias se actualizan a mano; no hay Dependabot.

- `main` es la rama estable y está protegida; `development` es la rama de integración.
- Cada cambio se hace en una rama `feature/<módulo>-<descripción>` que sale de `development` y entra a ella por pull request con el CI en verde. Cuando `development` está estable, se fusiona a `main` por pull request.
- Commits cortos en español con el formato `tipo(módulo): descripción`, por ejemplo `feat(mediciones): validar lote del ESP32`.

## 📜 Créditos y licencias

La interfaz adapta componentes de una plantilla con licencia MIT y usa fotos de dominio público y CC0. El detalle de autoría y licencias está en [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## 🤝 Equipo

| Integrante | Carnet |
|---|---|
| Aquino Cortez, José Daniel | AC21051 |
| Gálvez Rodas, Jennyfer Alexandra | GR22078 |
| Méndez Sosa, José Roberto | MS24030 |
| Ramírez Hernández, Jakelin Johana | RH21014 |

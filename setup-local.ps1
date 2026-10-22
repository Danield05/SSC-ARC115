<#
.SYNOPSIS
  Prepara SSC-ARC115 para correr en local: Python, npm y base de datos.

.DESCRIPTION
  Uso, en PowerShell y desde la raiz del repo:

      .\setup-local.ps1            todo: backend, frontend y base de datos
      .\setup-local.ps1 -SinBase   solo backend y frontend (sin tocar la base)

  Que hace, en orden:
    1. Revisa que esten Python 3.12+ y Node 22+ (y avisa si falta Docker).
    2. Crea backend\.venv e instala requirements-local.txt.
    3. Corre "npm install" en frontend.
    4. Levanta la base local (Docker) y crea las tablas.
    5. Te dice como crear el administrador y arrancar la API y el frontend.

  Es repetible: lo que ya esta instalado o creado se omite. No guarda secretos
  ni cambia variables de entorno fuera de este script.
#>
param(
    [switch]$SinBase
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Paso($texto) { Write-Host "`n== $texto" -ForegroundColor Cyan }
function Aviso($texto) { Write-Host "AVISO: $texto" -ForegroundColor Yellow }
function Falla($texto) { Write-Host "ERROR: $texto" -ForegroundColor Red; exit 1 }
function Existe($comando) { [bool](Get-Command $comando -ErrorAction SilentlyContinue) }

function PuertoAbierto([int]$puerto) {
    $cliente = New-Object System.Net.Sockets.TcpClient
    try {
        $espera = $cliente.BeginConnect('127.0.0.1', $puerto, $null, $null)
        return ($espera.AsyncWaitHandle.WaitOne(500) -and $cliente.Connected)
    } catch { return $false } finally { $cliente.Close() }
}

# ---------------------------------------------------------------- 1. Herramientas
Paso '1/5 Revisando herramientas'
if (-not (Existe 'python')) { Falla 'Falta Python 3.12 o superior: https://www.python.org/downloads/' }
$versionPython = (& python -c "import sys; print('%d.%d' % sys.version_info[:2])")
if ([version]$versionPython -lt [version]'3.12') {
    Falla "Python $versionPython es muy viejo: se necesita 3.12 o superior."
}
if (-not (Existe 'node')) { Falla 'Falta Node.js 22 o superior: https://nodejs.org/' }
$versionNode = (& node --version).TrimStart('v')
if ([int]$versionNode.Split('.')[0] -lt 22) {
    Falla "Node $versionNode es muy viejo: se necesita 22 o superior."
}
$hayDocker = Existe 'docker'
Write-Host "Python $versionPython, Node $versionNode, Docker: $(if ($hayDocker) { 'si' } else { 'no' })"

# ---------------------------------------------------------------- 2. Backend
Paso '2/5 Backend: entorno virtual y paquetes de Python'
$python = Join-Path $PSScriptRoot 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    & python -m venv 'backend\.venv'
    if ($LASTEXITCODE -ne 0) { Falla 'No se pudo crear el entorno virtual backend\.venv.' }
}
& $python -m pip install --upgrade pip --quiet
Write-Host 'Instalando paquetes de Python (puede tardar unos minutos la primera vez)...'
& $python -m pip install -q -r requirements-local.txt
if ($LASTEXITCODE -ne 0) { Falla 'No se pudieron instalar los paquetes de Python.' }

# ---------------------------------------------------------------- 3. Frontend
Paso '3/5 Frontend: paquetes de npm'
Push-Location 'frontend'
try {
    & npm install
    if ($LASTEXITCODE -ne 0) { Falla 'npm install fallo.' }
} finally { Pop-Location }

# ---------------------------------------------------------------- 4. Base de datos
Paso '4/5 Base de datos local (puerto 8001)'
$baseLista = $false
if ($SinBase) {
    Write-Host 'Omitido (-SinBase).'
} elseif (PuertoAbierto 8001) {
    Write-Host 'La base ya esta corriendo en el puerto 8001.'
    $baseLista = $true
} elseif ($hayDocker) {
    & docker compose up -d
    if ($LASTEXITCODE -ne 0) { Falla 'docker compose fallo. Abre Docker Desktop y vuelve a intentar.' }
    for ($i = 0; $i -lt 30 -and -not (PuertoAbierto 8001); $i++) { Start-Sleep -Seconds 1 }
    if (PuertoAbierto 8001) { $baseLista = $true } else { Aviso 'La base no respondio en 30 segundos.' }
} else {
    Aviso 'No hay Docker ni una base corriendo en el puerto 8001.'
    Write-Host 'Opcion sin Docker: en OTRA terminal, desde backend\ con el entorno activo, corre:'
    Write-Host '    moto_server -p 8001' -ForegroundColor Green
    Write-Host 'y luego vuelve a ejecutar este script.'
}

if ($baseLista) {
    # Las variables solo existen mientras corre este script; se restauran al terminar.
    $nombres = 'DYNAMODB_ENDPOINT', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION', 'AWS_PROFILE'
    $guardadas = @{}
    foreach ($n in $nombres) { $guardadas[$n] = [Environment]::GetEnvironmentVariable($n, 'Process') }
    try {
        $env:DYNAMODB_ENDPOINT = 'http://localhost:8001'
        $env:AWS_ACCESS_KEY_ID = 'local'
        $env:AWS_SECRET_ACCESS_KEY = 'local'
        $env:AWS_DEFAULT_REGION = 'us-east-1'
        Remove-Item Env:AWS_PROFILE -ErrorAction SilentlyContinue
        & $python 'backend\scripts\create_tables.py'
        if ($LASTEXITCODE -ne 0) { Falla 'No se pudieron crear las tablas.' }
    } finally {
        foreach ($n in $nombres) { [Environment]::SetEnvironmentVariable($n, $guardadas[$n], 'Process') }
    }
}

# ---------------------------------------------------------------- 5. Siguientes pasos
Paso '5/5 Listo. Siguientes pasos'
Write-Host @'

A) Crear el primer administrador (una sola vez; pide la contrasena por teclado):

     cd backend
     .\.venv\Scripts\Activate.ps1
     $env:AWS_ACCESS_KEY_ID="local"; $env:AWS_SECRET_ACCESS_KEY="local"; $env:AWS_DEFAULT_REGION="us-east-1"
     python scripts/create_admin.py --local tu-correo@ejemplo.com

B) Arrancar la API (terminal 1, desde backend\ con el entorno activo):

     $env:AWS_ACCESS_KEY_ID="local"; $env:AWS_SECRET_ACCESS_KEY="local"; $env:AWS_DEFAULT_REGION="us-east-1"
     $env:DYNAMODB_ENDPOINT="http://localhost:8001"
     $env:JWT_SECRET="cualquier-texto-largo-de-prueba"
     $env:MAIL_CONSOLE="1"     # los correos se imprimen aqui en vez de enviarse
     uvicorn app.main:app --reload

C) Arrancar el frontend (terminal 2):

     cd frontend
     npm run dev

   Y abrir http://localhost:5173

Datos de ejemplo opcionales (desde backend\, con el entorno activo):

     python scripts/seed_demo_users.py --local          # promotor y evaluador
     python scripts/seed_demo_measurements.py --local   # paciente con 30 dias de mediciones

Mas detalles: README.md, seccion "Ejecutar el proyecto en local".
'@ -ForegroundColor Green

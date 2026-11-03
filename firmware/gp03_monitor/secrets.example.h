// Copia este archivo como secrets.h (junto al .ino) y llena tus valores.
// secrets.h está en .gitignore: NUNCA se sube al repositorio.
#pragma once

#define WIFI_SSID "nombre-de-la-red"
#define WIFI_PASSWORD "contraseña-de-la-red"

// Dirección base de la API, sin barra final y sin ruta (el firmware agrega /measurements, etc.).
#define API_URL "https://j8g15moj2m.execute-api.us-east-1.amazonaws.com"

// Identificador y clave que muestra la página de administración al dar de alta el dispositivo
// (la clave se muestra una sola vez).
#define DEVICE_ID "ESP32-GP03-01"
#define API_KEY "clave-del-dispositivo"

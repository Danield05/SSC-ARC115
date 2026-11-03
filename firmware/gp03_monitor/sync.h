// Wi-Fi, hora por NTP y envío por lotes a la API. Nada se pierde sin red: lo pendiente queda en
// la cola local y se envía cuando vuelve la conexión.
#pragma once
#include <Arduino.h>

namespace syncer {

enum class Status : uint8_t {
  OFFLINE,      // sin Wi-Fi
  CONNECTING,
  ONLINE,       // conectado, nada pendiente o esperando el siguiente intento
  KEY_INVALID,  // la API respondió 401: no se reintenta hasta reiniciar
};

void begin();
// Llamar en cada vuelta de loop(). Con allowBlocking = false solo mantiene el Wi-Fi y la hora
// (no hace peticiones HTTPS, que pueden tardar hasta HTTP_TIMEOUT_MS).
void update(bool allowBlocking);

Status status();
bool timeValid();
// Fecha y hora actuales en ISO-8601 UTC con Z. false si el reloj aún no se ha puesto.
bool nowIso(char* out, size_t size);
// Mensaje corto del último envío ("Enviado", "Reintentando", …) para la pantalla.
const char* lastMessage();

}  // namespace syncer

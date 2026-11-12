// Página local del aparato: el promotor abre http://<IP del aparato> desde un celular o PC en la
// misma red Wi-Fi, escribe el PIN y el código del paciente, y el aparato mide a ese paciente.
// No necesita Internet ni pasa por AWS. La IP se muestra en la pantalla de reposo.
//
// Seguridad: es HTTP sin cifrar (el PIN viaja en claro dentro de la red local), el PIN es corto y
// tras WEB_FAIL_LIMIT intentos fallidos se bloquea WEB_BLOCK_MS. Sin LOCAL_PIN en secrets.h (de 4
// caracteres o más) la página queda apagada.
#pragma once
#include <Arduino.h>

namespace webpage {

// Registra las rutas. Llamar una vez en setup().
void begin();
// Atiende al navegador (y arranca el servidor cuando hay Wi-Fi). Llamar en cada vuelta de loop().
void update();

// El aparato solo acepta una orden desde la página cuando está en reposo.
void setIdle(bool idle);

// Si hubo una orden válida desde la página, copia el código del paciente y devuelve true (una sola
// vez por orden). La orden vence a los WEB_REQUEST_TTL_MS si el aparato no la toma.
bool takeRequest(char* patient, size_t size);

bool enabled();
// Texto para la pantalla, por ejemplo "IP 192.168.1.50". false si no hay Wi-Fi o la página está apagada.
bool addressText(char* out, size_t size);

}  // namespace webpage

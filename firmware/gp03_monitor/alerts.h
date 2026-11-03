// Umbrales, LED y buzzer. Todo sin bloquear (con millis). El servidor recalcula la alerta, pero el
// dispositivo debe avisar aunque no haya red.
//
//   verde    = todo bien           amarillo = aviso (pendientes sin sincronizar, memoria al 80 %,
//   rojo + buzzer = alerta de umbral                   sin hora, sensor que no responde)
#pragma once
#include <Arduino.h>

namespace alerts {

void begin();
// Misma regla que el servidor: temperatura <= mínimo o >= máximo, o SpO2 por debajo del mínimo.
bool isAlert(float tempC, int spo2);

void setWarning(bool on);  // enciende el amarillo mientras haya algo que atender
void trigger();            // rojo y buzzer intermitente durante ALERT_BUZZ_MS
void beep();               // pitido corto de confirmación
void update();             // llamar en cada vuelta de loop()

}  // namespace alerts

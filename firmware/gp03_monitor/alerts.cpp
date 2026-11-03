#include "alerts.h"

#include "config.h"

namespace alerts {

static bool g_warning = false;
static unsigned long g_alertUntil = 0;
static unsigned long g_beepUntil = 0;

void begin() {
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
}

bool isAlert(float tempC, int spo2) {
  return tempC <= TEMP_LOW_C || tempC >= TEMP_HIGH_C || spo2 < SPO2_MIN;
}

void setWarning(bool on) { g_warning = on; }

void trigger() { g_alertUntil = millis() + ALERT_BUZZ_MS; }

void beep() { g_beepUntil = millis() + 120; }

void update() {
  unsigned long now = millis();
  bool alarm = (long)(g_alertUntil - now) > 0;
  // Pitidos de 200 ms cada 400 ms mientras dura la alerta.
  bool buzz = (alarm && (now / 200) % 2 == 0) || (long)(g_beepUntil - now) > 0;
  digitalWrite(PIN_BUZZER, buzz ? HIGH : LOW);
  digitalWrite(PIN_LED_RED, alarm ? HIGH : LOW);
  digitalWrite(PIN_LED_YELLOW, !alarm && g_warning ? HIGH : LOW);
  digitalWrite(PIN_LED_GREEN, !alarm && !g_warning ? HIGH : LOW);
}

}  // namespace alerts

#include "input.h"

#include "config.h"

namespace input {

struct Button {
  uint8_t pin;
  bool down;               // estado estable (true = presionado)
  bool lastRaw;
  unsigned long changedAt;
  unsigned long pressedAt;
};

static Button btn = {PIN_BTN, false, false, 0, 0};

void begin() {
  pinMode(PIN_BTN, INPUT_PULLUP);
}

// Devuelve cuánto duró la pulsación al soltar, o 0 si no hubo una pulsación completa.
static unsigned long update(Button& b) {
  bool raw = digitalRead(b.pin) == LOW;
  unsigned long now = millis();
  if (raw != b.lastRaw) {
    b.lastRaw = raw;
    b.changedAt = now;
  }
  if (now - b.changedAt < BTN_DEBOUNCE_MS || raw == b.down) return 0;
  b.down = raw;
  if (b.down) {
    b.pressedAt = now;
    return 0;
  }
  return max(1UL, now - b.pressedAt);
}

Event poll() {
  unsigned long held = update(btn);
  if (held) return held >= BTN_LONG_MS ? Event::LONG : Event::SHORT;
  return Event::NONE;
}

}  // namespace input

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

static Button next = {PIN_BTN_NEXT, false, false, 0, 0};
static Button ok = {PIN_BTN_OK, false, false, 0, 0};

void begin() {
  pinMode(PIN_BTN_NEXT, INPUT_PULLUP);
  pinMode(PIN_BTN_OK, INPUT_PULLUP);
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
  unsigned long held = update(next);
  if (held) return held >= BTN_LONG_MS ? Event::NEXT_LONG : Event::NEXT_SHORT;
  held = update(ok);
  if (held) return held >= BTN_LONG_MS ? Event::OK_LONG : Event::OK_SHORT;
  return Event::NONE;
}

}  // namespace input

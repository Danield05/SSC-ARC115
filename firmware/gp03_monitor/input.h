// Un botón con antirrebote y pulsación larga. Cableado a GND con INPUT_PULLUP.
#pragma once
#include <Arduino.h>

namespace input {

// SHORT: pulsación menor a BTN_LONG_MS. LONG: igual o mayor. Se decide al soltar.
enum class Event : uint8_t { NONE, SHORT, LONG };

void begin();
// Se llama en cada vuelta de loop(). El evento sale al soltar el botón.
Event poll();

}  // namespace input

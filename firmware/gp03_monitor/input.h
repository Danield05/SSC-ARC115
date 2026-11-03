// Dos botones con antirrebote y pulsación larga. Cableados a GND con INPUT_PULLUP.
#pragma once
#include <Arduino.h>

namespace input {

enum class Event : uint8_t { NONE, NEXT_SHORT, NEXT_LONG, OK_SHORT, OK_LONG };

void begin();
// Se llama en cada vuelta de loop(). El evento sale al soltar el botón.
Event poll();

}  // namespace input

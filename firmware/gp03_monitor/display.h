// Pantalla OLED I2C de 128x64 (SSD1306). Si la OLED real es SH1106, hay que cambiar la biblioteca.
#pragma once
#include <Arduino.h>

namespace display {

bool begin();

// Pantalla con barra de título, hasta tres líneas de texto y un pie.
void show(const char* title, const char* line1 = "", const char* line2 = "",
          const char* line3 = "", const char* footer = "");

// Igual, pero con un valor grande en el centro (por ejemplo, el peso que se está leyendo).
void showBig(const char* title, const char* big, const char* line = "", const char* footer = "");

}  // namespace display

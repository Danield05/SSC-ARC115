// Prueba F0 · Pantalla OLED I2C 128x64 (SSD1306, 0x3C). Si la pantalla es SH1106 y se ve
// corrida o con basura, hay que usar otra biblioteca.
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>

Adafruit_SSD1306 oled(128, 64, &Wire, -1);

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  Wire.setClock(100000);
  if (!oled.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED no encontrada (0x3C).");
    while (true) delay(1000);
  }
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(2);
  oled.setCursor(0, 0);
  oled.println("GP03");
  oled.setTextSize(1);
  oled.println("Monitor de salud");
  oled.println("Prueba de pantalla OK");
  oled.display();
}

void loop() {}

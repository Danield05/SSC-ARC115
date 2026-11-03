// Prueba F0 · Escáner I2C. Deben aparecer 0x3C (OLED), 0x57 (MAX30102) y 0x5A (MLX90614).
// Guardar una captura del monitor serial (115200) como evidencia para el documento.
#include <Wire.h>

#define PIN_SDA 21
#define PIN_SCL 22

void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(100000);  // el MLX90614 usa SMBus
}

void loop() {
  Serial.println("Buscando dispositivos I2C...");
  int found = 0;
  for (uint8_t address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      Serial.printf("  0x%02X\n", address);
      found++;
    }
  }
  Serial.printf("Encontrados: %d (esperados: 0x3C, 0x57, 0x5A)\n\n", found);
  delay(3000);
}

// Prueba F0 · MLX90614 (infrarrojo). Mide la temperatura de la PIEL, no la interna.
// Para calibrar: al menos 10 mediciones contra un termometro clinico, siempre en la misma zona
// y a la misma distancia; calcular el desfase y guardarlo en TEMP_OFFSET_C (config.h).
#include <Adafruit_MLX90614.h>
#include <Wire.h>

Adafruit_MLX90614 mlx;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  Wire.setClock(100000);
  if (!mlx.begin()) {
    Serial.println("MLX90614 no encontrado (0x5A). Revisa las conexiones.");
    while (true) delay(1000);
  }
}

void loop() {
  Serial.printf("Objeto: %.2f C   Ambiente: %.2f C\n", mlx.readObjectTempC(), mlx.readAmbientTempC());
  delay(500);
}

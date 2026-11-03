// Prueba F0 · Calibración de la báscula (celdas de carga + HX711).
// 1) Con la báscula VACÍA, enviar 't' por el monitor serial (115200): hace la tara.
// 2) Poner una masa patrón conocida (5, 10 y 20 kg) y enviar su peso en kg, por ejemplo "10".
//    Imprime el factor de calibración = (lectura cruda - tara) / kg.
// 3) Copiar el promedio de los factores a HX711_SCALE_FACTOR en config.h y anotar el error con
//    cada masa patrón en una tabla (evidencia del documento).
#include <HX711.h>

#define PIN_DT 32
#define PIN_SCK 33

HX711 scale;

void setup() {
  Serial.begin(115200);
  scale.begin(PIN_DT, PIN_SCK);
  Serial.println("Vacia la bascula y envia 't' para la tara.");
}

void loop() {
  if (!Serial.available()) return;
  String input = Serial.readStringUntil('\n');
  input.trim();
  if (input == "t") {
    scale.set_scale(1.0f);
    scale.tare(20);
    Serial.println("Tara hecha. Pon una masa patron y envia su peso en kg.");
    return;
  }
  float kg = input.toFloat();
  if (kg <= 0) return;
  long raw = scale.get_value(20);  // lectura promedio menos la tara
  Serial.printf("Masa %.2f kg -> lectura %ld -> factor %.2f\n", kg, raw, raw / kg);
}

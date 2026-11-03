// Prueba F0 · MAX30102. Imprime las señales IR y roja; con el dedo puesto, IR debe superar
// FINGER_IR_MIN (50000). Luego calcula SpO2 y pulso con el algoritmo de la biblioteca.
// Comparar al menos 10 mediciones contra un oxímetro comercial (evidencia del documento).
#include <MAX30105.h>
#include <Wire.h>
#include <spo2_algorithm.h>

MAX30105 sensor;
uint32_t irBuffer[100], redBuffer[100];

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  Wire.setClock(100000);
  if (!sensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30102 no encontrado (0x57). Revisa las conexiones.");
    while (true) delay(1000);
  }
  sensor.setup(60, 4, 2, 100, 411, 4096);
  Serial.println("Pon el dedo en el sensor...");
}

void loop() {
  for (int i = 0; i < 100; i++) {
    while (!sensor.available()) sensor.check();
    redBuffer[i] = sensor.getFIFORed();
    irBuffer[i] = sensor.getFIFOIR();
    sensor.nextSample();
  }
  int32_t spo2, heartRate;
  int8_t spo2Valid, heartRateValid;
  maxim_heart_rate_and_oxygen_saturation(irBuffer, 100, redBuffer, &spo2, &spo2Valid, &heartRate,
                                         &heartRateValid);
  Serial.printf("IR=%lu  SpO2=%ld (%s)  Pulso=%ld (%s)\n", (unsigned long)irBuffer[99], (long)spo2,
                spo2Valid ? "valido" : "invalido", (long)heartRate,
                heartRateValid ? "valido" : "invalido");
}

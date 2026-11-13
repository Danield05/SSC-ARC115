// Prueba F0 · Termistor NTC de 100 kOhm (de CONTACTO). Imprime el ADC crudo, la resistencia y los °C.
// Cableado: 3V3 -> NTC -> GPIO35 -> resistencia fija de 10 kOhm -> GND.
// Sin tocar el sensor debe marcar la temperatura del cuarto. Con el sensor apoyado en la piel sube
// poco a poco hasta estabilizarse. Para calibrar, comparar al menos 10 lecturas con un termómetro
// clínico y anotar la diferencia. Guardar una captura del monitor serial (115200) como evidencia.
#include <math.h>

#define PIN_NTC 35            // ADC1, solo entrada
#define R_FIXED 10000.0f      // resistencia fija del divisor
#define R0 100000.0f          // NTC a 25 °C
#define BETA 3950.0f
#define T0_C 25.0f
#define ADC_SAMPLES 16        // se promedian para bajar el ruido
#define OFFSET_C 0.0f         // aquí se mide el valor "puro"; el firmware usa TEMP_OFFSET_C de config.h

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_NTC, ADC_11db);
}

void loop() {
  uint32_t sum = 0;
  for (int i = 0; i < ADC_SAMPLES; i++) sum += analogRead(PIN_NTC);
  float adc = sum / (float)ADC_SAMPLES;

  if (adc < 50 || adc > 4045) {
    Serial.printf("ADC %.0f: pegado a un extremo. NTC desconectado o en corto? Revisa el cableado.\n", adc);
    delay(1000);
    return;
  }
  float a = constrain(adc, 1.0f, 4094.0f);
  float rNtc = R_FIXED * ((4095.0f / a) - 1.0f);
  float invT = logf(rNtc / R0) / BETA + 1.0f / (T0_C + 273.15f);
  float celsius = 1.0f / invT - 273.15f + OFFSET_C;

  Serial.printf("ADC: %.1f   Resistencia NTC: %.0f ohm   Temperatura: %.2f C\n", adc, rNtc, celsius);
  delay(1000);
}

// Lectura de los tres parámetros. Cada medición es un "paso" que se llama una y otra vez desde
// loop() hasta que devuelve true, así la pantalla y los botones siguen respondiendo.
#pragma once
#include <Arduino.h>

namespace sensors {

enum SensorBit : uint8_t { SENSOR_OLED = 1, SENSOR_MLX = 2, SENSOR_MAX = 4, SENSOR_HX711 = 8 };

// Inicia el bus I2C (100 kHz) y los sensores. Devuelve los bits de los que NO respondieron.
uint8_t begin();
bool oledFound();

// Peso: tara con la báscula vacía (al arrancar y con pulsación larga del botón 1).
void tare();
void weightStart();
// true cuando el valor estuvo estable WEIGHT_WINDOW_MS; `live` es la lectura actual.
bool weightStep(float& stableKg, float& liveKg);

// Temperatura (infrarrojo, piel).
void temperatureStart();
bool temperatureStep(float& tempC, float& liveC, int& progressPercent);

// Oximetría y pulso.
void oximeterStart();
// true cuando hay OXI_GOOD_NEEDED lecturas válidas. `finger` indica si hay dedo; `progress` 0-100.
bool oximeterStep(int& spo2, int& bpm, bool& finger, int& progressPercent);

}  // namespace sensors

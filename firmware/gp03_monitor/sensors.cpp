#include "sensors.h"

#include <Adafruit_MLX90614.h>
#include <HX711.h>
#include <MAX30105.h>
#include <Wire.h>
#include <spo2_algorithm.h>

#include "config.h"

namespace sensors {

static HX711 scale;
static Adafruit_MLX90614 mlx;
static MAX30105 particle;
static bool g_oled = false;
static bool g_hx = false, g_mlx = false, g_max = false;

// ───────────── utilidades ─────────────

static float medianOf(float* values, int n) {
  for (int i = 1; i < n; i++) {
    float key = values[i];
    int j = i - 1;
    while (j >= 0 && values[j] > key) {
      values[j + 1] = values[j];
      j--;
    }
    values[j + 1] = key;
  }
  return values[n / 2];
}

static int medianInt(int* values, int n) {
  for (int i = 1; i < n; i++) {
    int key = values[i];
    int j = i - 1;
    while (j >= 0 && values[j] > key) {
      values[j + 1] = values[j];
      j--;
    }
    values[j + 1] = key;
  }
  return values[n / 2];
}

// ───────────── arranque ─────────────

static bool i2cPresent(uint8_t address) {
  Wire.beginTransmission(address);
  return Wire.endTransmission() == 0;
}

uint8_t begin() {
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.setClock(I2C_CLOCK_HZ);

  uint8_t missing = 0;
  g_oled = i2cPresent(OLED_ADDRESS);
  if (!g_oled) missing |= SENSOR_OLED;

  g_mlx = mlx.begin();
  if (!g_mlx) missing |= SENSOR_MLX;

  g_max = particle.begin(Wire, I2C_SPEED_STANDARD);
  if (g_max) {
    // brillo 60, promedio de 4 muestras, modo rojo+IR, 100 Hz, pulso 411 us, rango 4096:
    // salen 25 muestras por segundo, que es lo que espera el algoritmo de SpO2.
    particle.setup(60, 4, 2, 100, 411, 4096);
  } else {
    missing |= SENSOR_MAX;
  }

  scale.begin(PIN_HX711_DT, PIN_HX711_SCK);
  scale.set_scale(HX711_SCALE_FACTOR);
  g_hx = scale.wait_ready_timeout(1000);
  if (g_hx) scale.tare(10);
  else missing |= SENSOR_HX711;
  return missing;
}

bool oledFound() { return g_oled; }

// ───────────── peso ─────────────

static const int WEIGHT_N = WEIGHT_WINDOW_MS / WEIGHT_SAMPLE_MS;
static float w_samples[WEIGHT_N];
static int w_count = 0;
static unsigned long w_last = 0;

void tare() {
  if (g_hx) scale.tare(10);
}

void weightStart() {
  w_count = 0;
  w_last = 0;
}

bool weightStep(float& stableKg, float& liveKg) {
  if (!g_hx) return false;
  unsigned long now = millis();
  if (now - w_last < WEIGHT_SAMPLE_MS || !scale.is_ready()) return false;
  w_last = now;
  float v = scale.get_units(1);
  liveKg = v;
  if (w_count < WEIGHT_N) {
    w_samples[w_count++] = v;
  } else {
    memmove(w_samples, w_samples + 1, sizeof(float) * (WEIGHT_N - 1));
    w_samples[WEIGHT_N - 1] = v;
  }
  if (w_count < WEIGHT_N) return false;

  float lo = w_samples[0], hi = w_samples[0];
  for (int i = 1; i < WEIGHT_N; i++) {
    lo = min(lo, w_samples[i]);
    hi = max(hi, w_samples[i]);
  }
  if (hi - lo > WEIGHT_STABLE_KG || lo < WEIGHT_MIN_KG) return false;
  float copy[WEIGHT_N];
  memcpy(copy, w_samples, sizeof(copy));
  stableKg = roundf(medianOf(copy, WEIGHT_N) * 10.0f) / 10.0f;
  return stableKg <= WEIGHT_MAX_KG;
}

// ───────────── temperatura ─────────────

static float t_samples[TEMP_SAMPLES];
static int t_count = 0;
static unsigned long t_last = 0;

void temperatureStart() {
  t_count = 0;
  t_last = 0;
}

bool temperatureStep(float& tempC, float& liveC, int& progressPercent) {
  progressPercent = t_count * 100 / TEMP_SAMPLES;
  if (!g_mlx) return false;
  unsigned long now = millis();
  if (now - t_last < TEMP_SAMPLE_MS) return false;
  t_last = now;
  float v = mlx.readObjectTempC() + TEMP_OFFSET_C;
  if (isnan(v)) return false;
  liveC = v;
  if (v < TEMP_VALID_MIN_C || v > TEMP_VALID_MAX_C) {
    t_count = 0;  // lectura fuera de rango (sensor mal apuntado): se empieza de nuevo
    return false;
  }
  t_samples[t_count++] = v;
  progressPercent = t_count * 100 / TEMP_SAMPLES;
  if (t_count < TEMP_SAMPLES) return false;
  float sum = 0;
  for (int i = 0; i < TEMP_SAMPLES; i++) sum += t_samples[i];
  tempC = roundf(sum / TEMP_SAMPLES * 10.0f) / 10.0f;
  return true;
}

// ───────────── oximetría y pulso ─────────────

enum class OxiPhase { WAIT_FINGER, FILL, ROLL };
static uint32_t irBuf[OXI_BUFFER], redBuf[OXI_BUFFER];
static OxiPhase o_phase = OxiPhase::WAIT_FINGER;
static int o_filled = 0;
static int o_new = 0;
static int o_goodSpo2[OXI_GOOD_NEEDED], o_goodBpm[OXI_GOOD_NEEDED];
static int o_good = 0;
static bool o_finger = false;

void oximeterStart() {
  o_phase = OxiPhase::WAIT_FINGER;
  o_filled = 0;
  o_new = 0;
  o_good = 0;
  o_finger = false;
  if (g_max) {
    particle.clearFIFO();
    particle.wakeUp();
  }
}

// Calcula con el buffer completo; guarda la lectura si es válida. true al juntar las necesarias.
static bool compute(int& spo2Out, int& bpmOut) {
  int32_t spo2 = 0, hr = 0;
  int8_t spo2Valid = 0, hrValid = 0;
  maxim_heart_rate_and_oxygen_saturation(irBuf, OXI_BUFFER, redBuf, &spo2, &spo2Valid, &hr,
                                         &hrValid);
  if (spo2Valid && hrValid && spo2 >= OXI_SPO2_VALID_MIN && spo2 <= 100 &&
      hr >= OXI_BPM_VALID_MIN && hr <= OXI_BPM_VALID_MAX) {
    o_goodSpo2[o_good] = spo2;
    o_goodBpm[o_good] = hr;
    o_good++;
  }
  if (o_good < OXI_GOOD_NEEDED) return false;
  spo2Out = medianInt(o_goodSpo2, o_good);
  bpmOut = medianInt(o_goodBpm, o_good);
  return true;
}

bool oximeterStep(int& spo2, int& bpm, bool& finger, int& progressPercent) {
  finger = o_finger;
  progressPercent = o_good * 100 / OXI_GOOD_NEEDED;
  if (!g_max) return false;
  particle.check();
  while (particle.available()) {
    uint32_t red = particle.getFIFORed();
    uint32_t ir = particle.getFIFOIR();
    particle.nextSample();

    o_finger = ir >= FINGER_IR_MIN;
    finger = o_finger;
    if (!o_finger) {  // se quitó el dedo: se empieza de nuevo
      o_phase = OxiPhase::WAIT_FINGER;
      o_filled = 0;
      o_new = 0;
      o_good = 0;
      continue;
    }
    if (o_phase == OxiPhase::WAIT_FINGER) o_phase = OxiPhase::FILL;

    if (o_phase == OxiPhase::FILL) {
      irBuf[o_filled] = ir;
      redBuf[o_filled] = red;
      if (++o_filled == OXI_BUFFER) {
        o_phase = OxiPhase::ROLL;
        o_new = 0;
        if (compute(spo2, bpm)) return true;
      }
    } else {  // ROLL: se corre la ventana OXI_STEP muestras y se recalcula
      if (o_new == 0) {
        memmove(irBuf, irBuf + OXI_STEP, sizeof(uint32_t) * (OXI_BUFFER - OXI_STEP));
        memmove(redBuf, redBuf + OXI_STEP, sizeof(uint32_t) * (OXI_BUFFER - OXI_STEP));
      }
      irBuf[OXI_BUFFER - OXI_STEP + o_new] = ir;
      redBuf[OXI_BUFFER - OXI_STEP + o_new] = red;
      if (++o_new == OXI_STEP) {
        o_new = 0;
        if (compute(spo2, bpm)) return true;
      }
    }
  }
  progressPercent = o_good * 100 / OXI_GOOD_NEEDED;
  return false;
}

}  // namespace sensors

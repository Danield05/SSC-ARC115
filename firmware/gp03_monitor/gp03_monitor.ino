// SSC-ARC115 · Dispositivo de monitoreo de salud comunitario (GP03)
//
// Mide peso, temperatura (infrarroja) y SpO2/pulso de un paciente con código, muestra los
// resultados en la OLED, los guarda en la memoria flash interna (LittleFS) y, cuando hay Wi-Fi,
// los envía por lotes a la API. Funciona sin internet. No es un dispositivo de diagnóstico:
// registra y avisa por umbral.
//
// Flujo: REPOSO → ELEGIR_PACIENTE → MEDIR_PESO → MEDIR_TEMP → MEDIR_OXIMETRO → RESULTADOS → REPOSO
//   Botón 1 (siguiente): cambia de paciente. Pulsación larga en reposo: tara de la báscula.
//   Botón 2 (OK): acepta. Pulsación larga: cancela.
// Antes de compilar: copiar secrets.example.h como secrets.h y llenarlo.

#include "alerts.h"
#include "config.h"
#include "display.h"
#include "input.h"
#include "secrets.h"
#include "sensors.h"
#include "storage.h"
#include "sync.h"

enum class State : uint8_t {
  IDLE,
  PICK_PATIENT,
  MEASURE_WEIGHT,
  MEASURE_TEMP,
  MEASURE_OXI,
  RESULTS,
  MESSAGE,
};

static State state = State::IDLE;
static unsigned long stateSince = 0;
static unsigned long lastDraw = 0;
static unsigned long messageUntil = 0;
static uint8_t missingSensors = 0;
static bool storageOk = false;
static uint8_t memoryPercent = 0;
static unsigned long lastMemoryCheck = 0;

static Record current;
static char patients[MAX_PATIENTS][PATIENT_CODE_LEN];
static int patientCount = 0;
static int patientIndex = 0;

// Lecturas en vivo para la pantalla.
static float liveWeight = 0, liveTemp = 0;

static void enter(State next) {
  state = next;
  stateSince = millis();
  lastDraw = 0;
}

static void showMessage(const char* line1, const char* line2 = "", unsigned long ms = 2000) {
  display::show("GP03 Monitor", line1, line2);
  messageUntil = millis() + ms;
  enter(State::MESSAGE);
}

static bool due(unsigned long every) {
  unsigned long now = millis();
  if (now - lastDraw < every) return false;
  lastDraw = now;
  return true;
}

static bool timedOut() { return millis() - stateSince > MEASURE_TIMEOUT_MS; }

// ───────────── pacientes ─────────────

// Usa la lista bajada de la API; si no hay, recorre P-0001 a P-00NN como respaldo.
static void loadPatientList() {
  patientCount = storage::loadPatients(patients, MAX_PATIENTS);
  if (patientCount == 0) {
    for (int i = 0; i < FALLBACK_PATIENTS && i < MAX_PATIENTS; i++)
      snprintf(patients[i], PATIENT_CODE_LEN, "P-%04d", i + 1);
    patientCount = FALLBACK_PATIENTS;
  }
  patientIndex = 0;
}

// ───────────── estados ─────────────

static const char* wifiText() {
  switch (syncer::status()) {
    case syncer::Status::ONLINE: return "Wi-Fi: conectado";
    case syncer::Status::CONNECTING: return "Wi-Fi: conectando...";
    case syncer::Status::KEY_INVALID: return "API: clave invalida";
    default: return "Wi-Fi: sin red";
  }
}

static void drawIdle() {
  char l2[24], l3[28];
  snprintf(l2, sizeof(l2), "Pendientes: %lu", (unsigned long)storage::pendingCount());
  if (!syncer::timeValid())
    snprintf(l3, sizeof(l3), "Sin hora: espera Wi-Fi");
  else
    snprintf(l3, sizeof(l3), "Memoria: %u%%", memoryPercent);
  const char* footer = !storageOk                  ? "Error de memoria"
                       : storage::isFull()         ? "Memoria llena, sincroniza"
                       : (missingSensors != 0)     ? "Sensor sin responder"
                                                   : "OK: medir  B1 largo: tara";
  display::show("GP03 Monitor", wifiText(), l2, l3, footer);
}

static void idleState(input::Event ev) {
  if (due(500)) drawIdle();
  if (ev == input::Event::NEXT_LONG) {
    sensors::tare();
    alerts::beep();
    showMessage("Bascula en cero", "Tara hecha", 1200);
  } else if (ev == input::Event::OK_SHORT) {
    if (!storageOk) showMessage("Error de memoria", "No se puede medir");
    else if (!syncer::timeValid()) showMessage("Sin hora", "Conecta el Wi-Fi", 2500);
    else if (storage::isFull()) showMessage("Memoria llena", "Sincroniza primero", 2500);
    else if (missingSensors & (sensors::SENSOR_HX711 | sensors::SENSOR_MLX | sensors::SENSOR_MAX))
      showMessage("Sensor sin responder", "Revisa las conexiones", 2500);
    else {
      loadPatientList();
      enter(State::PICK_PATIENT);
    }
  }
}

static void pickPatientState(input::Event ev) {
  if (ev == input::Event::NEXT_SHORT) patientIndex = (patientIndex + 1) % patientCount;
  if (ev == input::Event::OK_LONG) {
    enter(State::IDLE);
    return;
  }
  if (ev == input::Event::OK_SHORT) {
    memset(&current, 0, sizeof(current));
    strcpy(current.patient, patients[patientIndex]);
    sensors::weightStart();
    alerts::beep();
    enter(State::MEASURE_WEIGHT);
    return;
  }
  if (ev == input::Event::NEXT_SHORT || due(1000)) {
    char count[16];
    snprintf(count, sizeof(count), "%d de %d", patientIndex + 1, patientCount);
    display::showBig("Paciente", patients[patientIndex], count, "B1: siguiente  OK: elegir");
    lastDraw = millis();
  }
}

static void cancelMeasurement(const char* reason) {
  showMessage("Medicion cancelada", reason, 2500);
}

static void weightState(input::Event ev) {
  if (ev == input::Event::OK_LONG) return cancelMeasurement("");
  if (timedOut()) return cancelMeasurement("Sin peso estable");
  float stable;
  if (sensors::weightStep(stable, liveWeight)) {
    current.weightKg = stable;
    sensors::temperatureStart();
    alerts::beep();
    enter(State::MEASURE_TEMP);
    return;
  }
  if (due(200)) {
    char big[16];
    snprintf(big, sizeof(big), "%.1f kg", liveWeight);
    display::showBig("Peso", big, "Suba y quede quieto", current.patient);
  }
}

static void temperatureState(input::Event ev) {
  if (ev == input::Event::OK_LONG) return cancelMeasurement("");
  if (timedOut()) return cancelMeasurement("Sin lectura de temperatura");
  float value;
  int progress;
  if (sensors::temperatureStep(value, liveTemp, progress)) {
    current.tempC = value;
    sensors::oximeterStart();
    alerts::beep();
    enter(State::MEASURE_OXI);
    return;
  }
  if (due(200)) {
    char big[16], line[24];
    snprintf(big, sizeof(big), "%.1f C", liveTemp);
    snprintf(line, sizeof(line), "Apunte a la frente %d%%", progress);
    display::showBig("Temperatura", big, line, current.patient);
  }
}

static void oximeterState(input::Event ev) {
  if (ev == input::Event::OK_LONG) return cancelMeasurement("");
  if (timedOut()) return cancelMeasurement("Sin lectura de SpO2");
  int spo2, bpm, progress;
  bool finger;
  if (sensors::oximeterStep(spo2, bpm, finger, progress)) {
    current.spo2 = spo2;
    current.bpm = bpm;
    current.alert = alerts::isAlert(current.tempC, current.spo2);
    if (current.alert) alerts::trigger();
    else alerts::beep();
    enter(State::RESULTS);
    return;
  }
  if (due(250)) {
    char line[24];
    if (finger) snprintf(line, sizeof(line), "Midiendo %d%%", progress);
    else snprintf(line, sizeof(line), "Ponga el dedo");
    display::showBig("SpO2 y pulso", finger ? "Quieto..." : "- - -", line, current.patient);
  }
}

static void saveCurrent() {
  char id[40];
  storage::makeRecordId(id, sizeof(id), storage::nextSequence());
  strcpy(current.id, id);
  if (!syncer::nowIso(current.ts, sizeof(current.ts))) return showMessage("Sin hora", "No se guardo", 2500);
  if (!storage::append(current)) return showMessage("Error al guardar", "Memoria llena?", 3000);
  // Línea CSV opcional por Serial, solo para depurar (el PC no es parte del sistema).
  Serial.printf("%s,%s,%.1f,%.1f,%d,%d,%d\n", current.ts, current.patient, current.weightKg,
                current.tempC, current.spo2, current.bpm, current.alert ? 1 : 0);
  showMessage("Guardado", current.patient, 1800);
}

static void resultsState(input::Event ev) {
  if (ev == input::Event::OK_SHORT) return saveCurrent();
  if (ev == input::Event::NEXT_SHORT || ev == input::Event::OK_LONG)
    return showMessage("Descartado", "No se guardo", 1500);
  if (due(500)) {
    char l1[28], l2[28];
    snprintf(l1, sizeof(l1), "%.1f kg  %.1f C", current.weightKg, current.tempC);
    snprintf(l2, sizeof(l2), "SpO2 %d%%  Pulso %d", current.spo2, current.bpm);
    display::show(current.alert ? "ALERTA" : "Resultado", l1, l2,
                  current.alert ? "Fuera de rango" : "Dentro del rango", "OK: guardar  B1: borrar");
  }
}

// ───────────── arranque y ciclo ─────────────

static void updateWarning() {
  if (millis() - lastMemoryCheck > 2000) {  // usedBytes() recorre el sistema de archivos
    lastMemoryCheck = millis();
    memoryPercent = storage::usedPercent();
  }
  bool warning = !storageOk || storage::pendingCount() > 0 || memoryPercent >= MEMORY_WARN_PERCENT ||
                 !syncer::timeValid() || missingSensors != 0 ||
                 syncer::status() == syncer::Status::KEY_INVALID;
  alerts::setWarning(warning);
}

void setup() {
  Serial.begin(115200);
  alerts::begin();
  input::begin();
  missingSensors = sensors::begin();
  display::begin();
  display::show("GP03 Monitor", "Iniciando...", DEVICE_ID);
  storageOk = storage::begin();
  syncer::begin();
  if (missingSensors) {
    char list[28] = "";
    if (missingSensors & sensors::SENSOR_MLX) strcat(list, "MLX ");
    if (missingSensors & sensors::SENSOR_MAX) strcat(list, "MAX ");
    if (missingSensors & sensors::SENSOR_HX711) strcat(list, "HX711 ");
    if (missingSensors & sensors::SENSOR_OLED) strcat(list, "OLED ");
    display::show("Sin respuesta de:", list, "Revisa las conexiones");
    Serial.printf("Sensores sin responder: %s\n", list);
    delay(2500);
  }
  Serial.printf("GP03 listo. Pendientes: %lu\n", (unsigned long)storage::pendingCount());
  enter(State::IDLE);
}

void loop() {
  alerts::update();
  input::Event ev = input::poll();
  // Las peticiones HTTPS pueden tardar hasta HTTP_TIMEOUT_MS: solo se hacen en reposo.
  syncer::update(state == State::IDLE);
  updateWarning();

  switch (state) {
    case State::IDLE: idleState(ev); break;
    case State::PICK_PATIENT: pickPatientState(ev); break;
    case State::MEASURE_WEIGHT: weightState(ev); break;
    case State::MEASURE_TEMP: temperatureState(ev); break;
    case State::MEASURE_OXI: oximeterState(ev); break;
    case State::RESULTS: resultsState(ev); break;
    case State::MESSAGE:
      if ((long)(millis() - messageUntil) >= 0) enter(State::IDLE);
      break;
  }
}

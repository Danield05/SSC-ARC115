// SSC-ARC115 · Dispositivo de monitoreo de salud comunitario (GP03)
//
// Mide peso, temperatura (termistor NTC de contacto) y SpO2/pulso de un paciente con código, muestra los
// resultados en la OLED, los guarda en la memoria flash interna (LittleFS) y, cuando hay Wi-Fi,
// los envía por lotes a la API. Funciona sin internet. No es un dispositivo de diagnóstico:
// registra y avisa por umbral.
//
// Flujo: REPOSO → MEDIR_PESO → MEDIR_TEMP → MEDIR_OXIMETRO → RESULTADOS → REPOSO
//   El dispositivo no elige paciente. La medición empieza de tres formas:
//     · Botón (pulsación corta) en reposo: sin paciente. Queda en la bandeja «Sin asignar» de la web y el
//       promotor la asigna cuando hay internet.
//     · Página local del aparato (webpage.h): desde un celular en la misma red se abre la IP que
//       muestra la pantalla de reposo, se escribe el PIN y el código del paciente. No usa Internet.
//     · Orden «Medir» de la web: en reposo y con Wi-Fi, el aparato pregunta a la API cada pocos
//       segundos; si hay una orden, mide a ese paciente y la medición llega ya asignada.
//   Un solo botón. Reposo: corta = medir, larga = tara de la báscula. Midiendo: larga = cancelar.
//   Resultados: corta = guardar, larga = descartar.
// Antes de compilar: copiar secrets.example.h como secrets.h y llenarlo.

#include "alerts.h"
#include "config.h"
#include "display.h"
#include "input.h"
#include "secrets.h"
#include "sensors.h"
#include "storage.h"
#include "sync.h"
#include "webpage.h"

enum class State : uint8_t {
  IDLE,
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
// Última orden «Medir» atendida. Si se cancela o se descarta, la API la sigue ofreciendo hasta que
// vence (5 min); sin esto el aparato volvería a medir al mismo paciente.
static char lastCommand[CMD_ID_LEN] = "";

// Lecturas en vivo para la pantalla.
static float liveWeight = 0, liveTemp = 0;

static void enter(State next) {
  state = next;
  webpage::setIdle(next == State::IDLE);
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

// ───────────── paciente de la medición ─────────────

// Lo que se muestra como paciente: su código, o «Sin asignar» si la medición no lo trae.
static const char* patientLabel() { return current.patient[0] ? current.patient : "Sin asignar"; }

static void startMeasurement(const char* patient, const char* command) {
  memset(&current, 0, sizeof(current));
  strlcpy(current.patient, patient, sizeof(current.patient));
  strlcpy(current.command, command, sizeof(current.command));
  sensors::weightStart();
  alerts::beep();
  enter(State::MEASURE_WEIGHT);
}

// Si no se puede medir ahora, devuelve true y el motivo en dos líneas para la pantalla.
static bool measureBlocked(const char*& line1, const char*& line2) {
  if (!storageOk) {
    line1 = "Error de memoria", line2 = "No se puede medir";
  } else if (!syncer::timeValid()) {
    line1 = "Sin hora", line2 = "Conecta el Wi-Fi";
  } else if (storage::isFull()) {
    line1 = "Memoria llena", line2 = "Sincroniza primero";
  } else if (missingSensors & (sensors::SENSOR_HX711 | sensors::SENSOR_NTC | sensors::SENSOR_MAX)) {
    line1 = "Sensor sin responder", line2 = "Revisa las conexiones";
  } else {
    return false;
  }
  return true;
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
                                                   : "Corto:medir Largo:tara";
  char ip[28];
  display::show("GP03 Monitor", webpage::addressText(ip, sizeof(ip)) ? ip : wifiText(), l2, l3, footer);
}

static void idleState(input::Event ev) {
  if (due(500)) drawIdle();
  const char *why1, *why2;
  if (ev == input::Event::LONG) {
    sensors::tare();
    alerts::beep();
    showMessage("Bascula en cero", "Tara hecha", 1200);
  } else if (ev == input::Event::SHORT) {
    if (measureBlocked(why1, why2)) showMessage(why1, why2, 2500);
    else startMeasurement("", "");  // sin paciente: va a la bandeja «Sin asignar»
  } else if (ev == input::Event::NONE) {
    char commandId[CMD_ID_LEN], patient[PATIENT_CODE_LEN];
    // Primero lo que pide la página local (rápido); la consulta a la API puede tardar unos segundos.
    if (webpage::takeRequest(patient, sizeof(patient))) {
      if (measureBlocked(why1, why2)) showMessage(why1, why2, 2500);
      else startMeasurement(patient, "");
    } else if (syncer::takeCommand(commandId, sizeof(commandId), patient, sizeof(patient))) {
      // La API ofrece la orden mientras esté «tomada»: si ya se atendió (se canceló, se descartó
      // o venció la medición), no se repite. Si no se puede medir, vence sola a los 5 min.
      if (strcmp(commandId, lastCommand) == 0) return;
      strlcpy(lastCommand, commandId, sizeof(lastCommand));
      if (measureBlocked(why1, why2)) showMessage(why1, why2, 2500);
      else startMeasurement(patient, commandId);
    }
  }
}

static void cancelMeasurement(const char* reason) {
  showMessage("Medicion cancelada", reason, 2500);
}

static void weightState(input::Event ev) {
  if (ev == input::Event::LONG) return cancelMeasurement("");
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
    display::showBig("Peso", big, "Suba y quede quieto", patientLabel());
  }
}

static void temperatureState(input::Event ev) {
  if (ev == input::Event::LONG) return cancelMeasurement("");
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
    snprintf(line, sizeof(line), "Apoye en la piel %d%%", progress);
    display::showBig("Temperatura", big, line, patientLabel());
  }
}

static void oximeterState(input::Event ev) {
  if (ev == input::Event::LONG) return cancelMeasurement("");
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
    display::showBig("SpO2 y pulso", finger ? "Quieto..." : "- - -", line, patientLabel());
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
  showMessage("Guardado", patientLabel(), 1800);
}

static void resultsState(input::Event ev) {
  if (ev == input::Event::SHORT) return saveCurrent();
  if (ev == input::Event::LONG)
    return showMessage("Descartado", "No se guardo", 1500);
  if (due(500)) {
    char l1[28], l2[28];
    snprintf(l1, sizeof(l1), "%.1f kg  %.1f C", current.weightKg, current.tempC);
    snprintf(l2, sizeof(l2), "SpO2 %d%%  Pulso %d", current.spo2, current.bpm);
    display::show(current.alert ? "ALERTA" : "Resultado", l1, l2,
                  current.alert ? "Fuera de rango" : "Dentro del rango", "Corto:ok Largo:borrar");
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
  webpage::begin();
  if (missingSensors) {
    char list[28] = "";
    if (missingSensors & sensors::SENSOR_NTC) strcat(list, "NTC ");
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
  webpage::update();
  updateWarning();

  switch (state) {
    case State::IDLE: idleState(ev); break;
    case State::MEASURE_WEIGHT: weightState(ev); break;
    case State::MEASURE_TEMP: temperatureState(ev); break;
    case State::MEASURE_OXI: oximeterState(ev); break;
    case State::RESULTS: resultsState(ev); break;
    case State::MESSAGE:
      if ((long)(millis() - messageUntil) >= 0) enter(State::IDLE);
      break;
  }
}

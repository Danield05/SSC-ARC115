#include "sync.h"

#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <time.h>

#include "certs.h"
#include "config.h"
#include "secrets.h"
#include "storage.h"

namespace syncer {

static Status g_status = Status::OFFLINE;
static const char* g_message = "Sin enviar";
static bool g_wifiStarted = false;
static bool g_ntpStarted = false;
static unsigned long g_lastWifiTry = 0;
static unsigned long g_nextAttempt = 0;
static unsigned long g_backoff = SYNC_BACKOFF_MIN_MS;
static unsigned long g_lastPatients = 0;
static bool g_patientsTried = false;

// ───────────── hora ─────────────

bool timeValid() { return time(nullptr) >= MIN_VALID_EPOCH; }

bool nowIso(char* out, size_t size) {
  time_t t = time(nullptr);
  if (t < MIN_VALID_EPOCH) return false;
  struct tm utc;
  gmtime_r(&t, &utc);
  strftime(out, size, "%Y-%m-%dT%H:%M:%SZ", &utc);
  return true;
}

Status status() { return g_status; }
const char* lastMessage() { return g_message; }

// ───────────── HTTP ─────────────

static String url(const String& path) { return String(API_URL) + path; }

// Hace la petición con el certificado de la API verificado. Devuelve el código HTTP (negativo si
// no hubo conexión) y deja la respuesta en `response`.
static int request(const char* method, const String& path, const String& body, String& response) {
  WiFiClientSecure client;
  client.setCACert(ROOT_CA);  // setInsecure() solo para pruebas, y habría que declararlo
  HTTPClient http;
  http.setTimeout(HTTP_TIMEOUT_MS);
  http.setConnectTimeout(10000);
  if (!http.begin(client, url(path))) return -1;
  http.addHeader("x-api-key", API_KEY);
  int code;
  if (strcmp(method, "POST") == 0) {
    http.addHeader("Content-Type", "application/json");
    code = http.POST(body);
  } else {
    code = http.GET();
  }
  if (code > 0) response = http.getString();
  http.end();
  return code;
}

static void fail() {
  g_message = "Reintentando";
  g_nextAttempt = millis() + g_backoff;
  g_backoff = min(g_backoff * 2, (unsigned long)SYNC_BACKOFF_MAX_MS);
}

// ───────────── lista de pacientes ─────────────

// GET /devices/{id}/patients. La hora del servidor (server_time) no sirve para poner el reloj:
// con la fecha de 1970 el certificado TLS no se puede validar, así que la hora sale de NTP.
static void fetchPatients() {
  g_patientsTried = true;
  g_lastPatients = millis();
  String response;
  int code = request("GET", String("/devices/") + DEVICE_ID + "/patients", "", response);
  if (code == 401) {
    g_status = Status::KEY_INVALID;
    g_message = "Clave invalida";
    return;
  }
  if (code != 200) return;
  JsonDocument doc;
  if (deserializeJson(doc, response)) return;
  static char codes[MAX_PATIENTS][PATIENT_CODE_LEN];
  int n = 0;
  for (JsonVariant v : doc["patients"].as<JsonArray>()) {
    const char* c = v.as<const char*>();
    if (c && strlen(c) < PATIENT_CODE_LEN && n < MAX_PATIENTS) strcpy(codes[n++], c);
  }
  if (n > 0) storage::savePatients(codes, n);
}

// ───────────── envío de mediciones ─────────────

static float round1(float v) { return roundf(v * 10.0f) / 10.0f; }

static String buildBody(const Record* recs, int n) {
  JsonDocument doc;
  doc["device_id"] = DEVICE_ID;
  JsonArray arr = doc["records"].to<JsonArray>();
  for (int i = 0; i < n; i++) {
    JsonObject o = arr.add<JsonObject>();
    o["record_id"] = recs[i].id;
    o["patient_code"] = recs[i].patient;
    o["ts"] = recs[i].ts;
    o["weight_kg"] = round1(recs[i].weightKg);
    o["temp_c"] = round1(recs[i].tempC);
    o["spo2"] = recs[i].spo2;
    o["bpm"] = recs[i].bpm;
    o["alert"] = recs[i].alert;
  }
  String body;
  serializeJson(doc, body);
  return body;
}

static bool listHas(JsonArray list, const char* id) {
  for (JsonVariant v : list)
    if (strcmp(v.as<const char*>() ? v.as<const char*>() : "", id) == 0) return true;
  return false;
}

// Envía de a un registro para encontrar el que la API rechaza con 422 sin trabar la cola.
static void sendOneByOne(const Record* recs, int n) {
  for (int i = 0; i < n; i++) {
    if (recs[i].id[0] == 0) {  // línea dañada: se descarta
      storage::rejectFirst(recs[i]);
      continue;
    }
    String response;
    int code = request("POST", "/measurements", buildBody(&recs[i], 1), response);
    if (code == 200) {
      storage::markSynced(1);
    } else if (code == 422) {
      storage::rejectFirst(recs[i]);
    } else if (code == 401) {
      g_status = Status::KEY_INVALID;
      g_message = "Clave invalida";
      return;
    } else {
      fail();
      return;
    }
  }
  g_message = "Enviado";
  g_backoff = SYNC_BACKOFF_MIN_MS;
}

static void sendBatch() {
  static Record recs[SYNC_BATCH_SIZE];
  int n = storage::readPending(recs, SYNC_BATCH_SIZE);
  if (n == 0) return;

  // Las líneas dañadas no se pueden enviar: se resuelven una por una.
  for (int i = 0; i < n; i++) {
    if (recs[i].id[0] == 0) {
      sendOneByOne(recs, n);
      return;
    }
  }

  String response;
  int code = request("POST", "/measurements", buildBody(recs, n), response);
  g_status = Status::ONLINE;
  if (code == 200) {
    JsonDocument doc;
    if (deserializeJson(doc, response)) {
      fail();
      return;
    }
    JsonArray saved = doc["saved"].as<JsonArray>();
    JsonArray duplicates = doc["duplicates"].as<JsonArray>();
    // El puntero avanza con los ids de `saved` y de `duplicates`, en orden.
    int acknowledged = 0;
    while (acknowledged < n &&
           (listHas(saved, recs[acknowledged].id) || listHas(duplicates, recs[acknowledged].id)))
      acknowledged++;
    storage::markSynced(acknowledged);
    if (acknowledged < n) {
      fail();
    } else {
      g_message = "Enviado";
      g_backoff = SYNC_BACKOFF_MIN_MS;
      g_nextAttempt = 0;  // si queda más, se manda el siguiente lote enseguida
    }
  } else if (code == 401) {
    g_status = Status::KEY_INVALID;  // no se reintenta en bucle
    g_message = "Clave invalida";
  } else if (code == 422) {
    sendOneByOne(recs, n);
  } else {
    fail();  // 5xx o sin red
  }
}

// ───────────── ciclo principal ─────────────

void begin() {
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
}

void update(bool allowBlocking) {
  if (g_status == Status::KEY_INVALID) return;
  unsigned long now = millis();

  if (WiFi.status() != WL_CONNECTED) {
    g_status = g_wifiStarted && now - g_lastWifiTry < 10000 ? Status::CONNECTING : Status::OFFLINE;
    if (!g_wifiStarted || now - g_lastWifiTry >= WIFI_RETRY_MS) {
      WiFi.disconnect();
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
      g_wifiStarted = true;
      g_lastWifiTry = now;
    }
    return;
  }
  g_status = Status::ONLINE;
  if (!g_ntpStarted) {
    configTime(0, 0, NTP_SERVER_1, NTP_SERVER_2);  // el servidor guarda todo en UTC
    g_ntpStarted = true;
  }
  if (!allowBlocking || !timeValid()) return;  // con la fecha de 1970 el TLS no valida

  if (!g_patientsTried || now - g_lastPatients >= PATIENTS_REFRESH_MS) fetchPatients();
  if (g_status == Status::KEY_INVALID) return;

  if (storage::pendingCount() > 0 && now >= g_nextAttempt) sendBatch();
}

}  // namespace syncer

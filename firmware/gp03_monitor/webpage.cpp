#include "webpage.h"

#include <WebServer.h>
#include <WiFi.h>

#include "config.h"
#include "secrets.h"
#include "storage.h"

// El PIN va en secrets.h (ignorado por git). Sin él, la página no se enciende.
#ifndef LOCAL_PIN
#define LOCAL_PIN ""
#endif

namespace webpage {

static WebServer server(LOCAL_PAGE_PORT);
static bool g_started = false;
static bool g_idle = false;

static bool g_pending = false;
static char g_patient[PATIENT_CODE_LEN];
static unsigned long g_requestedAt = 0;

static uint8_t g_fails = 0;
static bool g_blocked = false;
static unsigned long g_blockedUntil = 0;

bool enabled() { return strlen(LOCAL_PIN) >= 4; }

// ───────────── validaciones ─────────────

// Compara sin cortar en la primera diferencia (no delata cuántos caracteres acertó).
static bool pinMatches(const String& given) {
  const char* pin = LOCAL_PIN;
  size_t n = strlen(pin);
  if (given.length() != n) return false;
  uint8_t diff = 0;
  for (size_t i = 0; i < n; i++) diff |= (uint8_t)given[i] ^ (uint8_t)pin[i];
  return diff == 0;
}

// Mismo formato que acepta la API: letras, números y guiones.
static bool validPatient(const String& code) {
  if (code.length() == 0 || code.length() >= PATIENT_CODE_LEN) return false;
  for (size_t i = 0; i < code.length(); i++) {
    char c = code[i];
    bool ok = (c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c == '-';
    if (!ok) return false;
  }
  return true;
}

// ───────────── página ─────────────

static const char STYLE[] PROGMEM =
    "<style>body{font-family:system-ui,sans-serif;margin:0;background:#f4f7f7;color:#1f2937}"
    "main{max-width:420px;margin:0 auto;padding:20px}"
    "h1{font-size:22px;margin:0 0 4px;color:#115e59}p{margin:6px 0}"
    ".card{background:#fff;border-radius:12px;padding:16px;margin-top:14px;border:1px solid #e5e7eb}"
    "label{display:block;margin-top:12px;font-weight:600;font-size:14px}"
    "input{width:100%;box-sizing:border-box;padding:12px;font-size:18px;border:1px solid #9ca3af;border-radius:8px}"
    "button{width:100%;margin-top:16px;padding:14px;font-size:18px;font-weight:700;color:#fff;"
    "background:#0f766e;border:0;border-radius:8px}"
    ".ok{background:#ecfdf5;border-color:#34d399}.err{background:#fef2f2;border-color:#f87171}"
    ".muted{color:#6b7280;font-size:13px}</style>";

static String pageStart() {
  String html = F("<!doctype html><html lang='es'><head><meta charset='utf-8'>"
                  "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                  "<title>GP03 Monitor</title>");
  html += FPSTR(STYLE);
  html += F("</head><body><main><h1>GP03 Monitor</h1><p class='muted'>");
  html += DEVICE_ID;
  html += F("</p>");
  return html;
}

static void sendPage(int code, const String& body) {
  server.sendHeader("Cache-Control", "no-store");
  server.send(code, "text/html; charset=utf-8", body);
}

static void handleRoot() {
  String html = pageStart();
  html += F("<div class='card'><p><b>Estado:</b> ");
  html += g_idle ? F("listo para medir") : F("ocupado (midiendo o mostrando un mensaje)");
  html += F("</p><p><b>Pendientes de sincronizar:</b> ");
  html += String((unsigned long)storage::pendingCount());
  html += F("</p><p><b>Memoria usada:</b> ");
  html += String(storage::usedPercent());
  html += F(" %</p></div>");
  html += F("<form class='card' method='post' action='/medir'>"
            "<label for='p'>Código del paciente</label>"
            "<input id='p' name='p' placeholder='P-0004' maxlength='19' required "
            "autocapitalize='characters' autocomplete='off'>"
            "<label for='pin'>PIN</label>"
            "<input id='pin' name='pin' type='password' inputmode='numeric' maxlength='12' required "
            "autocomplete='off'>"
            "<button type='submit'>Medir</button></form>"
            "<p class='muted'>La medición queda guardada a nombre de ese paciente y se envía a la "
            "nube cuando haya internet.</p></main></body></html>");
  sendPage(200, html);
}

static void reply(int code, const String& message, bool ok) {
  String html = pageStart();
  html += ok ? F("<div class='card ok'><p>") : F("<div class='card err'><p>");
  html += message;
  html += F("</p></div><p><a href='/'>Volver</a></p></main></body></html>");
  sendPage(code, html);
}

static void handleMeasure() {
  unsigned long now = millis();
  if (g_blocked && (long)(now - g_blockedUntil) < 0) {
    return reply(429, F("Demasiados intentos con PIN incorrecto. Espera un minuto."), false);
  }
  g_blocked = false;

  if (!pinMatches(server.arg("pin"))) {
    if (++g_fails >= WEB_FAIL_LIMIT) {
      g_fails = 0;
      g_blocked = true;
      g_blockedUntil = now + WEB_BLOCK_MS;
    }
    return reply(403, F("PIN incorrecto."), false);
  }
  g_fails = 0;

  String patient = server.arg("p");
  patient.trim();
  patient.toUpperCase();
  if (!validPatient(patient)) {
    return reply(400, F("Código de paciente no válido. Usa letras, números y guiones, por ejemplo P-0004."), false);
  }
  if (!g_idle) {
    return reply(409, F("El aparato está ocupado. Intenta de nuevo cuando termine."), false);
  }

  patient.toCharArray(g_patient, sizeof(g_patient));
  g_requestedAt = now;
  g_pending = true;
  reply(200, "Orden enviada. Mira la pantalla del aparato: medirá a <b>" + patient + "</b>.", true);
}

// ───────────── ciclo ─────────────

void begin() {
  if (!enabled()) {
    Serial.println("Pagina local apagada: define LOCAL_PIN (4 caracteres o mas) en secrets.h");
    return;
  }
  server.on("/", HTTP_GET, handleRoot);
  server.on("/medir", HTTP_POST, handleMeasure);
  server.onNotFound([]() { server.send(404, "text/plain", "No encontrado"); });
}

void update() {
  if (!enabled()) return;
  if (!g_started && WiFi.status() == WL_CONNECTED) {
    server.begin();
    g_started = true;
    Serial.printf("Pagina local: http://%s\n", WiFi.localIP().toString().c_str());
  }
  if (g_started) server.handleClient();
}

void setIdle(bool idle) { g_idle = idle; }

bool takeRequest(char* patient, size_t size) {
  if (!g_pending) return false;
  g_pending = false;
  if (millis() - g_requestedAt > WEB_REQUEST_TTL_MS) return false;  // venció sin que la tomara
  if (strlen(g_patient) >= size) return false;
  strcpy(patient, g_patient);
  return true;
}

bool addressText(char* out, size_t size) {
  if (!enabled() || WiFi.status() != WL_CONNECTED) return false;
  snprintf(out, size, "IP %s", WiFi.localIP().toString().c_str());
  return true;
}

}  // namespace webpage

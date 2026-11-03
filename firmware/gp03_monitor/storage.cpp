#include "storage.h"

#include "secrets.h"

#include <LittleFS.h>
#include <Preferences.h>

namespace storage {

static const char* QUEUE = "/queue.csv";
static const char* QUEUE_TMP = "/queue.tmp";
static const char* INDEX = "/sync.idx";
static const char* COMPACT = "/compact.cfg";
static const char* PATIENTS = "/patients.csv";
static const char* REJECTED = "/rejected.csv";
static const size_t LINE_BYTES = 160;

static Preferences prefs;
static uint32_t g_total = 0;    // líneas en /queue.csv
static uint32_t g_synced = 0;   // líneas ya enviadas (al inicio del archivo)
static uint32_t g_offset = 0;   // byte donde empieza la primera línea pendiente

// ───────────── utilidades ─────────────

// Lee una línea (sin el \n). Devuelve su largo en bytes con el \n incluido, o 0 al terminar.
static size_t readLine(File& f, char* buf, size_t size) {
  if (!f.available()) return 0;
  size_t n = f.readBytesUntil('\n', buf, size - 1);
  buf[n] = 0;
  if (n > 0 && buf[n - 1] == '\r') buf[n - 1] = 0;
  return n + 1;
}

static bool parseLine(const char* line, Record& r) {
  char copy[LINE_BYTES];
  strncpy(copy, line, sizeof(copy) - 1);
  copy[sizeof(copy) - 1] = 0;
  char* fields[8];
  int count = 0;
  char* p = copy;
  while (count < 8) {
    fields[count++] = p;
    char* comma = strchr(p, ',');
    if (!comma) break;
    *comma = 0;
    p = comma + 1;
  }
  if (count != 8) return false;
  if (strlen(fields[0]) >= sizeof(r.id) || strlen(fields[1]) >= sizeof(r.patient) ||
      strlen(fields[2]) >= sizeof(r.ts))
    return false;
  strcpy(r.id, fields[0]);
  strcpy(r.patient, fields[1]);
  strcpy(r.ts, fields[2]);
  r.weightKg = atof(fields[3]);
  r.tempC = atof(fields[4]);
  r.spo2 = atoi(fields[5]);
  r.bpm = atoi(fields[6]);
  r.alert = atoi(fields[7]) != 0;
  return true;
}

static void formatLine(const Record& r, char* out, size_t size) {
  snprintf(out, size, "%s,%s,%s,%.1f,%.1f,%d,%d,%d\n", r.id, r.patient, r.ts, r.weightKg, r.tempC,
           r.spo2, r.bpm, r.alert ? 1 : 0);
}

static void saveIndex() {
  File f = LittleFS.open(INDEX, FILE_WRITE);
  if (!f) return;
  f.printf("%lu %lu\n", (unsigned long)g_offset, (unsigned long)g_synced);
  f.flush();
  f.close();
}

static void loadIndex() {
  g_offset = 0;
  g_synced = 0;
  File f = LittleFS.open(INDEX, FILE_READ);
  if (!f) return;
  char buf[48];
  size_t n = f.readBytes(buf, sizeof(buf) - 1);
  buf[n] = 0;
  f.close();
  unsigned long off = 0, syn = 0;
  if (sscanf(buf, "%lu %lu", &off, &syn) == 2) {
    g_offset = off;
    g_synced = syn;
  }
}

static uint32_t countLines() {
  File f = LittleFS.open(QUEUE, FILE_READ);
  if (!f) return 0;
  uint32_t lines = 0;
  uint8_t chunk[256];
  while (f.available()) {
    size_t n = f.read(chunk, sizeof(chunk));
    for (size_t i = 0; i < n; i++)
      if (chunk[i] == '\n') lines++;
  }
  f.close();
  return lines;
}

// Si el programa se cortó a medio registro, la línea quedó sin \n: se cierra para que el
// siguiente registro no se pegue a ella.
static void closePartialLine() {
  File f = LittleFS.open(QUEUE, FILE_READ);
  if (!f || f.size() == 0) {
    if (f) f.close();
    return;
  }
  f.seek(f.size() - 1);
  int last = f.read();
  f.close();
  if (last == '\n') return;
  File a = LittleFS.open(QUEUE, FILE_APPEND);
  if (a) {
    a.print('\n');
    a.flush();
    a.close();
  }
}

// ───────────── compactación: conservar los últimos registros ─────────────
// Orden seguro ante un corte de energía: 1) /queue.tmp completo, 2) /compact.cfg con el puntero
// nuevo, 3) se borra la cola y se renombra, 4) se escribe el puntero, 5) se borra el cfg.
// recoverCompaction() termina el trabajo si el corte ocurrió entre esos pasos.

static void recoverCompaction() {
  if (!LittleFS.exists(COMPACT)) {
    LittleFS.remove(QUEUE_TMP);  // un tmp sin cfg está incompleto: se descarta
    return;
  }
  File c = LittleFS.open(COMPACT, FILE_READ);
  char buf[48];
  size_t n = c ? c.readBytes(buf, sizeof(buf) - 1) : 0;
  buf[n] = 0;
  if (c) c.close();
  unsigned long off = 0, syn = 0;
  if (sscanf(buf, "%lu %lu", &off, &syn) == 2) {
    if (LittleFS.exists(QUEUE_TMP)) {
      LittleFS.remove(QUEUE);
      LittleFS.rename(QUEUE_TMP, QUEUE);
    }
    g_offset = off;
    g_synced = syn;
    saveIndex();
  }
  LittleFS.remove(COMPACT);
}

static void compact() {
  uint32_t keep = usedPercent() >= MEMORY_WARN_PERCENT + 10 ? 500 : MAX_KEEP_RECORDS;
  if (g_total <= keep) return;
  uint32_t drop = g_total - keep;
  if (drop > g_synced) drop = g_synced;  // jamás se borra algo sin sincronizar
  if (drop == 0) return;

  File src = LittleFS.open(QUEUE, FILE_READ);
  if (!src) return;
  char line[LINE_BYTES];
  uint32_t dropBytes = 0;
  for (uint32_t i = 0; i < drop; i++) {
    size_t n = readLine(src, line, sizeof(line));
    if (n == 0) break;
    dropBytes += n;
  }
  File dst = LittleFS.open(QUEUE_TMP, FILE_WRITE);
  if (!dst) {
    src.close();
    return;
  }
  uint8_t chunk[256];
  bool ok = true;
  while (src.available()) {
    size_t n = src.read(chunk, sizeof(chunk));
    if (dst.write(chunk, n) != n) {
      ok = false;
      break;
    }
  }
  dst.flush();
  dst.close();
  src.close();
  if (!ok) {
    LittleFS.remove(QUEUE_TMP);
    return;
  }

  uint32_t newOffset = g_offset - dropBytes;
  uint32_t newSynced = g_synced - drop;
  File c = LittleFS.open(COMPACT, FILE_WRITE);
  if (!c) {
    LittleFS.remove(QUEUE_TMP);
    return;
  }
  c.printf("%lu %lu\n", (unsigned long)newOffset, (unsigned long)newSynced);
  c.flush();
  c.close();
  LittleFS.remove(QUEUE);
  LittleFS.rename(QUEUE_TMP, QUEUE);
  g_offset = newOffset;
  g_synced = newSynced;
  g_total -= drop;
  saveIndex();
  LittleFS.remove(COMPACT);
}

// ───────────── API pública ─────────────

bool begin() {
  if (!LittleFS.begin(true)) return false;  // true = formatear si es la primera vez
  prefs.begin("gp03", false);
  recoverCompaction();
  if (!LittleFS.exists(QUEUE)) {
    File f = LittleFS.open(QUEUE, FILE_WRITE);
    if (f) f.close();
  }
  closePartialLine();
  loadIndex();
  g_total = countLines();
  File f = LittleFS.open(QUEUE, FILE_READ);
  uint32_t size = f ? f.size() : 0;
  if (f) f.close();
  // Puntero corrupto o de otro archivo: se reenvía desde el inicio (el servidor ignora duplicados).
  if (g_synced > g_total || g_offset > size) {
    g_offset = 0;
    g_synced = 0;
    saveIndex();
  }
  compact();
  return true;
}

uint32_t nextSequence() {
  uint32_t next = prefs.getUInt("seq", 0) + 1;
  prefs.putUInt("seq", next);
  return next;
}

void makeRecordId(char* out, size_t size, uint32_t sequence) {
  snprintf(out, size, "%s-%06lu", DEVICE_ID, (unsigned long)sequence);
}

bool append(const Record& record) {
  if (usedPercent() >= MEMORY_WARN_PERCENT + 10) compact();
  if (isFull()) return false;
  char line[LINE_BYTES];
  formatLine(record, line, sizeof(line));
  File f = LittleFS.open(QUEUE, FILE_APPEND);
  if (!f) return false;
  size_t len = strlen(line);
  bool ok = f.write((const uint8_t*)line, len) == len;
  f.flush();
  f.close();
  if (ok) g_total++;
  return ok;
}

int readPending(Record* out, int maxCount) {
  File f = LittleFS.open(QUEUE, FILE_READ);
  if (!f) return 0;
  f.seek(g_offset);
  char line[LINE_BYTES];
  int n = 0;
  while (n < maxCount && (uint32_t)n < g_total - g_synced) {
    if (readLine(f, line, sizeof(line)) == 0) break;
    if (!parseLine(line, out[n])) {
      memset(&out[n], 0, sizeof(Record));  // id vacío: línea dañada
    }
    n++;
  }
  f.close();
  return n;
}

void markSynced(int count) {
  if (count <= 0) return;
  File f = LittleFS.open(QUEUE, FILE_READ);
  if (!f) return;
  f.seek(g_offset);
  char line[LINE_BYTES];
  uint32_t bytes = 0;
  int done = 0;
  while (done < count) {
    size_t n = readLine(f, line, sizeof(line));
    if (n == 0) break;
    bytes += n;
    done++;
  }
  f.close();
  g_offset += bytes;
  g_synced += done;
  saveIndex();
  compact();
}

void rejectFirst(const Record& record) {
  File f = LittleFS.open(REJECTED, FILE_APPEND);
  if (f) {
    char line[LINE_BYTES];
    formatLine(record, line, sizeof(line));
    f.print(line);
    f.flush();
    f.close();
  }
  markSynced(1);
}

uint32_t pendingCount() { return g_total - g_synced; }
uint32_t totalCount() { return g_total; }

uint8_t usedPercent() {
  size_t total = LittleFS.totalBytes();
  if (total == 0) return 0;
  return (uint8_t)((uint64_t)LittleFS.usedBytes() * 100 / total);
}

bool isFull() { return usedPercent() >= MEMORY_FULL_PERCENT; }

void savePatients(const char codes[][PATIENT_CODE_LEN], int count) {
  File f = LittleFS.open(PATIENTS, FILE_WRITE);
  if (!f) return;
  for (int i = 0; i < count; i++) f.println(codes[i]);
  f.flush();
  f.close();
}

int loadPatients(char codes[][PATIENT_CODE_LEN], int maxCount) {
  File f = LittleFS.open(PATIENTS, FILE_READ);
  if (!f) return 0;
  int n = 0;
  char line[PATIENT_CODE_LEN + 4];
  while (n < maxCount && readLine(f, line, sizeof(line)) > 0) {
    if (line[0] == 0 || strlen(line) >= PATIENT_CODE_LEN) continue;
    strcpy(codes[n++], line);
  }
  f.close();
  return n;
}

}  // namespace storage

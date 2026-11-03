// Prueba F0 · LittleFS en la flash interna. Muestra el tamaño de la flash y de la partición, y
// comprueba que un registro escrito con flush se puede volver a leer (también tras reiniciar).
#include <LittleFS.h>

void setup() {
  Serial.begin(115200);
  delay(500);
  if (!LittleFS.begin(true)) {
    Serial.println("No se pudo montar LittleFS.");
    return;
  }
  Serial.printf("Flash: %u bytes\n", ESP.getFlashChipSize());
  Serial.printf("LittleFS: %u bytes en total, %u usados\n", (unsigned)LittleFS.totalBytes(),
                (unsigned)LittleFS.usedBytes());
  Serial.printf("Capacidad estimada: %u registros de ~70 bytes\n", (unsigned)(LittleFS.totalBytes() / 70));

  File f = LittleFS.open("/prueba.csv", FILE_APPEND);
  f.printf("registro de prueba %lu\n", (unsigned long)millis());
  f.flush();
  f.close();

  f = LittleFS.open("/prueba.csv", FILE_READ);
  Serial.println("Contenido de /prueba.csv (debe crecer con cada reinicio):");
  while (f.available()) Serial.write(f.read());
  f.close();
}

void loop() {}

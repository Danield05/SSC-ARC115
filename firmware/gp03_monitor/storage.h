// Cola local de mediciones en la flash interna (LittleFS).
//
//   /queue.csv   una línea por registro: record_id,patient_code,ts,weight_kg,temp_c,spo2,bpm,alert
//                [,command_id]  (patient_code vacío = sin paciente; command_id solo si vino de una
//                orden «Medir» de la web; las líneas viejas de 8 campos se siguen leyendo)
//   /sync.idx    puntero de sincronización: "<byte inicial de lo pendiente> <registros ya enviados>"
//   /rejected.csv  registros que la API rechazó con 422
//
// Regla de oro: nunca se borra un registro que no se haya sincronizado. Cada registro se guarda
// con flush antes de dar la medición por buena.
#pragma once
#include <Arduino.h>
#include "config.h"

struct Record {
  char id[40];                      // vacío = línea dañada (se descarta al sincronizar)
  char patient[PATIENT_CODE_LEN];   // vacío = sin paciente: va a la bandeja «Sin asignar»
  char command[CMD_ID_LEN];         // id de la orden «Medir» que originó el registro (o vacío)
  char ts[24];                      // ISO-8601 UTC con Z
  float weightKg;
  float tempC;
  int spo2;
  int bpm;
  bool alert;
};

namespace storage {

bool begin();

// Número de secuencia que sobrevive a reinicios (NVS). Si se borra toda la flash al subir el
// programa, el contador vuelve a 0 y el servidor responderá "duplicates" hasta superar el anterior.
uint32_t nextSequence();
void makeRecordId(char* out, size_t size, uint32_t sequence);

bool append(const Record& record);

// Hasta maxCount registros pendientes, del más antiguo al más nuevo.
int readPending(Record* out, int maxCount);
// Avanza el puntero sobre los primeros `count` pendientes (enviados o duplicados).
void markSynced(int count);
// Mueve el primer pendiente a /rejected.csv y avanza el puntero.
void rejectFirst(const Record& record);

uint32_t pendingCount();
uint32_t totalCount();
uint8_t usedPercent();
bool isFull();  // memoria casi llena (ya se intentó liberar lo sincronizado)

}  // namespace storage

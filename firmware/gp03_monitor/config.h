// Configuración del firmware GP03: pines, umbrales, tamaños y calibración.
// Nada de esto es secreto. Las credenciales van en secrets.h (ver secrets.example.h).
#pragma once

// ───────────── Pines (cableado del prototipo, tomado de codigo.txt el 7-nov-2026) ─────────────
// Reglas del ESP32: no usar GPIO 6 a 11 (flash); 34 a 39 son solo entrada;
// cuidado con 0, 2, 12 y 15 (arranque). El LED verde en GPIO12 funciona si va a GND con su
// resistencia; si el equipo no arranca, no debe haber nada que lleve ese pin a 3.3 V.
#define PIN_I2C_SDA 21     // OLED 0x3C, MAX30102 0x57
#define PIN_I2C_SCL 22
#define PIN_HX711_DT 18    // alimentar el HX711 a 3.3 V
#define PIN_HX711_SCK 19
#define PIN_LED_GREEN 12
#define PIN_LED_YELLOW 14
#define PIN_LED_RED 13
#define PIN_BUZZER 27
#define PIN_NTC 35         // termistor NTC: ADC1, solo entrada. Cableado: 3V3 → NTC → GPIO35 → 10 kΩ → GND
#define PIN_BTN_NEXT 4     // botón 1: siguiente (pulsación larga: tara de la báscula)
#define PIN_BTN_OK 26      // botón 2: aceptar (pulsación larga: cancelar). PROVISIONAL: el prototipo
                           // solo tiene un botón; cablear el segundo a GPIO26 y GND.

#define I2C_CLOCK_HZ 100000  // I2C estándar (100 kHz)
#define OLED_ADDRESS 0x3C

// ───────────── Umbrales de alerta (los mismos que el servidor) ─────────────
#define TEMP_LOW_C 35.0f
#define TEMP_HIGH_C 38.0f
#define SPO2_MIN 92

// ───────────── Peso (celdas de carga + HX711) ─────────────
// Factor de calibración: (lectura cruda − tara) / kg. Se obtiene con
// firmware/pruebas/hx711_calibracion y masas patrón de 5, 10 y 20 kg.
#define HX711_SCALE_FACTOR 1.0f
#define WEIGHT_SAMPLE_MS 100
#define WEIGHT_WINDOW_MS 2000      // estable = variación <= WEIGHT_STABLE_KG durante este tiempo
#define WEIGHT_STABLE_KG 0.1f
#define WEIGHT_MIN_KG 1.0f         // por debajo se considera la báscula vacía
#define WEIGHT_MAX_KG 500.0f       // límite del contrato con la API

// ───────────── Temperatura (termistor NTC de 100 kΩ, de CONTACTO) ─────────────
// Se apoya sobre la piel y tarda en llegar a su temperatura, así que la lectura se da por buena
// cuando se estabiliza (poca variación durante TEMP_WINDOW_MS). Se calibra con al menos 10
// mediciones contra un termómetro clínico, siempre en la misma zona y con el mismo contacto.
// Se limpia entre pacientes.
#define NTC_R_FIXED 10000.0f       // resistencia fija del divisor (ohmios)
#define NTC_R0 100000.0f           // resistencia del NTC a NTC_T0_C
#define NTC_BETA 3950.0f
#define NTC_T0_C 25.0f
#define NTC_ADC_SAMPLES 16         // lecturas del ADC que se promedian en cada muestra (baja el ruido)
#define NTC_ADC_MIN_OK 50          // ADC pegado a un extremo = NTC desconectado o en corto
#define NTC_ADC_MAX_OK 4045
// Valor heredado del código de Roberto; recalibrar contra un termómetro de referencia.
// Un NTC bien cableado no debería necesitar restar 20 °C: si hace falta, revisar el divisor.
#define TEMP_OFFSET_C -20.0f
#define TEMP_SAMPLE_MS 250
#define TEMP_WINDOW_MS 4000        // estable = variación <= TEMP_STABLE_C durante este tiempo
#define TEMP_STABLE_C 0.2f
#define TEMP_VALID_MIN_C 25.0f     // fuera de este rango no hay lectura (sensor al aire o sin contacto)
#define TEMP_VALID_MAX_C 45.0f

// ───────────── Oximetría (MAX30102) ─────────────
#define FINGER_IR_MIN 50000UL      // señal IR por debajo de esto = sin dedo
#define OXI_BUFFER 100             // muestras por cálculo (≈ 4 s a 25 muestras/s)
#define OXI_STEP 25                // muestras nuevas entre cálculos (≈ 1 s)
#define OXI_GOOD_NEEDED 5          // lecturas válidas que se promedian
#define OXI_SPO2_VALID_MIN 70
#define OXI_BPM_VALID_MIN 30
#define OXI_BPM_VALID_MAX 220

// ───────────── Tiempos de la interfaz ─────────────
#define MEASURE_TIMEOUT_MS 60000UL // cada paso de medición se cancela si no termina
#define BTN_DEBOUNCE_MS 30
#define BTN_LONG_MS 800
#define ALERT_BUZZ_MS 5000UL

// ───────────── Almacenamiento local (LittleFS en la flash interna) ─────────────
// ≈ 70 bytes por registro. Con la partición por defecto (≈ 1,5 MB) caben ≈ 21.000.
#define MAX_KEEP_RECORDS 10000     // se conservan los últimos; nunca se borra uno sin sincronizar
#define MEMORY_WARN_PERCENT 80
#define MEMORY_FULL_PERCENT 95

// ───────────── Sincronización ─────────────
#define SYNC_BATCH_SIZE 20
#define HTTP_TIMEOUT_MS 25000      // el servidor manda el correo antes de responder (Gmail ≤ 10 s)
#define SYNC_BACKOFF_MIN_MS 5000UL
#define SYNC_BACKOFF_MAX_MS 300000UL
#define COMMAND_POLL_MS 5000UL     // cada cuánto se pregunta a la API si hay una orden «Medir»
#define COMMAND_TIMEOUT_MS 8000UL  // plazo de esa consulta (la de lotes espera hasta HTTP_TIMEOUT_MS)
#define COMMAND_CONNECT_MS 3000UL  // y para conectar: con Wi-Fi pero sin API no se bloquea ~18 s
#define COMMAND_POLL_FAIL_MS 20000UL  // si la API no responde, se consulta cada tanto
#define WIFI_RETRY_MS 15000UL
#define MIN_VALID_EPOCH 1767225600L  // 2026-01-01: antes de eso el reloj no se ha puesto
#define NTP_SERVER_1 "pool.ntp.org"
#define NTP_SERVER_2 "time.google.com"

// ───────────── Página local (ver webpage.h) ─────────────
#define LOCAL_PAGE_PORT 80
#define WEB_FAIL_LIMIT 5             // PIN incorrecto: tras este número de intentos se bloquea
#define WEB_BLOCK_MS 60000UL
#define WEB_REQUEST_TTL_MS 120000UL  // una orden de la página vence si el aparato no la toma

// ───────────── Pacientes ─────────────
// El dispositivo no elige paciente: la medición sale sin paciente (bandeja «Sin asignar» de la
// web) o con el de la orden «Medir» que dejó el promotor desde la web.
#define PATIENT_CODE_LEN 20
#define CMD_ID_LEN 24              // «CMD-» y 12 caracteres hexadecimales

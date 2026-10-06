// wall-e-robot/firmware/include/config.h
// Kevin Gámez - 13/09/2026

#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ============================================================
// MODULOS: el "interruptor" de pruebas aisladas.
//
// 1 = el módulo está cableado/activo en esta prueba.
// 0 = no se inicializa y reporta valores neutros (para que la
//     GUI no muestre alertas falsas por hardware ausente).
//
// Cambiada estas variables para probar SOLO lo que haya
// conectado en el banco, sin tocar el resto del código.
// ============================================================
typedef struct {
    bool servos;   // PCA9685 + servos de usuario (canales 0-4)
    bool radar;    // HC-SR04 + servo de barrido (canal 5)
    bool bateria;  // INA219 (voltaje/corriente)
    bool oled;     // SSD1306 0.96" (se deja apagado en la 1ª entrega)
    bool motores;  // L298N, 2 motores CC (d-pad)
} ModulosActivos;

static const ModulosActivos MODULOS = { true, true, false, false, false };

// --- Habilitación por servo de usuario (mismo orden que los canales 0-4) ---
// cuello, hombro_izquierdo, hombro_derecho, pulgar_izquierdo, pulgar_derecho.
// El servo del radar (canal 5) NO va aquí: lo gobierna el firmware en el
// barrido autónomo (ver CANAL_RADAR), no recibe comandos "servo" de la app.
static const bool SERVOS_ACTIVOS[] = { true, true, true, true, true };

// --- Canales de la PCA9685 ---
static const uint8_t CANAL_RADAR = 5;

// --- Red (modo AP: el ESP32 crea su propia red) ---
static const char* WIFI_AP_SSID        = "WALL-E";
static const char* WIFI_AP_CLAVE       = "wall-e-robot";
static const int   PUERTO_SERVIDOR     = 8080;

// --- Umbrales / tiempos (valores de arranque, calibrar con hardware) ---
static const float   UMBRAL_OBSTACULO_CM  = 15.0;   // "obstáculo cercano"
static const int     TIEMPO_MANUAL_TIMEOUT_MS = 2000;  // histéresis auto->manual

// --- Barrido del servo del radar ---
static const int      RADAR_SERVO_GRAUS_MIN = -45;
static const int      RADAR_SERVO_GRAUS_MAX = 45;
static const uint32_t PASO_BARRIDO_MS       = 50;

// --- Periodos de telemetría (loop no bloqueante por millis()) ---
static const uint32_t ENVIO_ESTADO_MS      = 500;
static const uint32_t LECTURA_RADAR_MS     = 250;
static const uint32_t LECTURA_BATERIA_MS   = 1000;

// --- Estimación de batería (2S LiPo típico; recalibrar con el pack real) ---
static const float BATERIA_VOLTAJE_MIN     = 6.6;    // ~ vacío
static const float BATERIA_VOLTAJE_MAX     = 8.4;    // ~ cargado
static const float BATERIA_CAPACIDAD_MAH   = 2000;   // capacidad del pack

#endif // CONFIG_H
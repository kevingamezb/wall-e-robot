// wall-e-robot/firmware/include/config.h
// Kevin Gámez - 13/09/2026

#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// MODULOS: el "interruptor" de pruebas aisladas.
//
// 1 = el módulo está cableado/activo en esta prueba.
// 0 = no se inicializa y reporta valores neutros (para que la
//     GUI no muestre alertas falsas por hardware ausente).
//
// Cambiada estas variables para probar SOLO lo que haya
// conectado en el banco, sin tocar el resto del código.

typedef struct {
    bool servos;   // 3 servos MG90S directos a GPIO (2 brazos + cuello)
    bool radar;    // HC-SR04 fijo al frente (sin servo de barrido)
    bool bateria;  // INA219 (voltaje/corriente)
    bool oled;     // SSD1306 0.96"
    bool motores;  // TB6612FNG, 2 motores CC (d-pad)
} ModulosActivos;

static const ModulosActivos MODULOS = { true, false, true, true, true };

// --- Habilitación por servo de usuario (mismo orden que la app) ---
// cuello, hombro_izquierdo, hombro_derecho, pulgar_izquierdo, pulgar_derecho.
// El hardware real solo trae 3 servos (cuello + los 2 brazos): los pulgares
// quedan en 0, pero su nombre sigue vivo en el protocolo para no tocar la app.
static const bool SERVOS_ACTIVOS[] = { true, true, true, false, false };

// --- Red (modo AP: el ESP32 crea su propia red) ---
static const char* WIFI_AP_SSID        = "WALL-E";
static const char* WIFI_AP_CLAVE       = "wall-e-robot";
static const int   PUERTO_SERVIDOR     = 8080;

// --- Umbrales / tiempos (valores de arranque, calibrar con hardware) ---
static const float   UMBRAL_OBSTACULO_CM  = 15.0;   // "obstáculo cercano"
// Timeout de presencia del operador en modo manual: si no llega ningún
// comando de la app en este tiempo, se detienen los motores (seguridad)
// y el robot puede volver a modo automático (histéresis auto->manual).
static const int     TIEMPO_MANUAL_TIMEOUT_MS = 2000;

// --- Periodos de telemetría (loop no bloqueante por millis()) ---
static const uint32_t ENVIO_ESTADO_MS      = 500;
static const uint32_t LECTURA_RADAR_MS     = 250;
static const uint32_t LECTURA_BATERIA_MS   = 1000;

// --- Estimación de batería (2S LiPo típico; recalibrar con el pack real) ---
static const float BATERIA_VOLTAJE_MIN     = 6.6;    // ~ vacío
static const float BATERIA_VOLTAJE_MAX     = 8.4;    // ~ cargado
static const float BATERIA_CAPACIDAD_MAH   = 2000;   // capacidad del pack

#endif // CONFIG_H
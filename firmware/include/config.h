// wall-e-robot/firmware/include/config.h
// Kevin Gámez - 13/09/2026

#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// Interruptor de pruebas aisladas: con un flag en false, el módulo no se
// inicializa y la telemetría reporta valores neutros. Así se prueba en el
// banco solo lo que esté cableado, sin tocar el resto del código.
typedef struct {
    bool servos;     // 3 servos MG90S (2 brazos + cuello)
    bool distancia;  // HC-SR04 fijo al frente (mide distancia, sin barrido)
    bool bateria;    // INA219
    bool oled;       // SSD1306 0.96"
    bool motores;    // TB6612FNG (d-pad)
} ModulosActivos;

static const ModulosActivos MODULOS = { true, false, true, true, true };

// Servos habilitados, en el orden que espera la app: cuello, hombro_izquierdo,
// hombro_derecho, pulgar_izquierdo, pulgar_derecho. El hardware real solo trae
// 3 servos: los pulgares quedan en false, pero conservan su nombre en el
// protocolo para no obligar a cambiar la app.
static const bool SERVOS_ACTIVOS[] = { true, true, true, false, false };

// Red en modo AP: el ESP32 crea su propia red.
static const char* WIFI_AP_SSID        = "WALL-E";
static const char* WIFI_AP_CLAVE       = "wall-e-robot";
static const int   PUERTO_SERVIDOR     = 8080;

// Valores de arranque: calibrar contra el hardware real.
static const float   UMBRAL_OBSTACULO_CM  = 15.0;   // distancia de "obstáculo cercano"

// Presencia del operador en modo manual
static const int     TIEMPO_MANUAL_TIMEOUT_MS = 2000;

// Periodos de telemetría y sensores (loop no bloqueante por millis()).
static const uint32_t ENVIO_ESTADO_MS      = 500;
static const uint32_t LECTURA_DISTANCIA_MS = 250;
static const uint32_t LECTURA_BATERIA_MS   = 1000;

// Estimación de batería para un 2S LiPo típico: nivel = (V - MIN) / (MAX - MIN).
// TODO(calibrar): ajustar MIN/MAX y la capacidad contra el pack real.
static const float BATERIA_VOLTAJE_MIN     = 6.6;    // ~vacío
static const float BATERIA_VOLTAJE_MAX     = 8.4;    // ~cargado
static const float BATERIA_CAPACIDAD_MAH   = 2000;   // capacidad del pack

#endif // CONFIG_H
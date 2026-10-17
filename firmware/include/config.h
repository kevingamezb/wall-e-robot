// wall-e-robot/firmware/include/config.h
// Kevin Gámez - 13/09/2026

#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// Credenciales: se usa secrets.h si existe (ver secrets.example.h); si no,
// los #ifndef siguientes aportan los valores por defecto.
#if __has_include("secrets.h")
    #include "secrets.h"
#endif
#ifndef WIFI_AP_CLAVE
    #define WIFI_AP_CLAVE ""
#endif
#ifndef OTA_USUARIO
    #define OTA_USUARIO "walle"
#endif
#ifndef OTA_CLAVE
    #define OTA_CLAVE ""
#endif

// Versión del firmware; se reporta en la telemetría y en el portal OTA.
static const char* PROYECTO_VERSION = "1.0.0";

// Hardware instalado: cada flag habilita la inicialización y el uso del
// módulo en setup()/loop().
typedef struct {
    bool servos;     // 3 servos MG90S (2 brazos + cuello)
    bool distancia;  // HC-SR04 fijo al frente (mide distancia, sin barrido)
    bool bateria;    // INA219
    bool oled;       // SSD1306 0.96"
    bool motores;    // TB6612FNG (d-pad)
} ModulosActivos;

// Configuración actual: todos los módulos activos.
static const ModulosActivos MODULOS = { true, true, true, true, true };

// true si algún módulo de MODULOS está desactivado (lo advierten los LEDs
// y la telemetría).
static inline bool hayModuloInactivo() {
    return !MODULOS.servos || !MODULOS.distancia || !MODULOS.bateria ||
           !MODULOS.oled   || !MODULOS.motores;
}

// Flags por servo en el orden de Servos::IndiceServo (cuello, brazo izq.,
// brazo der.); un false ignora el servo sin perder su ángulo comandado.
static const bool SERVOS_ACTIVOS[] = { true, true, true};

// SSID del AP WiFi y puerto del servidor TCP de telemetría/mando (app Python).
static const char* WIFI_AP_SSID        = "WALL-E";
static const int   PUERTO_SERVIDOR     = 8080;

// OTA
static const bool     OTA_ACTIVADO        = true;

// Plazo (ms) que la guardia de rollback espera la confirmación del self-test;
// si vence sin confirmar, se revierte a la versión anterior.
static const uint32_t OTA_AUTOCONFIRMA_MS = 15000;

// Puerto HTTP del portal web OTA.
static const int      PUERTO_OTA_WEB      = 80;

static const float   UMBRAL_OBSTACULO_CM  = 15.0;   // Distancia (cm) de "obstáculo cercano" (alerta)

// Sin órdenes del operador en modo manual durante este tiempo (ms), se
// detienen los motores.
static const int     TIEMPO_MANUAL_TIMEOUT_MS = 2000;

// Periodos (ms) de telemetría y sensores
static const uint32_t ENVIO_ESTADO_MS      = 500;   // envío del estado al cliente
static const uint32_t LECTURA_DISTANCIA_MS = 250;   // muestreo del HC-SR04
static const uint32_t LECTURA_BATERIA_MS   = 1000;  // lectura del INA219

// Estimación de batería: voltajes (V) entre los que se interpola el nivel
// y capacidad (mAh) para estimar la autonomía.
static const float BATERIA_VOLTAJE_MIN     = 6.6;
static const float BATERIA_VOLTAJE_MAX     = 8.4;
static const float BATERIA_CAPACIDAD_MAH   = 2000;

#endif // CONFIG_H
#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// secrets.h es obligatorio. Usa secrets.example.h como plantilla local.
#if !__has_include("secrets.h")
    #error "Falta firmware/include/secrets.h: copia secrets.example.h y define WIFI_AP_CLAVE, OTA_USUARIO y OTA_CLAVE."
#endif

#include "secrets.h"

// WPA2 exige 8 caracteres y sizeof cuenta también el terminador nulo.
static_assert(sizeof(WIFI_AP_CLAVE) >= 9,
              "WIFI_AP_CLAVE debe tener al menos 8 caracteres (WPA2).");
static_assert(sizeof(OTA_USUARIO) >= 2,
              "OTA_USUARIO no puede estar vacío.");
static_assert(sizeof(OTA_CLAVE) >= 9,
              "OTA_CLAVE debe tener al menos 8 caracteres.");

static const char* PROYECTO_VERSION = "1.1.0";

// Versión del protocolo TCP+JSON. La app (app/comunicacion/conexion.py)
// publica y valida el mismo número; subirlo solo cuando cambie el contrato.
static const int PROTOCOLO_VERSION = 1;

// Tamaño máximo de una línea JSON entrante. Si se supera sin '\n', se
// descarta completa para no agotar la RAM del ESP32.
static const int MAX_MENSAJE_ENTRANTE = 4096;

typedef struct {
    bool servos;     // 3 servos MG90S (2 brazos + cuello)
    bool distancia;  // HC-SR04 fijo al frente (mide distancia, sin barrido)
    bool bateria;    // INA219
    bool oled;       // SSD1306 0.96"
    bool motores;    // TB6612FNG (d-pad)
} ModulosActivos;

static const ModulosActivos MODULOS = { true, true, true, true, true };

static inline bool hayModuloInactivo() {
    return !MODULOS.servos || !MODULOS.distancia || !MODULOS.bateria ||
           !MODULOS.oled   || !MODULOS.motores;
}

// Flags por servo en el orden de Servos::IndiceServo (cuello, brazo izq.,
// brazo der.); un false ignora el servo sin perder su ángulo comandado.
static const bool SERVOS_ACTIVOS[] = { true, true, true};

static const char* WIFI_AP_SSID        = "WALL-E";
static const int   PUERTO_SERVIDOR     = 8080;

static const bool     OTA_ACTIVADO        = true;

// Plazo (ms) que la guardia de rollback espera la confirmación del self-test;
// si vence sin confirmar, se revierte a la versión anterior.
static const uint32_t OTA_AUTOCONFIRMA_MS = 15000;

static const int      PUERTO_OTA_WEB      = 80;

static const float   UMBRAL_OBSTACULO_CM  = 25.0;

// Sin órdenes del operador en modo manual durante este tiempo (ms), se
// detienen los motores.
static const int     TIEMPO_MANUAL_TIMEOUT_MS = 2000;

// El firmware arranca en manual para no moverse sin supervisión.
static const uint32_t TIEMPO_SIN_CONEXION_AUTOMATICO_MS = 600000;  // 10 min

static const uint32_t ENVIO_ESTADO_MS      = 500;
static const uint32_t LECTURA_DISTANCIA_MS = 250;
static const uint32_t LECTURA_BATERIA_MS   = 250;

// El PWM de los motores (1 kHz) mete transitorios en la lectura del INA219.
// Muestreo más rápido + filtro EMA para quedarnos con la tendencia.
static const float BATERIA_FILTRO_ALPHA = 0.5f;

// El nivel se actualiza en reposo para evitar el efecto de la caída de tensión bajo carga.
static const float   BATERIA_CORRIENTE_REPOSO_A = 0.05f;
static const uint32_t BATERIA_REPOSO_ESTABLE_MS = 500;

// Antigüedad máxima de la última medición para que Auto pueda moverse. Si el
// sensor deja de responder, los motores se detienen en vez de seguir a ciegas.
static const uint32_t TIEMPO_MAX_LECTURA_MS = 750;

// Estimación de batería: voltajes (V) entre los que se interpola el nivel
// y capacidad (mAh) para estimar la autonomía.
static const float BATERIA_VOLTAJE_MIN     = 6.6;
static const float BATERIA_VOLTAJE_MAX     = 8.4;
static const float BATERIA_CAPACIDAD_MAH   = 2000;

#endif

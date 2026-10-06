// wall-e-robot/firmware/src/main.cpp
// Kevin Gámez - 13/09/2026

#include <Arduino.h>
#include <WiFi.h>

#include "config.h"
#include "comunicacion.h"
#include "servos.h"
#include "motores.h"
#include "radar.h"
#include "bateria.h"
#include "oled.h"


// Instancia única del servidor de comunicación. La logica de negocio
// (main) se conecta a ella, sin saber nada de JSON ni TCP.
Comunicacion comunicacion(PUERTO_SERVIDOR);

// Marcas de tiempo para el loop no bloqueante (por millis()).
static uint32_t s_ultimaEnvioMs   = 0;
static uint32_t s_ultimaBateriaMs = 0;

// Transiciones de alerta: solo se loguea al ENCENDER la alerta (cooldown),
// no en cada envío de estado mientras la alerta persiste.
static bool s_advertenciaAnterior = false;
static bool s_errorAnterior       = false;


void setup() {

    Serial.begin(115200);
    delay(300);   // tiempo para que el monitor USB termine de arrancar

    // ===== 1) Red: el ESP32 crea su propia WiFi (modo AP) =====
    WiFi.mode(WIFI_AP);
    WiFi.softAP(WIFI_AP_SSID, WIFI_AP_CLAVE);
    Serial.print("AP iniciada: SSID='");
    Serial.print(WIFI_AP_SSID);
    Serial.print("' IP=");
    Serial.println(WiFi.softAPIP());

    comunicacion.iniciarServidor();

    // ===== 2) Módulos (solo si su flag de pruebas aisladas está en 1) =====
    // config.h -> MODULOS.{servos, radar, bateria, oled, motores}.
    // Con un flag en 0, el módulo NO se toca (ni se mueve ni se lee) y
    // la telemetría manda valores neutros para que la GUI no grite.
    if (MODULOS.servos) {
        servos.iniciar();
        Serial.println("MODULO servos   = activo");
    } else {
        Serial.println("MODULO servos   = INACTIVO (flag=0)");
    }

    if (MODULOS.radar) {
        // El barrido del radar necesita la placa PCA9685 para mover el
        // servo (canal 5), aunque el modulo de servos esté en 0.
        if (!MODULOS.servos) {
            servos.iniciar();   // solo inicia la PCA9685, sin servos de usuario
        }
        radar.iniciar();
        Serial.println("MODULO radar    = activo");
    } else {
        Serial.println("MODULO radar    = INACTIVO (flag=0)");
    }

    if (MODULOS.bateria) {
        bateria.iniciar();
        Serial.println("MODULO bateria  = activo");
    } else {
        Serial.println("MODULO bateria  = INACTIVO (flag=0)");
    }

    if (MODULOS.motores) {
        motores.iniciar();
        Serial.println("MODULO motores  = activo");
    } else {
        Serial.println("MODULO motores  = INACTIVO (flag=0)");
    }

    if (MODULOS.oled) {
        oled.iniciar();
        Serial.println("MODULO oled     = activo");
    } else {
        Serial.println("MODULO oled     = INACTIVO (flag=0)");
    }

    Serial.println("Setup completo.");
}


// ============================= Loop principal =============================
// Nada de delay(): todo avanza por intervalos de millis(). Así la red, el
// radar (HC-SR04) y los servos nunca se congelan unos a otros.

void loop() {

    uint32_t ahoraMs = millis();

    // 1) Red: atiende al PC conectado y procesa sus comandos
    comunicacion.escucharCliente();

    // 2) Sensores periódicos
    if (MODULOS.radar) {
        radar.actualizar();          // máquina de estados del HC-SR04
        barridoRadar.actualizar();   // mueve el servo del radar de a poco
    }

    if (MODULOS.bateria &&
        (ahoraMs - s_ultimaBateriaMs >= LECTURA_BATERIA_MS)) {
        bateria.actualizarLectura();
        s_ultimaBateriaMs = ahoraMs;
    }

    // 3) Telemetría (estado -> app, cada ENVIO_ESTADO_MS)
    if (ahoraMs - s_ultimaEnvioMs >= ENVIO_ESTADO_MS) {

        s_ultimaEnvioMs = ahoraMs;

        // Distancia: -1 = sin lectura (radar apagado/lejos) -> null en JSON.
        float distancia = MODULOS.radar ? radar.distanciaCm() : -1.0f;

        bool advertencia = MODULOS.radar
                         && radar.obstaculoCercano(UMBRAL_OBSTACULO_CM);

        // Error critico: batería al borde (mismo criterio que el simulador).
        bool error = MODULOS.bateria && bateria.nivel() < 0.10f;

        // Posiciones de los servos: siempre se mandan las últimas ordenes
        // que vino de la app (aunque el flag del módulo esté en 0).
        int angulos[Servos::CANTIDAD];
        servos.angulosUsuario(angulos);

        comunicacion.enviarEstado(
            bateria.nivel(),
            comunicacion.modo(),
            advertencia,
            error,
            distancia,
            bateria.consumoWatts(),
            comunicacion.estaConectado(),
            bateria.cargando(),
            bateria.minutosRestantes(),
            angulos, Servos::CANTIDAD);

        // Pantalla OLED (no hace nada si el módulo está apagado)
        if (MODULOS.oled) {
            oled.mostrar(bateria.nivel(), distancia,
                         comunicacion.modo(), comunicacion.estaConectado());
        }

        // Logs de alerta con cooldown: se avisan solo al TRANSICIONAR a la
        // alerta, no en cada envío de estado mientras persiste.
        if (advertencia && !s_advertenciaAnterior) {
            comunicacion.enviarLog(
                "RADAR",
                "Obstáculo muy cerca: " + String(radar.distanciaCm(), 1) + "cm",
                "advertencia");
        }
        if (error && !s_errorAnterior) {
            comunicacion.enviarLog("BATERIA", "Nivel crítico de batería", "error");
        }

        s_advertenciaAnterior = advertencia;
        s_errorAnterior       = error;
    }
}
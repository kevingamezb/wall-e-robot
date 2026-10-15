// wall-e-robot/firmware/src/main.cpp
// Kevin Gámez - 13/09/2026

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <ESP32Servo.h>
#include "esp_task_wdt.h"

#include "config.h"
#include "pines.h"
#include "comunicacion.h"
#include "servos.h"
#include "motores.h"
#include "distancia.h"
#include "bateria.h"
#include "oled.h"
#include "leds.h"
#include "auto.h"


Comunicacion comunicacion(PUERTO_SERVIDOR);

// Marcas de tiempo del loop no bloqueante.
static uint32_t s_ultimaEnvioMs   = 0;
static uint32_t s_ultimaBateriaMs = 0;

// Estado anterior de las alertas
static bool s_advertenciaAnterior = false;
static bool s_errorAnterior       = false;

// Evita repetir el aviso del timeout de seguridad en cada vuelta.
static bool s_timeoutAvisado = false;


void setup() {

    Serial.begin(115200);
    delay(300);

    // Si el loop se cuelga ESP32 se reinicia solo.
    esp_task_wdt_init(10, true);
    esp_task_wdt_add(nullptr);

    // I2C compartido por el INA219 y el OLED.
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);

    // Los timers LEDC se reservan una sola vez porque los comparten ESP32Servo
    // (servos) y ESP32PWM (motores).
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);

    leds.iniciar();

    // Red: el ESP32 crea su propia WiFi (modo AP).
    WiFi.mode(WIFI_AP);
    WiFi.softAP(WIFI_AP_SSID, WIFI_AP_CLAVE);
    Serial.print("AP iniciada: SSID='");
    Serial.print(WIFI_AP_SSID);
    Serial.print("' IP=");
    Serial.println(WiFi.softAPIP());

    comunicacion.iniciarServidor();

    // Cada módulo se inicializa solo si su flag está activo (ver config.h).
    if (MODULOS.servos) {
        servos.iniciar();
        Serial.println("MODULO servos   = activo");
    } else {
        Serial.println("MODULO servos   = INACTIVO (flag=0)");
    }

    if (MODULOS.distancia) {
        sensorDistancia.iniciar();
        Serial.println("MODULO distancia = activo");
    } else {
        Serial.println("MODULO distancia = INACTIVO (flag=0)");
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

    if (MODULOS.motores && MODULOS.distancia) {
        autoRobot.iniciar();
        Serial.println("MODULO auto     = activo");
    } else {
        Serial.println("MODULO auto     = INACTIVO (falta motores o ultrasonido)");
    }

    Serial.println("Setup completo.");
}


// Loop principal.
void loop() {

    uint32_t ahoraMs = millis();

    esp_task_wdt_reset();   // evita que el watchdog reinicie el ESP32 si el loop tarda mucho

    // Red
    comunicacion.escucharCliente();

    // Seguridad: en modo manual, si el operador deja de mandar comandos, se
    // detienen los motores.
    if (MODULOS.motores && comunicacion.modo() == "manual" &&
        (ahoraMs - comunicacion.ultimaOrdenMs()
         > (unsigned long)TIEMPO_MANUAL_TIMEOUT_MS)) {

        motores.detener();
        if (!s_timeoutAvisado) {
            comunicacion.enviarLog(
                "SEGURIDAD",
                "Sin comando del operador: motores detenidos",
                "advertencia");
            s_timeoutAvisado = true;
        }
    } else {
        s_timeoutAvisado = false;
    }

    // Sensores periódicos
    if (MODULOS.distancia) {
        sensorDistancia.actualizar();
    }

    if (MODULOS.bateria &&
        (ahoraMs - s_ultimaBateriaMs >= LECTURA_BATERIA_MS)) {
        bateria.actualizarLectura();
        s_ultimaBateriaMs = ahoraMs;
    }

    autoRobot.modoAutonomo(comunicacion.modo() == "automatico");

    if (MODULOS.motores && MODULOS.distancia) {
        autoRobot.actualizar();
    }

    // Rampa de los motores
    if (MODULOS.motores) {
        motores.actualizar();
    }

    // Telemetría
    if (ahoraMs - s_ultimaEnvioMs >= ENVIO_ESTADO_MS) {

        s_ultimaEnvioMs = ahoraMs;

        // Distancia -1 = sin lectura; Comunicacion la manda como null.
        float distancia = MODULOS.distancia ? sensorDistancia.distanciaCm()
                                            : -1.0f;

        // Criterio de alertas.
        bool advertencia = MODULOS.distancia
                         && sensorDistancia.obstaculoCercano(UMBRAL_OBSTACULO_CM);

        bool error = MODULOS.bateria && bateria.nivel() < 0.10f;

        String navegacion = (comunicacion.modo() == "manual")
                          ? String("recto")
                          : autoRobot.navegacion();

        leds.actualizar(advertencia, error);

        // Se reportan siempre los últimos ángulos pedidos por la app.
        int angulos[Servos::CANTIDAD];
        servos.angulosUsuario(angulos);

        comunicacion.enviarEstado(
            bateria.nivel(),
            comunicacion.modo(),
            advertencia,
            error,
            distancia,
            navegacion,
            bateria.consumoWatts(),
            comunicacion.estaConectado(),
            bateria.cargando(),
            bateria.minutosRestantes(),
            angulos, Servos::CANTIDAD);

        // La pantalla no hace nada si el módulo está apagado.
        if (MODULOS.oled) {
            oled.mostrar(bateria.nivel(), distancia,
                         comunicacion.modo(), comunicacion.estaConectado());
        }

        // Logs con cooldown
        if (advertencia && !s_advertenciaAnterior) {
            comunicacion.enviarLog(
                "DISTANCIA",
                "Obstáculo muy cerca: " + String(sensorDistancia.distanciaCm(), 1) + "cm",
                "advertencia");
        }
        if (error && !s_errorAnterior) {
            comunicacion.enviarLog("BATERIA", "Nivel crítico de batería", "error");
        }

        s_advertenciaAnterior = advertencia;
        s_errorAnterior       = error;
    }
}

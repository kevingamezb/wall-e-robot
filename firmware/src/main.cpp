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
#include "ota.h"


// Impide la confirmación de Arduino antes de que el self-test valide el arranque.
extern "C" bool verifyRollbackLater() {
    return true;
}


Comunicacion comunicacion(PUERTO_SERVIDOR);

static uint32_t s_ultimaEnvioMs   = 0;
static uint32_t s_ultimaBateriaMs = 0;

// Estado anterior de las alertas (para enviar cada log solo al cambiar).
static bool s_advertenciaAnterior = false;
static bool s_errorAnterior       = false;

// Evita repetir el aviso del timeout de seguridad en cada vuelta.
static bool s_timeoutAvisado = false;

static bool s_otaConfirmado = false;


void setup() {

    Serial.begin(115200);
    delay(300);

    // Watchdog de tarea (10 s): si loop() se cuelga, el ESP32 se reinicia solo.
    esp_task_wdt_init(10, true);
    esp_task_wdt_add(nullptr);

    // Arma la guardia temprano para cubrir bloqueos en setup().
    ota.iniciarGuardiaRollback();

    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);

    // Los timers LEDC se reservan una sola vez porque los comparten ESP32Servo
    // (servos) y ESP32PWM (motores).
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);

    leds.iniciar();

    WiFi.mode(WIFI_AP);
    if (!WiFi.softAP(WIFI_AP_SSID, WIFI_AP_CLAVE)) {
        Serial.println("ERROR: no se pudo iniciar el AP WiFi.");
    }
    Serial.print("AP iniciada: SSID='");
    Serial.print(WIFI_AP_SSID);
    Serial.print("' IP=");
    Serial.println(WiFi.softAPIP());

    comunicacion.iniciarServidor();

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

    // OTA después de WiFi y de los módulos (el portal depende del AP).
    comunicacion.setInfoFirmware(PROYECTO_VERSION, ota.pendiente());
    ota.iniciar();

    Serial.println("Setup completo.");
}


// Evita esperas en el loop para atender la red y medir el eco del HC-SR04.
void loop() {

    uint32_t ahoraMs = millis();

    esp_task_wdt_reset();

    if (!s_otaConfirmado) {
        s_otaConfirmado = true;
        if (ota.pendiente()) {
            String motivo;
            if (ota.selfTestInicial(motivo)) {
                Serial.println("[OTA] Self-test OK: confirmando version.");
                ota.confirmar();
            } else {
                Serial.println("[OTA] Self-test FALLO (" + motivo +
                               "): la guardia revertira.");
            }
        }
    }

    ota.procesar();

    comunicacion.escucharCliente();

    // Si nadie se conecta durante 10 minutos, se devuelve el control al robot.
    if (comunicacion.modo() == "manual" &&
        comunicacion.sinConexionDurante(
            (unsigned long)TIEMPO_SIN_CONEXION_AUTOMATICO_MS)) {

        comunicacion.setModo("automatico");
        Serial.println("[MODO] Sin conexion durante 10 min: modo automatico");
    }

    // Lee millis() después de escucharCliente() para evitar que la resta sin signo desborde.
    if (MODULOS.motores && comunicacion.modo() == "manual" &&
        (millis() - comunicacion.ultimaOrdenMs()
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

    if (MODULOS.distancia) {
        sensorDistancia.actualizar();
    }

    if (MODULOS.bateria &&
        (ahoraMs - s_ultimaBateriaMs >= LECTURA_BATERIA_MS)) {
        bateria.actualizarLectura();
        s_ultimaBateriaMs = ahoraMs;
    }

    // Sin sensor activo, el modo automático mantiene los motores detenidos.
    const bool autonomiaDisponible = MODULOS.motores && MODULOS.distancia;
    const bool pideAutonomo        = comunicacion.modo() == "automatico";
    const bool enAutonomo          = autonomiaDisponible && pideAutonomo;

    autoRobot.modoAutonomo(enAutonomo);

    if (enAutonomo) {
        autoRobot.actualizar();
    } else if (pideAutonomo && MODULOS.motores) {
        motores.detener();
    }

    if (MODULOS.motores) {
        motores.actualizar();
    }

    if (ahoraMs - s_ultimaEnvioMs >= ENVIO_ESTADO_MS) {

        s_ultimaEnvioMs = ahoraMs;

        float distancia = MODULOS.distancia ? sensorDistancia.distanciaCm()
                                            : -1.0f;

        bool advertencia = MODULOS.distancia
                         && sensorDistancia.obstaculoCercano(UMBRAL_OBSTACULO_CM);

        const float nivelBateria = bateria.nivel();
        bool error = MODULOS.bateria && nivelBateria >= 0.0f && nivelBateria < 0.10f;

        String navegacion = enAutonomo ? autoRobot.navegacion()
                                       : String("alto");

        leds.actualizar(advertencia, error, hayModuloInactivo());

        int angulos[Servos::CANTIDAD];
        servos.angulosUsuario(angulos);

        comunicacion.setInfoFirmware(PROYECTO_VERSION, ota.pendiente());

        comunicacion.enviarEstado(
            nivelBateria,
            comunicacion.modo(),
            advertencia,
            error,
            distancia,
            navegacion,
            enAutonomo && autoRobot.bloqueado(),
            bateria.consumoWatts(),
            comunicacion.estaConectado(),
            bateria.cargando(),
            hayModuloInactivo(),
            bateria.minutosRestantes(),
            angulos, Servos::CANTIDAD);

        if (MODULOS.oled) {
            oled.mostrar(nivelBateria, distancia,
                         comunicacion.modo(), comunicacion.estaConectado());
        }

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

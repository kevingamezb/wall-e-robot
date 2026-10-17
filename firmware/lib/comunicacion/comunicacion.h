// wall-e-robot/firmware/lib/comunicacion/comunicacion.h
// Kevin Gamez - 26/08/2026

#ifndef COMUNICACION_H
#define COMUNICACION_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFi.h>

/*
 *  Comunicacion: contrato TCP + JSON con la GUI (app Python).
 *
 *  Medio: WiFi (TCP). El ESP32 es el SERVIDOR y la app Python el cliente.
 *  Formato: un objeto JSON por línea terminado en '\n', sin anidar mensajes.
 *  Tipos salientes: "estado" (telemetría periódica) y "log" (eventos). Los
 *  comandos entrantes traen "tipo": "servo", "modo", "motor" o "multi" (lote).
 *
 *  Los ángulos de servo se validan contra LIMITES[] antes de aplicarse.
 */
class Comunicacion {

private:

    // Red
    WiFiServer servidor;   // servidor TCP (el ESP32 escucha)
    WiFiClient cliente;    // cliente activo (telemetría y comandos)

    // Mensaje entrante en construcción (hasta '\n').
    String mensajeEntrante;

    int    puerto;         // puerto TCP del servidor

    // Modo actual del robot ("automatico"/"manual").
    String _modoActual = "automatico";

    // millis() de la última orden recibida.
    unsigned long _ultimaOrdenMs = 0;

    // true una vez que el servidor TCP quedó escuchando (self-test OTA).
    bool _escuchando = false;

    // Info publicada en cada "estado" (la fija main.cpp).
    String _versionFirmware = "0.0.0";
    bool   _otaPendiente    = false;

    // Interpreta un JSON completo y ejecuta las acciones.
    void procesarMensaje(const String& mensaje);

    // Ejecuta un comando ("servo", "modo" o "motor").
    void aplicarComando(const JsonVariantConst& comando);

public:

    // Crea el servidor TCP en el puerto indicado (aún no lo abre).
    Comunicacion(int puerto);

    // Abre el servidor TCP y lo deja a la escucha.
    void iniciarServidor();

    // Acepta un cliente y procesa los mensajes completos disponibles.
    // No bloqueante: debe llamarse de forma periódica.
    void escucharCliente();

    // Envía una línea terminada en '\n' si hay cliente conectado.
    void enviarMensaje(const String& mensaje);

    // Publica un objeto "estado" con la telemetría del robot. distancia_cm y
    // tiempo_restante_min negativos se envían como null (sin dato).
    void enviarEstado(float bateria, const String& modo,
                      bool hay_advertencia, bool hay_error,
                      float distancia_cm, const String& navegacion,
                      float consumo_watts,
                      bool conexion_activa, bool cargando,
                      bool modulo_inactivo,
                      float tiempo_restante_min,
                      const int* angulos_servos, int cantidad_servos);

    // Publica un objeto "log" con origen, mensaje y nivel de severidad.
    void enviarLog(const String& origen, const String& mensaje,
                   const String& nivel);

    // true si hay un cliente conectado.
    bool estaConectado();

    // true si el servidor TCP está escuchando.
    bool estaEscuchando() const;

    // Información de firmware publicada en cada "estado".
    void setInfoFirmware(const char* version, bool ota_pendiente);

    // Modo actual del robot: "automatico" o "manual".
    const String& modo() const;

    // millis() de la última orden recibida (0 si aún no llegó ninguna).
    unsigned long ultimaOrdenMs() const;
};

// Instancia global (definida en firmware/src/main.cpp).
extern Comunicacion comunicacion;

#endif // COMUNICACION_H

// wall-e-robot/firmware/lib/comunicacion/comunicacion.h
// Kevin Gamez - 26/08/2026

#ifndef COMUNICACION_H
#define COMUNICACION_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFi.h>

/*
 *  Protocolo de comunicación ESP32 <-> App Python.
 *
 *  Medio: WiFi (TCP). El ESP32 es el SERVIDOR y la app Python el cliente.
 *  Formato: JSON, un mensaje por línea terminada en '\n'.
 */
class Comunicacion {

private:

    // Red
    WiFiServer servidor;
    WiFiClient cliente;

    // Mensaje entrante en construcción (hasta '\n').
    String mensajeEntrante;

    int    puerto;

    // Modo actual del robot ("automatico"/"manual").
    String _modoActual = "automatico";

    // millis() de la última orden recibida.
    unsigned long _ultimaOrdenMs = 0;

    // Interpreta un JSON completo y ejecuta las acciones.
    void procesarMensaje(const String& mensaje);

    // Ejecuta un comando ("servo", "modo" o "motor").
    void aplicarComando(const JsonVariantConst& comando);

public:

    Comunicacion(int puerto);

    void iniciarServidor();

    void escucharCliente();

    void enviarMensaje(const String& mensaje);

    void enviarEstado(float bateria, const String& modo,
                      bool hay_advertencia, bool hay_error,
                      float distancia_cm, const String& navegacion,
                      float consumo_watts,
                      bool conexion_activa, bool cargando,
                      float tiempo_restante_min,
                      const int* angulos_servos, int cantidad_servos);

    void enviarLog(const String& origen, const String& mensaje,
                   const String& nivel);

    bool estaConectado();

    const String& modo() const;

    // millis() de la última orden recibida (0 si aún no llegó ninguna).
    unsigned long ultimaOrdenMs() const;
};

#endif // COMUNICACION_H

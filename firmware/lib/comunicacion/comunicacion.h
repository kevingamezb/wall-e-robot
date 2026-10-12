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
 *
 *  App -> ESP32 (comandos):
 *    {"tipo":"servo","servo":"cuello","angulo":30}
 *    {"tipo":"modo","modo":"manual"}
 *    {"tipo":"motor","direccion":"arriba"}
 *    {"tipo":"multi","comandos":[{...},{...}]}
 *
 *  ESP32 -> App (telemetría y logs):
 *    {"tipo":"estado","bateria":0.85,"modo":"manual",
 *     "hay_advertencia":false,"hay_error":false,
 *     "distancia_cm":30.5,"consumo_watts":3.2,"conexion_activa":true,
 *     "cargando":false,"tiempo_restante_min":42,
 *     "posiciones_servos":{"cuello":0,"hombro_izquierdo":10,...}}
 *
 *  "distancia_cm" y "tiempo_restante_min" pueden venir como null (sin lectura
 *  de radar / sin estimación); la app los interpreta como "campo ausente".
 *
 *  Encapsula todo lo de red + el modo del robot (servidor, clientes, JSON y el
 *  despacho de comandos hacia servos/motores). El resto del firmware no
 *  necesita saber de WiFi ni de JSON.
 */
class Comunicacion {

private:

    // Red
    WiFiServer servidor;    // espera conexiones entrantes
    WiFiClient cliente;     // el PC conectado (solo uno a la vez)

    // TCP entrega bytes, no mensajes: se acumula hasta encontrar '\n' y recién
    // ahí se pasa el contenido completo a procesarMensaje().
    String mensajeEntrante;

    int    puerto;

    // Modo actual del robot ("automatico"/"manual"). Lo consultan enviarEstado(),
    // main.cpp y el OLED.
    String _modoActual = "automatico";

    // millis() de la última orden recibida. main.cpp lo usa para el timeout de
    // seguridad en modo manual (parar si el operador deja de mandar comandos).
    unsigned long _ultimaOrdenMs = 0;

    // Interpreta un JSON completo y ejecuta las acciones. Un "multi" aplica
    // cada sub-comando de "comandos".
    void procesarMensaje(const String& mensaje);

    // Ejecuta UN comando ("servo", "modo" o "motor"). Lo reutiliza
    // procesarMensaje() para el mensaje completo o para cada sub-comando.
    void aplicarComando(const JsonVariantConst& comando);

public:

    // Crea el servidor en el puerto indicado (no lo arranca todavía).
    Comunicacion(int puerto);

    // Arranca el servidor TCP.
    void iniciarServidor();

    // Acepta clientes nuevos y procesa los mensajes pendientes. Llamar
    // repetidamente en loop() para no perder datos.
    void escucharCliente();

    // Envía un string crudo como línea JSON.
    void enviarMensaje(const String& mensaje);

    // Envía el estado (telemetría ampliada). angulos_servos es opcional
    // (nullptr para omitir posiciones); distancias/tiempos negativos se mandan
    // como null.
    void enviarEstado(float bateria, const String& modo,
                      bool hay_advertencia, bool hay_error,
                      float distancia_cm, float consumo_watts,
                      bool conexion_activa, bool cargando,
                      float tiempo_restante_min,
                      const int* angulos_servos, int cantidad_servos);

    // Envía una línea de log:
    // {"tipo":"log","origen":...,"mensaje":...,"nivel":...}
    void enviarLog(const String& origen, const String& mensaje,
                   const String& nivel);

    // True si hay un PC conectado (no const: WiFiClient::connected() no es const).
    bool estaConectado();

    // Modo actual ("automatico" / "manual").
    const String& modo() const;

    // millis() de la última orden recibida (0 si aún no llegó ninguna).
    unsigned long ultimaOrdenMs() const;
};

#endif // COMUNICACION_H

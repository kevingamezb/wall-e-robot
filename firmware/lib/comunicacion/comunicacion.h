// wall-e-robot/firmware/lib/comunicacion/comunicacion.h
// Kevin Gamez - 26/08/2026

#ifndef COMUNICACION_H
#define COMUNICACION_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFi.h>

/*
 *  Protocolo de Comunicación ESP32 <-> App Python
 *
 *  Medio fisico:  WiFi (TCP)
 *  Formato:       JSON
 *  Delimitador:   Salto de linea ('\n')
 *
 *  El ESP32 actua como SERVIDOR TCP. La app Python se
 *  conecta como cliente. Ambos intercambian mensajes
 *  JSON terminados en '\n'.
 *
 *  Flujo de datos:
 *  App Python  -->  ESP32   (comandos)
 *    {"tipo":"servo","servo":"cuello","angulo":30}
 *    {"tipo":"modo","modo":"manual"}
 *    {"tipo":"motor","direccion":"arriba"}          (d-pad del gamepad)
 *    {"tipo":"multi","comandos":[{...},{...}]}      (varios de golpe)
 *
 *  ESP32  -->  App Python  (telemetria y logs)
 *    {"tipo":"estado",
 *     "bateria":0.85,"modo":"manual",
 *     "hay_advertencia":false,"hay_error":false,     <-- alertas de la GUI
 *     "distancia_cm":30.5,"consumo_watts":3.2,
 *     "conexion_activa":true,
 *     "cargando":false,"tiempo_restante_min":42,     <-- sol de carga
 *     "posiciones_servos":{"cuello":0,
 *        "hombro_izquierdo":10,...}}                 <-- gamepad
 *
 *  "distancia_cm" y "tiempo_restante_min" pueden venir como null
 *  (sin lectura de radar / sin estimación de batería). La app las
 *  interpreta como "campo ausente" y no toca lo que ya sabía.
 *
 *  Estructura de la clase
 *  Encapsula TODO lo relacionado con la red + el modo actual del robot:
 *  levantar el servidor, aceptar clientes, recibir mensajes, enviar
 *  respuestas y ejecutar el comando recibido sobre las librerías de
 *  hardware (servos, motores). El resto del firmware (sensores, logica)
 *  no necesita saber nada sobre WiFi ni JSON.
 */
class Comunicacion {

private:

    // Red
    WiFiServer servidor;    // Espera conexiones entrantes en un puerto
    WiFiClient cliente;     // Representa al PC conectado (solo 1 a la vez)

    // Buffer de recepcion
    // Acumula bytes hasta encontrar '\n'. Cuando lo encuentra,
    // el contenido completo se pasa a procesarMensaje().
    String mensajeEntrante;

    int    puerto;

    // Modo actual del robot. Lo actualiza procesarModo() y lo consulta
    // enviarEstado() y main.cpp (lógica + OLED).
    String _modoActual = "automatico";

    // Interpreta un JSON completo y ejecuta las acciones correspondientes.
    // Si es tipo "multi", aplica cada sub-comando de "comandos".
    void procesarMensaje(const String& mensaje);

    // Ejecuta UN comando del protocolo ("servo", "modo" o "motor").
    // Reutilizable: procesarMensaje() la llama para el mensaje completo
    // o para cada elemento de un "multi".
    void aplicarComando(const JsonVariantConst& comando);

public:

    // Ciclo de vida

    // Crea el servidor en el puerto indicado (no lo arranca aun)
    Comunicacion(int puerto);

    // Arranca el servidor TCP para que pueda aceptar conexiones
    void iniciarServidor();

    // Uso principal (llamar en loop())

    // Acepta clientes nuevos y procesa todos los mensajes pendientes.
    // Debe llamarse repetidamente en loop() para no perder datos.
    void escucharCliente();

    // Envio de datos al PC

    // Envia un string crudo como linea JSON
    void enviarMensaje(const String& mensaje);

    // Envia el estado del robot (telemetría ampliada). angulos_servos es
    // opcional (nullptr para omitir posiciones); distancias/tiempos
    // negativos se mandan como null en el JSON.
    void enviarEstado(float bateria, const String& modo,
                      bool hay_advertencia, bool hay_error,
                      float distancia_cm, float consumo_watts,
                      bool conexion_activa, bool cargando,
                      float tiempo_restante_min,
                      const int* angulos_servos, int cantidad_servos);

    // Envia una linea de log con origen, mensaje y nivel
    // Formato: {"tipo":"log","origen":...,"mensaje":...,"nivel":...}
    void enviarLog(const String& origen, const String& mensaje,
                   const String& nivel);

    // True si hay un PC conectado y puede recibir datos
    // (no const: WiFiClient::connected() no es const en este framework)
    bool estaConectado();

    // Modo actual del robot ("automatico" / "manual")
    const String& modo() const;
};

#endif // COMUNICACION_H
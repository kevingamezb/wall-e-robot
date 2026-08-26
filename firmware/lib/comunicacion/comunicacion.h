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
 *    {"tipo":"modo","modo":"manual"};
 *  ESP32  -->  App Python  (telemetria y logs)
 *    {"tipo":"estado","bateria":0.85,"modo":"manual",
 *     "distancia_cm":30.5,"consumo_watts":3.2,
 *     "conexion_activa":true}
 *    {"tipo":"log","origen":"RADAR",
 *     "mensaje":"Obstaculo a 8cm","nivel":"advertencia"};
 *
 *  Por qué un delimitador?
 *  TCP es un flujo de bytes continuo, no un flujo de
 *  mensajes. Un solo envio puede llegar fragmentado en
 *  varias lecturas, o varias cosas de un solo burst.
 *  El '\n' permite saber donde termina cada mensaje.
 *
 *  Estructura de la clase
 *  Esta clase encapsula TODO lo relacionado con la red:
 *  levantar el servidor, aceptar clientes, recibir
 *  mensajes, enviar respuestas. El resto del firmware
 *  (servos, sensores, logica) no necesita saber nada
 *  sobre WiFi ni JSON.
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

    // Interpreta un JSON completo y ejecuta la accion correspondiente
    void procesarMensaje(const String& mensaje);

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

    // Envia el estado del robot: bateria, modo, distancia, consumo
    // Formato: {"tipo":"estado","bateria":...,"modo":...,...}
    void enviarEstado(float bateria, const String& modo,
                      float distancia_cm, float consumo_watts,
                      bool conexion_activa);

    // Envia una linea de log con origen, mensaje y nivel
    // Formato: {"tipo":"log","origen":...,"mensaje":...,"nivel":...}
    void enviarLog(const String& origen, const String& mensaje,
                   const String& nivel);

    // True si hay un PC conectado y puede recibir datos
    bool estaConectado() const;
};

#endif // COMUNICACION_H

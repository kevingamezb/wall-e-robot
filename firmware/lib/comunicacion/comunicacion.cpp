// wall-e-robot/firmware/lib/comunicacion/comunicacion.cpp
// Kevin Gamez - 26/08/2026

#include "comunicacion.h"


//  Limites fisicos de cada servo
// Cada servo tiene un rango de movimiento seguro.
// Si la app envia un angulo fuera de este rango, se rechaza.
// Estos valores deben coincidir con los limites reales del hardware.

struct LimiteServo {
    const char* nombre;
    int minimo;
    int maximo;
};

static const LimiteServo LIMITES[] = {
    { "cuello",            -70,  70 },
    { "hombro_izquierdo",  -50,  50 },
    { "hombro_derecho",    -50,  50 },
    { "pulgar_izquierdo",  -22,  22 },
    { "pulgar_derecho",    -22,  22 },
};

static const int CANTIDAD_SERVOS = sizeof(LIMITES) / sizeof(LIMITES[0]);

// Busca el servo por nombre y devuelve true si el angulo esta en rango.
// Si el servo no existe, devuelve false (rechazamos por seguridad).
static bool anguloValidoParaServo(const char* servo, int angulo) {

    for (int i = 0; i < CANTIDAD_SERVOS; i++) {
        if (strcmp(servo, LIMITES[i].nombre) == 0) {
            return angulo >= LIMITES[i].minimo
                && angulo <= LIMITES[i].maximo;
        }
    }

    return false;
}


//  Constructor

Comunicacion::Comunicacion(int puerto)
    : puerto(puerto)
    , servidor(puerto)
    , mensajeEntrante("") {}


//  Servidor TCP

void Comunicacion::iniciarServidor() {

    servidor.begin();
    Serial.print("Servidor TCP listo en puerto ");
    Serial.println(puerto);
}


//  Recepcion de mensajes

// TCP entrega bytes, no mensajes. Un JSON como:
//   {"tipo":"servo","servo":"cuello","angulo":30}\n
//
// puede llegar partido en dos lecturas:
//   Lectura 1: {"tipo":"servo","ser
//   Lectura 2: vo":"cuello","angulo":30}\n
//
// Por eso acumulamos en 'mensajeEntrante' byte a byte
// hasta encontrar '\n', que marca el fin de un mensaje completo.

void Comunicacion::escucharCliente() {

    // Paso 1: aceptar conexion si no hay cliente
    if (!cliente || !cliente.connected()) {

        cliente = servidor.available();

        if (cliente) {
            Serial.println("Cliente conectado.");
            mensajeEntrante = "";
        }
    }

    // Si nadie esta conectado, no hay nada que hacer
    if (!cliente || !cliente.connected()) {
        return;
    }

    // Paso 2: leer todos los bytes pendientes
    while (cliente.available() > 0) {

        char c = cliente.read();

        if (c == '\n') {

            // Mensaje completo: procesarlo
            if (mensajeEntrante.length() > 0) {
                procesarMensaje(mensajeEntrante);
            }

            // Limpiar buffer para el siguiente mensaje
            mensajeEntrante = "";

        } else if (c != '\r') {

            // Ignoramos '\r' (viene de "\r\n") y acumulamos el resto
            mensajeEntrante += c;
        }
    }
}


//  Envio de mensajes

// Envia un string como una linea JSON.
// Agrega '\n' al final para que el receptor sepa donde termina.
void Comunicacion::enviarMensaje(const String& mensaje) {

    if (!cliente || !cliente.connected()) {
        return;
    }

    cliente.print(mensaje);
    cliente.print('\n');
}


//  Envio de telemetria (ESP32 -> Python)

// La app Python espera este formato en conexion.py:
//   mensaje["tipo"] == "estado"
//   mensaje["bateria"]
//   mensaje["modo"]
//   mensaje["distancia_cm"]
//   mensaje["consumo_watts"]
//   mensaje["conexion_activa"]

void Comunicacion::enviarEstado(float bateria, const String& modo,          // IMPORTANTE: Enum en vez de String
                                float distancia_cm, float consumo_watts,
                                bool conexion_activa) {

    if (!cliente || !cliente.connected()) {
        return;
    }

    StaticJsonDocument<512> doc;

    doc["tipo"]            = "estado";
    doc["bateria"]         = bateria;
    doc["modo"]            = modo;
    doc["distancia_cm"]    = distancia_cm;
    doc["consumo_watts"]   = consumo_watts;
    doc["conexion_activa"] = conexion_activa;

    String buffer;
    serializeJson(doc, buffer);
    enviarMensaje(buffer);
}


//  Envio de logs (ESP32 -> Python)

// La app Python espera este formato en conexion.py:
//   mensaje["tipo"] == "log"
//   mensaje["origen"]   -> de donde viene el log
//   mensaje["mensaje"]  -> texto descriptivo
//   mensaje["nivel"]    -> "info", "advertencia" o "error"

void Comunicacion::enviarLog(const String& origen, const String& mensaje,
                             const String& nivel) {

    if (!cliente || !cliente.connected()) {
        return;
    }

    StaticJsonDocument<512> doc;

    doc["tipo"]    = "log";
    doc["origen"]  = origen;
    doc["mensaje"] = mensaje;
    doc["nivel"]   = nivel;

    String buffer;
    serializeJson(doc, buffer);
    enviarMensaje(buffer);
}


//  Comando: mover servo

// La app Python envia:
//   {"tipo":"servo","servo":"cuello","angulo":30}
//
// Validamos que el servo exista y que el angulo este en rango.
// Si todo esta bien, imprimimos por Serial (futuro: enviar a la
// libreria de servos).

static void procesarServo(const StaticJsonDocument<4096>& doc) {

    const char* servo = doc["servo"];
    int angulo = doc["angulo"] | 0;

    if (servo == nullptr) {
        Serial.println("Error: falta el nombre del servo.");
        return;
    }

    if (!anguloValidoParaServo(servo, angulo)) {
        Serial.print("Error: angulo invalido para '");
        Serial.print(servo);
        Serial.print("': ");
        Serial.println(angulo);
        return;
    }

    Serial.print("Servo '");
    Serial.print(servo);
    Serial.print("' -> ");
    Serial.print(angulo);
    Serial.println(" grados.");

    // TODO: conectar con la libreria de servos
    // servos.mover(servo, angulo);
}


//  Comando: cambiar modo

// La app Python envia:
//   {"tipo":"modo","modo":"manual"}
//   {"tipo":"modo","modo":"automatico"}

static void procesarModo(const StaticJsonDocument<4096>& doc) {

    const char* modo = doc["modo"];

    if (modo == nullptr) {
        Serial.println("Error: falta el campo 'modo'.");
        return;
    }

    if (strcmp(modo, "automatico") != 0 &&
        strcmp(modo, "manual") != 0) {
        Serial.print("Error: modo desconocido: ");
        Serial.println(modo);
        return;
    }

    Serial.print("Modo cambiado a '");
    Serial.print(modo);
    Serial.println("'.");

    // TODO: conectar con la logica de control del robot
}


//  Despacho de mensajes

// Recibe un JSON completo, lee el campo "tipo" y llama
// a la funcion correspondiente. Si el tipo no existe o
// no se reconoce, imprime un error por Serial.

void Comunicacion::procesarMensaje(const String& lineaJson) {

    StaticJsonDocument<4096> doc;

    DeserializationError error = deserializeJson(doc, lineaJson);

    if (error) {
        Serial.print("JSON invalido: ");
        Serial.println(error.c_str());
        return;
    }

    const char* tipo = doc["tipo"];

    if (tipo == nullptr) {
        Serial.println("Error: campo 'tipo' requerido.");
        return;
    }

    if (strcmp(tipo, "servo") == 0) {
        procesarServo(doc);

    } else if (strcmp(tipo, "modo") == 0) {
        procesarModo(doc);

    } else {
        Serial.print("Tipo desconocido: ");
        Serial.println(tipo);
    }
}


//  Estado de conexion

bool Comunicacion::estaConectado() const {
    return cliente && cliente.connected();
}

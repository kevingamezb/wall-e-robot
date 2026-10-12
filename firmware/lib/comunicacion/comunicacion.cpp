// wall-e-robot/firmware/lib/comunicacion/comunicacion.cpp
// Kevin Gamez - 26/08/2026

#include "comunicacion.h"
#include "servos.h"
#include "motores.h"


// Rango seguro de cada servo. Un ángulo fuera de rango se rechaza (debe
// coincidir con los topes reales del hardware).
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

// True si el servo existe y el ángulo está dentro de su rango. Un servo
// desconocido devuelve false (se rechaza por seguridad).
static bool anguloValidoParaServo(const char* servo, int angulo) {

    for (int i = 0; i < CANTIDAD_SERVOS; i++) {
        if (strcmp(servo, LIMITES[i].nombre) == 0) {
            return angulo >= LIMITES[i].minimo
                && angulo <= LIMITES[i].maximo;
        }
    }

    return false;
}


Comunicacion::Comunicacion(int puerto)
    : puerto(puerto)
    , servidor(puerto)
    , mensajeEntrante("") {}


void Comunicacion::iniciarServidor() {

    servidor.begin();
    Serial.print("Servidor TCP listo en puerto ");
    Serial.println(puerto);
}


void Comunicacion::escucharCliente() {

    // Acepta una conexión si no hay cliente activo.
    if (!cliente || !cliente.connected()) {

        cliente = servidor.available();

        if (cliente) {
            Serial.println("Cliente conectado.");
            mensajeEntrante = "";
        }
    }

    if (!cliente || !cliente.connected()) {
        return;
    }

    // Acumula bytes hasta el '\n' que cierra cada mensaje.
    while (cliente.available() > 0) {

        char c = cliente.read();

        if (c == '\n') {

            if (mensajeEntrante.length() > 0) {
                procesarMensaje(mensajeEntrante);
            }

            mensajeEntrante = "";

        } else if (c != '\r') {
            // Ignora el '\r' que puede venir de "\r\n".
            mensajeEntrante += c;
        }
    }
}


void Comunicacion::enviarMensaje(const String& mensaje) {

    if (!cliente || !cliente.connected()) {
        return;
    }

    cliente.print(mensaje);
    cliente.print('\n');
}


// La app Python (conexion.py) parsea este formato de forma tolerante: los
// campos que no vienen (o vienen null) no pisan lo que ya sabía.
void Comunicacion::enviarEstado(float bateria, const String& modo,
                                bool hay_advertencia, bool hay_error,
                                float distancia_cm, float consumo_watts,
                                bool conexion_activa, bool cargando,
                                float tiempo_restante_min,
                                const int* angulos_servos, int cantidad_servos) {

    if (!cliente || !cliente.connected()) {
        return;
    }

    StaticJsonDocument<1024> doc;

    doc["tipo"]               = "estado";
    doc["bateria"]            = bateria;
    doc["modo"]               = modo;
    doc["hay_advertencia"]    = hay_advertencia;
    doc["hay_error"]          = hay_error;

    // Distancia negativa = sin lectura: null.
    if (distancia_cm >= 0.0f) {
        doc["distancia_cm"] = distancia_cm;
    } else {
        doc["distancia_cm"] = nullptr;
    }

    doc["consumo_watts"]      = consumo_watts;
    doc["conexion_activa"]    = conexion_activa;
    doc["cargando"]           = cargando;

    // Minutos negativos = sin estimación: null.
    if (tiempo_restante_min >= 0.0f) {
        doc["tiempo_restante_min"] = tiempo_restante_min;
    } else {
        doc["tiempo_restante_min"] = nullptr;
    }

    // Orden de posiciones_servos, igual al que usa la app.
    static const char* const NOMBRES_SERVOS_ESTADO[] = {
        "cuello", "hombro_izquierdo", "hombro_derecho",
        "pulgar_izquierdo", "pulgar_derecho",
    };

    if (angulos_servos != nullptr) {
        JsonObject pos = doc.createNestedObject("posiciones_servos");
        for (int i = 0;
             i < cantidad_servos && i < (int)(sizeof(NOMBRES_SERVOS_ESTADO) / sizeof(NOMBRES_SERVOS_ESTADO[0]));
             i++) {
            pos[NOMBRES_SERVOS_ESTADO[i]] = angulos_servos[i];
        }
    }

    String buffer;
    serializeJson(doc, buffer);
    enviarMensaje(buffer);
}


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


// {"tipo":"servo","servo":"cuello","angulo":30}
// Valida nombre y ángulo (LIMITES[]) y delega el movimiento a la librería de
// servos. Con el módulo deshabilitado, moverServo() igual guarda el ángulo
// para que la telemetría refleje lo que la GUI cree que mandó.
void Comunicacion::aplicarComando(const JsonVariantConst& comando) {

    const char* tipo = comando["tipo"];

    if (tipo == nullptr) {
        Serial.println("Error: campo 'tipo' requerido.");
        return;
    }

    if (strcmp(tipo, "servo") == 0) {

        const char* servo  = comando["servo"];
        int         angulo = comando["angulo"] | 0;

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

        servos.moverServo(servo, angulo);

        Serial.print("Servo '");
        Serial.print(servo);
        Serial.print("' -> ");
        Serial.print(angulo);
        Serial.println(" grados.");

    } else if (strcmp(tipo, "modo") == 0) {

        const char* modo = comando["modo"];

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

        _modoActual = modo;
        Serial.print("Modo cambiado a '");
        Serial.print(modo);
        Serial.println("'.");

    } else if (strcmp(tipo, "motor") == 0) {

        const char* direccion = comando["direccion"];

        if (direccion == nullptr) {
            Serial.println("Error: falta el campo 'direccion'.");
            return;
        }

        // mover() ignora direcciones no mapeadas y no hace nada si el módulo
        // está deshabilitado.
        motores.mover(direccion);

        Serial.print("Motor -> ");
        Serial.println(direccion);

    } else {
        Serial.print("Tipo desconocido: ");
        Serial.println(tipo);
        // Avisa también a la app para que un comando no reconocido no sea un
        // fallo silencioso del protocolo.
        enviarLog("COMANDO",
                  "Comando no reconocido: " + String(tipo), "advertencia");
    }
}


// Aplica un mensaje completo. Si "tipo" es "multi", recorre "comandos"; si no,
// aplica el mensaje tal cual.
void Comunicacion::procesarMensaje(const String& lineaJson) {

    StaticJsonDocument<4096> doc;

    DeserializationError error = deserializeJson(doc, lineaJson);

    if (error) {
        Serial.print("JSON invalido: ");
        Serial.println(error.c_str());
        return;
    }

    // Toda orden válida cuenta como "presencia del operador" para el timeout
    // de seguridad de main.cpp.
    _ultimaOrdenMs = millis();

    const char* tipo = doc["tipo"];

    if (tipo == nullptr) {
        Serial.println("Error: campo 'tipo' requerido.");
        return;
    }

    if (strcmp(tipo, "multi") == 0) {

        JsonArray comandos = doc["comandos"].as<JsonArray>();

        if (comandos.isNull()) {
            Serial.println("Error: 'multi' requiere un array 'comandos'.");
            return;
        }

        for (JsonVariant subComando : comandos) {
            aplicarComando(subComando.as<JsonVariantConst>());
        }

    } else {
        aplicarComando(doc.as<JsonVariantConst>());
    }
}


bool Comunicacion::estaConectado() {
    return cliente && cliente.connected();
}


const String& Comunicacion::modo() const {
    return _modoActual;
}


unsigned long Comunicacion::ultimaOrdenMs() const {
    return _ultimaOrdenMs;
}

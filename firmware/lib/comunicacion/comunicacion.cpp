#include "comunicacion.h"
#include "config.h"
#include "servos.h"
#include "motores.h"


// Rango angular válido por servo, en las unidades lógicas de la app.
struct LimiteServo {
    const char* nombre;
    int minimo;
    int maximo;
};

static const LimiteServo LIMITES[] = {
    { "cuello",            -70,  70 },
    { "hombro_izquierdo",  -50,  50 },
    { "hombro_derecho",    -50,  50 }
};

static const int CANTIDAD_SERVOS = sizeof(LIMITES) / sizeof(LIMITES[0]);

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
    , mensajeEntrante("")
    , _ultimaOrdenMs(0)
    , _ultimaConexionMs(0) {}


void Comunicacion::iniciarServidor() {

    servidor.begin();
    _escuchando = true;
    Serial.print("Servidor TCP listo en puerto ");
    Serial.println(puerto);
}


void Comunicacion::escucharCliente() {

    if (!cliente || !cliente.connected()) {

        if (_operadorConectado) {
            _ultimaConexionMs = millis();
            if (_modoActual == "manual") {
                _detenido = _detenido || !motores.detenidos();
                motores.detenerAhora();
                servos.mantenerGesto();
                terminarDemo();
            }
        }
        _operadorConectado = false;
        cliente = servidor.available();

        if (cliente) {
            ++_revisionControl;
            _operadorConectado = true;
            Serial.println("Cliente conectado.");
            mensajeEntrante   = "";
            _descartando      = false;
            _ultimaConexionMs = millis();
        }
    }

    if (!cliente || !cliente.connected()) {
        return;
    }

    while (cliente.available() > 0) {

        char c = cliente.read();

        if (c == '\n') {

            if (mensajeEntrante.length() > 0 && !_descartando) {
                procesarMensaje(mensajeEntrante);

            } else if (_descartando) {
                Serial.println("Comando descartado: supera el tamano maximo.");
            }

            mensajeEntrante = "";
            _descartando    = false;

        } else if (c != '\r') {
            if (_descartando) {
                continue;   // ya se avisó; se ignora hasta el próximo '\n'
            }

            if ((int)mensajeEntrante.length() >= MAX_MENSAJE_ENTRANTE) {
                // Línea sin fin: se tira entera para no crecer sin límite.
                mensajeEntrante = "";
                _descartando    = true;
                enviarLog("PROTOCOLO",
                          "Mensaje demasiado largo: descartado",
                          "advertencia");
                continue;
            }

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


void Comunicacion::enviarEstado(float bateria, float voltajeBateria, float corrienteBateria,
                                const String& modo,
                                bool hay_advertencia, bool hay_error,
                                float distancia_cm, const String& navegacion,
                                bool auto_bloqueado,
                                float consumo_watts,
                                bool conexion_activa, bool cargando,
                                bool modulo_inactivo,
                                float tiempo_restante_min,
                                const int* angulos_servos, int cantidad_servos) {

    if (!cliente || !cliente.connected()) {
        return;
    }

    StaticJsonDocument<1024> doc;

    doc["protocolo"]           = PROTOCOLO_VERSION;
    doc["tipo"]               = "estado";
    doc["bateria"]            = bateria;
    if (voltajeBateria > 0.0f) {
        doc["voltaje_bateria_v"] = voltajeBateria;
        doc["corriente_bateria_a"] = corrienteBateria;
    }
    doc["modo"]               = modo;
    doc["detenido"]           = _detenido;
    doc["demo_activa"]        = _demoActiva;
    doc["hay_advertencia"]    = hay_advertencia;
    doc["hay_error"]          = hay_error;

    // Distancia negativa = sin lectura: null.
    if (distancia_cm >= 0.0f) {
        doc["distancia_cm"] = distancia_cm;
    } else {
        doc["distancia_cm"] = nullptr;
    }

    doc["navegacion"]         = navegacion;
    doc["auto_bloqueado"]     = auto_bloqueado;
    doc["consumo_watts"]      = consumo_watts;
    doc["conexion_activa"]    = conexion_activa;
    doc["cargando"]           = cargando;
    doc["modulo_inactivo"]    = modulo_inactivo;
    doc["version_firmware"]   = _versionFirmware;
    doc["ota_pendiente"]      = _otaPendiente;

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

    doc["protocolo"] = PROTOCOLO_VERSION;
    doc["tipo"]    = "log";
    doc["origen"]  = origen;
    doc["mensaje"] = mensaje;
    doc["nivel"]   = nivel;

    String buffer;
    serializeJson(doc, buffer);
    enviarMensaje(buffer);
}


void Comunicacion::aplicarComando(const JsonVariantConst& comando) {

    const char* tipo = comando["tipo"];

    if (tipo == nullptr) {
        Serial.println("Error: campo 'tipo' requerido.");
        return;
    }

    if (strcmp(tipo, "detener") == 0) {
        servos.mantenerGesto();
        setModo("manual");
        _detenido = true;
        enviarLog("CONTROL", "Detenido por el usuario", "info");
    } else if (strcmp(tipo, "demo") == 0) {
        if (_demoActiva) {
            return;
        }
        setModo("manual");
        _detenido = true;
        _inicioDemoMs = millis();
        _demoActiva = true;
    } else if (strcmp(tipo, "servo") == 0) {
        if (_detenido) {
            return;
        }

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

        setModo(modo);
        Serial.print("Modo cambiado a '");
        Serial.print(modo);
        Serial.println("'.");

    } else if (strcmp(tipo, "motor") == 0) {
        if (_detenido || _modoActual != "manual") {
            return;
        }

        const char* direccion = comando["direccion"];

        if (direccion == nullptr) {
            Serial.println("Error: falta el campo 'direccion'.");
            return;
        }

        if (strcmp(direccion, "arriba") != 0 && strcmp(direccion, "abajo") != 0 &&
            strcmp(direccion, "izquierda") != 0 && strcmp(direccion, "derecha") != 0) {
            return;
        }
        motores.mover(direccion);
        _ultimaOrdenMs = millis();

        Serial.print("Motor -> ");
        Serial.println(direccion);

    } else {
        Serial.print("Tipo desconocido: ");
        Serial.println(tipo);
        enviarLog("COMANDO",
                  "Comando no reconocido: " + String(tipo), "advertencia");
    }
}


void Comunicacion::procesarMensaje(const String& lineaJson) {

    StaticJsonDocument<4096> doc;

    DeserializationError error = deserializeJson(doc, lineaJson);

    if (error) {
        Serial.print("JSON invalido: ");
        Serial.println(error.c_str());
        return;
    }

    // Ante una versión nueva, avisa una vez y sigue aplicando los campos conocidos.
    int version = doc["protocolo"] | PROTOCOLO_VERSION;
    if (version > PROTOCOLO_VERSION && !_avisoProtocolo) {
        _avisoProtocolo = true;
        enviarLog("PROTOCOLO",
                  "La app usa el protocolo " + String(version) +
                  "; el firmware soporta " + String(PROTOCOLO_VERSION),
                  "advertencia");
    }

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


bool Comunicacion::estaEscuchando() const {
    return _escuchando;
}


void Comunicacion::setInfoFirmware(const char* version, bool ota_pendiente) {
    _versionFirmware = version;
    _otaPendiente    = ota_pendiente;
}


const String& Comunicacion::modo() const {
    return _modoActual;
}


void Comunicacion::setModo(const String& modo) {
    if (modo != "automatico" && modo != "manual") {
        return;
    }
    terminarDemo();
    motores.detenerAhora();
    ++_revisionControl;
    _detenido = false;
    _modoActual = modo;
}

void Comunicacion::terminarDemo() {
    if (_demoActiva) {
        servos.aplicarGesto(nullptr);
        _demoActiva = false;
    }
}

bool Comunicacion::sinConexionDurante(unsigned long ms) {
    // La resta sin signo tolera el desbordamiento de millis().
    return !estaConectado() && (millis() - _ultimaConexionMs >= ms);
}


unsigned long Comunicacion::ultimaOrdenMs() const {
    return _ultimaOrdenMs;
}

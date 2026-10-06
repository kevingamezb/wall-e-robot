// wall-e-robot/firmware/lib/radar/radar.cpp
// Kevin Gámez - 13/09/2026

#include "radar.h"
#include "servos.h"
#include "config.h"
#include "pines.h"

// Velocidad del sonido en aire: 343 m/s = 0.0343 cm por microsegundo.
// La onda viaja ida y vuelta, por eso se divide entre dos.
static const float VELOCIDAD_SONIDO_CM_POR_US = 0.0343f;
static const int   DURACION_TRIG_US           = 10;    // pulso que pide el HC-SR04
static const uint32_t TIMEOUT_SIN_ECO_US      = 40000; // ~7 m: sin eco en ese tiempo
static const float MAX_DISTANCIA_CM           = 400.0f; // filtrar ruido lejano


Radar radar(PIN_RADAR_TRIG, PIN_RADAR_ECHO);
BarridoRadar barridoRadar;


Radar::Radar(uint8_t pinTrig, uint8_t pinEcho)
    : _pinTrig(pinTrig)
    , _pinEcho(pinEcho)
    , _fase(FASE_ESPERANDO)
    , _placaLista(false)
    , _lecturaNueva(false)
    , _distanciaCm(-1.0f)
    , _microsInicio(0)
    , _microsEco(0)
    , _ultimaLecturaMs(0) {}


void Radar::iniciar() {

    pinMode(_pinTrig, OUTPUT);
    pinMode(_pinEcho, INPUT);

    digitalWrite(_pinTrig, LOW);   // reposo: nunca iniciar un pulso

    _placaLista = true;
}


void Radar::actualizar() {

    if (!_placaLista) {
        return;   // módulo deshabilitado en esta prueba
    }

    switch (_fase) {

    case FASE_ESPERANDO: {

        // Empezar un ciclo solo después del intervalo de muestreo.
        uint32_t ahoraMs = millis();
        if ((ahoraMs - _ultimaLecturaMs) < LECTURA_RADAR_MS) {
            break;   // aún no toca medir
        }

        digitalWrite(_pinTrig, HIGH);
        _microsInicio = micros();
        _lecturaNueva = false;   // empieza un ciclo: la lectura "nueva" se reinicia
        _fase = FASE_PULSO_ENVIADO;
        break;
    }

    case FASE_PULSO_ENVIADO: {

        // Esperar los 10us del pulso y bajarlo.
        if ((uint32_t)(micros() - _microsInicio) >= DURACION_TRIG_US) {

            digitalWrite(_pinTrig, LOW);
            _microsInicio = micros();     // reusar como base del timeout del eco
            _fase = FASE_ESPERANDO_ECO;
        }
        break;
    }

    case FASE_ESPERANDO_ECO: {

        if (digitalRead(_pinEcho) == HIGH) {
            _microsEco = micros();        // llegó el borde ascendente
            _fase = FASE_MIDIENDO_ECO;

        } else if ((uint32_t)(micros() - _microsInicio) >= TIMEOUT_SIN_ECO_US) {
            // No volvió eco (nada a esa distancia o sensor sin responder).
            _distanciaCm = -1.0f;
            _lecturaNueva = true;
            _fase = FASE_ESPERANDO;
        }
        break;
    }

    case FASE_MIDIENDO_ECO: {

        if (digitalRead(_pinEcho) == LOW) {

            uint32_t duracion = (uint32_t)(micros() - _microsEco);
            float cm = (float)duracion * VELOCIDAD_SONIDO_CM_POR_US / 2.0f;

            // Filtrar valores absurdos (eco rebotado, ruido del aula de robótica).
            _distanciaCm = (cm > MAX_DISTANCIA_CM) ? -1.0f : cm;

            _lecturaNueva = true;
            _fase = FASE_ESPERANDO;
        }
        break;
    }
    }
}


bool Radar::hayLecturaNueva() const {
    return _lecturaNueva;
}


float Radar::distanciaCm() const {
    // En firmware: "distancia 1.0" no existe; el -1 lo lee main.cpp
    // y decide mandar null en el JSON (la GUI lo espera opcional).
    return _distanciaCm;
}


bool Radar::obstaculoCercano(float umbralCm) const {
    return _distanciaCm >= 0.0f && _distanciaCm <= umbralCm;
}


// =========================== Barrido del radar ===========================

BarridoRadar::BarridoRadar()
    : _angulo(RADAR_SERVO_GRAUS_MIN)
    , _paso(3)
    , _ultimoPasoMs(0)
    , _activo(MODULOS.radar) {}   // si el módulo radar está apagado, no barrer


void BarridoRadar::actualizar() {

    if (!_activo) {
        return;
    }

    uint32_t ahoraMs = millis();
    if ((ahoraMs - _ultimoPasoMs) < PASO_BARRIDO_MS) {
        return;   // aún no toca avanzar el barrido
    }

    _ultimoPasoMs = ahoraMs;
    _angulo += _paso;

    // Rebote en los extremos y vuelve al revés.
    if (_angulo >= RADAR_SERVO_GRAUS_MAX) {
        _angulo = RADAR_SERVO_GRAUS_MAX;
        _paso = -abs(_paso);
    } else if (_angulo <= RADAR_SERVO_GRAUS_MIN) {
        _angulo = RADAR_SERVO_GRAUS_MIN;
        _paso = abs(_paso);
    }

    servos.moverRadar(_angulo);
}


bool BarridoRadar::estaActivo() const {
    return _activo;
}
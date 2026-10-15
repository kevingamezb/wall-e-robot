// wall-e-robot/firmware/lib/distancia/distancia.cpp
// Kevin Gámez - 13/09/2026

#include "distancia.h"
#include "config.h"
#include "pines.h"

// El sonido viaja a 343 m/s = 0.0343 cm/us; el eco recorre ida y vuelta, por
// eso la distancia se divide entre dos.
static const float VELOCIDAD_SONIDO_CM_POR_US = 0.0343f;
static const int   DURACION_TRIG_US           = 10;     // pulso que pide el HC-SR04
static const uint32_t TIMEOUT_SIN_ECO_US      = 40000;  // ~7 m: más allá, no se espera eco
static const float MAX_DISTANCIA_CM           = 400.0f; // filtra ecos lejanos/ruido


SensorDistancia sensorDistancia(PIN_US_TRIG, PIN_US_ECHO);


SensorDistancia::SensorDistancia(uint8_t pinTrig, uint8_t pinEcho)
    : _pinTrig(pinTrig)
    , _pinEcho(pinEcho)
    , _fase(FASE_ESPERANDO)
    , _sensorListo(false)
    , _lecturaNueva(false)
    , _distanciaCm(-1.0f)
    , _microsInicio(0)
    , _microsEco(0)
    , _ultimaLecturaMs(0) {}


void SensorDistancia::iniciar() {

    pinMode(_pinTrig, OUTPUT);
    pinMode(_pinEcho, INPUT);

    digitalWrite(_pinTrig, LOW);   // en reposo, nunca arrancar un pulso

    _sensorListo = true;
}


void SensorDistancia::actualizar() {

    if (!_sensorListo) {
        return;
    }

    switch (_fase) {

    case FASE_ESPERANDO: {

        // Arranca un ciclo solo después del intervalo de muestreo.
        uint32_t ahoraMs = millis();
        if ((ahoraMs - _ultimaLecturaMs) < LECTURA_DISTANCIA_MS) {
            break;
        }

        digitalWrite(_pinTrig, HIGH);
        _microsInicio = micros();
        _lecturaNueva = false;   // nuevo ciclo: se descarta la marca anterior
        _fase = FASE_PULSO_ENVIADO;
        break;
    }

    case FASE_PULSO_ENVIADO: {

        if ((uint32_t)(micros() - _microsInicio) >= DURACION_TRIG_US) {

            digitalWrite(_pinTrig, LOW);
            _microsInicio = micros();     // base del timeout del eco
            _fase = FASE_ESPERANDO_ECO;
        }
        break;
    }

    case FASE_ESPERANDO_ECO: {

        if (digitalRead(_pinEcho) == HIGH) {
            _microsEco = micros();        // llegó el borde ascendente
            _fase = FASE_MIDIENDO_ECO;

        } else if ((uint32_t)(micros() - _microsInicio) >= TIMEOUT_SIN_ECO_US) {
            // Sin eco: nada en rango o sensor sin responder.
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

            // Descarta valores absurdos.
            _distanciaCm = (cm > MAX_DISTANCIA_CM) ? -1.0f : cm;

            _lecturaNueva = true;
            _fase = FASE_ESPERANDO;
        }
        break;
    }
    }
}


bool SensorDistancia::hayLecturaNueva() const {
    return _lecturaNueva;
}


float SensorDistancia::distanciaCm() const {
    // -1 se propaga hasta main.cpp, que decide mandar null en el JSON.
    return _distanciaCm;
}


bool SensorDistancia::obstaculoCercano(float umbralCm) const {
    return _distanciaCm >= 0.0f && _distanciaCm <= umbralCm;
}

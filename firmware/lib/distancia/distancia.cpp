#include "distancia.h"
#include "config.h"
#include "pines.h"

// El sonido viaja a 343 m/s = 0.0343 cm/us; el eco recorre ida y vuelta, por
// eso la distancia se divide entre dos.
static const float VELOCIDAD_SONIDO_CM_POR_US = 0.0343f;
static const int   DURACION_TRIG_US           = 10;     // pulso que pide el HC-SR04
static const uint32_t TIMEOUT_SIN_ECO_US     = 40000;  // ~7 m: más allá, no se espera eco
static const uint32_t TIMEOUT_ECO_US         = 40000;  // eco atascado en HIGH: cortar igual
static const float MAX_DISTANCIA_CM           = 400.0f; // filtra ecos lejanos/ruido


SensorDistancia sensorDistancia(PIN_US_TRIG, PIN_US_ECHO);


SensorDistancia::SensorDistancia(uint8_t pinTrig, uint8_t pinEcho)
    : _pinTrig(pinTrig)
    , _pinEcho(pinEcho)
    , _fase(FASE_ESPERANDO)
    , _sensorListo(false)
    , _lecturaNueva(false)
    , _algunaLectura(false)
    , _distanciaCm(-1.0f)
    , _microsInicio(0)
    , _microsEco(0)
    , _ultimaLecturaMs(0) {}


void SensorDistancia::iniciar() {

    pinMode(_pinTrig, OUTPUT);
    pinMode(_pinEcho, INPUT);

    digitalWrite(_pinTrig, LOW);

    _sensorListo = true;
}


bool SensorDistancia::listo() const {
    return _sensorListo;
}


void SensorDistancia::actualizar() {

    if (!_sensorListo) {
        return;
    }

    switch (_fase) {

    case FASE_ESPERANDO: {

        uint32_t ahoraMs = millis();
        if ((ahoraMs - _ultimaLecturaMs) < LECTURA_DISTANCIA_MS) {
            break;
        }

        digitalWrite(_pinTrig, HIGH);
        _inicioPulsoMs = ahoraMs;
        _microsInicio = micros();
        _lecturaNueva = false;
        _fase = FASE_PULSO_ENVIADO;
        break;
    }

    case FASE_PULSO_ENVIADO: {

        if ((uint32_t)(micros() - _microsInicio) >= DURACION_TRIG_US) {

            digitalWrite(_pinTrig, LOW);
            _microsInicio = micros();
            _fase = FASE_ESPERANDO_ECO;
        }
        break;
    }

    case FASE_ESPERANDO_ECO: {

        if (digitalRead(_pinEcho) == HIGH) {
            _microsEco = micros();
            _fase = FASE_MIDIENDO_ECO;

        } else if ((uint32_t)(micros() - _microsInicio) >= TIMEOUT_SIN_ECO_US) {
            // Sin eco: nada en rango o sensor sin responder.
            finalizarLectura(-1.0f);

        }
        break;
    }

    case FASE_MIDIENDO_ECO: {

        if (digitalRead(_pinEcho) == LOW) {

            uint32_t duracion = (uint32_t)(micros() - _microsEco);
            float cm = (float)duracion * VELOCIDAD_SONIDO_CM_POR_US / 2.0f;

            finalizarLectura(cm > MAX_DISTANCIA_CM ? -1.0f : cm);

        } else if ((uint32_t)(micros() - _microsEco) >= TIMEOUT_ECO_US) {
            // Si ECHO queda en HIGH, vence el plazo y la medición termina sin lectura.
            finalizarLectura(-1.0f);
        }
        break;
    }
    }
}


void SensorDistancia::finalizarLectura(float distanciaCm) {

    _distanciaCm    = distanciaCm;
    _lecturaNueva   = true;
    _algunaLectura  = true;
    _ultimaLecturaMs = millis();   // base del intervalo y de la frescura
    _inicioUltimaLecturaMs = _inicioPulsoMs;
    _fase           = FASE_ESPERANDO;
}


bool SensorDistancia::hayLecturaNueva() const {
    return _lecturaNueva;
}


float SensorDistancia::distanciaCm() const {
    return _distanciaCm;
}


bool SensorDistancia::obstaculoCercano(float umbralCm) const {
    return _distanciaCm >= 0.0f && _distanciaCm <= umbralCm;
}


bool SensorDistancia::lecturaFresca(uint32_t maxMs) const {

    if (!_algunaLectura) {
        return false;
    }

    return (uint32_t)(millis() - _ultimaLecturaMs) <= maxMs;
}

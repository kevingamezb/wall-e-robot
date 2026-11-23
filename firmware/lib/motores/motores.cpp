#include "motores.h"
#include "pines.h"

// Limita el PWM al 70 % para los motores de 6 V con la batería a 8,4 V.
static const int VELOCIDAD_GIRO = 178;

// El signo compensa la inversión del cableado actual.
static const int SENTIDO_MOTORES = -1;

// La rampa limita el cambio de velocidad para evitar tirones.
static const int       PASO_RAMPA         = 15;
static const uint32_t  INTERVALO_RAMPA_MS = 12;


Motores motores(PIN_MOTOR_AIN1, PIN_MOTOR_AIN2,
                PIN_MOTOR_BIN1, PIN_MOTOR_BIN2,
                PIN_MOTOR_PWMA, PIN_MOTOR_PWMB,
                PIN_MOTOR_STBY);


Motores::Motores(uint8_t ain1, uint8_t ain2, uint8_t bin1, uint8_t bin2,
                 uint8_t pwma, uint8_t pwmb, uint8_t stby)
    : _ain1(ain1), _ain2(ain2), _bin1(bin1), _bin2(bin2)
    , _pwma(pwma), _pwmb(pwmb), _stby(stby)
    , _activo(false)
    , _metaA(0), _metaB(0), _velA(0), _velB(0), _ultimaRampaMs(0) {}


void Motores::iniciar() {

    for (const uint8_t pin : { _ain1, _ain2, _bin1, _bin2 }) {
        pinMode(pin, OUTPUT);
    }

    pinMode(_stby, OUTPUT);
    digitalWrite(_stby, HIGH);

    _pwmA.attachPin(_pwma, 1000, 8);
    _pwmB.attachPin(_pwmb, 1000, 8);

    _metaA = _metaB = 0;
    _velA  = _velB  = 0;
    _rueda(_ain1, _ain2, _pwmA, 0);
    _rueda(_bin1, _bin2, _pwmB, 0);

    _activo = true;
}


// Aplica una velocidad con signo a una rueda del TB6612FNG:
void Motores::_rueda(uint8_t inA, uint8_t inB, ESP32PWM& pwm, int velocidad) {

    if (velocidad > 0) {
        digitalWrite(inA, HIGH);
        digitalWrite(inB, LOW);
    } else if (velocidad < 0) {
        digitalWrite(inA, LOW);
        digitalWrite(inB, HIGH);
    } else {
        digitalWrite(inA, LOW);
        digitalWrite(inB, LOW);
    }

    pwm.writeScaled(abs(velocidad) / 255.0f);
}


void Motores::mover(const String& direccion) {

    if (!_activo) {
        return;
    }

    if (direccion == "arriba") {
        _metaA =  SENTIDO_MOTORES * VELOCIDAD_GIRO;
        _metaB =  SENTIDO_MOTORES * VELOCIDAD_GIRO;

    } else if (direccion == "abajo") {
        _metaA = -SENTIDO_MOTORES * VELOCIDAD_GIRO;
        _metaB = -SENTIDO_MOTORES * VELOCIDAD_GIRO;

    } else if (direccion == "izquierda") {
        _metaA = -SENTIDO_MOTORES * VELOCIDAD_GIRO;
        _metaB =  SENTIDO_MOTORES * VELOCIDAD_GIRO;

    } else if (direccion == "derecha") {
        _metaA =  SENTIDO_MOTORES * VELOCIDAD_GIRO;
        _metaB = -SENTIDO_MOTORES * VELOCIDAD_GIRO;
    }
}


void Motores::girarBallet(int pwm) {
    if (_activo) {
        _metaA = SENTIDO_MOTORES * constrain(pwm, 0, VELOCIDAD_GIRO);
        _metaB = -_metaA;
    }
}

void Motores::detener() {

    _metaA = 0;
    _metaB = 0;
}

void Motores::detenerAhora() {
    detener();
    _velA = _velB = 0;
    if (_activo) {
        _rueda(_ain1, _ain2, _pwmA, 0);
        _rueda(_bin1, _bin2, _pwmB, 0);
    }
}

static int avanzarRampa(int velocidad, int meta) {
    // Al invertir, cada rueda pasa un intervalo de PWM por cero.
    if ((velocidad < 0 && meta > 0) || (velocidad > 0 && meta < 0)) {
        meta = 0;
    }
    return velocidad + constrain(meta - velocidad, -PASO_RAMPA, PASO_RAMPA);
}


void Motores::actualizar() {

    if (!_activo) {
        return;
    }

    uint32_t ahoraMs = millis();
    if (ahoraMs - _ultimaRampaMs < INTERVALO_RAMPA_MS) {
        return;
    }
    _ultimaRampaMs = ahoraMs;

    _velA = avanzarRampa(_velA, _metaA);
    _velB = avanzarRampa(_velB, _metaB);

    _rueda(_ain1, _ain2, _pwmA, _velA);
    _rueda(_bin1, _bin2, _pwmB, _velB);
}

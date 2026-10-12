// wall-e-robot/firmware/lib/motores/motores.cpp
// Kevin Gámez - 13/09/2026

#include "motores.h"
#include "pines.h"

// Velocidad fija con la que gira el d-pad (0-255 PWM). Los motores son de
// 6 V y la batería llega a 8,4 V: 178/255 ~ 70 %, para no sobrevoltarlos.
static const int VELOCIDAD_GIRO = 178;

// Rampa anti-tirón: cada cuántos ms se acerca la velocidad real a la meta
// y en cuánto.
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

    // STBY en HIGH: sin esto el TB6612 no mueve nada.
    pinMode(_stby, OUTPUT);
    digitalWrite(_stby, HIGH);

    // PWM por ESP32PWM (LEDC), no analogWrite: choca con ESP32Servo.
    _pwmA.attachPin(_pwma, 1000, 8);
    _pwmB.attachPin(_pwmb, 1000, 8);

    // Sin giro al encender: nada debe moverse hasta que la app lo diga.
    _metaA = _metaB = 0;
    _velA  = _velB  = 0;
    _rueda(_ain1, _ain2, _pwmA, 0);
    _rueda(_bin1, _bin2, _pwmB, 0);

    _activo = true;
}


// Aplica una velocidad con signo a una rueda del TB6612FNG.
//   velocidad > 0 -> inA=HIGH, inB=LOW  (gira adelante)
//   velocidad < 0 -> inA=LOW,  inB=HIGH (gira atrás)
//   velocidad ==0 -> ambos LOW (parada libre)
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

    pwm.writeScaled(abs(velocidad) / 255.0f);   // duty 0.0 .. 1.0
}


void Motores::mover(const String& direccion) {

    if (!_activo) {
        return;   // el módulo no está cableado/activo: no mover nada
    }

    if (direccion == "arriba") {
        _metaA =  VELOCIDAD_GIRO;
        _metaB =  VELOCIDAD_GIRO;

    } else if (direccion == "abajo") {
        _metaA = -VELOCIDAD_GIRO;
        _metaB = -VELOCIDAD_GIRO;

    } else if (direccion == "izquierda") {
        // Giro en el sitio: ruedas contrapuestas.
        _metaA = -VELOCIDAD_GIRO;
        _metaB =  VELOCIDAD_GIRO;

    } else if (direccion == "derecha") {
        _metaA =  VELOCIDAD_GIRO;
        _metaB = -VELOCIDAD_GIRO;
    }
}


void Motores::detener() {

    // Se frenan las METAS: las velocidades reales bajan de a poco por la
    // rampa (frenado suave en vez de un corte seco).
    _metaA = 0;
    _metaB = 0;
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

    // Un "paso" de rampa hacia la meta (sin pasarse de ella).
    if (_velA < _metaA) { _velA = min(_metaA, _velA + PASO_RAMPA); }
    if (_velA > _metaA) { _velA = max(_metaA, _velA - PASO_RAMPA); }
    if (_velB < _metaB) { _velB = min(_metaB, _velB + PASO_RAMPA); }
    if (_velB > _metaB) { _velB = max(_metaB, _velB - PASO_RAMPA); }

    _rueda(_ain1, _ain2, _pwmA, _velA);
    _rueda(_bin1, _bin2, _pwmB, _velB);
}

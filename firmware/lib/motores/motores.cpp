// wall-e-robot/firmware/lib/motores/motores.cpp
// Kevin Gámez - 13/09/2026

#include "motores.h"
#include "pines.h"

// Velocidad fija con la que gira el d-pad (0-255 PWM). Calibrar sobre el
// suelo real: 200 es un valor moderado para pruebas de banco.
static const int VELOCIDAD_GIRO = 200;

// Rampa anti-tirón: cada cuántos ms se acerca la velocidad real a la meta
// y en cuánto (de 0 a 200 son ~14 pasos -> unos 170 ms de aceleración).
static const int       PASO_RAMPA       = 15;
static const uint32_t  INTERVALO_RAMPA_MS = 12;


Motores motores(PIN_MOTOR_IN1, PIN_MOTOR_IN2,
                PIN_MOTOR_IN3, PIN_MOTOR_IN4,
                PIN_MOTOR_ENA, PIN_MOTOR_ENB);


Motores::Motores(uint8_t in1, uint8_t in2, uint8_t in3, uint8_t in4,
                 uint8_t enA, uint8_t enB)
    : _in1(in1), _in2(in2), _in3(in3), _in4(in4)
    , _enA(enA), _enB(enB)
    , _activo(false)
    , _metaA(0), _metaB(0), _velA(0), _velB(0), _ultimaRampaMs(0) {}


void Motores::iniciar() {

    for (const uint8_t pin : { _in1, _in2, _in3, _in4, _enA, _enB }) {
        pinMode(pin, OUTPUT);
    }

    // Sin giro al encender: nada debe moverse hasta que la app lo diga.
    _metaA = _metaB = 0;
    _velA  = _velB  = 0;
    _rueda(_in1, _in2, _enA, 0);
    _rueda(_in3, _in4, _enB, 0);

    _activo = true;
}


// Aplica una velocidad con signo a una rueda del L298N.
//   velocidad > 0 -> inA=HIGH, inB=LOW  (gira adelante)
//   velocidad < 0 -> inA=LOW,  inB=HIGH (gira atrás)
//   velocidad ==0 -> ambos LOW (freno libre en el driver)
void Motores::_rueda(uint8_t inA, uint8_t inB, uint8_t en, int velocidad) {

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

    analogWrite(en, abs(velocidad));
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

    _rueda(_in1, _in2, _enA, _velA);
    _rueda(_in3, _in4, _enB, _velB);
}
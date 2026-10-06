// wall-e-robot/firmware/lib/motores/motores.cpp
// Kevin Gámez - 13/09/2026

#include "motores.h"
#include "pines.h"

// Velocidad fija con la que gira el d-pad (0-255 PWM). Calibrar sobre el
// suelo real: 200 es un valor moderado para pruebas de banco.
static const int VELOCIDAD_GIRO = 200;


Motores motores(PIN_MOTOR_IN1, PIN_MOTOR_IN2,
                PIN_MOTOR_IN3, PIN_MOTOR_IN4,
                PIN_MOTOR_ENA, PIN_MOTOR_ENB);


Motores::Motores(uint8_t in1, uint8_t in2, uint8_t in3, uint8_t in4,
                 uint8_t enA, uint8_t enB)
    : _in1(in1), _in2(in2), _in3(in3), _in4(in4)
    , _enA(enA), _enB(enB)
    , _activo(false) {}


void Motores::iniciar() {

    for (const uint8_t pin : { _in1, _in2, _in3, _in4, _enA, _enB }) {
        pinMode(pin, OUTPUT);
    }

    // Sin giro al encender: nada debe moverse hasta que la app lo diga.
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
        _rueda(_in1, _in2, _enA,  VELOCIDAD_GIRO);
        _rueda(_in3, _in4, _enB,  VELOCIDAD_GIRO);

    } else if (direccion == "abajo") {
        _rueda(_in1, _in2, _enA, -VELOCIDAD_GIRO);
        _rueda(_in3, _in4, _enB, -VELOCIDAD_GIRO);

    } else if (direccion == "izquierda") {
        // Giro en el sitio: ruedas contrapuestas.
        _rueda(_in1, _in2, _enA, -VELOCIDAD_GIRO);
        _rueda(_in3, _in4, _enB,  VELOCIDAD_GIRO);

    } else if (direccion == "derecha") {
        _rueda(_in1, _in2, _enA,  VELOCIDAD_GIRO);
        _rueda(_in3, _in4, _enB, -VELOCIDAD_GIRO);
    }
}


void Motores::detener() {

    _rueda(_in1, _in2, _enA, 0);
    _rueda(_in3, _in4, _enB, 0);
}
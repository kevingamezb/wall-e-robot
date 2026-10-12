// wall-e-robot/firmware/lib/leds/leds.cpp
// Kevin Gámez - 13/10/2026

#include "leds.h"
#include "pines.h"


Leds leds;


Leds::Leds()
    : _activo(false) {}


void Leds::iniciar() {

    pinMode(PIN_LED_ROJO, OUTPUT);
    pinMode(PIN_LED_AMARILLO, OUTPUT);

    digitalWrite(PIN_LED_ROJO, LOW);
    digitalWrite(PIN_LED_AMARILLO, LOW);

    _activo = true;
}


void Leds::actualizar(bool hayAdvertencia, bool hayError) {

    if (!_activo) {
        return;
    }

    bool alerta = hayAdvertencia || hayError;

    digitalWrite(PIN_LED_ROJO,     alerta ? HIGH : LOW);
    digitalWrite(PIN_LED_AMARILLO, alerta ? LOW  : HIGH);
}

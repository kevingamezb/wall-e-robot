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

    // Arranca apagados; actualizar() fija el estado real.
    digitalWrite(PIN_LED_ROJO, LOW);
    digitalWrite(PIN_LED_AMARILLO, LOW);

    _activo = true;
}


void Leds::actualizar(bool hayAdvertencia, bool hayError, bool hayModuloInactivo) {

    if (!_activo) {
        return;
    }

    // Cualquiera de las tres condiciones se considera alerta.
    bool alerta = hayAdvertencia || hayError || hayModuloInactivo;

    digitalWrite(PIN_LED_ROJO,     alerta ? HIGH : LOW);
    digitalWrite(PIN_LED_AMARILLO, alerta ? LOW  : HIGH);
}

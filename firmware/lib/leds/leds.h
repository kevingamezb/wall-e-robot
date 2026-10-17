// wall-e-robot/firmware/lib/leds/leds.h
// Kevin Gámez - 13/10/2026

#ifndef LEDS_H
#define LEDS_H

#include <Arduino.h>

/*
 *  Leds: dos indicadores de estado (rojo y amarillo) en GPIO.
 *
 *  Resumen visual: rojo = alerta (advertencia, error o módulo inactivo);
 *  amarillo = operación normal.
 */
class Leds {

public:

    Leds();

    // Configura los pines como salida.
    void iniciar();

    // Enciende el rojo si hay cualquier alerta; el amarillo, si todo está
    // en orden.
    void actualizar(bool hayAdvertencia, bool hayError, bool hayModuloInactivo);

private:

    bool _activo;
};

extern Leds leds;

#endif // LEDS_H

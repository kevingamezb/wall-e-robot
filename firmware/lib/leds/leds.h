// wall-e-robot/firmware/lib/leds/leds.h
// Kevin Gámez - 13/10/2026

#ifndef LEDS_H
#define LEDS_H

#include <Arduino.h>

/*
 *  Leds: 2 indicadores de estado.
 *   - Amarillo: robot funcionando sin alertas.
 *   - Rojo    : advertencia de radar o error de batería.
 *
 *  El LED verde de "encendido" va directo al riel de 5 V, sin GPIO.
 */
class Leds {

public:

    Leds();

    void iniciar();

    // Refresca los LEDs según las alertas del estado.
    void actualizar(bool hayAdvertencia, bool hayError);

private:

    bool _activo;
};

// Instancia única global.
extern Leds leds;

#endif // LEDS_H

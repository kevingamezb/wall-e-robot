#ifndef LEDS_H
#define LEDS_H

#include <Arduino.h>

class Leds {

public:

    Leds();

    void iniciar();

    // Rojo para advertencias, errores o módulos inactivos. Amarillo en operación normal.
    void actualizar(bool hayAdvertencia, bool hayError, bool hayModuloInactivo);

private:

    bool _activo;
};

extern Leds leds;

#endif

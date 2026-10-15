// wall-e-robot/firmware/lib/auto/auto.cpp
// Kevin Gámez - 15/10/2026

#include "auto.h"
#include "config.h"
#include "distancia.h"
#include "motores.h"


Auto autoRobot;


Auto::Auto()
    : _modoAutonomo(true)
    , _navegacion("recto") {}


void Auto::iniciar() {

    // Sin hardware propio que configurar;
    _modoAutonomo = true;
    _navegacion   = "recto";
}


void Auto::actualizar() {

    if (!_modoAutonomo) {
        return;   // en manual manda el operador
    }

    if (!sensorDistancia.hayLecturaNueva()) {
        return;   // el sensor aún no terminó un ciclo de medición
    }

    if (hayObstaculo()) {

        // Obstáculo: se desvía girando en el sitio hasta quedar libre.
        motores.mover("derecha");
        _navegacion = "derecha";

    } else {

        motores.mover("arriba");
        _navegacion = "recto";
    }
}


void Auto::modoAutonomo(bool activo) {

    if (_modoAutonomo && !activo) {
        // Salida de automático.
        motores.detener();
        _navegacion = "recto";
    }

    _modoAutonomo = activo;
}


bool Auto::hayObstaculo() const {
    // obstaculoCercano() ya descarta las lecturas sin eco (distancia -1).
    return sensorDistancia.obstaculoCercano(UMBRAL_OBSTACULO_CM);
}


const String& Auto::navegacion() const {
    return _navegacion;
}

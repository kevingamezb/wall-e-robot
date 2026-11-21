#ifndef AUTO_H
#define AUTO_H

#include <Arduino.h>
#include "decision.h"

// Aplica las decisiones de navegación autónoma al controlador de motores.
class Auto {

public:

    Auto();

    void iniciar();

    void actualizar();

    void modoAutonomo(bool activo);

    bool hayObstaculo() const;

    // Última maniobra decidida: "recto" | "izquierda" | "derecha" | "alto".
    const String& navegacion() const;
    bool bloqueado() const { return _bloqueado; }

private:

    bool   _modoAutonomo;
    String _navegacion;
    NavegacionAuto _decision;
    bool _bloqueado = false;
};

extern Auto autoRobot;

#endif

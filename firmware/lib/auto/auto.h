// wall-e-robot/firmware/lib/auto/auto.h
// Kevin Gámez - 15/10/2026

#ifndef AUTO_H
#define AUTO_H

#include <Arduino.h>

/*
 *  Auto: navegación autónoma.
 */
class Auto {

public:

    Auto();

    // No toca hardware
    void iniciar();

    // Decide y aplica la maniobra del ciclo. Debe llamarse en modo automático.
    void actualizar();

    // Sincroniza el modo.
    void modoAutonomo(bool activo);

    // true si hay lectura y el obstáculo está a UMBRAL_OBSTACULO_CM o menos.
    bool hayObstaculo() const;

    // Última maniobra decidida: "recto" | "izquierda" | "derecha" | "alto".
    const String& navegacion() const;

private:

    bool   _modoAutonomo;
    String _navegacion;
};

extern Auto autoRobot;

#endif // AUTO_H

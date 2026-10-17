// wall-e-robot/firmware/lib/auto/auto.h
// Kevin Gámez - 15/10/2026

#ifndef AUTO_H
#define AUTO_H

#include <Arduino.h>

/*
 *  Auto: navegación autónoma de evasión.
 *
 *  Cierra el lazo sensor de distancia -> motores: en modo automático decide una
 *  maniobra por ciclo y la aplica. El resultado se publica vía navegacion().
 */
class Auto {

public:

    // Constructor: arranca en modo automático y navegación "recto".
    Auto();

    // Reinicia el estado interno; no toca hardware.
    void iniciar();

    // Decide y aplica la maniobra del ciclo; debe llamarse en modo automático.
    void actualizar();

    // Sincroniza el modo; al salir de automático detiene los motores.
    void modoAutonomo(bool activo);

    // true si hay lectura válida (no -1) y el obstáculo está dentro de
    // UMBRAL_OBSTACULO_CM.
    bool hayObstaculo() const;

    // Última maniobra decidida: "recto" | "izquierda" | "derecha" | "alto".
    const String& navegacion() const;

private:

    bool   _modoAutonomo;
    String _navegacion;
};

extern Auto autoRobot;

#endif // AUTO_H

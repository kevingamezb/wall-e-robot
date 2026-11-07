// wall-e-robot/firmware/lib/decision/decision.h
// Kevin Gámez - 03/11/2026
//
// Decisión pura de navegación autónoma.
//
// No depende de Arduino ni del hardware, así que se puede probar con
// PlatformIO en el entorno nativo (pio test -e native). Auto solo traduce el
// resultado a comandos de motor.

#ifndef DECISION_H
#define DECISION_H

#include <stdint.h>

enum class ManiobraDecision : uint8_t {
    ALTO,       // sin lectura, lectura vieja o sin eco: no moverse
    RECTO,      // camino libre
    DERECHA,    // obstáculo dentro del umbral: girar
};

// Decide la maniobra a partir de la frescura y la distancia.
//   lecturaFresca: la última medición terminó dentro del plazo permitido.
//   distanciaCm:   última distancia; negativa = sin eco.
//   umbralCm:      distancia mínima libre.
ManiobraDecision decidirManiobra(bool lecturaFresca, float distanciaCm,
                                 float umbralCm);

// Nombre estable para telemetría: "alto" | "recto" | "derecha".
const char* nombreManiobra(ManiobraDecision maniobra);

#endif // DECISION_H

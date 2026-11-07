// wall-e-robot/firmware/lib/decision/decision.cpp
// Kevin Gámez - 03/11/2026

#include "decision.h"

ManiobraDecision decidirManiobra(bool lecturaFresca, float distanciaCm,
                                 float umbralCm) {

    // Sin lectura fresca no se avanza a ciegas.
    if (!lecturaFresca) {
        return ManiobraDecision::ALTO;
    }

    // -1 = el HC-SR04 no recibió eco; tampoco se avanza.
    if (distanciaCm < 0.0f) {
        return ManiobraDecision::ALTO;
    }

    // El borde exacto del umbral ya se considera obstáculo.
    if (distanciaCm <= umbralCm) {
        return ManiobraDecision::DERECHA;
    }

    return ManiobraDecision::RECTO;
}

const char* nombreManiobra(ManiobraDecision maniobra) {

    switch (maniobra) {
        case ManiobraDecision::RECTO:   return "recto";
        case ManiobraDecision::DERECHA: return "derecha";
        case ManiobraDecision::ALTO:
        default:                        return "alto";
    }
}

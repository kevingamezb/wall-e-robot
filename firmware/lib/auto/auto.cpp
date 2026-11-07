// wall-e-robot/firmware/lib/auto/auto.cpp
// Kevin Gámez - 15/10/2026

#include "auto.h"
#include "config.h"
#include "decision.h"
#include "distancia.h"
#include "motores.h"


Auto autoRobot;


Auto::Auto()
    : _modoAutonomo(true)
    , _navegacion("alto") {}


void Auto::iniciar() {

    // Sin hardware propio que configurar: solo reinicia el estado. Arranca
    // detenido y no se moverá hasta tener una lectura fresca y válida.
    _modoAutonomo = true;
    _navegacion   = "alto";
    motores.detener();
}


void Auto::actualizar() {

    if (!_modoAutonomo) {
        return;   // en manual manda el operador
    }

    // La decisión es pura y se prueba en el entorno nativo. Sin lectura
    // fresca, sin eco o con obstáculo cerca, la respuesta nunca es "avanzar
    // a ciegas".
    ManiobraDecision decision = decidirManiobra(
        sensorDistancia.lecturaFresca(TIEMPO_MAX_LECTURA_MS),
        sensorDistancia.distanciaCm(),
        UMBRAL_OBSTACULO_CM);

    switch (decision) {

    case ManiobraDecision::RECTO:
        motores.mover("arriba");
        break;

    case ManiobraDecision::DERECHA:
        // Obstáculo: se desvía girando en el sitio hasta quedar libre.
        motores.mover("derecha");
        break;

    case ManiobraDecision::ALTO:
    default:
        motores.detener();
        break;
    }

    _navegacion = nombreManiobra(decision);
}


void Auto::modoAutonomo(bool activo) {

    if (activo == _modoAutonomo) {
        return;
    }

    // En CUALQUIER transición (manual -> automático o al revés) se detienen
    // los motores: el primer movimiento debe ser una decisión explícita, no
    // una orden heredada del modo anterior.
    motores.detener();
    _navegacion = "alto";
    _modoAutonomo = activo;
}


bool Auto::hayObstaculo() const {
    // obstaculoCercano() ya descarta las lecturas sin eco (distancia -1).
    return sensorDistancia.obstaculoCercano(UMBRAL_OBSTACULO_CM);
}


const String& Auto::navegacion() const {
    return _navegacion;
}

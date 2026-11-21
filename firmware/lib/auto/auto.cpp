#include "auto.h"
#include "config.h"
#include "distancia.h"
#include "motores.h"
#include "servos.h"


Auto autoRobot;


Auto::Auto()
    : _modoAutonomo(true)
    , _navegacion("alto") {}


void Auto::iniciar() {

    _modoAutonomo = true;
    _navegacion   = "alto";
    _decision.reiniciar();
    _bloqueado = false;
    motores.detener();
}


void Auto::actualizar() {

    if (!_modoAutonomo) {
        return;
    }

    const auto decision = _decision.actualizar(
        millis(), motores.detenidos(),
        sensorDistancia.lecturaFresca(TIEMPO_MAX_LECTURA_MS),
        sensorDistancia.distanciaCm(),
        sensorDistancia.inicioUltimaLecturaMs(),
        UMBRAL_OBSTACULO_CM);

    _navegacion = nombreManiobra(decision.maniobra);
    _bloqueado = decision.bloqueado;
    if (decision.maniobra == ManiobraDecision::ALTO) {
        motores.detener();
    } else {
        motores.mover(decision.maniobra == ManiobraDecision::RECTO ? "arriba" : _navegacion);
    }

    if (MODULOS.servos) {
        switch (decision.gesto) {
            case GestoAuto::CUELLO_DERECHA:   servos.aplicarGesto("cuello", 18); break;
            case GestoAuto::CUELLO_IZQUIERDA: servos.aplicarGesto("cuello", -18); break;
            case GestoAuto::SALUDO:           servos.aplicarGesto("hombro_izquierdo", 25); break;
            case GestoAuto::NINGUNO:          servos.aplicarGesto(nullptr); break;
        }
    }
}


void Auto::modoAutonomo(bool activo) {

    if (activo == _modoAutonomo) {
        return;
    }

    // Detiene los motores al cambiar de modo para descartar la orden anterior.
    motores.detener();
    servos.aplicarGesto(nullptr);
    _decision.reiniciar();
    _bloqueado = false;
    _navegacion = "alto";
    _modoAutonomo = activo;
}


bool Auto::hayObstaculo() const {
    return sensorDistancia.obstaculoCercano(UMBRAL_OBSTACULO_CM);
}


const String& Auto::navegacion() const {
    return _navegacion;
}

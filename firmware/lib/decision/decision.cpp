#include "decision.h"

namespace {
constexpr uint32_t PAUSA_MS = 400;
constexpr uint32_t GIRO_MS = 350;
// El segundo giro cruza la orientación inicial para explorar el otro lado.
constexpr uint32_t CONTRAGIRO_MS = 700;
constexpr uint32_t SALUDO_MS = 350;
}

void NavegacionAuto::reiniciar() {
    _fase = Fase::FRENAR;
    _intentos = 0;
}

DecisionAuto NavegacionAuto::actualizar(uint32_t ahora, bool motoresDetenidos,
                                       bool lecturaFresca, float distanciaCm,
                                       uint32_t inicioLectura, float umbralCm) {
    const bool valida = lecturaFresca && distanciaCm >= 0.0f;
    const bool libre = valida && distanciaCm > umbralCm;

    if (!valida && (_fase == Fase::AVANZAR || _fase == Fase::GIRO ||
                    _fase == Fase::SALUDO)) {
        _fase = Fase::FRENAR;
    }

    switch (_fase) {
        case Fase::FRENAR:
            if (motoresDetenidos) {
                _fase = Fase::MEDIR;
                _desde = ahora;
            }
            return {};

        case Fase::MEDIR:
            // El pulso debe salir después de detener las ruedas.
            if (!lecturaFresca || ahora - inicioLectura >= ahora - _desde) {
                return {};
            }
            if (libre) {
                if (_intentos == 2) {
                    _intentos = 0;
                    _fase = Fase::SALUDO;
                    _desde = ahora;
                    return {ManiobraDecision::ALTO, GestoAuto::SALUDO};
                }
                _intentos = 0;
                _fase = Fase::AVANZAR;
                return {ManiobraDecision::RECTO};
            }
            if (_intentos == 2) {
                _fase = Fase::BLOQUEADO;
                return {ManiobraDecision::ALTO, GestoAuto::NINGUNO, true};
            }
            if (!valida) {
                return {};
            }
            if (_intentos == 1) {
                _giroDerecha = !_giroDerecha;
                _fase = Fase::GIRO;
                _desde = ahora;
                ++_intentos;
                return {_giroDerecha ? ManiobraDecision::DERECHA : ManiobraDecision::IZQUIERDA};
            }
            [[fallthrough]];

        case Fase::AVANZAR:
            if (libre) {
                return {ManiobraDecision::RECTO};
            }
            _giroDerecha = _primeroDerecha;
            _primeroDerecha = !_primeroDerecha;
            _fase = Fase::PAUSA;
            return {};

        case Fase::PAUSA:
            if (!motoresDetenidos || !valida) {
                return {};
            }
            if (libre) {
                _fase = Fase::FRENAR;
                return {};
            }
            _fase = Fase::GESTO_CUELLO;
            _desde = ahora;
            [[fallthrough]];

        case Fase::GESTO_CUELLO:
            if (!valida || libre) {
                _fase = Fase::FRENAR;
                return {};
            }
            if (ahora - _desde < PAUSA_MS) {
                return {ManiobraDecision::ALTO, _giroDerecha ? GestoAuto::CUELLO_DERECHA
                                                           : GestoAuto::CUELLO_IZQUIERDA};
            }
            _fase = Fase::GIRO;
            _desde = ahora;
            ++_intentos;
            [[fallthrough]];

        case Fase::GIRO:
            if (ahora - _desde >= (_intentos == 1 ? GIRO_MS : CONTRAGIRO_MS)) {
                _fase = Fase::FRENAR;
                return {};
            }
            return {_giroDerecha ? ManiobraDecision::DERECHA : ManiobraDecision::IZQUIERDA};

        case Fase::SALUDO:
            if (libre && ahora - _desde < SALUDO_MS) {
                return {ManiobraDecision::ALTO, GestoAuto::SALUDO};
            }
            _fase = Fase::FRENAR;
            return {};

        case Fase::BLOQUEADO:
            if (libre) {
                _intentos = 0;
                _fase = Fase::AVANZAR;
                return {ManiobraDecision::RECTO};
            }
            return {ManiobraDecision::ALTO, GestoAuto::NINGUNO, true};
    }
    return {};
}

const char* nombreManiobra(ManiobraDecision maniobra) {
    switch (maniobra) {
        case ManiobraDecision::RECTO:     return "recto";
        case ManiobraDecision::DERECHA:   return "derecha";
        case ManiobraDecision::IZQUIERDA: return "izquierda";
        case ManiobraDecision::ALTO:
        default:                          return "alto";
    }
}

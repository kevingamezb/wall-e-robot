// Sin dependencias de Arduino o del hardware. Se prueba con pio test -e native.

#ifndef DECISION_H
#define DECISION_H

#include <stdint.h>

enum class ManiobraDecision : uint8_t {
    ALTO,       // sin lectura, lectura vieja o sin eco: no moverse
    RECTO,
    DERECHA,
    IZQUIERDA,
};

enum class GestoAuto : uint8_t { NINGUNO, CUELLO_DERECHA, CUELLO_IZQUIERDA, SALUDO };

struct DecisionAuto {
    ManiobraDecision maniobra;
    GestoAuto gesto;
    bool bloqueado;
};

class NavegacionAuto {
public:
    void reiniciar();
    DecisionAuto actualizar(uint32_t ahora, bool motoresDetenidos,
                            bool lecturaFresca, float distanciaCm,
                            uint32_t inicioLectura, float umbralCm);

private:
    enum class Fase { FRENAR, MEDIR, AVANZAR, PAUSA, GESTO_CUELLO, GIRO, SALUDO, BLOQUEADO };

    Fase _fase = Fase::FRENAR;
    uint32_t _desde = 0;
    unsigned _intentos = 0;
    bool _primeroDerecha = true;
    bool _giroDerecha = true;
};

// Nombres estables para la telemetría.
const char* nombreManiobra(ManiobraDecision maniobra);

#endif

// wall-e-robot/firmware/lib/servos/servos.cpp
// Kevin Gámez - 13/09/2026

#include "servos.h"
#include "config.h"
#include "pines.h"

// Mapeo nombre -> índice de servo físico. El nombre es el que usa la app en
// el comando {"tipo":"servo","servo":...}; -1 = nombre sin servo en el hardware.
struct ParServo {
    const char* nombre;
    int         indice;
};

static const ParServo MAPA_SERVOS[] = {
    { "cuello",             0 },
    { "hombro_izquierdo",   1 },
    { "hombro_derecho",     2 },
    { "pulgar_izquierdo",  -1 },
    { "pulgar_derecho",    -1 },
};

static const int CANTIDAD_NOMBRES = sizeof(MAPA_SERVOS) / sizeof(MAPA_SERVOS[0]);

// Pines físicos de cada servo (índices 0, 1 y 2).
static const uint8_t PINES_SERVO[Servos::CANTIDAD_FISICA] = {
    PIN_SERVO_CUELLO, PIN_SERVO_BRAZO_IZQ, PIN_SERVO_BRAZO_DER,
};

// Los MG90S se usan entre 10 y 170 grados para no forzarlos contra los topes.
// La app centra el servo en 0 grados, que corresponde a 90 físicos.
static const int SERVO_GRAU_MIN = 10;
static const int SERVO_GRAU_MAX = 170;
static const int SERVO_CENTRO   = 90;


Servos servos;   // instancia global única, como en comunicacion.h se acordó


Servos::Servos()
    : _listo(false) {

    for (int i = 0; i < CANTIDAD; i++) {
        _angulos[i] = 0;   // arrancamos "en reposo"
    }
}


void Servos::iniciar() {

    for (int i = 0; i < CANTIDAD_FISICA; i++) {
        _servos[i].setPeriodHertz(50);            // 50 Hz: frecuencia clásica
        _servos[i].attach(PINES_SERVO[i], 500, 2400);
    }

    _listo = true;

    // Escribimos la posición inicial de los servos habilitados.
    for (int i = 0; i < CANTIDAD; i++) {
        if (habilitado(i)) {
            escribirServo(i, _angulos[i]);
        }
    }
}


int Servos::indiceDe(const char* nombre) const {

    for (int i = 0; i < CANTIDAD_NOMBRES; i++) {
        if (strcmp(nombre, MAPA_SERVOS[i].nombre) == 0) {
            return MAPA_SERVOS[i].indice;
        }
    }
    return -1;   // no existe ese servo
}


bool Servos::habilitado(int indice) const {
    return indice >= 0 && indice < CANTIDAD_FISICA && SERVOS_ACTIVOS[indice];
}


void Servos::escribirServo(int indice, int angulo) {

    if (!_listo || indice < 0 || indice >= CANTIDAD_FISICA) {
        return;   // sin servo físico no hay a quién escribirle
    }

    // El centro de la app (0 grados) es 90 físicos. Clamp a 10..170.
    int pos = constrain(SERVO_CENTRO + angulo, SERVO_GRAU_MIN, SERVO_GRAU_MAX);
    _servos[indice].write(pos);
}


void Servos::moverServo(const char* nombre, int angulo) {

    int indice = indiceDe(nombre);
    if (indice < 0) {
        return;   // pulgar o nombre desconocido: no hay servo que mover
    }

    _angulos[indice] = angulo;                 // siempre guardamos...
    if (habilitado(indice)) {
        escribirServo(indice, angulo);         // ...y movemos solo si está activo
    }
}


void Servos::angulosUsuario(int destino[CANTIDAD]) const {
    for (int i = 0; i < CANTIDAD; i++) {
        destino[i] = _angulos[i];
    }
}

// wall-e-robot/firmware/lib/servos/servos.cpp
// Kevin Gámez - 13/09/2026

#include "servos.h"
#include "config.h"
#include "pines.h"

// Mapeo nombre -> canal. El nombre es el que usa la app en el comando
// {"tipo":"servo","servo":...}; el canal es dónde está el servo en la placa.
struct ParServoCanal {
    const char* nombre;
    uint8_t     canal;
};

static const ParServoCanal MAPA_SERVOS[] = {
    { "cuello",             0 },
    { "hombro_izquierdo",   1 },
    { "hombro_derecho",     2 },
    { "pulgar_izquierdo",   3 },
    { "pulgar_derecho",     4 },
};

static const int CANTIDAD_SERVOS = sizeof(MAPA_SERVOS) / sizeof(MAPA_SERVOS[0]);

// Pulsos estándar para servos de hobby: 500us..2500us ~ -90..90 grados.
static const int PULSO_MIN_US = 500;
static const int PULSO_MAX_US = 2500;
static const int GRAUS_MIN    = -90;
static const int GRAUS_MAX    = 90;


Servos servos;   // instancia global única, como en comunicacion.h se acordó


Servos::Servos()
    : _placa(DIR_PCA9685)
    , _placaLista(false) {

    for (int i = 0; i < CANTIDAD; i++) {
        _angulos[i] = 0;   // arrancamos "en reposo"
    }
}


void Servos::iniciar() {

    _placa.begin();
    _placa.setPWMFreq(50);   // 50 Hz: frecuencia clásica de los servos
    _placaLista = true;

    // Escribimos la posición inicial de los canales habilitados.
    for (int i = 0; i < CANTIDAD; i++) {
        if (habilitado(i)) {
            escribirPulso(i, _angulos[i]);
        }
    }
}


uint8_t Servos::canalDe(const char* nombre) const {

    for (int i = 0; i < CANTIDAD_SERVOS; i++) {
        if (strcmp(nombre, MAPA_SERVOS[i].nombre) == 0) {
            return MAPA_SERVOS[i].canal;
        }
    }
    return 255;   // no existe ese servo
}


bool Servos::habilitado(uint8_t canal) const {
    return canal < CANTIDAD && SERVOS_ACTIVOS[canal];
}


void Servos::escribirPulso(uint8_t canal, int angulo) {

    if (!_placaLista) {
        return;   // sin placa no hay a quién escribirle
    }

    // map(-90..90, 500us..2500us): centro del servo = 0°.
    int us = map(angulo, GRAUS_MIN, GRAUS_MAX, PULSO_MIN_US, PULSO_MAX_US);
    _placa.writeMicroseconds(canal, (uint16_t)us);
}


void Servos::moverServo(const char* nombre, int angulo) {

    uint8_t canal = canalDe(nombre);
    if (canal == 255) {
        return;   // nombre desconocido (comunicacion ya validó, doble cerrojo)
    }

    _angulos[canal] = angulo;                 // siempre guardamos...
    if (habilitado(canal)) {
        escribirPulso(canal, angulo);         // ...y movemos solo si está activo
    }
}


void Servos::moverRadar(int angulo) {
    escribirPulso(CANAL_RADAR, angulo);
}


void Servos::angulosUsuario(int destino[CANTIDAD]) const {
    for (int i = 0; i < CANTIDAD; i++) {
        destino[i] = _angulos[i];
    }
}
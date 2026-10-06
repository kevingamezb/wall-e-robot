// wall-e-robot/firmware/lib/servos/servos.h
// Kevin Gámez - 13/09/2026

#ifndef SERVOS_H
#define SERVOS_H

#include <Arduino.h>
#include <Adafruit_PWMServoDriver.h>

/*
 *  Servos: capa limpia sobre la PCA9685 para los 5 servos de
 *  usuario + el servo del radar.
 *
 *  - Traduce el nombre que manda la app ("cuello", "pulgar_izquierdo"...)
 *    al canal físico de la placa (MAPA_SERVOS[]).
 *  - Respeta SERVOS_ACTIVOS[]: cada servo se mueve solo si su flag
 *    está en 1 (pruebas aisladas).
 *  - Guarda SIEMPRE el último ángulo comandado aunque el servo esté
 *    inactivo, para que la telemetría (enviarEstado) refleje lo que
 *    la GUI cree que está mandando.
 *
 *  El servo del radar (CANAL_RADAR) es aparte: no aparece en
 *  MAPA_SERVOS porque no es una articulación de usuario. Se mueve
 *  con moverRadar(), que llama el firmware en su barrido autónomo.
 */

class Servos {

public:

    static const int CANTIDAD = 5;   // cuántos servos de usuario hay

    Servos();

    // Inicia la placa (llamar solo si MODULOS.servos o radar está activo).
    // Si no se llama, moverServo()/moverRadar() solo guardan el ángulo.
    void iniciar();

    // Mueve un servo de usuario por nombre (lo que manda "{"tipo":"servo"}").
    void moverServo(const char* nombre, int angulo);

    // Mueve el servo del radar (canal 5). No depende de SERVOS_ACTIVOS,
    // si no de que la placa esté iniciada (MODULOS.radar o servos).
    void moverRadar(int angulo);

    // Copia los ángulos actuales (últimos comandados) al arreglo destino.
    void angulosUsuario(int destino[CANTIDAD]) const;

private:

    uint8_t canalDe(const char* nombre) const;
    bool    habilitado(uint8_t canal) const;
    void    escribirPulso(uint8_t canal, int angulo);

    Adafruit_PWMServoDriver _placa;
    bool   _placaLista;
    int    _angulos[CANTIDAD];
};

// Instancia única global (la usan comunicacion.cpp y main.cpp).
extern Servos servos;

#endif // SERVOS_H
// wall-e-robot/firmware/lib/servos/servos.h
// Kevin Gámez - 13/09/2026

#ifndef SERVOS_H
#define SERVOS_H

#include <Arduino.h>
#include <ESP32Servo.h>

/*
 *  Servos: capa sobre los 3 servos MG90S conectados directo a GPIO.
 */
class Servos {

public:

    static const int CANTIDAD        = 3;   // servos que reporta la app TODO(calibrar): ajustar contra app.
    static const int CANTIDAD_FISICA = 3;   // servos realmente cableados

    Servos();

    // Configura los 3 servos.
    void iniciar();

    // Mueve un servo por nombre, como llega en {"tipo":"servo"}.
    void moverServo(const char* nombre, int angulo);

    // Copia los últimos ángulos comandados al arreglo destino.
    void angulosUsuario(int destino[CANTIDAD]) const;

private:

    // Orden de _servos[] y de SERVOS_ACTIVOS[].
    enum IndiceServo {
        IDX_CUELLO = 0,
        IDX_HOMBRO_IZQ,
        IDX_HOMBRO_DER
    };

    int  indiceDe(const char* nombre) const;
    bool habilitado(int indice) const;
    void escribirServo(int indice, int angulo);

    Servo _servos[CANTIDAD_FISICA];
    bool  _listo;
    int   _angulos[CANTIDAD];
};

// Instancia única global.
extern Servos servos;

#endif // SERVOS_H

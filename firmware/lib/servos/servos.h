#ifndef SERVOS_H
#define SERVOS_H

#include <Arduino.h>
#include <ESP32Servo.h>

/*
 *  Servos: capa sobre los servos MG90S conectados directo a GPIO.
 *
 *  Traduce los nombres de la app a índices físicos, valida topes y guarda el
 *  último ángulo comandado aunque el servo no esté cableado (SERVOS_ACTIVOS[]).
 */
class Servos {

public:

    static const int CANTIDAD        = 3;   // servos que reporta la app TODO(calibrar): ajustar contra app.
    static const int CANTIDAD_FISICA = 3;   // servos realmente cableados

    Servos();

    void iniciar();

    // Mueve un servo por nombre (como llega en {"tipo":"servo"}); ignora
    // nombres desconocidos.
    void moverServo(const char* nombre, int angulo);

    // Pose temporal. Un nombre nulo devuelve el servo a su último ángulo manual.
    void aplicarGesto(const char* nombre, int angulo = 0);

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
    int   _servoGesto = -1;
    int   _anguloGesto = 0;
};

extern Servos servos;

#endif

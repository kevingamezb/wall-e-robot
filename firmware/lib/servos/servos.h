// wall-e-robot/firmware/lib/servos/servos.h
// Kevin Gámez - 13/09/2026

#ifndef SERVOS_H
#define SERVOS_H

#include <Arduino.h>
#include <ESP32Servo.h>

/*
 *  Servos: capa limpia sobre 3 servos MG90S conectados directo a GPIO.
 *
 *  - Traduce el nombre que manda la app ("cuello", "hombro_izquierdo"...)
 *    al servo físico (MAPA_SERVOS[] en servos.cpp).
 *  - Respeta SERVOS_ACTIVOS[]: cada servo se mueve solo si su flag
 *    está en 1 (pruebas aisladas).
 *  - Guarda SIEMPRE el último ángulo comandado aunque el servo esté
 *    inactivo, para que la telemetría (enviarEstado) refleje lo que
 *    la GUI cree que está mandando.
 *
 *  El hardware real no trae pulgares ni servo de radar: esos nombres
 *  se aceptan (para no romper el protocolo de la app) pero no mueven
 *  nada.
 */

class Servos {

public:

    static const int CANTIDAD        = 5;   // servos que reporta la app
    static const int CANTIDAD_FISICA = 3;   // servos realmente cableados

    Servos();

    // Configura los 3 servos (llamar solo si MODULOS.servos está activo).
    // Si no se llama, moverServo() solo guarda el ángulo.
    void iniciar();

    // Mueve un servo de usuario por nombre (lo que manda "{"tipo":"servo"}").
    void moverServo(const char* nombre, int angulo);

    // Copia los ángulos actuales (últimos comandados) al arreglo destino.
    void angulosUsuario(int destino[CANTIDAD]) const;

private:

    // Orden del arreglo _servos[] y de SERVOS_ACTIVOS[].
    enum IndiceServo {
        IDX_CUELLO = 0,
        IDX_HOMBRO_IZQ,
        IDX_HOMBRO_DER,
        IDX_PULGAR_IZQ,
        IDX_PULGAR_DER,
    };

    int  indiceDe(const char* nombre) const;
    bool habilitado(int indice) const;
    void escribirServo(int indice, int angulo);

    Servo _servos[CANTIDAD_FISICA];
    bool  _listo;
    int   _angulos[CANTIDAD];
};

// Instancia única global (la usan comunicacion.cpp y main.cpp).
extern Servos servos;

#endif // SERVOS_H

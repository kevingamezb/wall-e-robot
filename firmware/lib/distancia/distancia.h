// wall-e-robot/firmware/lib/distancia/distancia.h
// Kevin Gámez - 13/09/2026

#ifndef DISTANCIA_H
#define DISTANCIA_H

#include <Arduino.h>

/*
 *  SensorDistancia: lectura del HC-SR04 en modo no bloqueante.
 *
 *  Avanza por una máquina de estados en cada llamada a actualizar(), sin
 *  esperar activa. distanciaCm() devuelve -1 cuando no hay eco (centinela de
 *  "sin lectura").
 */

class SensorDistancia {

public:

    // Fija los pines TRIG/ECHO; no los configura hasta iniciar().
    SensorDistancia(uint8_t pinTrig, uint8_t pinEcho);

    // Configura los pines y deja el sensor en reposo.
    void iniciar();

    // true si iniciar() ya configuró el sensor (usado por el self-test OTA).
    bool listo() const;

    // Avanza la máquina de estados; llamar con frecuencia (no bloqueante).
    void actualizar();

    // true una vez por medición completada; se limpia al iniciar el ciclo siguiente.
    bool hayLecturaNueva() const;

    // Última distancia en cm; -1 = sin eco.
    float distanciaCm() const;

    // true si hay lectura válida dentro del umbral.
    bool obstaculoCercano(float umbralCm) const;

private:

    enum Fase {
        FASE_ESPERANDO,
        FASE_PULSO_ENVIADO,     // TRIG arriba (10us)
        FASE_ESPERANDO_ECO,     // esperando borde ascendente del ECO
        FASE_MIDIENDO_ECO,      // esperando borde descendente del ECO
    };

    uint8_t _pinTrig;
    uint8_t _pinEcho;

    Fase   _fase;
    bool   _sensorListo;    // iniciar() ya corrió
    bool   _lecturaNueva;   // aviso de medición completada
    float  _distanciaCm;    // último valor

    uint32_t _microsInicio;     // marcas de tiempo por micros()
    uint32_t _microsEco;
    uint32_t _ultimaLecturaMs;  // fin del último ciclo (para el intervalo)
};

extern SensorDistancia sensorDistancia;

#endif // DISTANCIA_H

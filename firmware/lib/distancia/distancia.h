// wall-e-robot/firmware/lib/distancia/distancia.h
// Kevin Gámez - 13/09/2026

#ifndef DISTANCIA_H
#define DISTANCIA_H

#include <Arduino.h>

/*
 *  SensorDistancia: lectura del HC-SR04 sin bloqueos.
 */

class SensorDistancia {

public:

    SensorDistancia(uint8_t pinTrig, uint8_t pinEcho);

    // Configura los pines y deja el sensor en reposo.
    void iniciar();

    void actualizar();

    bool hayLecturaNueva() const;

    float distanciaCm() const;

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

#ifndef DISTANCIA_H
#define DISTANCIA_H

#include <Arduino.h>


class SensorDistancia {

public:

    // Fija los pines TRIG/ECHO; no los configura hasta iniciar().
    SensorDistancia(uint8_t pinTrig, uint8_t pinEcho);

    void iniciar();

    // true si iniciar() ya configuró el sensor (usado por el self-test OTA).
    bool listo() const;

    // Avanza la máquina de estados; llamar con frecuencia (no bloqueante).
    void actualizar();

    // true una vez por medición completada; se limpia al iniciar el ciclo siguiente.
    bool hayLecturaNueva() const;

    // Última distancia en cm; -1 = sin eco.
    float distanciaCm() const;

    bool obstaculoCercano(float umbralCm) const;

    // true si la última medición terminó hace maxMs o menos. Incluye las
    // mediciones sin eco: son frescas, pero distanciaCm() devuelve -1.
    bool lecturaFresca(uint32_t maxMs) const;

    uint32_t inicioUltimaLecturaMs() const { return _inicioUltimaLecturaMs; }

private:

    void finalizarLectura(float distanciaCm);

    enum Fase {
        FASE_ESPERANDO,
        FASE_PULSO_ENVIADO,     // TRIG arriba (10us)
        FASE_ESPERANDO_ECO,
        FASE_MIDIENDO_ECO,
    };

    uint8_t _pinTrig;
    uint8_t _pinEcho;

    Fase   _fase;
    bool   _sensorListo;
    bool   _lecturaNueva;
    bool   _algunaLectura;  // al menos un ciclo terminó
    float  _distanciaCm;

    uint32_t _microsInicio;
    uint32_t _microsEco;
    uint32_t _ultimaLecturaMs;
    uint32_t _inicioPulsoMs = 0;
    uint32_t _inicioUltimaLecturaMs = 0;
};

extern SensorDistancia sensorDistancia;

#endif

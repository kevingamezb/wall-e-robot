// wall-e-robot/firmware/lib/motores/motores.h
// Kevin Gámez - 13/09/2026

#ifndef MOTORES_H
#define MOTORES_H

#include <Arduino.h>
#include <ESP32Servo.h> // se usa PWM para controlar la velocidad de los motores

/*
 *  Motores: 2 motores CC por driver TB6612FNG.
 */

class Motores {

public:

    Motores(uint8_t ain1, uint8_t ain2, uint8_t bin1, uint8_t bin2,
            uint8_t pwma, uint8_t pwmb, uint8_t stby);

    void iniciar();

    // Aplica una dirección.
    void mover(const String& direccion);

    void detener();

    // Acerca las velocidades reales a sus metas.
    void actualizar();

private:

    void _rueda(uint8_t inA, uint8_t inB, ESP32PWM& pwm, int velocidad);

    uint8_t _ain1, _ain2, _bin1, _bin2, _pwma, _pwmb, _stby;
    ESP32PWM _pwmA, _pwmB;
    bool    _activo;

    // Metas (lo que pide mover()) vs. reales (lo que evoluciona por la rampa).
    int       _metaA, _metaB;
    int       _velA,  _velB;
    uint32_t  _ultimaRampaMs;
};

extern Motores motores;

#endif // MOTORES_H

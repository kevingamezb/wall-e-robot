// wall-e-robot/firmware/lib/motores/motores.h
// Kevin Gámez - 13/09/2026

#ifndef MOTORES_H
#define MOTORES_H

#include <Arduino.h>
#include <ESP32Servo.h> // se usa PWM para controlar la velocidad de los motores

/*
 *  Motores: dos motores CC sobre el driver TB6612FNG (d-pad).
 *
 *  mover() fija una meta de velocidad por rueda; actualizar() la alcanza de
 *  forma gradual (rampa anti-tirón). La velocidad se expresa en PWM 0-255 con
 *  signo, donde el signo define el sentido de giro.
 */

class Motores {

public:

    // Recibe los pines del driver; no configura hardware hasta iniciar().
    Motores(uint8_t ain1, uint8_t ain2, uint8_t bin1, uint8_t bin2,
            uint8_t pwma, uint8_t pwmb, uint8_t stby);

    // Configura pines, habilita STBY y deja las ruedas detenidas.
    void iniciar();

    // Fija la meta de velocidad según la dirección (d-pad).
    void mover(const String& direccion);

    // Detiene por rampa: pone las metas a cero.
    void detener();

    // Acerca las velocidades reales a sus metas (un paso de rampa).
    void actualizar();

private:

    // Escribe el sentido en IN1/IN2 y el duty PWM de una rueda.
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

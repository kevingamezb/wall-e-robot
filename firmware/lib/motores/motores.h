#ifndef MOTORES_H
#define MOTORES_H

#include <Arduino.h>
#include <ESP32Servo.h>


class Motores {

public:

    // Recibe los pines del driver; no configura hardware hasta iniciar().
    Motores(uint8_t ain1, uint8_t ain2, uint8_t bin1, uint8_t bin2,
            uint8_t pwma, uint8_t pwmb, uint8_t stby);

    void iniciar();

    // Fija la meta de cada rueda. El PWM con signo indica velocidad y sentido.
    void mover(const String& direccion);

    // Solicita una parada gradual mediante la rampa.
    void detener();

    bool detenidos() const { return _velA == 0 && _velB == 0; }

    void actualizar();

private:

    void _rueda(uint8_t inA, uint8_t inB, ESP32PWM& pwm, int velocidad);

    uint8_t _ain1, _ain2, _bin1, _bin2, _pwma, _pwmb, _stby;
    ESP32PWM _pwmA, _pwmB;
    bool    _activo;

    int       _metaA, _metaB;
    int       _velA,  _velB;
    uint32_t  _ultimaRampaMs;
};

extern Motores motores;

#endif

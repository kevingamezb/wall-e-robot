// wall-e-robot/firmware/lib/motores/motores.h
// Kevin Gámez - 13/09/2026

#ifndef MOTORES_H
#define MOTORES_H

#include <Arduino.h>
#include <ESP32Servo.h>   // reutilizamos ESP32PWM para el PWM de los motores

/*
 *  Motores: 2 motores CC por driver TB6612FNG.
 *
 *  Traduce el comando de dirección de la app ({"tipo":"motor","direccion":...})
 *  a velocidades diferenciales de las ruedas:
 *      arriba      -> ambas adelante
 *      abajo       -> ambas atrás
 *      izquierda   -> giro a la izquierda (ruedas contrapuestas)
 *      derecha     -> giro a la derecha  (ruedas contrapuestas)
 *
 *  El PWM va por ESP32PWM (LEDC) y no por analogWrite(): analogWrite comparte
 *  timers con ESP32Servo y deja un servo sin responder.
 *
 *  TODO(hardware): confirmar qué rueda es A y cuál B contra el robot. Si el
 *  robot avanza al revés, se canjean las ruedas en _rueda().
 */

class Motores {

public:

    // Pines del TB6612FNG (ver pines.h).
    Motores(uint8_t ain1, uint8_t ain2, uint8_t bin1, uint8_t bin2,
            uint8_t pwma, uint8_t pwmb, uint8_t stby);

    // Configura los pines, habilita el driver (STBY) y deja velocidad 0.
    void iniciar();

    // Aplica una dirección ("arriba","abajo","izquierda","derecha").
    void mover(const String& direccion);

    void detener();

    // Acerca las velocidades reales a sus metas. Llamar seguido en loop()
    // para evitar el tirón 0->máx.
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

// Instancia única global (comunicacion.cpp y main.cpp).
extern Motores motores;

#endif // MOTORES_H

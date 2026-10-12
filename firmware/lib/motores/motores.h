// wall-e-robot/firmware/lib/motores/motores.h
// Kevin Gámez - 13/09/2026

#ifndef MOTORES_H
#define MOTORES_H

#include <Arduino.h>
#include <ESP32Servo.h>   // reutilizamos ESP32PWM para el PWM de los motores

/*
 *  Motores: control de 2 motores CC por driver TB6612FNG.
 *
 *  Traduce el comando de dirección de la app
 *  ({"tipo":"motor","direccion":"arriba"}) a velocidades
 *  diferenciales de las ruedas:
 *      arriba      -> ambas adelante
 *      abajo       -> ambas atrás
 *      izquierda   -> giro a la izquierda (diferencial)
 *      derecha     -> giro a la derecha (diferencial)
 *
 *  "izquierda" y "derecha" son GIROS EN EL SITIO. Los nombres de los
 *  canales del TB6612FNG (AIN1/AIN2, BIN1/BIN2, PWMA/PWMB) y cuál rueda
 *  es A o B hay que verificarlos contra el robot real. Si el robot va al
 *  revés, se canjea A/B en _rueda().
 *
 *  El PWM va por ESP32PWM (LEDC) y NO por analogWrite(): analogWrite choca
 *  con los timers de ESP32Servo y un servo deja de responder.
 */

class Motores {

public:

    // Pines del TB6612FNG (ver pines.h).
    Motores(uint8_t ain1, uint8_t ain2, uint8_t bin1, uint8_t bin2,
            uint8_t pwma, uint8_t pwmb, uint8_t stby);

    // Configura los pines, habilita el driver (STBY) y fija velocidad 0.
    void iniciar();

    // Aplica una dirección ("arriba","abajo","izquierda","derecha").
    // Si el módulo no está activo, no hace nada.
    void mover(const String& direccion);

    void detener();

    // Ramps de las velocidades hacia sus metas (llamar seguido en loop()).
    // Evita el tirón 0->máx: los motores aceleran/desaceleran de a poco.
    void actualizar();

private:

    void _rueda(uint8_t inA, uint8_t inB, ESP32PWM& pwm, int velocidad);

    uint8_t _ain1, _ain2, _bin1, _bin2, _pwma, _pwmb, _stby;
    ESP32PWM _pwmA, _pwmB;
    bool    _activo;

    // Velocidades META (lo que pide mover()) vs REALES (lo que se escribe
    // al PWM, que evoluciona de a poco por la rampa).
    int       _metaA, _metaB;
    int       _velA,  _velB;
    uint32_t  _ultimaRampaMs;
};

// Instancia única global (comunicacion.cpp y main.cpp).
extern Motores motores;

#endif // MOTORES_H

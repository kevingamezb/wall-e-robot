// wall-e-robot/firmware/lib/motores/motores.h
// Kevin Gámez - 13/09/2026

#ifndef MOTORES_H
#define MOTORES_H

#include <Arduino.h>

/*
 *  Motores: control de 2 motores CC por driver L298N.
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
 *  canales L298N (IN1..IN4, ENA/ENB) y cuál rueda es A o B hay que
 *  verificarlos contra el robot real (a veces IN1/IN2 son la rueda
 *  derecha). Si el robot va al revés, se canjea A/B en _ruedas().
 */

class Motores {

public:

    // Los 6 pines del L298N (ver pines.h).
    Motores(uint8_t in1, uint8_t in2, uint8_t in3, uint8_t in4,
            uint8_t enA, uint8_t enB);

    // Configura los pines como salida y fija velocidad 0; marca el módulo activo.
    void iniciar();

    // Aplica una dirección ("arriba","abajo","izquierda","derecha").
    // Si el módulo no está activo, no hace nada.
    void mover(const String& direccion);

    void detener();

    // Ramps de las velocidades hacia sus metas (llamar seguido en loop()).
    // Evita el tirón 0->200: los motores aceleran/desaceleran de a poco.
    void actualizar();

private:

    void _rueda(uint8_t inA, uint8_t inB, uint8_t en, int velocidad);

    uint8_t _in1, _in2, _in3, _in4, _enA, _enB;
    bool    _activo;

    // Velocidades META (lo que pide mover()) vs REALES (lo que se escribe
    // a los pines, que evoluciona de a poco por la rampa).
    int       _metaA, _metaB;
    int       _velA,  _velB;
    uint32_t  _ultimaRampaMs;
};

// Instancia única global (comunicacion.cpp y main.cpp).
extern Motores motores;

#endif // MOTORES_H
// wall-e-robot/firmware/lib/bateria/bateria.h
// Kevin Gámez - 13/09/2026

#ifndef BATERIA_H
#define BATERIA_H

#include <Arduino.h>
#include <Adafruit_INA219.h>

/*
 *  Bateria: lectura del nivel de carga por el INA219.
 *
 *  El INA219 mide voltaje y corriente en el bus de alimentación.
 *  Con eso calculamos:
 *      - nivel: 0.0..1.0 (mapeado entre BATERIA_VOLTAJE_MIN/MAX de config)
 *      - corriente (A) y consumo (W) -> para "consumo_watts" del estado
 *      - cargando y minutos restantes (estimación heurística, ver abajo)
 *
 *  Reglas de pruebas aisladas (coherente con el resto):
 *   - Si MODULOS.bateria == 0, no se toca el I2C y los captadores
 *     devuelven valores NEUTROS (nivel 1.0, 0 A, 0 W), para que la
 *     GUI no muestre alertas falsas por el sensor sin conectar.
 */
class Bateria {

public:

    Bateria();

    void iniciar();

    // Lee el sensor y guarda el último voltaje/corriente.
    // Llamar con la frecuencia LECTURA_BATERIA_MS desde main.cpp.
    void actualizarLectura();

    float nivel() const;        // 0.0..1.0 (o 1.0 si el módulo está apagado)
    float corrienteA() const;   // corriente del bus (A)
    float consumoWatts() const; // V * A
    bool  cargando() const;     // heurística por sentido de la corriente

    // Minutos restantes estimados con la carga disponible y el consumo
    // actual. -1 si no se puede estimar (sin consumo o módulo apagado).
    float minutosRestantes() const;

private:

    Adafruit_INA219 _sensor;
    bool   _activo;
    float  _voltaje;
    float  _corriente;
};

// Instancia única global.
extern Bateria bateria;

#endif // BATERIA_H
// wall-e-robot/firmware/lib/bateria/bateria.h
// Kevin Gámez - 13/09/2026

#ifndef BATERIA_H
#define BATERIA_H

#include <Arduino.h>
#include <Adafruit_INA219.h>

/*
 *  Bateria: nivel de carga leído por el INA219.
 */
class Bateria {

public:

    Bateria();

    void iniciar();

    // Lee el sensor y guarda voltaje/corriente. Llamar cada LECTURA_BATERIA_MS.
    void actualizarLectura();

    float nivel() const;        // 0.0-1.0 (1.0 si el módulo está apagado)
    float corrienteA() const;   // corriente del bus (A)
    float consumoWatts() const; // V * A
    bool  cargando() const;     // heurística por el sentido de la corriente

    // Minutos restantes con la carga disponible y el consumo actual.
    // -1 si no se puede estimar (sin consumo o módulo apagado).
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

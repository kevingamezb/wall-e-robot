// wall-e-robot/firmware/lib/bateria/bateria.h
// Kevin Gámez - 13/09/2026

#ifndef BATERIA_H
#define BATERIA_H

#include <Arduino.h>
#include <Adafruit_INA219.h>

/*
 *  Bateria: telemetría de energía sobre el INA219 (bus I2C).
 *
 *  Abstrae el sensor de voltaje/corriente y deriva nivel de carga, consumo y
 *  autonomía. Si el INA219 no responde, queda inactiva y devuelve valores
 *  neutros para no generar falsas alertas.
 */
class Bateria {

public:

    Bateria();

    // Inicializa el INA219; si falla, la clase queda inactiva.
    void iniciar();

    // true si el INA219 se inicializó bien (usado por el self-test OTA).
    bool activo() const;

    // Lee voltaje y corriente del sensor; llamar cada LECTURA_BATERIA_MS.
    void actualizarLectura();

    // Nivel de carga normalizado; 1.0 si el módulo está apagado.
    float nivel() const;        // 0.0-1.0
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

#ifndef BATERIA_H
#define BATERIA_H

#include <Arduino.h>
#include <Adafruit_INA219.h>

class Bateria {

public:

    Bateria();

    void iniciar();

    // true si el INA219 se inicializó bien (usado por el self-test OTA).
    bool activo() const;

    void actualizarLectura();

    float nivel() const;        // 0.0-1.0, o -1 si no hay lectura válida
    float corrienteA() const;
    float consumoWatts() const;
    bool  cargando() const;     // heurística por el sentido de la corriente

    // -1 si no se puede estimar (sin consumo o módulo apagado).
    float minutosRestantes() const;

private:

    Adafruit_INA219 _sensor;
    bool     _activo;
    float    _voltajeBus;      // VIN- (lado carga): para consumoWatts()
    float    _voltajeBateria;  // VIN+ (lado batería): para nivel()/autonomía
    float    _corriente;
    float    _nivel;           // nivel cacheado, se actualiza solo en reposo
    bool     _nivelInicializado;
    uint32_t _reposoDesdeMs;
};

extern Bateria bateria;

#endif

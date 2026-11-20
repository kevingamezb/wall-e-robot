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
 *
 *  El INA219 mide el bus en VIN- (lado carga); sumando la caída leída en el
 *  shunt se obtiene la tensión en VIN+ (lado batería). El nivel se calcula con
 *  esa tensión solo cuando la corriente es casi nula, para no confundir la
 *  caída I*R del cableado/batería con una descarga real.
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
    float nivel() const;        // 0.0-1.0, o -1 si no hay lectura válida
    float corrienteA() const;   // corriente del bus (A)
    float consumoWatts() const; // V * A
    bool  cargando() const;     // heurística por el sentido de la corriente

    // Minutos restantes con la carga disponible y el consumo actual.
    // -1 si no se puede estimar (sin consumo o módulo apagado).
    float minutosRestantes() const;

private:

    Adafruit_INA219 _sensor;
    bool     _activo;
    float    _voltajeBus;      // VIN- (lado carga): para consumoWatts()
    float    _voltajeBateria;  // VIN+ (lado batería): para nivel()/autonomía
    float    _corriente;       // corriente filtrada (A)
    float    _nivel;           // nivel cacheado, se actualiza solo en reposo
    bool     _nivelInicializado;
    uint32_t _reposoDesdeMs;
};

// Instancia única global.
extern Bateria bateria;

#endif // BATERIA_H

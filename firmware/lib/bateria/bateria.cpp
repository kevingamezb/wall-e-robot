// wall-e-robot/firmware/lib/bateria/bateria.cpp
// Kevin Gámez - 13/09/2026

#include "bateria.h"
#include "config.h"


Bateria bateria;


Bateria::Bateria()
    : _sensor()
    , _activo(false)
    , _voltaje(0.0f)
    , _corriente(0.0f) {}


void Bateria::iniciar() {

    if (!_sensor.begin()) {
        Serial.println("BATERIA: no se encontró el INA219 en el bus I2C.");
        return;   // _activo sigue en false: los captadores dan neutro
    }

    _activo = true;
    Serial.println("BATERIA: INA219 listo.");
}


void Bateria::actualizarLectura() {

    // Si el sensor no está activo no se toca el I2C.
    if (!_activo) {
        return;
    }

    _voltaje = _sensor.getBusVoltage_V();
    _corriente = _sensor.getCurrent_mA() / 1000.0f;   // mA -> A
}


float Bateria::nivel() const {

    if (!_activo) {
        return 1.0f;   // neutro: no hay alerta en la GUI sin el sensor
    }

    float nivel = (_voltaje - BATERIA_VOLTAJE_MIN)
                / (BATERIA_VOLTAJE_MAX - BATERIA_VOLTAJE_MIN);

    return constrain(nivel, 0.0f, 1.0f);
}


float Bateria::corrienteA() const {
    return _activo ? _corriente : 0.0f;
}


float Bateria::consumoWatts() const {
    return _activo ? _voltaje * _corriente : 0.0f;
}


bool Bateria::cargando() const {
    // Heurística: con el cargador conectado la corriente del bus
    // "entra" a la batería (signo opuesto/negativo según el cableado).
    return _activo && _corriente < -0.1f;
}


float Bateria::minutosRestantes() const {

    if (!_activo) {
        return -1.0f;
    }

    float watts = consumoWatts();
    if (watts <= 0.0f) {
        return -1.0f;   // sin consumo no se puede estimar
    }

    // Energía restante ~ capacidad_mAh * nivel * voltaje (Wh).
    // El INA219 de medición se actualiza en main.cpp con la frecuencia
    // LECTURA_BATERIA_MS; aquí solo se estima con el último valor.
    float energiaWh = (BATERIA_CAPACIDAD_MAH / 1000.0f) * nivel() * _voltaje;

    return energiaWh / watts * 60.0f;
}
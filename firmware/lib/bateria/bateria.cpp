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
        return;   // _activo queda en false
    }

    _activo = true;
    Serial.println("BATERIA: INA219 listo.");
}


bool Bateria::activo() const {
    return _activo;
}


void Bateria::actualizarLectura() {

    if (!_activo) {
        return;   // sensor inactivo: no tocar el I2C
    }

    _voltaje = _sensor.getBusVoltage_V();
    _corriente = _sensor.getCurrent_mA() / 1000.0f;
}


float Bateria::nivel() const {

    if (!_activo) {
        return 1.0f;   // neutro: sin sensor no debe haber alerta
    }

    // Interpolación lineal entre los voltajes mínimo y máximo de la batería.
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
    // Con el cargador, la corriente "entra" a la batería (signo negativo según
    // el cableado del INA219).
    return _activo && _corriente < -0.1f;
}


float Bateria::minutosRestantes() const {

    if (!_activo) {
        return -1.0f;
    }

    float watts = consumoWatts();
    if (watts <= 0.0f) {
        return -1.0f;   // sin consumo no hay nada que estimar
    }

    // Energía restante ~ capacidad_mAh * nivel * voltaje (Wh).
    float energiaWh = (BATERIA_CAPACIDAD_MAH / 1000.0f) * nivel() * _voltaje;

    return energiaWh / watts * 60.0f;
}

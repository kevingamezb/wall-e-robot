// wall-e-robot/firmware/lib/bateria/bateria.cpp
// Kevin Gámez - 13/09/2026

#include "bateria.h"
#include "config.h"

#include <math.h>   // fabsf()


Bateria bateria;


Bateria::Bateria()
    : _sensor()
    , _activo(false)
    , _voltajeBus(0.0f)
    , _voltajeBateria(0.0f)
    , _corriente(0.0f)
    , _nivel(-1.0f)
    , _nivelInicializado(false)
    , _reposoDesdeMs(0) {}


void Bateria::iniciar() {

    if (!_sensor.begin()) {
        Serial.println("BATERIA: no se encontró el INA219 en el bus I2C.");
        return;   // _activo queda en false
    }

    _activo = true;

    // Sembrar el filtro con la primera lectura real: si arrancara en 0, el
    // primer cálculo del nivel saldría falsamente crítico.
    _voltajeBus = _sensor.getBusVoltage_V();
    _voltajeBateria = _voltajeBus + _sensor.getShuntVoltage_mV() / 1000.0f;
    _corriente = _sensor.getCurrent_mA() / 1000.0f;

    Serial.println("BATERIA: INA219 listo.");
}


bool Bateria::activo() const {
    return _activo;
}


void Bateria::actualizarLectura() {

    if (!_activo) {
        return;   // sensor inactivo: no tocar el I2C
    }

    const float bus = _sensor.getBusVoltage_V();
    // getBusVoltage_V() mide VIN- (lado carga). Sumar la caída medida en el
    // shunt (VIN+ - VIN-) recupera la tensión en VIN+ (lado batería), sin
    // depender del valor del shunt ni estimar resistencias del cableado.
    const float bateria = bus + _sensor.getShuntVoltage_mV() / 1000.0f;
    const float corriente = _sensor.getCurrent_mA() / 1000.0f;

    // Filtro EMA: el PWM de 1 kHz de los motores ensucia ambas lecturas. Con
    // LECTURA_BATERIA_MS = 250 este alpha da una respuesta de ~0,5 s.
    _voltajeBus     += BATERIA_FILTRO_ALPHA * (bus - _voltajeBus);
    _voltajeBateria += BATERIA_FILTRO_ALPHA * (bateria - _voltajeBateria);
    _corriente      += BATERIA_FILTRO_ALPHA * (corriente - _corriente);

    // Después de la primera estimación esperamos al reposo. Con los motores en
    // marcha, la caída I*R de batería y cableado hace que la tensión baje y
    // vuelva a subir al parar: eso no es descarga, es sag de tensión.
    const uint32_t ahora = millis();
    if (fabsf(_corriente) < BATERIA_CORRIENTE_REPOSO_A) {
        if (_reposoDesdeMs == 0) {
            _reposoDesdeMs = ahora;
        }
    } else {
        _reposoDesdeMs = 0;
    }
    const bool reposoEstable = _reposoDesdeMs != 0 &&
                              ahora - _reposoDesdeMs >= BATERIA_REPOSO_ESTABLE_MS;
    if ((!_nivelInicializado || reposoEstable) &&
        isfinite(bateria) && bateria > 0.0f && isfinite(_voltajeBateria)) {
        _nivel = constrain(
            (_voltajeBateria - BATERIA_VOLTAJE_MIN) /
            (BATERIA_VOLTAJE_MAX - BATERIA_VOLTAJE_MIN), 0.0f, 1.0f);
        _nivelInicializado = true;
    }
}


float Bateria::nivel() const {

    if (!_activo) {
        return -1.0f;   // sin lectura
    }

    return _nivel;
}


float Bateria::corrienteA() const {
    return _activo ? _corriente : 0.0f;
}


float Bateria::consumoWatts() const {
    // Potencia entregada a la carga: se usa la tensión en VIN- (lado carga).
    return _activo ? _voltajeBus * _corriente : 0.0f;
}


bool Bateria::cargando() const {
    // Con el cargador, la corriente "entra" a la batería (signo negativo según
    // el cableado del INA219). El filtro evita falsos avisos al recargarse el
    // condensador después de parar los motores.
    return _activo && _corriente < -0.1f;
}


float Bateria::minutosRestantes() const {

    if (!_nivelInicializado) {
        return -1.0f;
    }

    float watts = consumoWatts();
    if (watts <= 0.0f) {
        return -1.0f;   // sin consumo no hay nada que estimar
    }

    // Energía restante ~ capacidad_mAh * nivel * voltaje (Wh).
    float energiaWh = (BATERIA_CAPACIDAD_MAH / 1000.0f) * nivel() * _voltajeBateria;

    return energiaWh / watts * 60.0f;
}

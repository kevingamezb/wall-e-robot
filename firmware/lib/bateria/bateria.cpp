#include "bateria.h"
#include "config.h"

#include <math.h>


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
        return;
    }

    _activo = true;

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
        return;
    }

    const float bus = _sensor.getBusVoltage_V();
    // El INA219 mide VIN-; suma la caída del shunt para obtener VIN+ (lado batería).
    const float bateria = bus + _sensor.getShuntVoltage_mV() / 1000.0f;
    const float corriente = _sensor.getCurrent_mA() / 1000.0f;

    // El filtro EMA atenúa el ruido del PWM de los motores.
    _voltajeBus     += BATERIA_FILTRO_ALPHA * (bus - _voltajeBus);
    _voltajeBateria += BATERIA_FILTRO_ALPHA * (bateria - _voltajeBateria);
    _corriente      += BATERIA_FILTRO_ALPHA * (corriente - _corriente);

    // Conserva el nivel previo bajo carga, cuando la caída de tensión sesga la estimación.
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
        return -1.0f;
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
    // La corriente negativa indica carga. El filtro atenúa el transitorio del condensador.
    return _activo && _corriente < -0.1f;
}


float Bateria::minutosRestantes() const {

    if (!_nivelInicializado) {
        return -1.0f;
    }

    float watts = consumoWatts();
    if (watts <= 0.0f) {
        return -1.0f;
    }

    // Energía restante ~ capacidad_mAh * nivel * voltaje (Wh).
    float energiaWh = (BATERIA_CAPACIDAD_MAH / 1000.0f) * nivel() * _voltajeBateria;

    return energiaWh / watts * 60.0f;
}

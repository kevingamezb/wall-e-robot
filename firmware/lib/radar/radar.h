// wall-e-robot/firmware/lib/radar/radar.h
// Kevin Gámez - 13/09/2026

#ifndef RADAR_H
#define RADAR_H

#include <Arduino.h>

/*
 *  Radar: lectura del HC-SR04 SIN bloqueos.
 *
 *  medir() con pulseIn() (lo clásico) congela el loop() hasta que
 *  vuelve el eco y desincroniza la telemetría -> nada de eso aquí.
 *
 *  El sensor se maneja con una pequeña máquina de estados por micros():
 *      ESPERANDO      -> subir TRIG 10us -> PULSO_ENVIADO
 *      PULSO_ENVIADO  -> bajar TRIG, esperar ECO (con timeout) -> ESPERANDO
 *                       -> (si sube) MEDIDO
 *      MEDIDO         -> esperar que baje ECO, calcular cm -> ESPERANDO
 *
 *  El propio barrido del servo (ángulo -45..45 yendo y volviendo) vive
 *  aquí en BarridoRadar(), que llama a servos.moverRadar(). Así main.cpp
 *  solo tiene que llamar hasta_actualizar() en cada vuelta del loop().
 *
 *  Reglas de la versión de pruebas aisladas:
 *   - Nada se inicializa si MODULOS.radar == 0.
 *   - distanciaCm() devuelve -1 (sin lectura) si no hay placa/sensor.
 */

class Radar {

public:

    Radar(uint8_t pinTrig, uint8_t pinEcho);

    // Configura pines y deja el sensor "idle" (sin disparar).
    void iniciar();

    // Avanza la máquina de estados. Llamar en cada pass del loop().
    // No llama a delay() ni bloquea.
    void actualizar();

    // True si durante actualizar() se completó una medición nueva.
    bool hayLecturaNueva() const;

    // Última distancia medida en cm (constante entre lecturas).
    float distanciaCm() const;

    // True si la última medición dio obstáculo en el umbral definido.
    // Con UMBRAL en config.h; usado por hay_advertencia del estado.
    bool obstaculoCercano(float umbralCm) const;

private:

    enum Fase {
        FASE_ESPERANDO,
        FASE_PULSO_ENVIADO,     // TRIG arriba (10us)
        FASE_ESPERANDO_ECO,     // esperando borde ascendente del ECO
        FASE_MIDIENDO_ECO,      // esperando borde descendente del ECO
    };

    // mide distancia desde el ciclo que empezó en FASE_PULSO_ENVIADO.
    void _medir();

    uint8_t _pinTrig;
    uint8_t _pinEcho;

    Fase   _fase;
    bool   _placaLista;     // sensor iniciado (lo prende main si hay módulo)
    bool   _lecturaNueva;   // aviso de lectura completada
    float  _distanciaCm;    // último valor

    uint32_t _microsInicio;  // marcas de tiempo por micros()
    uint32_t _microsEco;
    uint32_t _ultimaLecturaMs;  // último ciclo de medición completo (para el intervalo)
};


// Barrido autónomo del servo del radar sobre CANAL_RADAR.
class BarridoRadar {

public:

    BarridoRadar();
    void actualizar();
    bool estaActivo() const;

private:
    int      _angulo;
    int      _paso;           // +3 / -3 grados por avance
    uint32_t _ultimoPasoMs;
    bool     _activo;         // false si el radar está deshabilitado
};

// Instancias únicas globales (main.cpp).
extern Radar radar;
extern BarridoRadar barridoRadar;

#endif // RADAR_H
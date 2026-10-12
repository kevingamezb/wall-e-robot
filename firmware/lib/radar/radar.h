// wall-e-robot/firmware/lib/radar/radar.h
// Kevin Gámez - 13/09/2026

#ifndef RADAR_H
#define RADAR_H

#include <Arduino.h>

/*
 *  Radar: lectura del HC-SR04 sin bloqueos.
 *
 *  medir() con pulseIn() congela el loop() hasta que vuelve el eco y
 *  desincroniza la telemetría; por eso aquí se usa una máquina de estados
 *  por micros():
 *      ESPERANDO      -> subir TRIG 10us -> PULSO_ENVIADO
 *      PULSO_ENVIADO  -> bajar TRIG, esperar ECO (con timeout) -> MEDIDO
 *      MEDIDO         -> esperar que baje ECO, calcular cm -> ESPERANDO
 *
 *  El sensor va fijo mirando al frente: no hay servo de barrido. main.cpp solo
 *  tiene que llamar actualizar() en cada vuelta.
 *
 *  Con MODULOS.radar == 0 nada se inicializa y distanciaCm() devuelve -1.
 */

class Radar {

public:

    Radar(uint8_t pinTrig, uint8_t pinEcho);

    // Configura los pines y deja el sensor en reposo (sin disparar).
    void iniciar();

    // Avanza la máquina de estados. Llamar en cada vuelta del loop(); no bloquea.
    void actualizar();

    // True si la última pasada completó una medición nueva.
    bool hayLecturaNueva() const;

    // Última distancia medida en cm (constante entre lecturas).
    float distanciaCm() const;

    // True si la última medición entró en el umbral de obstáculo (config.h).
    bool obstaculoCercano(float umbralCm) const;

private:

    enum Fase {
        FASE_ESPERANDO,
        FASE_PULSO_ENVIADO,     // TRIG arriba (10us)
        FASE_ESPERANDO_ECO,     // esperando borde ascendente del ECO
        FASE_MIDIENDO_ECO,      // esperando borde descendente del ECO
    };

    uint8_t _pinTrig;
    uint8_t _pinEcho;

    Fase   _fase;
    bool   _sensorListo;    // iniciar() ya corrió
    bool   _lecturaNueva;   // aviso de medición completada
    float  _distanciaCm;    // último valor

    uint32_t _microsInicio;     // marcas de tiempo por micros()
    uint32_t _microsEco;
    uint32_t _ultimaLecturaMs;  // fin del último ciclo (para el intervalo)
};

// Instancia única global (main.cpp).
extern Radar radar;

#endif // RADAR_H

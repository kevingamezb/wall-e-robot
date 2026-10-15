// wall-e-robot/firmware/lib/oled/oled.h
// Kevin Gámez - 13/09/2026

#ifndef OLED_H
#define OLED_H

#include <Arduino.h>
#include <Adafruit_SSD1306.h>

/*
 *  Pantalla OLED 0.96'' (128x64, I2C).
 */
class PantallaOled {

public:

    PantallaOled();

    void iniciar();

    // Dibuja el resumen de telemetría.
    void mostrar(float bateria, float distanciaCm, const String& modo,
                 bool conexionActiva);

private:

    Adafruit_SSD1306 _pantalla;
    bool             _activo;
};

extern PantallaOled oled;

#endif // OLED_H

#ifndef OLED_H
#define OLED_H

#include <Arduino.h>
#include <Adafruit_SSD1306.h>

/*
 *  PantallaOled: OLED SSD1306 0.96" (128x64, bus I2C).
 *
 */
class PantallaOled {

public:

    PantallaOled();

    void iniciar();

    void mostrar(float bateria, float distanciaCm, const String& modo,
                 bool conexionActiva, bool mostrarOjos, bool ojosCerrados);

    // true si la SSD1306 se inicializó bien (usado por el self-test OTA).
    bool activo() const;

private:

    Adafruit_SSD1306 _pantalla;
    bool             _activo;
};

extern PantallaOled oled;

#endif

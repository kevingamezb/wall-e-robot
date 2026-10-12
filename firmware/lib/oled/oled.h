// wall-e-robot/firmware/lib/oled/oled.h
// Kevin Gámez - 13/09/2026

#ifndef OLED_H
#define OLED_H

#include <Arduino.h>
#include <Adafruit_SSD1306.h>

/*
 *  Pantalla OLED 0.96'' (128x64, I2C).
 *
 *  Muestra un resumen de telemetría (batería, distancia, modo y conexión).
 *  Con MODULOS.oled == 0 no se inicializa ni se escribe, para no ocupar el
 *  bus I2C mientras se prueban otros módulos; main.cpp solo llama a mostrar()
 *  si el flag está activo.
 */
class PantallaOled {

public:

    PantallaOled();

    void iniciar();

    // Dibuja el resumen de telemetría (no hace nada si el módulo está apagado).
    void mostrar(float bateria, float distanciaCm, const String& modo,
                 bool conexionActiva);

private:

    Adafruit_SSD1306 _pantalla;
    bool             _activo;
};

// Instancia única global.
extern PantallaOled oled;

#endif // OLED_H

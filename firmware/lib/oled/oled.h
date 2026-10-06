// wall-e-robot/firmware/lib/oled/oled.h
// Kevin Gámez - 13/09/2026

#ifndef OLED_H
#define OLED_H

#include <Arduino.h>
#include <Adafruit_SSD1306.h>

/*
 *  Pantalla OLED 0.96'' (128x64, I2C).
 *
 *  En la PRIMERA ENTREGA se deja apagada (MODULOS.oled == 0):
 *  el código compila y está listo, pero iniciar() no se llama y
 *  mostrar() no escribe nada, para no ocupar el bus I2C mientras
 *  se prueban los demás módulos.
 *
 *  Cuando el flag pase a 1, main.cpp llama a mostrar() después de
 *  cada actualización de telemetría y la pantalla refleja nivel de
 *  batería, distancia y modo sin tocar nada más del código.
 */
class PantallaOled {

public:

    PantallaOled();

    void iniciar();

    // Dibuja un resumen de telemetría (solo si el módulo está activo).
    void mostrar(float bateria, float distanciaCm, const String& modo,
                 bool conexionActiva);

private:

    Adafruit_SSD1306 _pantalla;
    bool             _activo;
};

// Instancia única global.
extern PantallaOled oled;

#endif // OLED_H
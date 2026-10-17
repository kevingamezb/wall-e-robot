// wall-e-robot/firmware/lib/oled/oled.h
// Kevin Gámez - 13/09/2026

#ifndef OLED_H
#define OLED_H

#include <Arduino.h>
#include <Adafruit_SSD1306.h>

/*
 *  PantallaOled: OLED SSD1306 0.96" (128x64, bus I2C).
 *
 *  Muestra un resumen de telemetría. Si la pantalla no responde, queda
 *  inactiva y mostrar() no dibuja nada.
 */
class PantallaOled {

public:

    // Configura tamaño 128x64 y el bus I2C compartido; sin pin de reset.
    PantallaOled();

    // Inicializa la SSD1306; si falla, la clase queda inactiva.
    void iniciar();

    // Dibuja batería, distancia, modo y estado de conexión.
    void mostrar(float bateria, float distanciaCm, const String& modo,
                 bool conexionActiva);

    // true si la SSD1306 se inicializó bien (usado por el self-test OTA).
    bool activo() const;

private:

    Adafruit_SSD1306 _pantalla;
    bool             _activo;
};

extern PantallaOled oled;

#endif // OLED_H

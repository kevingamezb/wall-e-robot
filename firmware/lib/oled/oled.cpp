// wall-e-robot/firmware/lib/oled/oled.cpp
// Kevin Gámez - 13/09/2026

#include "oled.h"

static const uint8_t OLED_ANCHO   = 128;
static const uint8_t OLED_ALTO    = 64;
static const uint8_t OLED_I2C_DIR = 0x3C;


PantallaOled oled;


// reset=-1: el módulo no tiene pin de reset;
PantallaOled::PantallaOled()
    : _pantalla(OLED_ANCHO, OLED_ALTO, &Wire, -1)
    , _activo(false) {}


void PantallaOled::iniciar() {

    if (!_pantalla.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_DIR)) {
        Serial.println("OLED: no se encontró la SSD1306 en 0x3C.");
        return;
    }

    _pantalla.clearDisplay();
    _pantalla.setTextSize(1);
    _pantalla.setTextColor(SSD1306_WHITE);
    _pantalla.setCursor(0, 0);
    _pantalla.print("WALL-E ROBOT");
    _pantalla.display();
    _pantalla.setRotation(2); // El hardware del robot tiene la pantalla al revés, así que la giramos 180º.

    _activo = true;
    Serial.println("OLED: pantalla lista.");
}


void PantallaOled::mostrar(float bateria, float distanciaCm,
                           const String& modo, bool conexionActiva) {

    if (!_activo) {
        return;   // módulo apagado
    }

    _pantalla.clearDisplay();

    _pantalla.setCursor(0, 0);
    _pantalla.print("BAT "); _pantalla.print(bateria * 100, 0); _pantalla.println("%");

    _pantalla.setCursor(0, 10);
    _pantalla.print("DIS "); _pantalla.print(distanciaCm, 1); _pantalla.println("cm");

    _pantalla.setCursor(0, 20);
    _pantalla.print("MODO "); _pantalla.println(modo);

    _pantalla.setCursor(0, 30);
    _pantalla.println(conexionActiva ? "CONECTADO" : "SIN CONEXION");

    _pantalla.display();
}

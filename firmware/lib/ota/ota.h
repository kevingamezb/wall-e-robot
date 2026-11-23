#ifndef OTA_H
#define OTA_H

#include <Arduino.h>

class Ota {

public:

    // Inicia la guardia antes de sensores y WiFi para cubrir cuelgues durante setup().
    void iniciarGuardiaRollback();

    // Levanta el portal web y ArduinoOTA. Llamar después de WiFi.softAP().
    void iniciar(const String& usuario, const String& clave, bool redProtegida);

    // Atiende clientes web y ArduinoOTA. Llamar en cada loop().
    void procesar();
    bool reinicioCredenciales(uint32_t& iniciadoMs) const;
    bool actualizando() const;

    void confirmar();

    void revertir();

    bool pendiente() const;

    // El servidor TCP solo se comprueba en arranque protegido.
    bool selfTestInicial(String& motivo, bool redProtegida);
};

extern Ota ota;

#endif

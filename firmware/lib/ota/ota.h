#ifndef OTA_H
#define OTA_H

#include <Arduino.h>

class Ota {

public:

    // Inicia la guardia antes de sensores y WiFi para cubrir cuelgues durante setup().
    void iniciarGuardiaRollback();

    // Levanta el portal web y ArduinoOTA. Llamar después de WiFi.softAP().
    void iniciar();

    // Atiende clientes web y ArduinoOTA. Llamar en cada loop().
    void procesar();

    void confirmar();

    void revertir();

    bool pendiente() const;

    // El self-test exige que el AP tenga IP y que el servidor TCP escuche.
    bool selfTestInicial(String& motivo);
};

extern Ota ota;

#endif

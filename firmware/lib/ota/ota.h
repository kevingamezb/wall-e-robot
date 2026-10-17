// wall-e-robot/firmware/lib/ota/ota.h
// Kevin Gámez - 16/10/2026

#ifndef OTA_H
#define OTA_H

#include <Arduino.h>

/*
 *  OTA: actualización de firmware por WiFi.
 *
 *  - Portal web (HTTP Basic Auth) en el puerto 80: el formulario pide el
 *    MD5 del .bin (campo de texto, antes del archivo) y el archivo; si la
 *    imagen se escribe sin error, el robot se reinicia en la versión nueva.
 *  - ArduinoOTA por si se prefiere subir desde PlatformIO/espota.
 *  - Rollback nativo (esp_ota): la imagen nueva arranca en estado
 *    PENDING_VERIFY. Una tarea FreeRTOS de guardia, independiente del loop,
 *    espera OTA_AUTOCONFIRMA_MS a que el self-test confirme; si no, revierte
 *    a la versión anterior.
 */
class Ota {

public:

    // Crea la tarea de guardia. Llamar temprano en setup(), antes de sensores
    // y WiFi, para que proteja también los cuelgues durante la inicialización.
    void iniciarGuardiaRollback();

    // Levanta el portal web y ArduinoOTA. Llamar después de WiFi.softAP().
    void iniciar();

    // Atiende clientes web y ArduinoOTA. Llamar en cada loop().
    void procesar();

    // El self-test pasó: confirma la versión y desarma el rollback.
    void confirmar();

    // Revierte manualmente a la versión anterior (reinicia).
    void revertir();

    // true si la app en ejecución está pendiente de confirmación.
    bool pendiente() const;

    // Comprobaciones internas de arranque (self-test). Solo el AP con IP y el
    // servidor TCP escuchando son fatales; los módulos habilitados que no
    // inicializan se registran como aviso (no revierten). Devuelve false y deja
    // el motivo en 'motivo' si falla algo fatal.
    bool selfTestInicial(String& motivo);
};

// Instancia única global.
extern Ota ota;

#endif // OTA_H

// Copia esta plantilla a firmware/include/secrets.h, que Git ignora.
// Elegir una clave propia del equipo; no reutilizar la de ejemplo.
// Requisitos validados al compilar (firmware/include/config.h):
//   - WIFI_AP_CLAVE: 8 caracteres o más (WPA2).
//   - OTA_USUARIO:   no vacío.
//   - OTA_CLAVE:     8 caracteres o más.

#ifndef SECRETS_H
#define SECRETS_H

#define WIFI_AP_CLAVE "CAMBIAR_CLAVE_AP"

// Credenciales del portal OTA y de ArduinoOTA.
#define OTA_USUARIO   "walle"
#define OTA_CLAVE     "CAMBIAR_CLAVE_OTA"

#endif

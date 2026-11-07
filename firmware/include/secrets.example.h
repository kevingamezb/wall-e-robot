// wall-e-robot/firmware/include/secrets.example.h
// Kevin Gámez - 16/10/2026
//
// Plantilla de credenciales: copiar este archivo como "secrets.h" (ese
// archivo está en .gitignore y no se versiona).
//
//   cp firmware/include/secrets.example.h firmware/include/secrets.h
//
// Elegir una clave propia del equipo; no reutilizar la de ejemplo.
//
// Requisitos validados al compilar (firmware/include/config.h):
//   - WIFI_AP_CLAVE: 8 caracteres o más (WPA2).
//   - OTA_USUARIO:   no vacío.
//   - OTA_CLAVE:     8 caracteres o más.

#ifndef SECRETS_H
#define SECRETS_H

// Clave del AP WiFi "WALL-E".
#define WIFI_AP_CLAVE "CAMBIAR_CLAVE_AP"

// Credenciales del portal OTA y de ArduinoOTA.
#define OTA_USUARIO   "walle"
#define OTA_CLAVE     "CAMBIAR_CLAVE_OTA"

#endif // SECRETS_H

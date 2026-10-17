// wall-e-robot/firmware/include/secrets.example.h
// Kevin Gámez - 16/10/2026
//
// Plantilla de credenciales: copiar este archivo como "secrets.h" (ese
// archivo está en .gitignore y no se versiona).

// Si "secrets.h" no existe, config.h usa estos mismos valores por defecto
// (ver los #ifndef en config.h).

#ifndef SECRETS_H
#define SECRETS_H

// Clave del AP WiFi "WALL-E".
#define WIFI_AP_CLAVE ""

// Credenciales del portal OTA. No dejar la clave vacía.
#define OTA_USUARIO   "walle"
#define OTA_CLAVE     ""

#endif // SECRETS_H

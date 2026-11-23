#include "credenciales.h"

#include <ArduinoJson.h>
#include <Preferences.h>

namespace {
constexpr char ESPACIO_NVS[] = "walle-red";
constexpr char CLAVE_NVS[] = "credenciales";
constexpr size_t MAX_LINEA = 512;

bool asciiValido(JsonVariantConst valor, size_t minimo, size_t maximo, bool usuario = false) {
    if (!valor.is<const char*>()) {
        return false;
    }
    const JsonString texto = valor.as<JsonString>();
    if (texto.size() < minimo || texto.size() > maximo) {
        return false;
    }
    for (size_t i = 0; i < texto.size(); ++i) {
        const unsigned char c = texto.c_str()[i];
        if (c < 32 || c > 126 || (usuario && (c == ' ' || c == ':'))) {
            return false;
        }
    }
    return true;
}

bool leerJson(const char* json, Credenciales& destino) {
    StaticJsonDocument<768> datos;
    if (deserializeJson(datos, json) ||
        !asciiValido(datos["wifi"], 8, 63) ||
        !asciiValido(datos["usuario_ota"], 1, 32, true) ||
        !asciiValido(datos["clave_ota"], 8, 63)) {
        return false;
    }
    destino.wifi = datos["wifi"].as<const char*>();
    destino.usuarioOta = datos["usuario_ota"].as<const char*>();
    destino.claveOta = datos["clave_ota"].as<const char*>();
    return true;
}
}  // namespace

bool Credenciales::cargar() {
    Preferences nvs;
    if (!nvs.begin(ESPACIO_NVS, true)) {
        return false;
    }
    const String json = nvs.getString(CLAVE_NVS);
    nvs.end();
    return leerJson(json.c_str(), *this);
}

Credenciales::Resultado Credenciales::guardar(const String& json) {
    Credenciales nuevas;
    if (json.length() > MAX_LINEA || !leerJson(json.c_str(), nuevas)) {
        return Resultado::INVALIDAS;
    }
    Preferences nvs;
    return nvs.begin(ESPACIO_NVS, false) &&
        nvs.putString(CLAVE_NVS, json) == json.length() ? Resultado::OK : Resultado::ERROR;
}

bool Credenciales::restaurarFabrica() {
    Preferences nvs;
    return nvs.begin(ESPACIO_NVS, false) &&
        (!nvs.isKey(CLAVE_NVS) || nvs.remove(CLAVE_NVS));
}

#pragma once

#include <Arduino.h>

class Credenciales {
public:
    enum class Resultado { OK, INVALIDAS, ERROR };

    bool cargar();
    static Resultado guardar(const String& json);
    static bool restaurarFabrica();

    String wifi;
    String usuarioOta;
    String claveOta;
};

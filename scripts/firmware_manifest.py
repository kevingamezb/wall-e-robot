# wall-e-robot/scripts/firmware_manifest.py
# Kevin Gámez - 16/10/2026
#
# Genera, tras compilar, el MD5 de firmware.bin y lo imprime junto a la versión.
# Ese MD5 es el que se pega en el portal web OTA (/update) para verificar la
# integridad de la subida.

import hashlib
import os
import re

# env lo inyecta SCons/PlatformIO al ejecutar este script como extra_script.
Import("env")


def _leer_version():
    """Extrae PROYECTO_VERSION de firmware/include/config.h, o '?' si falla."""

    raiz = env["PROJECT_DIR"]
    ruta = os.path.join(raiz, "firmware", "include", "config.h")

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            contenido = archivo.read()
    except OSError:
        return "?"

    coincidencia = re.search(r'PROYECTO_VERSION\s*=\s*"([^"]+)"', contenido)
    return coincidencia.group(1) if coincidencia else "?"


def generar_manifest(target, source, env):
    """Post-build de PlatformIO: escribe el .md5 del binario y resume la versión."""

    binario = target[0].get_abspath()

    if not os.path.isfile(binario):
        return

    with open(binario, "rb") as archivo:
        datos = archivo.read()

    md5 = hashlib.md5(datos).hexdigest()

    with open(binario + ".md5", "w", encoding="ascii") as archivo:
        archivo.write(md5)

    print("")
    print("===================== FIRMWARE OTA =====================")
    print("  Version : " + _leer_version())
    print("  Binario : " + binario)
    print("  Tamano  : %d bytes" % len(datos))
    print("  MD5     : " + md5)
    print("  (pega ese MD5 en el portal OTA: http://192.168.4.1/)")
    print("========================================================")
    print("")


env.AddPostAction("$BUILD_DIR/${PROGNAME}.bin", generar_manifest)

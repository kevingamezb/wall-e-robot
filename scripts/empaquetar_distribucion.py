# wall-e-robot/scripts/empaquetar_distribucion.py
# Kevin Gámez - 17/10/2026
#
# Construye un ZIP versionado listo para entregar al equipo:
#   - App de Windows empaquetada con PyInstaller (modo onedir).
#   - Recursos de la interfaz incluidos en el bundle.
#   - firmware.bin + firmware.bin.md5 de la MISMA version, compilados aparte
#     con una clave de distribucion (nunca la de desarrollo).
#   - LEEME.md y SHA256SUMS.txt (integridad, no autenticidad).
#
# No versiona artefactos: la salida vive en dist/ (ignorada por Git) y el
# paquete se ensambla en un temporal, sin mezclarse con builds anteriores.
#
# Uso:
#   python scripts/empaquetar_distribucion.py
#   python scripts/empaquetar_distribucion.py --firmware-bin RUTA/firmware.bin
#   python scripts/empaquetar_distribucion.py --solo-firmware   (solo el .bin)
#
# PyInstaller no cross-compila: cada ZIP se genera en su sistema operativo.
# En CI (ver .github/workflows/release.yml) el firmware se compila una vez
# con --solo-firmware y los builds de Windows lo adjuntan con --firmware-bin.
#
# Requisitos:
#   - PyInstaller instalado (requirements-dev.txt).
#   - PlatformIO (solo si se compila el firmware; ver --firmware-bin).
#   - empaquetado/secrets.distribucion.h con la clave del AP (no versionado).


import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
CARPETA_TRABAJO = RAIZ / "empaquetado"
SECRETS_DIST = CARPETA_TRABAJO / "secrets.distribucion.h"
LANZADOR = CARPETA_TRABAJO / "lanzador.py"
NOMBRE_APP = "Wall-E"

# Nombres que NUNCA deben entrar en la distribucion (secretos y artefactos de
# desarrollo). Se comprueba sobre cada parte de la ruta relativa.
PROHIBIDOS = {
    "secrets.h", "secrets.distribucion.h", ".env", ".envrc", ".git",
    ".vscode", "__pycache__", ".pytest_cache", ".coverage", ".pio",
    "modelo_3d",
}
# Sufijos de artefactos que tampoco deben viajar.
SUFIJOS_PROHIBIDOS = (".spec", ".log")


def leer_version(raiz: Path = RAIZ) -> str:
    """Extrae PROYECTO_VERSION de firmware/include/config.h (o '?' si falla)."""
    ruta = raiz / "firmware" / "include" / "config.h"
    try:
        contenido = ruta.read_text(encoding="utf-8")
    except OSError:
        return "?"
    coincidencia = re.search(r'PROYECTO_VERSION\s*=\s*"([^"]+)"', contenido)
    return coincidencia.group(1) if coincidencia else "?"


def md5_archivo(ruta: Path) -> str:
    """MD5 hex (32 minusculas) del archivo, igual que firmware_manifest.py."""
    return hashlib.md5(ruta.read_bytes()).hexdigest()


def sha256_archivo(ruta: Path) -> str:
    """SHA-256 hex del archivo."""
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def verificar_md5(bin_ruta: Path, md5_ruta: Path) -> bool:
    """True si el .md5 (texto plano, 32 hex) coincide con el MD5 del .bin."""
    if not bin_ruta.is_file() or not md5_ruta.is_file():
        return False
    esperado = md5_ruta.read_text(encoding="ascii").strip().lower()
    return esperado == md5_archivo(bin_ruta)


def contiene_prohibidos(carpeta: Path) -> list:
    """Lista de rutas (relativas) que no deberian estar en la distribucion."""
    hallazgos = []
    for elemento in sorted(carpeta.rglob("*")):
        relativa = elemento.relative_to(carpeta)
        if set(relativa.parts) & PROHIBIDOS:
            hallazgos.append(relativa)
        elif elemento.is_file() and relativa.suffix.lower() in SUFIJOS_PROHIBIDOS:
            hallazgos.append(relativa)
    return hallazgos


def lineas_sha256sums(carpeta: Path, excluir: str = "SHA256SUMS.txt") -> list:
    """Lineas '<sha256>  <ruta_relativa>' de todos los archivos, ordenadas."""
    lineas = []
    for archivo in sorted(carpeta.rglob("*")):
        if not archivo.is_file():
            continue
        relativa = archivo.relative_to(carpeta).as_posix()
        if relativa == excluir:
            continue
        lineas.append(f"{sha256_archivo(archivo)}  {relativa}")
    return sorted(lineas)


def escribir_sha256sums(carpeta: Path) -> Path:
    """Escribe SHA256SUMS.txt en la carpeta y devuelve su ruta."""
    destino = carpeta / "SHA256SUMS.txt"
    destino.write_text("\n".join(lineas_sha256sums(carpeta)) + "\n",
                       encoding="utf-8")
    return destino


def nombre_paquete(version: str) -> str:
    """Nombre de la carpeta raiz dentro del ZIP (y base del ZIP)."""
    return f"wall-e-{version}"


def _ignorar_temporal(directorio, nombres):
    """Filtro de copytree: omite artefactos de build/desarrollo."""
    return [n for n in nombres
            if n in ("__pycache__", ".pio") or n.endswith(".pyc")]


def localizar_platformio():
    """Ruta al ejecutable de PlatformIO, o None si no se encuentra."""
    for nombre in ("platformio", "pio"):
        encontrado = shutil.which(nombre)
        if encontrado:
            return encontrado
    penv = Path.home() / ".platformio" / "penv"
    candidatos = [
        penv / "bin" / "platformio",                    # Linux/macOS
        penv / "Scripts" / "platformio.exe",            # Windows
        penv / "Scripts" / "platformio",                # Windows (venv)
    ]
    for candidato in candidatos:
        if candidato.is_file():
            return str(candidato)
    return None


def construir_firmware_distribucion(temporal: Path) -> Path:
    """Compila el firmware en un arbol temporal con la clave de distribucion.

    Copia firmware/, platformio.ini y el manifiesto a un directorio temporal,
    coloca alli secrets.distribucion.h como secrets.h y ejecuta PlatformIO.
    No toca el arbol de trabajo ni secrets.h de desarrollo. Devuelve el .bin.
    """
    if not SECRETS_DIST.is_file():
        raise FileNotFoundError(
            "Falta la clave de distribucion. Copia empaquetado/"
            "secrets.distribucion.h desde firmware/include/secrets.example.h "
            "y rellena WIFI_AP_CLAVE / OTA_CLAVE (con una clave propia del "
            "equipo, no la de desarrollo)."
        )

    trabajo = temporal / "firmware_build"
    shutil.copytree(RAIZ / "firmware", trabajo / "firmware",
                    ignore=_ignorar_temporal)
    (trabajo / "scripts").mkdir()
    shutil.copy2(RAIZ / "scripts" / "firmware_manifest.py",
                 trabajo / "scripts" / "firmware_manifest.py")
    shutil.copy2(RAIZ / "platformio.ini", trabajo / "platformio.ini")

    (trabajo / "firmware" / "include" / "secrets.h").write_text(
        SECRETS_DIST.read_text(encoding="utf-8"), encoding="utf-8")

    pio = localizar_platformio()
    if not pio:
        raise FileNotFoundError(
            "No se encontro PlatformIO. Instalalo o pasa --firmware-bin."
        )

    print("[firmware] Compilando en temporal (clave de distribucion)...")
    subprocess.run([pio, "run"], cwd=str(trabajo), check=True)

    binario = trabajo / ".pio" / "build" / "esp32dev" / "firmware.bin"
    if not binario.is_file():
        raise FileNotFoundError("PlatformIO no genero firmware.bin.")
    return binario


def compilar_firmware_solo(salida: Path = None) -> Path:
    """Compila SOLO el firmware de distribucion y deja .bin + .md5 en salida.

    Pensado para CI: el firmware del ESP32 no depende del PC, asi que se
    compila una vez (en Linux) y los builds de Windows/macOS lo adjuntan con
    --firmware-bin. Devuelve la ruta del .bin copiado.
    """
    salida = Path(salida) if salida else RAIZ / "dist"
    salida.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="walle_fw_") as tmp_str:
        binario = construir_firmware_distribucion(Path(tmp_str))
        destino = salida / "firmware.bin"
        shutil.copy2(binario, destino)
        md5_origen = binario.with_name(binario.name + ".md5")
        md5_destino = salida / "firmware.bin.md5"
        if md5_origen.is_file():
            shutil.copy2(md5_origen, md5_destino)
        else:
            md5_destino.write_text(md5_archivo(destino), encoding="ascii")
    return destino


def construir_app(destino: Path, temporal: Path):
    """Empaqueta la app con PyInstaller (onedir) dentro de 'destino'."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError as error:
        raise ImportError(
            "PyInstaller no esta instalado. Ejecuta: "
            "python -m pip install -r requirements-dev.txt"
        ) from error

    separador = ";" if sys.platform == "win32" else ":"
    comando = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--onedir", "--windowed",
        "--name", NOMBRE_APP,
        "--distpath", str(destino),
        "--workpath", str(temporal / "pyinstaller_build"),
        "--specpath", str(temporal),
        "--paths", str(RAIZ),
        "--add-data", f"{RAIZ / 'app' / 'recursos'}{separador}app/recursos",
        # _imagingtk (C) importa PIL._tkinter_finder al crear PhotoImage;
        # PyInstaller no lo detecta y la app crashea al dibujar.
        "--hidden-import", "PIL._tkinter_finder",
        str(LANZADOR),
    ]
    print("[app] Empaquetando con PyInstaller (onedir)...")
    subprocess.run(comando, cwd=str(temporal), check=True)


def crear_leeme(destino: Path, version: str):
    """Genera LEEME.md con instrucciones de ejecucion y actualizacion."""
    plataforma = sys.platform
    if plataforma == "win32":
        titulo = f"# WALL-E {version} — Distribución (Windows)"
        ejecutar = """1. Abre la carpeta `Wall-E` y ejecuta `Wall-E.exe`."""
        config = "La configuración de teclas se guarda en `%APPDATA%\\Wall-E\\controles.json`."
    elif plataforma == "darwin":
        titulo = f"# WALL-E {version} — Distribución (macOS)"
        ejecutar = """1. Abre `Wall-E.app` (desde la carpeta o Applications)."""
        config = "La configuración de teclas se guarda en `~/Library/Application Support/Wall-E/controles.json`."
    else:
        titulo = f"# WALL-E {version} — Distribución (Linux)"
        ejecutar = """1. Da permisos de ejecución a `Wall-E/Wall-E` si es necesario: `chmod +x Wall-E/Wall-E`.
2. Ejecuta `./Wall-E/Wall-E` desde la carpeta o desde un lanzador."""
        config = "La configuración de teclas se guarda en `~/.config/wall-e/controles.json`."
    
    contenido = f"""{titulo}

Este paquete no requiere instalar Python: la aplicación viene empaquetada.

## Contenido

- `Wall-E/` — aplicación de escritorio (ejecutable).
- `firmware/firmware.bin` — firmware del ESP32 para actualización OTA.
- `firmware/firmware.bin.md5` — MD5 del firmware (lo pide el portal OTA).
- `firmware/version.txt` — versión del firmware incluido.
- `SHA256SUMS.txt` — hashes SHA-256 para comprobar la integridad.

## Ejecutar la aplicación

{ejecutar}
2. Arranca en modo simulador (no necesita el robot).
3. Para conectar al robot: conéctate a la red WiFi del robot y pulsa
   CONECTAR con la IP `192.168.4.1`.

{config}.

## Actualizar el firmware (OTA)

1. Conecta la PC a la red WiFi del robot.
2. Abre `http://192.168.4.1/` en el navegador.
3. Pega el MD5 de `firmware/firmware.bin.md5` y elige `firmware/firmware.bin`.
4. Pulsa Actualizar; el robot reinicia con la versión nueva.

La clave del WiFi del robot se entrega aparte, por un canal separado.

## Verificar la integridad (no es una firma)

`SHA256SUMS.txt` permite comprobar que los archivos no se corrompieron al
copiarlos; no acredita autoría ni autenticidad.
"""
    (destino / "LEEME.md").write_text(contenido, encoding="utf-8")


def empaquetar(firmware_bin=None, salida: Path = None):
    """Ensambla el paquete completo en un temporal y devuelve la ruta del ZIP."""
    salida = Path(salida) if salida else RAIZ / "dist"
    version = leer_version()
    if version == "?":
        raise RuntimeError("No se pudo leer PROYECTO_VERSION de config.h.")

    if not LANZADOR.is_file():
        raise FileNotFoundError(f"Falta el lanzador: {LANZADOR}")

    salida.mkdir(parents=True, exist_ok=True)
    sistema = sys.platform
    sufijo = "win64" if sistema == "win32" else "linux64" if sistema == "linux" else "macos64"
    zip_ruta = salida / f"{nombre_paquete(version)}-{sufijo}.zip"

    with tempfile.TemporaryDirectory(prefix="walle_pack_") as tmp_str:
        temporal = Path(tmp_str)
        raiz_paquete = temporal / nombre_paquete(version)

        # 1) App (onedir) dentro de la raiz del paquete.
        construir_app(raiz_paquete, temporal)

        # 2) Firmware de la misma version.
        firmware_destino = raiz_paquete / "firmware"
        firmware_destino.mkdir(parents=True, exist_ok=True)
        if firmware_bin:
            origen_bin = Path(firmware_bin).resolve()
            origen_md5 = origen_bin.with_name(origen_bin.name + ".md5")
            if not origen_bin.is_file():
                raise FileNotFoundError(f"No existe el bin: {origen_bin}")
        else:
            origen_bin = construir_firmware_distribucion(temporal)
            origen_md5 = origen_bin.with_name(origen_bin.name + ".md5")

        shutil.copy2(origen_bin, firmware_destino / "firmware.bin")
        if origen_md5.is_file():
            shutil.copy2(origen_md5, firmware_destino / "firmware.bin.md5")
        else:
            (firmware_destino / "firmware.bin.md5").write_text(
                md5_archivo(origen_bin), encoding="ascii")
        (firmware_destino / "version.txt").write_text(version + "\n",
                                                      encoding="utf-8")

        # 3) LEEME e integridad.
        crear_leeme(raiz_paquete, version)

        prohibidos = contiene_prohibidos(raiz_paquete)
        if prohibidos:
            lista = "\n  ".join(str(p) for p in prohibidos)
            raise RuntimeError(
                "El paquete contiene archivos prohibidos (secretos/"
                "artefactos):\n  " + lista)

        bin_final = firmware_destino / "firmware.bin"
        md5_final = firmware_destino / "firmware.bin.md5"
        if not verificar_md5(bin_final, md5_final):
            raise RuntimeError(
                "El MD5 del firmware incluido no coincide con el .bin.")

        escribir_sha256sums(raiz_paquete)

        # 4) ZIP con carpeta raiz wall-e-<version>/.
        with zipfile.ZipFile(zip_ruta, "w", zipfile.ZIP_DEFLATED) as zf:
            for archivo in sorted(raiz_paquete.rglob("*")):
                if archivo.is_file():
                    relativa = archivo.relative_to(
                        raiz_paquete.parent).as_posix()
                    zf.write(archivo, relativa)

    return zip_ruta


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Genera el ZIP de distribucion de WALL-E.")
    parser.add_argument("--firmware-bin", default=None,
                        help="Usar un firmware.bin ya compilado en vez de "
                             "compilar en temporal (avanzado).")
    parser.add_argument("--solo-firmware", action="store_true",
                        help="Solo compilar el firmware de distribucion "
                             "(deja firmware.bin + .md5 en --salida) y salir. "
                             "Para CI: compilar una vez y repartir con "
                             "--firmware-bin en el resto de plataformas.")
    parser.add_argument("--salida", default=None,
                        help="Carpeta de salida (por defecto: dist/).")
    args = parser.parse_args(argv)

    if args.solo_firmware:
        ruta = compilar_firmware_solo(
            Path(args.salida) if args.salida else None)
        print("\nListo:")
        print("  " + str(ruta))
        return 0

    zip_ruta = empaquetar(firmware_bin=args.firmware_bin, salida=args.salida)
    print("\nListo:")
    print("  " + str(zip_ruta))
    return 0


if __name__ == "__main__":
    sys.exit(main())

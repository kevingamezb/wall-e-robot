# wall-e-robot/scripts/empaquetar_distribucion.py
# Kevin Gámez - 17/10/2026
#
# Construye artefactos versionados listos para entregar al equipo:
#   - ZIP (por defecto): app de PyInstaller (onedir) + firmware + LEEME +
#     SHA256SUMS.txt.
#   - --exe: Wall-E.exe autocontenido para Windows (PyInstaller --onefile).
#   - --deb: paquete Debian/Ubuntu/Mint con la app, lanzador, icono, .desktop
#     y el firmware OTA.
#   - --solo-firmware: solo firmware.bin + firmware.bin.md5 (para CI).
#
# El firmware se compila SIEMPRE con una clave de distribucion (nunca la de
# desarrollo) y su MD5 se verifica antes de empaquetarlo.
#
# No versiona artefactos: la salida vive en dist/ (ignorada por Git) y cada
# paquete se ensambla en un temporal, sin mezclarse con builds anteriores.
#
# Uso:
#   python scripts/empaquetar_distribucion.py
#   python scripts/empaquetar_distribucion.py --firmware-bin RUTA/firmware.bin
#   python scripts/empaquetar_distribucion.py --solo-firmware   (solo el .bin)
#   python scripts/empaquetar_distribucion.py --exe             (solo Windows)
#   python scripts/empaquetar_distribucion.py --deb \
#       --firmware-bin dist/firmware.bin                        (solo Linux)
#
# PyInstaller no cross-compila: cada artefacto se genera en su sistema
# operativo. En CI (ver .github/workflows/release.yml) el firmware se compila
# una vez con --solo-firmware y los builds de Windows/Linux lo adjuntan con
# --firmware-bin.
#
# Requisitos:
#   - PyInstaller instalado (requirements-dev.txt).
#   - PlatformIO (solo si se compila el firmware; ver --firmware-bin).
#   - dpkg-deb (solo para --deb; viene con dpkg en Debian/Ubuntu).
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
MANTENEDOR = "Kevin Gámez <est.kevin.gamez@unimilitar.edu.co>"
# Icono dedicado (cuadrado, 1024x1024 recomendado). Si no existe se usa el
# antiguo titulo.png como respaldo para no romper builds sin diseno nuevo.
ICONO = RAIZ / "app" / "recursos" / "icono.png"
ICONO_RESPALDO = RAIZ / "app" / "recursos" / "titulo.png"

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


def _version_numerica(version: str) -> tuple[int, int, int, int]:
    """Convierte '1.2.3' en (1, 2, 3, 0), como exige el recurso PE."""
    numeros = [int(n) for n in re.findall(r"\d+", version)[:4]]
    return tuple((numeros + [0, 0, 0, 0])[:4])


def generar_version_info_windows(destino: Path, version: str) -> Path:
    """Genera el recurso de version PE que PyInstaller incrusta en el .exe.

    Windows y los antivirus usan estos metadatos para identificar al
    fabricante y al producto. Un ejecutable sin version info parece mas
    sospechoso para SmartScreen y los motores heuristicos.
    """
    a, b, c, d = _version_numerica(version)
    contenido = f"""# Generado por scripts/empaquetar_distribucion.py
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({a}, {b}, {c}, {d}),
    prodvers=({a}, {b}, {c}, {d}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'Kevin Gamez'),
         StringStruct('FileDescription', 'WALL-E - Panel de control del robot'),
         StringStruct('FileVersion', '{version}'),
         StringStruct('InternalName', 'Wall-E'),
         StringStruct('LegalCopyright', 'Copyright (C) 2026 Kevin Gamez'),
         StringStruct('OriginalFilename', 'Wall-E.exe'),
         StringStruct('ProductName', 'WALL-E'),
         StringStruct('ProductVersion', '{version}')])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")
    return destino


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


def validar_secrets_distribucion(ruta: Path = SECRETS_DIST):
    """Comprueba que las credenciales de distribución cumplen el mínimo.

    No imprime los valores. Refleja los static_assert de firmware/config.h
    para dar un error claro antes de invocar PlatformIO.
    """
    if not ruta.is_file():
        raise FileNotFoundError(f"Falta la clave de distribucion: {ruta}")

    contenido = ruta.read_text(encoding="utf-8")
    minimos = {"WIFI_AP_CLAVE": 8, "OTA_USUARIO": 1, "OTA_CLAVE": 8}
    for macro, minimo in minimos.items():
        coincidencia = re.search(
            rf'#define\s+{macro}\s+"([^"]*)"', contenido)
        if not coincidencia:
            raise RuntimeError(
                f"Falta {macro} en {ruta.name}.")
        if len(coincidencia.group(1)) < minimo:
            raise RuntimeError(
                f"{macro} en {ruta.name} debe tener al menos {minimo} "
                "caracteres (mira firmware/include/secrets.example.h).")


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

    validar_secrets_distribucion()

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
    salida = (Path(salida) if salida else RAIZ / "dist").resolve()
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


def ruta_icono_origen() -> Path | None:
    """Devuelve el icono dedicado o, si no existe, el titulo de respaldo."""
    for ruta in (ICONO, ICONO_RESPALDO):
        if ruta.is_file():
            return ruta
    return None


def generar_icono_cuadrado(destino: Path, formato: str, lado: int = 256):
    """Genera un icono cuadrado (ICO/PNG) desde el PNG de origen.

    Si el origen no es cuadrado, se centra sobre un lienzo transparente para
    que el icono no se deforme. El ICO incluye todos los tamanos que usa
    Windows; el PNG se redimensiona al tamano pedido. Devuelve la ruta o None
    si no hay origen o falta Pillow.
    """
    origen = ruta_icono_origen()
    if origen is None:
        return None
    try:
        from PIL import Image
    except ImportError:
        return None

    imagen = Image.open(origen).convert("RGBA")
    mayor = max(imagen.size)
    lienzo = Image.new("RGBA", (mayor, mayor), (0, 0, 0, 0))
    lienzo.paste(imagen, ((mayor - imagen.width) // 2,
                          (mayor - imagen.height) // 2), imagen)

    destino.parent.mkdir(parents=True, exist_ok=True)
    if formato == "ico":
        lienzo.save(destino, format="ICO",
                    sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (40, 40),
                           (48, 48), (64, 64), (128, 128), (256, 256)])
    else:
        lienzo.resize((lado, lado), Image.LANCZOS).save(destino, format="PNG")
    return destino


def _ejecutar_pyinstaller(destino: Path, temporal: Path, onefile: bool):
    """Invoca PyInstaller en modo onedir (ZIP/deb) o onefile (.exe)."""
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
        "--noconfirm", "--onefile" if onefile else "--onedir", "--windowed",
        # UPX comprime el binario y es un disparador clasico de heuristicas.
        "--noupx",
        "--name", NOMBRE_APP,
        "--distpath", str(destino),
        "--workpath", str(temporal / "pyinstaller_build"),
        "--specpath", str(temporal),
        "--paths", str(RAIZ),
        "--add-data", f"{RAIZ / 'app' / 'recursos'}{separador}app/recursos",
        # _imagingtk (C) importa PIL._tkinter_finder al crear PhotoImage;
        # PyInstaller no lo detecta y la app crashea al dibujar.
        "--hidden-import", "PIL._tkinter_finder",
    ]
    if sys.platform == "win32":
        icono = generar_icono_cuadrado(temporal / "wall-e.ico", "ico")
        if icono:
            comando += ["--icon", str(icono)]
        # Fabricante, producto y version visibles en las propiedades del .exe.
        info = generar_version_info_windows(
            temporal / "version_info.txt", leer_version())
        comando += ["--version-file", str(info)]
    comando.append(str(LANZADOR))

    modo = "onefile" if onefile else "onedir"
    print(f"[app] Empaquetando con PyInstaller ({modo})...")
    subprocess.run(comando, cwd=str(temporal), check=True)


def construir_app(destino: Path, temporal: Path):
    """Empaqueta la app con PyInstaller (onedir) dentro de 'destino'."""
    _ejecutar_pyinstaller(destino, temporal, onefile=False)


def construir_exe(salida: Path = None) -> Path:
    """Construye Wall-E.exe autocontenido (Windows, PyInstaller onefile)."""
    if sys.platform != "win32":
        raise RuntimeError(
            "El .exe solo se puede construir en Windows (PyInstaller no "
            "cross-compila)."
        )

    salida = (Path(salida) if salida else RAIZ / "dist").resolve()
    salida.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="walle_exe_") as tmp_str:
        _ejecutar_pyinstaller(salida, Path(tmp_str), onefile=True)

    exe = salida / f"{NOMBRE_APP}.exe"
    if not exe.is_file():
        raise FileNotFoundError("PyInstaller no genero Wall-E.exe.")
    return exe


def adjuntar_firmware(destino: Path, firmware_bin, temporal: Path, version: str):
    """Copia firmware.bin + firmware.bin.md5 + version.txt dentro de 'destino'.

    Si no se pasa un .bin ya compilado, lo compila con la clave de
    distribucion. Devuelve (ruta_bin, ruta_md5) ya copiados.
    """
    destino.mkdir(parents=True, exist_ok=True)
    if firmware_bin:
        origen_bin = Path(firmware_bin).resolve()
        origen_md5 = origen_bin.with_name(origen_bin.name + ".md5")
        if not origen_bin.is_file():
            raise FileNotFoundError(f"No existe el bin: {origen_bin}")
    else:
        origen_bin = construir_firmware_distribucion(temporal)
        origen_md5 = origen_bin.with_name(origen_bin.name + ".md5")

    bin_final = destino / "firmware.bin"
    md5_final = destino / "firmware.bin.md5"
    shutil.copy2(origen_bin, bin_final)
    if origen_md5.is_file():
        shutil.copy2(origen_md5, md5_final)
    else:
        md5_final.write_text(md5_archivo(origen_bin), encoding="ascii")
    (destino / "version.txt").write_text(version + "\n", encoding="utf-8")
    return bin_final, md5_final


def _arquitectura_debian() -> str:
    """Arquitectura dpkg de la maquina (amd64 si no se puede consultar)."""
    try:
        salida = subprocess.check_output(["dpkg", "--print-architecture"],
                                         text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "amd64"
    return salida or "amd64"


def crear_leeme_deb(destino: Path, version: str, arquitectura: str):
    """Genera el LEEME.md de la documentacion del paquete .deb."""
    contenido = f"""# WALL-E {version} — Paquete Debian ({arquitectura})

Instalado con `sudo apt install ./wall-e_{version}_{arquitectura}.deb` o
`sudo dpkg -i wall-e_{version}_{arquitectura}.deb`.

No requiere instalar Python: la aplicación viene empaquetada.

## Ejecutar

1. Abre **WALL-E** desde el menú de aplicaciones.
2. O ejecuta `wall-e` en una terminal.

La configuración de teclas se guarda en `~/.config/wall-e/controles.json`.

## Archivos instalados

- `/opt/wall-e/Wall-E` — aplicación de escritorio.
- `/usr/bin/wall-e` — lanzador.
- `/usr/share/wall-e/firmware/firmware.bin` — firmware OTA.
- `/usr/share/wall-e/firmware/firmware.bin.md5` — MD5 para el portal OTA.

## Actualizar el firmware (OTA)

1. Conecta la PC a la red WiFi del robot.
2. Abre `http://192.168.4.1/` en el navegador.
3. Pega el MD5 de `firmware.bin.md5` y elige `firmware.bin`.
4. Pulsa Actualizar; el robot reinicia con la versión nueva.

La clave del WiFi del robot se entrega aparte, por un canal separado.
"""
    (destino / "LEEME.md").write_text(contenido, encoding="utf-8")


def _copiar_copyright(destino: Path):
    """Escribe el archivo copyright que exige la seccion doc de Debian."""
    contenido = f"""Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: wall-e-robot
Source: https://github.com/kevingamezb/wall-e-robot

Files: *
Copyright: 2026 Kevin Gámez
License: GPL-3.0
 En los sistemas Debian, el texto completo de la GNU General Public License
 version 3 esta en /usr/share/common-licenses/GPL-3.
"""
    (destino / "copyright").write_text(contenido, encoding="utf-8")


def construir_deb(firmware_bin=None, salida: Path = None) -> Path:
    """Construye un .deb instalable (Linux) con la app + firmware OTA.

    Requiere dpkg-deb (viene con dpkg en Debian/Ubuntu/Mint). PyInstaller no
    cross-compila: el paquete se genera en Linux.
    """
    if sys.platform != "linux":
        raise RuntimeError(
            "El .deb solo se puede construir en Linux (dpkg-deb)."
        )
    if not shutil.which("dpkg-deb"):
        raise FileNotFoundError(
            "No se encontro dpkg-deb. Instala el paquete dpkg."
        )

    version = leer_version()
    if version == "?":
        raise RuntimeError("No se pudo leer PROYECTO_VERSION de config.h.")
    if not re.fullmatch(r"\d[A-Za-z0-9.+~-]*", version):
        raise RuntimeError(
            f"La version '{version}' no es valida para un paquete Debian."
        )

    salida = (Path(salida) if salida else RAIZ / "dist").resolve()
    salida.mkdir(parents=True, exist_ok=True)
    arquitectura = _arquitectura_debian()
    deb_ruta = salida / f"wall-e_{version}_{arquitectura}.deb"

    with tempfile.TemporaryDirectory(prefix="walle_deb_") as tmp_str:
        temporal = Path(tmp_str)
        raiz = temporal / "paquete"

        # 1) App onedir en /opt/wall-e (sin la carpeta intermedia Wall-E).
        construido = temporal / "pyinstaller"
        construir_app(construido, temporal)
        origen_app = construido / NOMBRE_APP
        if not origen_app.is_dir():
            raise FileNotFoundError("PyInstaller no genero la app onedir.")
        app_dir = raiz / "opt" / "wall-e"
        app_dir.mkdir(parents=True)
        for elemento in origen_app.iterdir():
            shutil.move(str(elemento), str(app_dir / elemento.name))

        # 2) Lanzador en /usr/bin.
        bin_dir = raiz / "usr" / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "wall-e").symlink_to(f"/opt/wall-e/{NOMBRE_APP}")

        # 3) Entrada de menú e icono.
        escritorio_dir = raiz / "usr" / "share" / "applications"
        escritorio_dir.mkdir(parents=True)
        (escritorio_dir / "wall-e.desktop").write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=WALL-E\n"
            "Comment=Panel de control del robot WALL-E\n"
            f"Exec=/opt/wall-e/{NOMBRE_APP}\n"
            "Icon=wall-e\n"
            "Terminal=false\n"
            "Categories=Utility;\n"
            "Keywords=robot;esp32;wall-e;\n",
            encoding="utf-8",
        )
        # Iconos en todos los tamanos que usan los escritorios (freedesktop).
        for lado in (16, 24, 32, 48, 64, 128, 256, 512):
            icono_dir = raiz / "usr" / "share" / "icons" / "hicolor" / \
                f"{lado}x{lado}" / "apps"
            icono_dir.mkdir(parents=True)
            generar_icono_cuadrado(icono_dir / "wall-e.png", "png", lado)

        # 4) Firmware OTA + documentación.
        doc_dir = raiz / "usr" / "share" / "doc" / "wall-e"
        doc_dir.mkdir(parents=True)
        crear_leeme_deb(doc_dir, version, arquitectura)
        _copiar_copyright(doc_dir)
        firmware_dir = raiz / "usr" / "share" / "wall-e" / "firmware"
        bin_final, md5_final = adjuntar_firmware(
            firmware_dir, firmware_bin, temporal, version)

        if not verificar_md5(bin_final, md5_final):
            raise RuntimeError(
                "El MD5 del firmware incluido no coincide con el .bin.")

        # 5) Metadatos Debian.
        tamano_kib = sum(
            archivo.stat().st_size for archivo in raiz.rglob("*")
            if archivo.is_file()
        ) // 1024
        debian = raiz / "DEBIAN"
        debian.mkdir()
        (debian / "control").write_text(
            "Package: wall-e\n"
            f"Version: {version}\n"
            "Section: utils\n"
            "Priority: optional\n"
            f"Architecture: {arquitectura}\n"
            f"Maintainer: {MANTENEDOR}\n"
            f"Installed-Size: {tamano_kib}\n"
            "Depends: libc6 (>= 2.35), libx11-6, libxext6, libxrender1, "
            "libxft2, "
            "libfontconfig1, libfreetype6, libgl1, libxcb1\n"
            "Description: Panel de control del robot WALL-E\n"
            " Aplicacion de escritorio (Tkinter) para controlar el robot\n"
            " WALL-E por WiFi. Incluye el firmware ESP32 (BIN + MD5) para\n"
            " actualizacion OTA.\n"
            "Homepage: https://github.com/kevingamezb/wall-e-robot\n",
            encoding="utf-8",
        )

        print("[deb] Construyendo el paquete Debian...")
        subprocess.run(
            ["dpkg-deb", "--root-owner-group", "--build",
             str(raiz), str(deb_ruta)],
            check=True,
        )

    return deb_ruta


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
2. Arranca en **SIN CONEXIÓN** y abre el modal para escribir la IP del robot.
3. Conéctate a la red WiFi del robot y pulsa CONECTAR con la IP `192.168.4.1`.
   Sin robot, el panel queda deshabilitado hasta conectar.

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
    salida = (Path(salida) if salida else RAIZ / "dist").resolve()
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
        bin_final, md5_final = adjuntar_firmware(
            firmware_destino, firmware_bin, temporal, version)

        # 3) LEEME e integridad.
        crear_leeme(raiz_paquete, version)

        prohibidos = contiene_prohibidos(raiz_paquete)
        if prohibidos:
            lista = "\n  ".join(str(p) for p in prohibidos)
            raise RuntimeError(
                "El paquete contiene archivos prohibidos (secretos/"
                "artefactos):\n  " + lista)

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
        description="Genera los artefactos de distribucion de WALL-E "
                    "(ZIP, .exe o .deb).")
    parser.add_argument("--firmware-bin", default=None,
                        help="Usar un firmware.bin ya compilado en vez de "
                             "compilar en temporal (avanzado).")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--solo-firmware", action="store_true",
                      help="Solo compilar el firmware de distribucion "
                           "(deja firmware.bin + .md5 en --salida) y salir. "
                           "Para CI: compilar una vez y repartir con "
                           "--firmware-bin en el resto de plataformas.")
    modo.add_argument("--exe", action="store_true",
                      help="Solo construir Wall-E.exe autocontenido (Windows).")
    modo.add_argument("--deb", action="store_true",
                      help="Solo construir el paquete .deb (Linux).")
    parser.add_argument("--salida", default=None,
                        help="Carpeta de salida (por defecto: dist/).")
    args = parser.parse_args(argv)

    salida = Path(args.salida) if args.salida else None

    if args.solo_firmware:
        ruta = compilar_firmware_solo(salida)
    elif args.exe:
        ruta = construir_exe(salida)
    elif args.deb:
        ruta = construir_deb(firmware_bin=args.firmware_bin, salida=salida)
    else:
        ruta = empaquetar(firmware_bin=args.firmware_bin, salida=salida)

    print("\nListo:")
    print("  " + str(ruta))
    return 0


if __name__ == "__main__":
    sys.exit(main())

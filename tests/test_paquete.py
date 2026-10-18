# wall-e-robot/tests/test_paquete.py
# Kevin Gámez - 17/10/2026

"""Pruebas del empaquetado de distribucion.

Cubren dos cosas:
  1. Que las rutas de recursos/configuracion resuelven bien (app/rutas.py) y
     que la app tiene un punto de entrada invocable.
  2. Que el empaquetador (scripts/empaquetar_distribucion.py) calcula bien
     MD5/SHA-256 y que un ZIP ya generado pasa las comprobaciones de
     integridad y contiene todos los archivos requeridos.
"""


import hashlib
import importlib.util
import re
import zipfile
from pathlib import Path

import pytest


RAIZ = Path(__file__).resolve().parents[1]


def _cargar_empaquetador():
    """Carga scripts/empaquetar_distribucion.py como modulo importable."""
    ruta = RAIZ / "scripts" / "empaquetar_distribucion.py"
    spec = importlib.util.spec_from_file_location(
        "empaquetar_distribucion", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def empaquetador():
    return _cargar_empaquetador()


# --------------------------------------------------------------- rutas / app

def test_rutas_en_codigo_fuente():
    """Sin congelar, las rutas apuntan al arbol del repositorio."""
    from app import rutas

    assert rutas.congelado() is False
    assert rutas.directorio_recursos() == RAIZ / "app" / "recursos"
    assert rutas.directorio_recursos().is_dir()
    assert rutas.ruta_controles() == RAIZ / "configuracion" / "controles.json"


def test_recursos_reales_existen():
    """Los PNG que usa la interfaz estan presentes en app/recursos."""
    from app.widgets.renderizado import carga_recursos

    assert carga_recursos.existe("ojo_normal")
    assert carga_recursos.ruta_asset("ojo_normal").is_file()


def test_app_tiene_punto_de_entrada():
    """app.main expone una funcion main() invocable (para el lanzador)."""
    from app.main import main

    assert callable(main)


# --------------------------------------------------------- helpers de hash

def test_leer_version_coincide_con_config(empaquetador):
    """leer_version extrae el mismo valor que hay en config.h."""
    config = (RAIZ / "firmware" / "include" / "config.h").read_text(
        encoding="utf-8")
    esperado = re.search(r'PROYECTO_VERSION\s*=\s*"([^"]+)"', config).group(1)

    assert empaquetador.leer_version(RAIZ) == esperado


def test_md5_y_sha256_de_archivo(empaquetador, tmp_path):
    """md5_archivo y sha256_archivo coinciden con hashlib."""
    archivo = tmp_path / "dato.bin"
    datos = b"wall-e"
    archivo.write_bytes(datos)

    assert empaquetador.md5_archivo(archivo) == hashlib.md5(datos).hexdigest()
    assert empaquetador.sha256_archivo(archivo) == \
        hashlib.sha256(datos).hexdigest()


def test_verificar_md5_acepta_y_rechaza(empaquetador, tmp_path):
    """verificar_md5 valida el par .bin/.md5 (formato 32 hex)."""
    binario = tmp_path / "firmware.bin"
    binario.write_bytes(b"contenido")
    md5 = tmp_path / "firmware.bin.md5"
    md5.write_text(hashlib.md5(b"contenido").hexdigest(), encoding="ascii")

    assert empaquetador.verificar_md5(binario, md5) is True

    md5.write_text("0" * 32, encoding="ascii")
    assert empaquetador.verificar_md5(binario, md5) is False


def test_contiene_prohibidos_detecta_secretos(empaquetador, tmp_path):
    """El guardia detecta secretos y artefactos de desarrollo."""
    (tmp_path / "secrets.h").write_text("clave", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_bytes(b"x")
    (tmp_path / "sano.txt").write_text("ok", encoding="utf-8")

    hallazgos = {str(p).replace("\\", "/")
                 for p in empaquetador.contiene_prohibidos(tmp_path)}

    assert "secrets.h" in hallazgos
    assert "__pycache__/x.pyc" in hallazgos
    assert not any("sano.txt" in h for h in hallazgos)


def test_contiene_prohibidos_limpio(empaquetador, tmp_path):
    """Un arbol sin secretos ni artefactos pasa el guardia."""
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("x", encoding="utf-8")

    assert empaquetador.contiene_prohibidos(tmp_path) == []


def test_lineas_sha256sums_ordenadas_y_completas(empaquetador, tmp_path):
    """SHA256SUMS lista todos los archivos excepto el propio archivo."""
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "SHA256SUMS.txt").write_text("viejo", encoding="utf-8")

    lineas = empaquetador.lineas_sha256sums(tmp_path)

    assert lineas == sorted(lineas)
    assert any(l.endswith("  a.txt") for l in lineas)
    assert any(l.endswith("  b.txt") for l in lineas)
    assert not any("SHA256SUMS.txt" in l for l in lineas)


def test_nombre_paquete(empaquetador):
    """El nombre del paquete usa la version."""
    assert empaquetador.nombre_paquete("1.0.0") == "wall-e-1.0.0"


# --------------------------------------------- integridad del firmware real

def test_firmware_compilado_corresponde_a_su_md5(empaquetador):
    """Si hay un firmware compilado, su .md5 coincide con el .bin."""
    binario = RAIZ / ".pio" / "build" / "esp32dev" / "firmware.bin"
    if not binario.is_file():
        pytest.skip("No hay firmware compilado en .pio/build/esp32dev/")

    md5 = binario.with_name(binario.name + ".md5")
    assert md5.is_file()
    assert empaquetador.verificar_md5(binario, md5) is True


# ------------------------------------------- integridad de un ZIP generado

def _zip_generado():
    import sys
    sufijo = "win64" if sys.platform == "win32" else "linux64" if sys.platform == "linux" else "macos64"
    zips = sorted((RAIZ / "dist").glob(f"wall-e-*-{sufijo}.zip"))
    return zips[-1] if zips else None


def test_zip_generado_es_integro():
    """El ZIP de dist/ (si existe) contiene lo requerido y valida SHA-256."""
    ruta_zip = _zip_generado()
    if ruta_zip is None:
        pytest.skip("No hay ZIP generado en dist/")

    with zipfile.ZipFile(ruta_zip) as zf:
        nombres = set(zf.namelist())

        # Archivos requeridos (con una carpeta raiz wall-e-<version>/).
        assert any(n.endswith("/LEEME.md") for n in nombres)
        assert any(n.endswith("/SHA256SUMS.txt") for n in nombres)
        assert any(n.endswith("/Wall-E/Wall-E.exe") or n.endswith("/Wall-E/Wall-E")
                   for n in nombres)
        assert any(n.endswith("/firmware/firmware.bin") for n in nombres)
        assert any(n.endswith("/firmware/firmware.bin.md5") for n in nombres)

        # El MD5 del firmware coincide con el .bin.
        bin_nombre = next(n for n in nombres
                          if n.endswith("/firmware/firmware.bin"))
        md5_nombre = next(n for n in nombres
                          if n.endswith("/firmware/firmware.bin.md5"))
        bin_bytes = zf.read(bin_nombre)
        md5_texto = zf.read(md5_nombre).decode("ascii").strip().lower()
        assert hashlib.md5(bin_bytes).hexdigest() == md5_texto

        # SHA256SUMS valida cada archivo (menos el propio listado).
        sums_nombre = next(n for n in nombres if n.endswith("/SHA256SUMS.txt"))
        raiz_zip = sums_nombre.rsplit("/", 1)[0]
        for linea in zf.read(sums_nombre).decode("utf-8").splitlines():
            if not linea.strip():
                continue
            esperado, rel = linea.split("  ", 1)
            contenido = zf.read(f"{raiz_zip}/{rel}")
            assert hashlib.sha256(contenido).hexdigest() == esperado

        # No viaja ningun archivo prohibido.
        prohibidos = ("secrets.h", "secrets.distribucion.h", "/.git/",
                      "__pycache__", ".coverage", "/.pio/")
        assert not any(p in n for n in nombres for p in prohibidos)

# wall-e-robot/app/rutas.py
# Kevin Gámez - 17/10/2026
#
# Resuelve las rutas de recursos y de configuración tanto al correr desde el
# código fuente como dentro de un ejecutable empaquetado con PyInstaller.
#
# En el código fuente las rutas cuelgan del árbol del repositorio; congelado,
# los recursos viajan dentro del bundle (sys._MEIPASS) y la configuración del
# usuario se escribe en la carpeta de configuración del sistema (%APPDATA% en
# Windows, ~/.config en Linux), nunca dentro del bundle.


import os
import sys
from pathlib import Path


def congelado() -> bool:
    """True si el código corre dentro de un bundle de PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def _base_bundle() -> Path:
    """Carpeta raíz de datos del bundle (o la del módulo si no está congelado)."""
    if congelado():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def directorio_recursos() -> Path:
    """Carpeta de los PNG de la interfaz (app/recursos)."""
    if congelado():
        return _base_bundle() / "app" / "recursos"
    return Path(__file__).resolve().parent / "recursos"


def directorio_configuracion() -> Path:
    """Carpeta escribible para la configuración del usuario."""
    if congelado():
        if sys.platform == "win32":
            base = os.environ.get("APPDATA") or str(Path.home())
            return Path(base) / "Wall-E"
        # Linux/macOS: usar XDG_CONFIG_HOME o ~/.config
        base = os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")
        return Path(base) / "wall-e"
    return Path(__file__).resolve().parents[1] / "configuracion"


def ruta_controles() -> Path:
    """Ruta del JSON con el mapeo de teclas persistente."""
    return directorio_configuracion() / "controles.json"

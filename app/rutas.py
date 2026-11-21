# PyInstaller extrae los recursos en sys._MEIPASS; la configuración persiste fuera del bundle.


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
        base = os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")
        return Path(base) / "wall-e"
    return Path(__file__).resolve().parents[1] / "configuracion"


def ruta_controles() -> Path:
    """Ruta del JSON con el mapeo de teclas persistente."""
    return directorio_configuracion() / "controles.json"

# wall-e-robot/tests/test_arquitectura.py
# Kevin Gámez - 03/11/2026

"""Pruebas de arquitectura por imports.

Las capas bajas (núcleo, comunicación y lógica de widgets) no deben depender
de Tkinter, Pillow ni de capas superiores (pantallas, renderizado, main). Así
se pueden probar sin abrir una ventana y la GUI no se filtra hacia el modelo.
"""


import ast
from pathlib import Path

import pytest


RAIZ = Path(__file__).resolve().parents[1]

# Capas que deben ser independientes de la interfaz gráfica.
CAPAS_BAJAS = [
    RAIZ / "app" / "nucleo",
    RAIZ / "app" / "comunicacion",
    RAIZ / "app" / "widgets" / "logica",
]

# Módulos prohibidos desde una capa baja.
PROHIBIDOS = {
    "tkinter",
    "PIL",
    "app.main",
    "app.pantallas",
    "app.widgets.renderizado",
}


def _archivos_python(carpeta: Path):
    """Todos los .py de la carpeta, incluidos subpaquetes."""
    return sorted(carpeta.rglob("*.py"))


def _es_guardia_main(nodo) -> bool:
    """True para el bloque 'if __name__ == "__main__":' del cajón de pruebas."""
    if not isinstance(nodo, ast.If):
        return False
    prueba = nodo.test
    if not isinstance(prueba, ast.Compare):
        return False
    if not isinstance(prueba.left, ast.Name) or prueba.left.id != "__name__":
        return False
    if len(prueba.comparators) != 1:
        return False
    comparador = prueba.comparators[0]
    return isinstance(comparador, ast.Constant) and comparador.value == "__main__"


def _imports(archivo: Path):
    """Devuelve los módulos que se importan al cargar el archivo.

    Se ignora el cajón 'if __name__ == "__main__"', que puede usar Tkinter
    para una prueba manual sin afectar a la arquitectura de la capa.
    """
    arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
    nombres = []

    for nodo in arbol.body:
        if _es_guardia_main(nodo):
            continue
        for subnodo in ast.walk(nodo):
            if isinstance(subnodo, ast.Import):
                nombres.extend(alias.name for alias in subnodo.names)
            elif isinstance(subnodo, ast.ImportFrom) and subnodo.module:
                nombres.append(subnodo.module)
                nombres.extend(f"{subnodo.module}.{alias.name}"
                               for alias in subnodo.names)

    return nombres


def _es_prohibido(nombre: str) -> bool:
    """True si el módulo es de GUI o de una capa superior."""
    for prohibido in PROHIBIDOS:
        if nombre == prohibido or nombre.startswith(prohibido + "."):
            return True
    return False


@pytest.mark.parametrize("carpeta", CAPAS_BAJAS, ids=lambda r: r.name)
def test_capas_bajas_no_importan_gui_ni_capas_superiores(carpeta):
    """Ningún archivo de una capa baja puede importar Tkinter, PIL ni GUI."""
    violaciones = []

    for archivo in _archivos_python(carpeta):
        for nombre in _imports(archivo):
            if _es_prohibido(nombre):
                violaciones.append(f"{archivo.relative_to(RAIZ)} -> {nombre}")

    assert not violaciones, (
        "Imports prohibidos en capas bajas:\n  " + "\n  ".join(violaciones))


def test_control_teclado_no_importa_tkinter():
    """La lógica de teclado usa winfo_class() y no depende de tkinter."""
    archivo = RAIZ / "app" / "widgets" / "logica" / "control_teclado.py"
    imports = _imports(archivo)

    assert not any(nombre == "tkinter" or nombre.startswith("tkinter.")
                   for nombre in imports)

# wall-e-robot/tests/conftest.py
# Kevin Gámez - 16/10/2026

"""Configuración común de la suite de pruebas.

Garantiza que la raíz del proyecto esté en sys.path (para poder importar el
paquete 'app' tal cual, sin instalarlo) y ofrece utilidades compartidas a los
tests que necesitan dibujar con Tkinter.
"""


import sys
from pathlib import Path

import pytest


RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


@pytest.fixture
def raiz_tk():
    """Raíz de Tkinter retirada (sin ventana visible) que se cierra al final.

    Si el entorno no tiene un display disponible, el test se omite en vez de
    fallar.
    """

    tk = pytest.importorskip("tkinter")

    try:
        raiz = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tkinter sin display disponible: {error}")

    raiz.withdraw()
    yield raiz
    raiz.destroy()


@pytest.fixture
def contador():
    """Contador invocable: registra cuántas veces se le llamó (con argumentos)."""

    class Contador:
        def __init__(self):
            self.avisos = 0
            self.ultimo = None

        def __call__(self, *args, **kwargs):
            self.avisos += 1
            self.ultimo = (args, kwargs)

    return Contador()

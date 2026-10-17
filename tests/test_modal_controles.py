# wall-e-robot/tests/test_modal_controles.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.pantallas.modal_controles: captura de teclas y avisos.

El modal se monta sobre una raíz de Tkinter retirada; no se muestra ventana.
"""


import types

import pytest

from app.widgets.logica.mapeo_teclado import MapeoTeclado
from app.pantallas.modal_controles import ModalControles


def _tecla(keysym):
    """Evento de teclado mínimo."""
    return types.SimpleNamespace(keysym=keysym)


@pytest.fixture
def modal(raiz_tk):
    """Modal con un mapeo de fábrica y un registro de cambios notificados."""
    cambios = []
    instancia = ModalControles(raiz_tk, MapeoTeclado(),
                               on_cambio=lambda: cambios.append(True))
    raiz_tk.update()
    yield instancia, cambios
    instancia.ventana.destroy()


def test_filas_muestran_las_teclas_de_fabrica(modal):
    """La fila de ARRIBA muestra la flecha por defecto."""
    instancia, _ = modal
    instancia._refrescar_filas()
    btn_arriba, _ = instancia._filas["arriba"]
    assert btn_arriba.cget("text") == "\u2191"


def test_captura_asigna_y_notifica(modal):
    """Capturar una tecla la asigna a la acción y notifica el cambio."""
    instancia, cambios = modal

    instancia._empezar_captura("arriba")
    assert instancia._capturando == "arriba"

    instancia._al_tecla(_tecla("U"))

    assert instancia.mapeo.tecla_de("arriba") == "U"
    assert len(cambios) == 1
    assert instancia._capturando is None


def test_escape_cancela_sin_modificar(modal):
    """Esc sale del modo captura sin tocar el mapeo."""
    instancia, _ = modal
    original = instancia.mapeo.tecla_de("abajo")

    instancia._empezar_captura("abajo")
    instancia._al_tecla(_tecla("Escape"))

    assert instancia.mapeo.tecla_de("abajo") == original


def test_modificadores_no_se_asignan(modal):
    """Un modificador solo no se asigna; la siguiente tecla sí."""
    instancia, _ = modal
    original = instancia.mapeo.tecla_de("abajo")

    instancia._empezar_captura("abajo")
    instancia._al_tecla(_tecla("Shift_L"))
    assert instancia.mapeo.tecla_de("abajo") == original

    instancia._al_tecla(_tecla("v"))
    assert instancia.mapeo.tecla_de("abajo") == "v"


def test_tecla_robada_avisa_quien_la_perdio(modal):
    """Asignar una tecla ya usada avisa que otra acción la perdió."""
    instancia, _ = modal

    instancia._empezar_captura("abajo")
    instancia._al_tecla(_tecla("q"))  # 'q' era de cuello_mas

    assert instancia.mapeo.tecla_de("abajo") == "q"
    assert instancia.mapeo.tecla_de("cuello_mas") is None
    assert "la perdi\u00f3" in instancia.lbl_estado.cget("text")


def test_limpiar_y_restaurar(modal):
    """Limpiar deja sin tecla y restaurar vuelve a fábrica."""
    instancia, _ = modal

    instancia._limpiar("abajo")
    assert instancia.mapeo.tecla_de("abajo") is None

    instancia._restaurar()
    assert instancia.mapeo.tecla_de("abajo") == "Down"


def test_tecla_sin_captura_no_hace_nada(modal):
    """Si no hay captura activa, una tecla se ignora."""
    instancia, cambios = modal
    original = instancia.mapeo._mapa.copy()

    instancia._al_tecla(_tecla("x"))

    assert instancia.mapeo._mapa == original
    assert cambios == []


def test_accion_inexistente_lanza_keyerror(modal):
    """_accion lanza KeyError para una acción desconocida."""
    instancia, _ = modal
    with pytest.raises(KeyError):
        instancia._accion("no_existe")

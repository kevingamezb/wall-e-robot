# wall-e-robot/tests/test_base_render.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.renderizado.base_render: helpers de dibujo HUD.

Usan una raíz de Tkinter retirada (sin ventana) y un Canvas real, de modo que
los helpers se ejecutan tal cual sin abrir ninguna interfaz.
"""


import pytest

from app.nucleo.paleta import Paleta
from app.widgets.renderizado.base_render import (
    RenderizadorBase, anillo_con_halo, banda_gradiente, corchetes_hud,
    fulgor_radial, interpolar_color, rectangulo_redondeado, scanlines, texto_hud,
)


@pytest.fixture
def lienzo(raiz_tk):
    """Canvas de Tkinter asociado a la raíz retirada."""
    import tkinter as tk
    canvas = tk.Canvas(raiz_tk, width=320, height=220, bg=Paleta.FONDO_WIDGET)
    canvas.pack()
    return canvas


def test_rectangulo_redondeado_devuelve_id(lienzo):
    """El rectángulo redondeado devuelve el id de un ítem válido."""
    rid = rectangulo_redondeado(lienzo, 10, 10, 310, 210, Paleta.RADIO_TARJETA,
                                outline=Paleta.BORDE_SUAVE, width=1)
    assert isinstance(rid, int) and rid > 0


@pytest.mark.parametrize(
    "t, esperado",
    [
        (0.0, "#000000"),
        (1.0, "#ffffff"),
        (0.5, "#808080"),
    ],
)
def test_interpolar_color_extremos_y_medio(t, esperado):
    """t=0 da el color inicial, t=1 el final y t=0.5 el gris medio."""
    assert interpolar_color("#000000", "#ffffff", t) == esperado


@pytest.mark.parametrize("t, esperado", [(-1.0, "#000000"), (2.0, "#ffffff")])
def test_interpolar_color_recorta_t(t, esperado):
    """Un t fuera de [0, 1] se recorta al extremo más cercano."""
    assert interpolar_color("#000000", "#ffffff", t) == esperado


def test_fulgor_radial_crea_una_capa_por_nivel(lienzo):
    """fulgor_radial crea tantos anillos como 'capas'."""
    ids = fulgor_radial(lienzo, 60, 170, 24, Paleta.AXIOM_CYAN, capas=4)
    assert len(ids) == 4


def test_anillo_con_halo_crea_una_capa_por_nivel(lienzo):
    """anillo_con_halo crea tantos aros como 'capas'."""
    ids = anillo_con_halo(lienzo, 150, 170, 8, 2, Paleta.NARANJA, capas=3)
    assert len(ids) == 3


def test_banda_gradiente_ambas_orientaciones(lienzo):
    """Cada orientación crea sus tiras."""
    vertical = banda_gradiente(lienzo, 200, 150, 230, 200,
                               Paleta.AXIOM_CYAN, Paleta.FONDO_WIDGET, tiras=8)
    horizontal = banda_gradiente(lienzo, 240, 150, 310, 170,
                                 Paleta.DORADO, Paleta.FONDO_WIDGET, tiras=8,
                                 orientacion="horizontal")
    assert len(vertical) == 8
    assert len(horizontal) == 8


def test_corchetes_hud_por_niveles(lienzo):
    """nivel=2 crea 2 x 4 esquinas x 1 polilínea = 8 ítems."""
    ids = corchetes_hud(lienzo, 20, 20, 300, 130, largo=14, nivel=2)
    assert len(ids) == 8


def test_scanlines_cuenta_lineas(lienzo):
    """separacion=4 sobre 110 px de alto produce 28 líneas."""
    ids = scanlines(lienzo, 20, 20, 300, 130, separacion=4)
    assert len(ids) == 28


def test_texto_hud_devuelve_id(lienzo):
    """El texto HUD devuelve el id de un ítem válido."""
    tid = texto_hud(lienzo, 20, 140, "MODO MANUAL", tamano=9)
    assert isinstance(tid, int) and tid > 0


def test_renderizador_base_cachea_ids(lienzo):
    """_primera_vez crea el ítem una sola vez y reutiliza su id."""
    render = RenderizadorBase(lienzo)
    creados = []

    def creador():
        creados.append(1)
        return lienzo.create_oval(0, 0, 10, 10)

    primero = render._primera_vez("aro", creador)
    segundo = render._primera_vez("aro", creador)

    assert primero == segundo
    assert len(creados) == 1


def test_renderizador_base_detecta_cambios():
    """_hay_cambio devuelve True la primera vez y solo si el valor cambia."""
    render = RenderizadorBase(None)

    assert render._hay_cambio("x", 1) is True
    assert render._hay_cambio("x", 1) is False
    assert render._hay_cambio("x", 2) is True

# wall-e-robot/tests/test_recoloreo.py
# Kevin Gámez - 18/10/2026

"""Pruebas de app.widgets.renderizado.recoloreo.

Cubren las matemáticas de color (hex <-> RGB e interpolación) y el tinte de
imágenes RGBA conservando el alfa. Solo usan Pillow: no necesitan display.
"""


import pytest
from PIL import Image

from app.nucleo.paleta import Paleta
from app.widgets.renderizado.recoloreo import Recoloreo


@pytest.fixture
def muestra():
    """PNG de 20x10 al vuelo: mitad izquierda opaca blanca, resto transparente."""
    imagen = Image.new("RGBA", (20, 10), (255, 255, 255, 0))
    for x in range(10):
        for y in range(10):
            imagen.putpixel((x, y), (255, 255, 255, 255))
    return imagen


# ------------------------------------------------------- conversiones hex<->rgb

def test_a_rgb_devuelve_tupla_de_canals():
    assert Recoloreo.a_rgb("#cba135") == (0xCB, 0xA1, 0x35)


def test_a_hex_devuelve_hexadecimal():
    assert Recoloreo.a_hex((0xCB, 0xA1, 0x35)) == "#cba135"


def test_ida_y_vuelta_sin_perdida():
    assert Recoloreo.a_hex(Recoloreo.a_rgb(Paleta.ROJO)) == Paleta.ROJO


# -------------------------------------------------------------- interpolación

@pytest.mark.parametrize(
    "t, esperado",
    [
        (0.0, "#000000"),
        (1.0, "#ffffff"),
        (0.5, "#808080"),
    ],
)
def test_interpolar_extremos_y_medio(t, esperado):
    """t=0 da el color inicial, t=1 el final y t=0.5 el gris medio."""
    assert Recoloreo.interpolar("#000000", "#ffffff", t) == esperado


@pytest.mark.parametrize("t, esperado", [(-1.0, "#000000"), (2.0, "#ffffff")])
def test_interpolar_recorta_t(t, esperado):
    """Un t fuera de [0, 1] se recorta al extremo más cercano."""
    assert Recoloreo.interpolar("#000000", "#ffffff", t) == esperado


# ------------------------------------------------------------------ tinte

def test_tenido_conserva_alfa(muestra):
    """El tinte pinta el dibujo opaco pero deja transparente el fondo."""
    tenida = Recoloreo.tenir(muestra, Paleta.DORADO)

    assert tenida.size == (20, 10)
    assert tenida.getpixel((2, 2)) == Recoloreo.a_rgb(Paleta.DORADO) + (255,)
    assert tenida.getpixel((15, 5))[3] == 0


def test_tenido_no_modifica_la_original(muestra):
    """tenir devuelve una copia: la imagen de entrada queda intacta."""
    Recoloreo.tenir(muestra, Paleta.ROJO)
    assert muestra.getpixel((2, 2)) == (255, 255, 255, 255)


def test_tenido_convierte_a_rgba_si_hace_falta():
    """Una imagen sin canal alfa se tiñe como opaca."""
    rgb = Image.new("RGB", (4, 4), (255, 255, 255))
    tenida = Recoloreo.tenir(rgb, Paleta.AXIOM_CYAN)

    assert tenida.mode == "RGBA"
    assert tenida.getpixel((0, 0))[:3] == Recoloreo.a_rgb(Paleta.AXIOM_CYAN)

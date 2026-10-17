# wall-e-robot/tests/test_carga_recursos.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.renderizado.carga_recursos.

Se usa un directorio temporal con un PNG generado al vuelo y una raíz de
Tkinter retirada, para no depender de que los assets reales estén exportados.
"""


import pytest
from PIL import Image

from app.nucleo.paleta import Paleta
from app.widgets.renderizado import carga_recursos


@pytest.fixture
def recursos(tmp_path, monkeypatch):
    """Redirige la carpeta de assets a un temp dir con un PNG de prueba.

    El PNG es de 20x10: la mitad izquierda opaca blanca y el resto transparente.
    """

    monkeypatch.setattr(carga_recursos, "DIRECTORIO", tmp_path)
    monkeypatch.setattr(carga_recursos, "_CACHE", {})

    muestra = Image.new("RGBA", (20, 10), (255, 255, 255, 0))
    for x in range(10):
        for y in range(10):
            muestra.putpixel((x, y), (255, 255, 255, 255))
    muestra.save(tmp_path / "prueba.png")

    return tmp_path


def test_existe_distingue_presente_de_ausente(recursos):
    """existe() reconoce el asset generado y descarta los que no están."""
    assert carga_recursos.existe("prueba") is True
    assert carga_recursos.existe("no_existe") is False


def test_tenido_conserva_alfa(recursos):
    """El tinte pinta el dibujo opaco pero deja transparente el fondo."""
    with Image.open(recursos / "prueba.png") as abierta:
        imagen = abierta.convert("RGBA")

    tenida = carga_recursos._tenido(imagen, Paleta.DORADO)

    assert tenida.size == (20, 10)
    assert tenida.getpixel((2, 2)) == (0xcb, 0xa1, 0x35, 255)
    assert tenida.getpixel((15, 5))[3] == 0


def test_cargar_escala_por_alto_conservando_aspecto(recursos, raiz_tk):
    """cargar() respeta el alto y conserva el aspecto (20x10 -> 60x30)."""
    foto = carga_recursos.cargar("prueba", Paleta.DORADO, 30)
    assert foto.height() == 30
    assert foto.width() == 60


def test_cargar_reutiliza_cache(recursos, raiz_tk):
    """El mismo pedido reutiliza la misma PhotoImage."""
    foto = carga_recursos.cargar("prueba", Paleta.DORADO, 30)
    assert carga_recursos.cargar("prueba", Paleta.DORADO, 30) is foto


def test_cargar_espejo_es_otra_foto(recursos, raiz_tk):
    """El espejo produce una PhotoImage distinta."""
    foto = carga_recursos.cargar("prueba", Paleta.DORADO, 30)
    foto_espejo = carga_recursos.cargar("prueba", Paleta.DORADO, 30, espejo=True)
    assert foto_espejo is not foto

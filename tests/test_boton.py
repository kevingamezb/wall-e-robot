# wall-e-robot/tests/test_boton.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.boton: estado y notificación del botón."""


from app.nucleo.paleta import Paleta
from app.widgets.logica.boton import Boton


def test_estado_inicial(contador):
    """Un botón nuevo no está presionado ni en hover."""
    b = Boton("Abrir mano")
    b.suscribir(contador)

    assert b.texto == "Abrir mano"
    assert b.presionado is False
    assert b.en_hover is False
    assert b.color_fondo == Paleta.FONDO_APP
    assert contador.avisos == 0


def test_presionar_notifica_una_vez(contador):
    """presionar() avisa a los suscriptores y cambia el color."""
    b = Boton("Abrir mano")
    b.suscribir(contador)

    b.presionar()

    assert contador.avisos == 1
    assert b.presionado is True
    assert b.color_fondo == Paleta.DORADO


def test_multiples_suscriptores_reciben_el_aviso():
    """Todos los suscriptores son notificados en cada presionar()."""
    b = Boton("Abrir mano")
    c1, c2 = _ContadorLocal(), _ContadorLocal()
    b.suscribir(c1)
    b.suscribir(c2)

    b.presionar()

    assert c1.avisos == 1
    assert c2.avisos == 1


def test_soltar_no_notifica(contador):
    """soltar() solo cambia el estado; no dispara avisos."""
    b = Boton("Abrir mano")
    b.suscribir(contador)

    b.presionar()
    b.soltar()

    assert b.presionado is False
    assert b.color_fondo == Paleta.FONDO_APP
    assert contador.avisos == 1


def test_presiones_repetidas_suman_avisos(contador):
    """Cada llamada a presionar() cuenta, aunque ya estuviera presionado."""
    b = Boton("Abrir mano")
    b.suscribir(contador)

    for _ in range(3):
        b.presionar()

    assert contador.avisos == 3


def test_hover(contador):
    """entrar_hover() cambia el color pero no notifica."""
    b = Boton("Abrir mano")
    b.suscribir(contador)

    b.entrar_hover()

    assert b.en_hover is True
    assert b.color_fondo == Paleta.DORADO_DIM
    assert contador.avisos == 0


def test_presionado_tiene_prioridad_sobre_hover():
    """En hover + presionado, el color vuelve a ser DORADO."""
    b = Boton("Abrir mano")
    b.entrar_hover()
    b.presionar()

    assert b.color_fondo == Paleta.DORADO


def test_salir_hover():
    """salir_hover() devuelve el botón a FONDO_APP."""
    b = Boton("Abrir mano")
    b.entrar_hover()
    b.salir_hover()

    assert b.en_hover is False
    assert b.color_fondo == Paleta.FONDO_APP


class _ContadorLocal:
    """Suscriptor mínimo para las pruebas que necesitan varios contadores."""

    def __init__(self):
        self.avisos = 0

    def __call__(self):
        self.avisos += 1

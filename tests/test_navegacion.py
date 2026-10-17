# wall-e-robot/tests/test_navegacion.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.navegacion: maniobra, símbolo y color."""


import pytest

from app.nucleo.estado import EstadoRobot, Maniobra, Modo
from app.nucleo.paleta import Paleta
from app.widgets.logica.navegacion import Navegacion, SIMBOLOS


@pytest.fixture
def nav():
    """Panel de navegación sobre un estado nuevo."""
    return Navegacion(EstadoRobot())


def test_automatico_recto(nav):
    """En automático recto, la etiqueta es RECTO y el color cian."""
    assert not nav.en_manual
    assert nav.maniobra == Maniobra.RECTO
    assert nav.etiqueta == "RECTO"
    assert nav.simbolo == SIMBOLOS[Maniobra.RECTO]
    assert nav.color == Paleta.AXIOM_CYAN


def test_automatico_alto_en_rojo(nav):
    """La maniobra ALTO se resalta en rojo."""
    nav.estado.navegacion = Maniobra.ALTO
    assert nav.etiqueta == "ALTO"
    assert nav.color == Paleta.ROJO


@pytest.mark.parametrize(
    "maniobra, etiqueta",
    [
        (Maniobra.RECTO,     "RECTO"),
        (Maniobra.IZQUIERDA, "IZQUIERDA"),
        (Maniobra.DERECHA,   "DERECHA"),
        (Maniobra.ALTO,      "ALTO"),
    ],
)
def test_etiquetas_en_automatico(nav, maniobra, etiqueta):
    """Cada maniobra expone su etiqueta y su símbolo."""
    nav.estado.navegacion = maniobra
    assert nav.etiqueta == etiqueta
    assert nav.simbolo == SIMBOLOS[maniobra]


def test_manual_manda_el_operador(nav):
    """En manual, la navegación muestra MANUAL en naranja."""
    nav.estado.modo = Modo.MANUAL
    assert nav.en_manual
    assert nav.etiqueta == "MANUAL"
    assert nav.color == Paleta.NARANJA
    assert nav.simbolo == "\u2014"

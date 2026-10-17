# wall-e-robot/tests/test_barras_consumo.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.barras_consumo: fracción, barras y color."""


import pytest

from app.nucleo.estado import EstadoRobot
from app.nucleo.paleta import Paleta
from app.widgets.logica.barras_consumo import BarrasConsumo


@pytest.fixture
def barras():
    """Barras de consumo sobre un estado nuevo."""
    return BarrasConsumo(EstadoRobot())


@pytest.mark.parametrize(
    "consumo, barritas, color",
    [
        (0.0,  0,  Paleta.GRIS),
        (4.2,  3,  Paleta.DORADO),
        (8.0,  5,  Paleta.NARANJA),
        (15.0, 10, Paleta.ROJO),
    ],
)
def test_consumo_sobre_quince_watts(barras, consumo, barritas, color):
    """Con máximo 15 W, el consumo se reparte en 10 barritas con umbral invertido."""
    barras.estado.consumo_watts = consumo
    barras.estado.max_consumo_watts = 15.0

    assert barras.barritas_encendidas == barritas
    assert barras.color == color


def test_fraccion_media(barras):
    """La fracción es consumo / máximo."""
    barras.estado.consumo_watts = 4.2
    barras.estado.max_consumo_watts = 15.0
    assert abs(barras.fraccion - 0.28) < 0.001


@pytest.mark.parametrize("maximo", [0.0, -1.0])
def test_maximo_no_positivo_no_divide(barras, maximo):
    """Si el máximo no es positivo, la fracción es 0 (sin división por cero)."""
    barras.estado.consumo_watts = 5.0
    barras.estado.max_consumo_watts = maximo

    assert barras.fraccion == 0.0
    assert barras.barritas_encendidas == 0
    assert barras.color == Paleta.GRIS


def test_etiqueta_watts(barras):
    """La etiqueta muestra el consumo con un decimal y unidad."""
    barras.estado.consumo_watts = 3.456
    assert barras.etiqueta_watts == "3.5 W"

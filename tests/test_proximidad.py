# wall-e-robot/tests/test_proximidad.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.proximidad: cercanía, obstáculo y etiqueta."""


import pytest

from app.nucleo.estado import EstadoRobot
from app.widgets.logica.proximidad import Proximidad, RANGO_MAX_CM


@pytest.fixture
def prox():
    """Medidor de proximidad sobre un estado nuevo."""
    return Proximidad(EstadoRobot())


def test_sin_lectura(prox):
    """Sin distancia, no hay obstáculo ni cercanía."""
    assert not prox.hay_obstaculo
    assert prox.cercania == 0.0
    assert prox.etiqueta == "SIN LECTURA"


@pytest.mark.parametrize(
    "distancia, cercania, etiqueta",
    [
        (150.0, 0.25, "150 cm"),
        (100.0, 0.5,  "100 cm"),
        (0.0,   1.0,  "0 cm"),
        (RANGO_MAX_CM, 0.0, f"{RANGO_MAX_CM} cm"),
    ],
)
def test_cercania_segun_distancia(prox, distancia, cercania, etiqueta):
    """La cercanía se mide de 0 (lejos) a 1 (pegado)."""
    prox.estado.distancia_obstaculo_cm = distancia
    assert prox.hay_obstaculo
    assert abs(prox.cercania - cercania) < 0.001
    assert prox.etiqueta == etiqueta


def test_fuera_de_rango_se_recorta(prox):
    """Más allá del rango máximo, la cercanía se satura en 0."""
    prox.estado.distancia_obstaculo_cm = 250.0
    assert prox.cercania == 0.0


def test_distancia_negativa_se_recorta(prox):
    """Una lectura negativa se trata como 0 (máxima cercanía)."""
    prox.estado.distancia_obstaculo_cm = -5.0
    assert prox.cercania == 1.0


def test_distancia_cm_reproduce_el_estado(prox):
    """La propiedad distancia_cm delega en el estado."""
    prox.estado.distancia_obstaculo_cm = 77.0
    assert prox.distancia_cm == 77.0

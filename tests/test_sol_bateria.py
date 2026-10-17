# wall-e-robot/tests/test_sol_bateria.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.sol_bateria: rayos, color y etiqueta."""


import pytest

from app.nucleo.estado import EstadoRobot
from app.nucleo.paleta import Paleta
from app.widgets.logica.sol_bateria import SolBateria


@pytest.fixture
def sol():
    """Sol de batería sobre un estado nuevo."""
    return SolBateria(EstadoRobot())


@pytest.mark.parametrize(
    "bateria, rayos, color, etiqueta",
    [
        (1.0, 12, Paleta.DORADO,  "12/12"),
        (0.5,  6, Paleta.NARANJA, "6/12"),
        (0.2,  2, Paleta.ROJO,    "2/12"),
    ],
)
def test_niveles_sin_cargar(sol, bateria, rayos, color, etiqueta):
    """La fracción de batería se traduce a rayos, color y etiqueta."""
    sol.estado.bateria = bateria
    assert sol.rayos_encendidos == rayos
    assert sol.color == color
    assert sol.etiqueta == etiqueta


@pytest.mark.parametrize(
    "rayos, color",
    [
        (0, Paleta.GRIS),
        (4, Paleta.ROJO),
        (5, Paleta.NARANJA),
        (7, Paleta.NARANJA),
        (8, Paleta.DORADO),
        (12, Paleta.DORADO),
    ],
)
def test_umbrales_de_color(sol, rayos, color):
    """Los cortes de color son 0 (gris), <=4 (rojo), <=7 (naranja), resto dorado."""
    sol.estado.bateria = rayos / SolBateria.TOTAL_RAYOS
    assert sol.rayos_encendidos == rayos
    assert sol.color == color


def test_cargando_muestra_todos_los_rayos(sol):
    """Cargando, el sol se ve lleno y en verde lima."""
    sol.estado.bateria = 0.2
    sol.estado.cargando = True

    assert sol.rayos_encendidos == SolBateria.TOTAL_RAYOS
    assert sol.color == Paleta.VERDE_LIMA
    assert sol.etiqueta == "cargando"


def test_tiempo_restante_se_delega_al_estado(sol):
    """tiempo_restante_min reproduce el valor del estado."""
    sol.estado.tiempo_restante_min = 42
    assert sol.tiempo_restante_min == 42

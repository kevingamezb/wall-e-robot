# wall-e-robot/tests/test_sol_bateria.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.sol_bateria: rayos, color y etiqueta."""


import pytest

from app.nucleo.estado import EstadoRobot
from app.nucleo.paleta import Paleta
from app.widgets.logica.sol_bateria import SolBateria


@pytest.fixture
def sol():
    """Sol de batería con conexión activa (hay lectura del robot)."""
    estado = EstadoRobot()
    estado.conexion_activa = True
    return SolBateria(estado)


@pytest.mark.parametrize(
    "bateria, rayos, color, etiqueta",
    [
        (1.0, 8, Paleta.DORADO,  "8 / 8"),
        (0.5, 4, Paleta.NARANJA, "4 / 8"),
        (0.2, 2, Paleta.ROJO,    "2 / 8"),
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
        (1, Paleta.ROJO),
        (2, Paleta.ROJO),
        (3, Paleta.NARANJA),
        (5, Paleta.NARANJA),
        (6, Paleta.DORADO),
        (8, Paleta.DORADO),
    ],
)
def test_umbrales_de_color(sol, rayos, color):
    """Los cortes de color son 0 (gris), 1-2 (rojo), 3-5 (naranja) y 6-8 (dorado)."""
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


def test_sin_datos_sol_lleno_pero_gris():
    """Sin conexión no hay lectura: el sol se ve lleno, en gris y dice 'sin datos'."""
    estado = EstadoRobot()
    estado.conexion_activa = False
    estado.bateria = 0.2
    sol = SolBateria(estado)

    assert sol.sin_datos is True
    assert sol.rayos_encendidos == SolBateria.TOTAL_RAYOS
    assert sol.color == Paleta.GRIS
    assert sol.etiqueta == "sin datos"


def test_sin_datos_manda_sobre_cargando():
    """Aunque 'cargando' quedara pegado, sin conexión gana 'sin datos'."""
    estado = EstadoRobot()
    estado.conexion_activa = False
    estado.cargando = True
    sol = SolBateria(estado)

    assert sol.color == Paleta.GRIS
    assert sol.etiqueta == "sin datos"

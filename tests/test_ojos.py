# wall-e-robot/tests/test_ojos.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.ojos: prioridad de las expresiones."""


import pytest

from app.nucleo.estado import EstadoRobot, Modo
from app.nucleo.paleta import Paleta
from app.widgets.logica.ojos import ExpresionOjos, Ojos


def _ojos(conexion=True, modo=Modo.AUTOMATICO, hay_error=False, distancia=80.0):
    estado = EstadoRobot()
    estado.conexion_activa = conexion
    estado.modo = modo
    estado.hay_error = hay_error
    estado.distancia_obstaculo_cm = distancia
    return Ojos(estado)


@pytest.mark.parametrize(
    "conexion, modo, hay_error, distancia, esperado, color",
    [
        (True,  Modo.AUTOMATICO, False, 80.0, ExpresionOjos.NORMAL,    Paleta.DORADO),
        (True,  Modo.MANUAL,     False,  5.0, ExpresionOjos.MANUAL,    Paleta.NARANJA),
        (True,  Modo.AUTOMATICO, False,  8.0, ExpresionOjos.OBSTACULO, Paleta.ROJO),
        (False, Modo.AUTOMATICO, False, 80.0, ExpresionOjos.SIN_DATOS, Paleta.GRIS),
        (True,  Modo.AUTOMATICO, True,  80.0, ExpresionOjos.ERROR,     Paleta.ROJO),
        (True,  Modo.MANUAL,     True,   3.0, ExpresionOjos.ERROR,     Paleta.ROJO),
        (False, Modo.AUTOMATICO, True,   3.0, ExpresionOjos.SIN_DATOS, Paleta.GRIS),
        (True,  Modo.AUTOMATICO, False,  None, ExpresionOjos.NORMAL,   Paleta.DORADO),
    ],
)
def test_expresion_y_color(conexion, modo, hay_error, distancia, esperado, color):
    """La prioridad es: sin conexión > error > manual > obstáculo > normal."""
    ojos = _ojos(conexion, modo, hay_error, distancia)
    assert ojos.expresion == esperado
    assert ojos.color == color


def test_obstaculo_justo_en_el_umbral_no_activa():
    """A 15.0 cm exactos todavía no hay obstáculo (el umbral es estricto)."""
    ojos = _ojos(distancia=15.0)
    assert ojos.expresion == ExpresionOjos.NORMAL


def test_descripcion_es_el_valor_de_la_expresion():
    """descripcion expone el texto legible de la expresión."""
    assert _ojos().descripcion == "normal"

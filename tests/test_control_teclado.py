# wall-e-robot/tests/test_control_teclado.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.control_teclado: eventos de Tk -> gamepad.

Se simulan los eventos de teclado con objetos mínimos (SimpleNamespace) y una
raíz de Tkinter retirada, sin abrir ninguna ventana.
"""


import types

import pytest

from app.nucleo.estado import EstadoRobot
from app.widgets.logica.control_teclado import ControlTeclado
from app.widgets.logica.gamepad import Gamepad
from app.widgets.logica.mapeo_teclado import MapeoTeclado, accion_por_id


def _tecla(keysym):
    """Un 'evento' de teclado mínimo (sin abrir ventana)."""
    return types.SimpleNamespace(keysym=keysym)


@pytest.fixture
def control(raiz_tk):
    """Control de teclado con un gamepad que acumula los comandos emitidos."""
    gamepad = Gamepad(EstadoRobot())
    comandos = []
    gamepad.suscribir_comando(comandos.append)
    return ControlTeclado(raiz_tk, MapeoTeclado(), gamepad), comandos


def test_flecha_emite_motor_y_auto_repite(control):
    """Una flecha enciende el botón y el auto-repetido re-emite el comando."""
    ctl, comandos = control

    ctl._al_presionar(_tecla("Up"))
    assert comandos[-1] == {"tipo": "motor", "direccion": "arriba"}
    assert ctl.gamepad.direccion_arriba.presionado

    ctl._al_presionar(_tecla("Up"))  # simula auto-repetido del teclado
    assert len(comandos) >= 2

    ctl._al_soltar(_tecla("Up"))
    assert not ctl.gamepad.direccion_arriba.presionado


def test_discreta_dispara_una_sola_vez(control):
    """Una acción discreta (reposo) emite un único comando aunque se auto-repita la tecla."""
    ctl, comandos = control
    n = len(comandos)

    ctl._al_presionar(_tecla("r"))
    ctl._al_presionar(_tecla("r"))

    assert len(comandos) == n + 1
    assert comandos[-1]["tipo"] == "multi"
    ctl._al_soltar(_tecla("r"))


def test_eje_avanza_paso_a_paso(control):
    """Una tecla de eje avanza por pasos mientras se sostiene."""
    ctl, comandos = control
    n = len(comandos)

    ctl._al_presionar(_tecla("q"))  # cuello_mas
    assert len(comandos) == n + 1
    assert comandos[-1] == {"tipo": "servo", "servo": "cuello", "angulo": 5}
    assert ctl.gamepad.cuello.posicion == 5

    ctl._aplicar_paso(accion_por_id("cuello_mas"))
    assert ctl.gamepad.cuello.posicion == 10

    ctl._al_soltar(_tecla("q"))
    assert "q" not in ctl._temporizadores
    ctl.raiz.update()
    assert ctl.gamepad.cuello.posicion == 10


def test_reposo_dispara_multi(control):
    """La tecla de reposo dispara un comando multi."""
    ctl, comandos = control
    n = len(comandos)

    ctl._al_presionar(_tecla("r"))
    ctl._al_soltar(_tecla("r"))

    assert len(comandos) == n + 1
    assert comandos[-1]["tipo"] == "multi"


@pytest.mark.parametrize("keysym", ["F12", "Shift_L"])
def test_teclas_ajenas_se_ignoran(control, keysym):
    """Las teclas sin mapear (y los modificadores) no generan comandos."""
    ctl, comandos = control
    n = len(comandos)

    ctl._al_presionar(_tecla(keysym))
    ctl._al_soltar(_tecla(keysym))

    assert len(comandos) == n


def test_presiones_simultaneas_independientes(control):
    """Cada tecla mantiene su propio estado al soltar la otra."""
    ctl, _ = control

    ctl._al_presionar(_tecla("Up"))
    ctl._al_presionar(_tecla("Left"))
    ctl._al_soltar(_tecla("Left"))

    assert ctl.gamepad.direccion_arriba.presionado
    ctl._al_soltar(_tecla("Up"))
    assert not ctl.gamepad.direccion_arriba.presionado


def test_limpiar_estado_al_perder_foco(control):
    """limpiar_estado suelta todos los botones y vacía las teclas pulsadas."""
    ctl, _ = control

    ctl._al_presionar(_tecla("r"))
    ctl.limpiar_estado()

    assert not ctl.gamepad.reposo.presionado
    assert not ctl._pulsadas


def test_auto_repite_del_eje_avanza(control, monkeypatch):
    """El callback de auto-repetición vuelve a avanzar el eje mientras se sostiene."""
    ctl, _ = control
    programados = []
    monkeypatch.setattr(ctl.raiz, "after",
                        lambda _ms, fn: programados.append(fn) or len(programados))
    monkeypatch.setattr(ctl.raiz, "after_cancel", lambda _id: None)

    ctl._al_presionar(_tecla("q"))
    assert ctl.gamepad.cuello.posicion == 5
    assert len(programados) == 1

    programados[0]()  # dispara el auto-repetido
    assert ctl.gamepad.cuello.posicion == 10

    ctl._al_soltar(_tecla("q"))
    assert "q" not in ctl._temporizadores

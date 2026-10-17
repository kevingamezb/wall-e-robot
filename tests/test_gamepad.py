# wall-e-robot/tests/test_gamepad.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.gamepad: comandos de motores y servos."""


import pytest

from app.nucleo.estado import EstadoRobot
from app.widgets.logica.gamepad import Gamepad


@pytest.fixture
def gamepad():
    """Gamepad sobre un estado nuevo, con un registro de los comandos emitidos."""
    estado = EstadoRobot()
    gp = Gamepad(estado)
    comandos = []
    gp.suscribir_comando(comandos.append)
    return gp, comandos


def test_direccion_motor(gamepad):
    """Pulsar una flecha emite un comando de motor."""
    gp, comandos = gamepad
    gp.direccion_arriba.presionar()
    assert comandos[-1] == {"tipo": "motor", "direccion": "arriba"}


def test_servo_dentro_de_rango(gamepad):
    """Mover un deslizador dentro de rango emite un comando de servo."""
    gp, comandos = gamepad
    gp.cuello.mover(30)
    assert comandos[-1] == {"tipo": "servo", "servo": "cuello", "angulo": 30}


def test_servo_fuera_de_rango_no_emite(gamepad):
    """Un movimiento fuera de rango no genera comando."""
    gp, comandos = gamepad
    gp.cuello.mover(30)
    gp.cuello.mover(500)
    assert len(comandos) == 1


def test_reposo_centra_los_servos(gamepad):
    """Reposo emite los tres servos a 0 y reinicia las posiciones."""
    gp, comandos = gamepad
    gp.cuello.mover(30)
    gp.hombro_izquierdo.mover(-20)
    gp.hombro_derecho.mover(20)

    gp.reposo.presionar()

    reposo = comandos[-1]
    assert reposo["tipo"] == "multi"
    assert all(c["tipo"] == "servo" and c["angulo"] == 0 for c in reposo["comandos"])
    assert [c["servo"] for c in reposo["comandos"]] == [
        "cuello", "hombro_izquierdo", "hombro_derecho"]
    assert gp.cuello.posicion == 0
    assert gp.hombro_izquierdo.posicion == 0
    assert gp.hombro_derecho.posicion == 0


def test_deshabilitado_descarta_comandos(gamepad):
    """Sin conexión, ningún comando sale del gamepad."""
    gp, comandos = gamepad
    gp.habilitar(False)

    gp.direccion_arriba.presionar()
    gp.cuello.mover(10)

    assert comandos == []


def test_rehabilitado_vuelve_a_emitir(gamepad):
    """Al reconectar, el gamepad vuelve a emitir comandos."""
    gp, comandos = gamepad
    gp.habilitar(False)
    gp.direccion_arriba.presionar()

    gp.habilitar(True)
    gp.direccion_abajo.presionar()

    assert comandos[-1] == {"tipo": "motor", "direccion": "abajo"}

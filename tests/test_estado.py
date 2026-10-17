# wall-e-robot/tests/test_estado.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.nucleo.estado: caja de estado y buffer del logger."""


import pytest

from app.nucleo.estado import (
    EstadoRobot, Logger, Modo, Maniobra, NivelConexion, NivelLog, PosicionServos,
)


def test_estado_valores_por_defecto():
    """El estado arranca en automático, batería llena y sin enlace."""
    estado = EstadoRobot()
    assert estado.modo == Modo.AUTOMATICO
    assert estado.bateria == 1.0
    assert estado.conexion_activa is False
    assert estado.nivel_conexion == NivelConexion.NULA
    assert estado.distancia_obstaculo_cm is None
    assert estado.navegacion == Maniobra.RECTO
    assert isinstance(estado.posiciones_servos, PosicionServos)


def test_estado_arranca_sin_enlace():
    """nivel_conexion nace en NULA porque aún no llegó ningún estado."""
    assert EstadoRobot().nivel_conexion == NivelConexion.NULA


def test_logger_agrega_y_notifica_suscriptores():
    """Cada línea nueva avisa a todos los suscriptores registrados."""
    logger = Logger()
    recibidas = []
    logger.agregar_suscriptor(recibidas.append)

    logger.agregar_linea("SISTEMA", "Prueba manual")

    assert len(recibidas) == 1
    assert recibidas[0].origen == "SISTEMA"
    assert recibidas[0].mensaje == "Prueba manual"
    assert recibidas[0].nivel == NivelLog.INFO


def test_logger_nivel_de_la_ultima_linea():
    """La severidad se conserva en la entrada de log."""
    logger = Logger()
    logger.agregar_linea("BATERIA", "Batería baja", NivelLog.ADVERTENCIA)

    ultima = logger.obtener_lineas()[-1]
    assert ultima.nivel == NivelLog.ADVERTENCIA
    assert ultima.nivel.value == "advertencia"


def test_logger_respeta_limite_por_defecto():
    """El buffer por defecto nunca supera las 30 líneas."""
    logger = Logger()
    for i in range(35):
        logger.agregar_linea("TEST", f"Mensaje {i}")

    assert len(logger.obtener_lineas()) == 30


@pytest.mark.parametrize("max_lineas, agregadas", [(1, 4), (3, 5), (5, 5)])
def test_logger_respeta_limite_personalizado(max_lineas, agregadas):
    """El buffer circular conserva exactamente max_lineas entradas."""
    logger = Logger(max_lineas=max_lineas)
    for i in range(agregadas):
        logger.agregar_linea("TEST", f"Mensaje {i}")

    assert len(logger.obtener_lineas()) == max_lineas


def test_logger_conserva_las_ultimas_lineas():
    """Al desbordar, se descartan las más antiguas y quedan las recientes."""
    logger = Logger(max_lineas=3)
    for i in range(5):
        logger.agregar_linea("TEST", f"M{i}")

    mensajes = [entrada.mensaje for entrada in logger.obtener_lineas()]
    assert mensajes == ["M2", "M3", "M4"]


def test_logger_obtener_lineas_devuelve_copia():
    """Modificar la lista devuelta no altera el buffer interno."""
    logger = Logger()
    logger.agregar_linea("TEST", "única")

    copia = logger.obtener_lineas()
    copia.clear()

    assert len(logger.obtener_lineas()) == 1

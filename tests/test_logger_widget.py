# wall-e-robot/tests/test_logger_widget.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.logger_widget: puente estado -> render."""


from app.nucleo.estado import EstadoRobot, NivelLog
from app.widgets.logica.logger_widget import LoggerWidget


def test_suscripcion_propaga_lineas():
    """Las líneas que llegan al logger del estado se propagan al widget."""
    estado = EstadoRobot()
    widget = LoggerWidget(estado)
    recibidas = []
    widget.suscribir(lambda entrada: recibidas.append(entrada.mensaje))

    estado.logger.agregar_linea("SISTEMA", "Iniciando subsistemas")
    estado.logger.agregar_linea("SENSOR", "Obstáculo a 8cm", NivelLog.ADVERTENCIA)

    assert recibidas == ["Iniciando subsistemas", "Obstáculo a 8cm"]


def test_lectura_del_buffer():
    """obtener_lineas refleja el buffer del logger del estado."""
    estado = EstadoRobot()
    widget = LoggerWidget(estado)

    estado.logger.agregar_linea("SISTEMA", "Iniciando subsistemas")
    estado.logger.agregar_linea("SENSOR", "Obstáculo a 8cm", NivelLog.ADVERTENCIA)

    lineas = widget.obtener_lineas()
    assert len(lineas) == 2
    assert lineas[-1].nivel == NivelLog.ADVERTENCIA

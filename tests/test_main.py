# wall-e-robot/tests/test_main.py
# Kevin Gámez - 29/10/2026

"""Pruebas de la conexión en segundo plano de app.main.

La ventana no se monta: se construye Aplicacion con __new__ y se inyectan una
pantalla falsa y una Comunicacion falsa para comprobar el hilo, la cola de
resultados y la cancelación sin abrir sockets reales.
"""


import queue

import pytest

from app.comunicacion.conexion import ConexionOffline
from app import main as modulo_main
from app.main import Aplicacion


class _PantallaFalsa:
    """Registra lo que la aplicación le pide mostrar."""

    def __init__(self):
        self.conectando = None
        self.conexion = None
        self.error = None

    def establecer_conectando(self, etiqueta):
        self.conectando = etiqueta

    def establecer_conexion(self, activa, etiqueta):
        self.conexion = (activa, etiqueta)

    def mostrar_error(self, mensaje):
        self.error = mensaje


class _ComunicacionFalsa:
    """Conexión falsa que solo recuerda si se cerró."""

    def __init__(self, ip, puerto):
        self.ip = ip
        self.puerto = puerto
        self.cerrada = False

    def cerrar(self):
        self.cerrada = True


class _HiloFalso:
    """Sustituto de threading.Thread: guarda el trabajo, no lo ejecuta."""

    creados = []

    def __init__(self, target, args, name, daemon):
        self.target = target
        self.args = args
        self.name = name
        self.daemon = daemon
        self.iniciado = False
        _HiloFalso.creados.append(self)

    def start(self):
        self.iniciado = True


@pytest.fixture
def hilos(monkeypatch):
    """Captura los hilos que la aplicación intente arrancar."""
    _HiloFalso.creados = []
    monkeypatch.setattr(modulo_main.threading, "Thread", _HiloFalso)
    return _HiloFalso.creados


@pytest.fixture
def app():
    """Aplicacion sin ventana, con pantalla falsa y sin conexión."""
    aplicacion = Aplicacion.__new__(Aplicacion)
    aplicacion.pantalla = _PantallaFalsa()
    aplicacion.conexion = ConexionOffline()
    aplicacion._conexion_pendiente = False
    aplicacion._intento_conexion = 0
    aplicacion._resultados_conexion = queue.Queue()
    return aplicacion


def test_conectar_abre_el_socket_en_un_hilo(app, hilos, monkeypatch):
    """Conectar no bloquea: el socket se crea en un hilo daemon."""
    monkeypatch.setattr(modulo_main, "Comunicacion", _ComunicacionFalsa)

    app._conectar("1.2.3.4", 8080)

    assert app._conexion_pendiente is True
    assert app.pantalla.conectando == "1.2.3.4"
    assert len(hilos) == 1
    assert hilos[0].name == "conexion-robot"
    assert hilos[0].daemon is True
    assert hilos[0].iniciado is True

    # El hilo publica el resultado y el ciclo lo aplica en el hilo de Tk.
    hilos[0].target(*hilos[0].args)
    app._procesar_resultados_conexion()

    assert isinstance(app.conexion, _ComunicacionFalsa)
    assert app.conexion.ip == "1.2.3.4"
    assert app.pantalla.conexion == (True, "1.2.3.4")
    assert app._conexion_pendiente is False


def test_error_al_conectar_se_muestra_sin_romper(app, hilos, monkeypatch):
    """Un fallo del socket deja la app offline y muestra el error."""
    class _ComunicacionCaida:
        def __init__(self, _ip, _puerto):
            raise OSError("sin ruta al robot")

    monkeypatch.setattr(modulo_main, "Comunicacion", _ComunicacionCaida)

    app._conectar("1.2.3.4", 8080)
    hilos[0].target(*hilos[0].args)
    app._procesar_resultados_conexion()

    assert isinstance(app.conexion, ConexionOffline)
    assert app._conexion_pendiente is False
    assert app.pantalla.conexion == (False, "SIN CONEXI\u00d3N")
    assert "sin ruta al robot" in app.pantalla.error


def test_un_intento_viejo_no_pisa_la_conexion_actual(app):
    """Si el usuario desconectó, el socket que llega tarde se cierra."""
    vieja = _ComunicacionFalsa("1.2.3.4", 8080)
    app._intento_conexion = 2   # ya hay un intento más nuevo
    app._resultados_conexion.put((1, "1.2.3.4", vieja, None))

    app._procesar_resultados_conexion()

    assert vieja.cerrada is True
    assert isinstance(app.conexion, ConexionOffline)


def test_desconectar_invalida_el_intento_en_curso(app):
    """Desconectar (o cancelar) descarta el resultado que aún no llegó."""
    app._conexion_pendiente = True
    app._intento_conexion = 1

    app._desconectar()

    assert app._conexion_pendiente is False
    assert app._intento_conexion == 2
    assert isinstance(app.conexion, ConexionOffline)
    assert app.pantalla.conexion == (False, "SIN CONEXI\u00d3N")


def test_no_lanza_dos_intentos_a_la_vez(app, monkeypatch):
    """Con un intento pendiente, pulsar Conectar de nuevo no crea otro hilo."""
    def _no_debe_crearse(*_args, **_kwargs):
        raise AssertionError("no debería abrirse un segundo hilo")

    monkeypatch.setattr(modulo_main.threading, "Thread", _no_debe_crearse)
    app._conexion_pendiente = True

    app._conectar("1.2.3.4", 8080)   # no lanza

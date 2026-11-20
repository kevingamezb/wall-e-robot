# wall-e-robot/tests/test_main.py
# Kevin Gámez - 29/10/2026

"""Pruebas de la conexión en segundo plano de app.main.

La ventana no se monta: se construye Aplicacion con __new__ y se inyectan una
pantalla falsa y una Comunicacion falsa para comprobar el hilo, la cola de
resultados y la cancelación sin abrir sockets reales.
"""


import queue
from unittest.mock import Mock

import pytest

from app.comunicacion.conexion import ConexionOffline
from app.nucleo.estado import EstadoRobot, Modo
from app import main as modulo_main
from app.main import Aplicacion


@pytest.mark.parametrize("salida, esperado", [
    ("    SSID : WALL-E:5G\r\n    BSSID : 00:00:00:00:00:00\r\n", "WALL-E:5G"),
    ("    Estado : desconectado\r\n", None),
])
def test_nombre_red_wifi_en_windows(monkeypatch, salida, esperado):
    consulta = Mock(return_value=Mock(stdout=salida))
    monkeypatch.setattr(modulo_main.sys, "platform", "win32")
    monkeypatch.setattr(modulo_main.subprocess, "CREATE_NO_WINDOW", 0x08000000,
                        raising=False)
    monkeypatch.setattr(modulo_main.subprocess, "run", consulta)

    assert modulo_main.nombre_red_wifi() == esperado
    assert consulta.call_args.args[0] == ["netsh", "wlan", "show", "interfaces"]


class _PantallaFalsa:
    """Registra lo que la aplicación le pide mostrar."""

    def __init__(self):
        self.conectando = None
        self.conexion = None
        self.error = None
        self.latencia = None
        self.dibujos = 0

    def establecer_conectando(self, etiqueta, reconectando=False):
        self.conectando = (etiqueta, reconectando)

    def establecer_conexion(self, activa, etiqueta):
        self.conexion = (activa, etiqueta)

    def mostrar_error(self, mensaje):
        self.error = mensaje

    def actualizar_latencia(self, milisegundos):
        self.latencia = milisegundos

    def dibujar(self):
        self.dibujos += 1


class _RootFalsa:
    """Raíz Tk mínima: solo agenda y cancela callbacks."""

    def __init__(self):
        self.agendados = []
        self.cancelados = []

    def after(self, milisegundos, callback):
        self.agendados.append((milisegundos, callback))
        return len(self.agendados)

    def after_cancel(self, ident):
        self.cancelados.append(ident)


class _ComunicacionFalsa:
    """Conexión falsa que recuerda si se cerró y los comandos enviados."""

    def __init__(self, ip, puerto):
        self.ip = ip
        self.puerto = puerto
        self.cerrada = False
        self.perdida = False
        self.mensajes = []

    def actualizar_estado(self, _estado):
        pass

    def enviar_mensaje(self, comando):
        self.mensajes.append(comando)

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
    """Aplicacion sin ventana, con pantalla, raíz y conexión falsas."""
    aplicacion = Aplicacion.__new__(Aplicacion)
    aplicacion.root = _RootFalsa()
    aplicacion.estado = EstadoRobot()
    aplicacion.pantalla = _PantallaFalsa()
    aplicacion.conexion = ConexionOffline()
    aplicacion._conexion_pendiente = False
    aplicacion._intento_conexion = 0
    aplicacion._resultados_conexion = queue.Queue()
    aplicacion._resultados_ota = queue.Queue()
    aplicacion._ultima_ip = None
    aplicacion._ultimo_puerto = modulo_main.PUERTO
    aplicacion._reconectando = False
    aplicacion._reintentos = 0
    aplicacion._reconexion_id = None
    return aplicacion


def _reintentar_agendado(app):
    """Ejecuta el callback de reconexión que esté agendado."""
    milisegundos, callback = app.root.agendados[-1]
    callback()
    return milisegundos


def test_conectar_abre_el_socket_en_un_hilo(app, hilos, monkeypatch):
    """Conectar no bloquea: el socket se crea en un hilo daemon."""
    monkeypatch.setattr(modulo_main, "Comunicacion", _ComunicacionFalsa)

    app._conectar("1.2.3.4", 8080)

    assert app._conexion_pendiente is True
    assert app.pantalla.conectando == ("1.2.3.4", False)
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
    assert app._ultima_ip == "1.2.3.4"


def test_atajo_m_alterna_modo(raiz_tk, monkeypatch):
    """El atajo comparte el cambio de modo y espera la telemetría."""
    from types import SimpleNamespace

    monkeypatch.setattr(modulo_main, "Comunicacion", _ComunicacionFalsa)
    app = Aplicacion(raiz_tk, modulo_main.escala_para_pantalla(1280, 720))
    app.conexion = _ComunicacionFalsa("1.2.3.4", 8080)
    evento = SimpleNamespace(keysym="m", widget=raiz_tk)
    app.control_teclado._al_presionar(evento)
    assert app.estado.modo == Modo.MANUAL

    app.control_teclado._al_soltar(evento)
    app.estado.modo = Modo.AUTOMATICO
    app.control_teclado._al_presionar(evento)
    assert app.estado.modo == Modo.AUTOMATICO
    assert app.conexion.mensajes == [
        {"tipo": "modo", "modo": "automatico"},
        {"tipo": "modo", "modo": "manual"},
    ]


def test_boton_modo_alterna_desde_el_arranque_manual(app, monkeypatch):
    """Con el estado inicial manual, el botón MODO pide automático."""
    monkeypatch.setattr(modulo_main, "Comunicacion", _ComunicacionFalsa)
    app.conexion = _ComunicacionFalsa("1.2.3.4", 8080)

    app._cambiar_modo()

    assert app.estado.modo == Modo.MANUAL
    assert app.conexion.mensajes == [{"tipo": "modo", "modo": "automatico"}]


def test_portal_ota_envia_basic_auth_y_abre_con_codigo(app, monkeypatch):
    codigo = "a" * 32
    conexion = Mock()
    conexion.getresponse.return_value.status = 200
    conexion.getresponse.return_value.read.return_value = codigo.encode("ascii")
    constructor = Mock(return_value=conexion)
    abrir = Mock(return_value=True)
    monkeypatch.setattr(modulo_main.http.client, "HTTPConnection", constructor)
    monkeypatch.setattr(modulo_main.webbrowser, "open", abrir)

    app._autenticar_ota(("usuario", "clave"))
    app._procesar_acceso_ota()

    constructor.assert_called_once_with("192.168.4.1", timeout=4)
    conexion.request.assert_called_once_with(
        "POST", "/acceso", headers={"Authorization": "Basic dXN1YXJpbzpjbGF2ZQ=="})
    conexion.close.assert_called_once()
    abrir.assert_called_once_with(f"http://192.168.4.1/acceso?codigo={codigo}")


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


# ------------------------------------------------------- reconexión automática
def test_error_al_conectar_programa_reintento(app, hilos, monkeypatch):
    """Un fallo deja el primer reintento agendado a 1 s."""
    class _ComunicacionCaida:
        def __init__(self, _ip, _puerto):
            raise OSError("sin ruta al robot")

    monkeypatch.setattr(modulo_main, "Comunicacion", _ComunicacionCaida)

    app._conectar("1.2.3.4", 8080)
    hilos[0].target(*hilos[0].args)
    app._procesar_resultados_conexion()

    assert app._reconectando is True
    assert app._reintentos == 1
    assert app.pantalla.conectando == ("1.2.3.4", True)
    assert app.root.agendados[-1][0] == modulo_main.RECONEXION_ESPERA_INICIAL_MS


def test_backoff_crece_hasta_el_maximo(app):
    """Las esperas son 1, 2, 4, 8 y luego se estabilizan en 10 s."""
    app._ultima_ip = "1.2.3.4"

    for _ in range(6):
        app._programar_reconexion()

    esperas = [milisegundos for milisegundos, _ in app.root.agendados]
    assert esperas == [1000, 2000, 4000, 8000, 10000, 10000]
    # Cada reprogramación cancela el temporizador anterior.
    assert len(app.root.cancelados) == 5


def test_reintento_abre_otro_hilo(app, hilos, monkeypatch):
    """Al vencer el temporizador se intenta conectar otra vez."""
    monkeypatch.setattr(modulo_main, "Comunicacion", _ComunicacionFalsa)
    app._ultima_ip = "1.2.3.4"
    app._ultimo_puerto = 8080
    app._programar_reconexion()

    espera = _reintentar_agendado(app)

    assert espera == modulo_main.RECONEXION_ESPERA_INICIAL_MS
    assert len(hilos) == 1
    assert app._conexion_pendiente is True
    assert app.pantalla.conectando == ("1.2.3.4", True)


def test_desconectar_cancela_la_reconexion(app):
    """Desconectar a mano detiene el backoff y desactiva el timer."""
    app._ultima_ip = "1.2.3.4"
    app._programar_reconexion()
    ident = app._reconexion_id
    callback = app.root.agendados[-1][1]

    app._desconectar()

    assert app._reconectando is False
    assert app._reintentos == 0
    assert app._reconexion_id is None
    assert ident in app.root.cancelados

    callback()   # un timer ya disparado no debe reconectar
    assert app._conexion_pendiente is False


def test_conexion_lograda_cancela_el_reintento(app):
    """Si el intento funciona, no queda ningún reintento pendiente."""
    app._ultima_ip = "1.2.3.4"
    app._programar_reconexion()
    ident = app._reconexion_id
    app._resultados_conexion.put(
        (app._intento_conexion, "1.2.3.4", _ComunicacionFalsa("1.2.3.4", 8080), None))

    app._procesar_resultados_conexion()

    assert app._reconectando is False
    assert app._reintentos == 0
    assert app._reconexion_id is None
    assert ident in app.root.cancelados


def test_perdida_de_conexion_programa_reintento(app):
    """Si el enlace se cae solo, la app pasa a offline y reintenta sola."""
    falsa = _ComunicacionFalsa("1.2.3.4", 8080)
    falsa.perdida = True
    app.conexion = falsa
    app._ultima_ip = "1.2.3.4"
    app.estado = EstadoRobot()

    app.ciclo()

    assert isinstance(app.conexion, ConexionOffline)
    assert falsa.cerrada is True
    assert app._reconectando is True
    assert app.pantalla.conexion == (False, "SIN CONEXI\u00d3N")
    assert any(milisegundos == modulo_main.RECONEXION_ESPERA_INICIAL_MS
               for milisegundos, _ in app.root.agendados)
    ultima = app.estado.logger.obtener_lineas()[-1]
    assert "Se perdió la conexión" in ultima.mensaje

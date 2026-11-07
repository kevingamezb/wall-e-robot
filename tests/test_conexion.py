# wall-e-robot/tests/test_conexion.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.comunicacion.conexion.

Cubre la conexión offline, el parseo tolerante del protocolo y la robustez de
red, todo sin abrir sockets reales (se inyecta un socket falso o se construye
la clase con __new__).
"""


import json
import socket
from collections import deque
from typing import cast

import pytest

from app.comunicacion import conexion as modulo_conexion
from app.comunicacion.conexion import (
    Comunicacion, Conexion, ConexionOffline,
    nivel_por_frescura, SEGUNDOS_SENAL_ALTA, SEGUNDOS_SENAL_MEDIA,
    PROTOCOLO_VERSION, MAX_BUFFER_ENTRADA, MAX_BUFFER_SALIDA,
    TIMEOUT_CONEXION_S,
)
from app.nucleo.estado import EstadoRobot, Modo, Maniobra, NivelConexion, NivelLog


# --------------------------------------------------------------- frescura
@pytest.mark.parametrize(
    "segundos, esperado",
    [
        (None, NivelConexion.NULA),
        (0.1,  NivelConexion.ALTA),
        (1.0,  NivelConexion.MEDIA),
        (5.0,  NivelConexion.BAJA),
    ],
)
def test_nivel_por_frescura(segundos, esperado):
    """La antigüedad del último estado decide el nivel de enlace."""
    assert nivel_por_frescura(segundos) == esperado


@pytest.mark.parametrize(
    "segundos, esperado",
    [
        (SEGUNDOS_SENAL_ALTA,  NivelConexion.MEDIA),  # justo en el corte
        (SEGUNDOS_SENAL_MEDIA, NivelConexion.BAJA),   # justo en el corte
    ],
)
def test_nivel_por_frescura_limites(segundos, esperado):
    """Los cortes de frescura son estrictos (<), el valor exacto baja de nivel."""
    assert nivel_por_frescura(segundos) == esperado


# --------------------------------------------------------------- offline
def test_offline_apaga_y_descarta():
    """Sin robot: no hay conexión ni señal y los comandos se descartan."""
    estado = EstadoRobot()
    estado.conexion_activa = True
    offline = ConexionOffline()

    offline.actualizar_estado(estado)
    offline.enviar_mensaje({"tipo": "motor", "direccion": "arriba"})  # no lanza

    assert estado.conexion_activa is False
    assert estado.nivel_conexion == NivelConexion.NULA


# ----------------------------------------------------------- protocolo real
@pytest.fixture
def proto():
    """Instancia de Comunicacion sin abrir socket (para probar el parseo)."""
    return Comunicacion.__new__(Comunicacion)


def test_parseo_estado_completo(proto):
    """Todos los campos del estado ampliado se aplican al EstadoRobot."""
    estado = EstadoRobot()

    proto._procesar_mensaje({
        "protocolo": PROTOCOLO_VERSION,
        "tipo": "estado",
        "bateria": 0.83,
        "modo": "manual",
        "hay_advertencia": True,
        "hay_error": False,
        "distancia_cm": 12.3,
        "navegacion": "alto",
        "consumo_watts": 3.4,
        "conexion_activa": True,
        "cargando": False,
        "modulo_inactivo": True,
        "tiempo_restante_min": 42,
        "version_firmware": "1.0.0",
        "ota_pendiente": True,
        "posiciones_servos": {
            "cuello": 30,
            "hombro_izquierdo": -18,
            "hombro_derecho": 0,
            "pulgar_izquierdo": 5,
            "pulgar_derecho": -5,
        },
    }, estado)

    assert estado.bateria == 0.83
    assert estado.modo == Modo.MANUAL
    assert estado.hay_advertencia is True
    assert estado.hay_error is False
    assert estado.distancia_obstaculo_cm == 12.3
    assert estado.navegacion == Maniobra.ALTO
    assert estado.consumo_watts == 3.4
    assert estado.conexion_activa is True
    assert estado.cargando is False
    assert estado.modulo_inactivo is True
    assert estado.tiempo_restante_min == 42
    assert estado.version_firmware == "1.0.0"
    assert estado.ota_pendiente is True
    assert estado.posiciones_servos.cuello == 30.0
    assert estado.posiciones_servos.hombro_izquierdo == -18.0


def test_estado_con_null_no_pisa_valores(proto):
    """Un campo null o ausente no borra el valor previo."""
    estado = EstadoRobot()
    proto._procesar_mensaje({
        "tipo": "estado",
        "distancia_cm": 12.3,
        "tiempo_restante_min": 42,
        "modulo_inactivo": True,
        "cargando": False,
    }, estado)

    proto._procesar_mensaje({
        "tipo": "estado",
        "distancia_cm": None,
        "tiempo_restante_min": None,
        "cargando": True,
    }, estado)

    assert estado.distancia_obstaculo_cm == 12.3
    assert estado.tiempo_restante_min == 42
    assert estado.cargando is True
    assert estado.modulo_inactivo is True


@pytest.mark.parametrize("mensaje", [["no soy", "dict"], {"hola": "mundo"}, 42])
def test_mensajes_sin_tipo_se_descartan(proto, mensaje):
    """La basura o los mensajes sin 'tipo' se ignoran sin romper."""
    estado = EstadoRobot()
    proto._procesar_mensaje(mensaje, estado)  # no lanza


@pytest.mark.parametrize("mensaje", [{"navegacion": "teletransporte"}])
def test_maniobra_desconocida_se_ignora(proto, mensaje):
    """Una maniobra fuera del catálogo no cambia el estado."""
    estado = EstadoRobot()
    estado.navegacion = Maniobra.ALTO
    proto._procesar_mensaje({"tipo": "estado", **mensaje}, estado)
    assert estado.navegacion == Maniobra.ALTO


def test_modo_desconocido_se_ignora(proto):
    """Un modo fuera del catálogo no cambia el estado."""
    estado = EstadoRobot()
    estado.modo = Modo.MANUAL
    proto._procesar_mensaje({"tipo": "estado", "modo": "turbo"}, estado)
    assert estado.modo == Modo.MANUAL


def test_log_de_red_se_integra(proto):
    """Un mensaje 'log' se añade al logger del estado."""
    estado = EstadoRobot()
    proto._procesar_mensaje({
        "tipo": "log",
        "origen": "DISTANCIA",
        "mensaje": "Obstáculo a 8cm",
        "nivel": "advertencia",
    }, estado)

    ultima = estado.logger.obtener_lineas()[-1]
    assert ultima.nivel == NivelLog.ADVERTENCIA
    assert ultima.origen == "DISTANCIA"


def test_protocolo_mas_nuevo_avisa_una_sola_vez(proto):
    """Un firmware con protocolo futuro se avisa una vez y se sigue leyendo."""
    estado = EstadoRobot()

    proto._procesar_mensaje(
        {"protocolo": PROTOCOLO_VERSION + 1, "tipo": "estado", "bateria": 0.7},
        estado)
    proto._procesar_mensaje(
        {"protocolo": PROTOCOLO_VERSION + 1, "tipo": "estado", "bateria": 0.6},
        estado)

    avisos = [linea for linea in estado.logger.obtener_lineas()
              if linea.origen == "PROTOCOLO"]
    assert len(avisos) == 1
    assert estado.bateria == 0.6


def test_comunicacion_tiene_cerrar():
    """La conexión real expone cerrar() para liberar el socket."""
    assert callable(getattr(Comunicacion, "cerrar", None))


# --------------------------------------------------------- robustez de red
class _SocketGuion:
    """Socket mínimo: entrega trozos en orden y luego queda sin datos."""

    def __init__(self, trozos=None, error_recv=None, error_send=None,
                 limite_send=None):
        self._trozos = deque(trozos or [])
        self._error_recv = error_recv
        self._error_send = error_send
        self._limite_send = limite_send
        self.enviado = bytearray()

    def recv(self, _n):
        if self._error_recv is not None:
            raise self._error_recv
        if self._trozos:
            return self._trozos.popleft()
        raise BlockingIOError()

    def send(self, datos):
        if self._error_send is not None:
            raise self._error_send
        cantidad = len(datos)
        if self._limite_send is not None:
            cantidad = min(cantidad, self._limite_send)
        self.enviado.extend(datos[:cantidad])
        return cantidad

    def close(self):
        pass


def _con(falso):
    """Comunicacion con un socket falso ya inyectado."""
    con = Comunicacion.__new__(Comunicacion)
    con.conexion = cast(socket.socket, falso)
    con._buffer_entrada = bytearray()
    con._buffer_salida = bytearray()
    con._perdida = False
    con._ultima_recepcion = None
    con._aviso_version = False
    return con


def test_primer_paquete_no_se_pierde():
    """Regresión: un solo paquete debe aplicarse (antes se descartaba)."""
    con = _con(_SocketGuion([b'{"tipo":"estado","bateria":0.5}\n']))
    estado = EstadoRobot(bateria=0.1)

    con.actualizar_estado(estado)

    assert estado.bateria == 0.5
    assert not con.perdida


def test_cierre_limpio_marca_perdida():
    """recv() == b'' es un cierre limpio y no debe pasar inadvertido."""
    con = _con(_SocketGuion([b""]))
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    assert con.perdida is True
    assert estado.nivel_conexion == NivelConexion.NULA


def test_varios_mensajes_en_un_paquete():
    """Un solo recv con estado + log debe procesar ambos."""
    con = _con(_SocketGuion([
        b'{"tipo":"estado","bateria":0.4}\n'
        b'{"tipo":"log","origen":"X","mensaje":"hola"}\n'
    ]))
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    assert estado.bateria == 0.4
    assert estado.logger.obtener_lineas()[-1].mensaje == "hola"


def test_mensaje_partido_entre_paquetes():
    """Una línea puede llegar en varios recv y debe unirse."""
    con = _con(_SocketGuion([
        b'{"tipo":"estado","bat',
        b'eria":0.25}\n',
    ]))
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    assert estado.bateria == 0.25


def test_json_corrupto_no_tumba_la_linea_buena():
    """Una línea corrupta se descarta y la línea válida sí se procesa."""
    con = _con(_SocketGuion([
        b'{"tipo":"estado","bateria":0.5}\n{"tipo": roto\n']))
    estado = EstadoRobot(bateria=0.1)

    con.actualizar_estado(estado)

    assert estado.bateria == 0.5
    assert not con.perdida


def test_utf8_partido_entre_paquetes():
    """Un carácter UTF-8 partido entre dos recv no debe romper el parseo."""
    con = _con(_SocketGuion([
        b'{"tipo":"log","origen":"X","mensaje":"ca\xc3',
        b'\xb1a"}\n',
    ]))
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    assert estado.logger.obtener_lineas()[-1].mensaje == "caña"


def test_nivel_de_log_desconocido_degrada_a_info():
    """Un nivel de log inventado no rompe: cae a INFO."""
    con = _con(_SocketGuion([
        b'{"tipo":"log","origen":"X","mensaje":"hola","nivel":"turbo"}\n']))
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    ultima = estado.logger.obtener_lineas()[-1]
    assert ultima.mensaje == "hola"
    assert ultima.nivel == NivelLog.INFO


def test_recv_caido_marca_perdida():
    """Un recv que lanza OSError marca perdida=True sin propagar la excepción."""
    con = _con(_SocketGuion(
        error_recv=ConnectionResetError("el robot se reinició")))
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    assert con.perdida is True
    assert estado.nivel_conexion == NivelConexion.NULA


def test_send_caido_marca_perdida():
    """Un send que lanza OSError marca perdida=True sin propagar la excepción."""
    con = _con(_SocketGuion(error_send=OSError("socket cerrado")))

    con.enviar_mensaje({"tipo": "motor", "direccion": "arriba"})

    assert con.perdida is True


def test_enviar_mensaje_serializa_json_con_salto():
    """El comando se serializa a JSON UTF-8 versionado y terminado en '\\n'."""
    falso = _SocketGuion()
    con = _con(falso)

    con.enviar_mensaje({"tipo": "motor", "direccion": "arriba"})

    assert falso.enviado.endswith(b"\n")
    assert json.loads(falso.enviado.decode()) == {
        "tipo": "motor",
        "direccion": "arriba",
        "protocolo": PROTOCOLO_VERSION,
    }


def test_envio_parcial_se_completa():
    """send() puede aceptar menos bytes; la cola debe vaciarse por completo."""
    falso = _SocketGuion(limite_send=4)
    con = _con(falso)

    con.enviar_mensaje({"tipo": "motor", "direccion": "arriba"})

    esperado = json.dumps({
        "tipo": "motor",
        "direccion": "arriba",
        "protocolo": PROTOCOLO_VERSION,
    }, ensure_ascii=False).encode("utf-8") + b"\n"
    assert bytes(falso.enviado) == esperado
    assert not con.perdida
    assert not con._buffer_salida


def test_backpressure_no_es_perdida_y_se_reintenta():
    """BlockingIOError en send deja el mensaje en cola para el próximo ciclo."""

    class _SocketLleno(_SocketGuion):
        def __init__(self):
            super().__init__()
            self.llamadas = 0

        def send(self, datos):
            self.llamadas += 1
            if self.llamadas == 1:
                raise BlockingIOError()
            return super().send(datos)

    falso = _SocketLleno()
    con = _con(falso)

    con.enviar_mensaje({"tipo": "modo", "modo": "manual"})
    assert not con.perdida
    assert con._buffer_salida

    con.actualizar_estado(EstadoRobot())
    assert bytes(falso.enviado).endswith(b"\n")
    assert not con._buffer_salida


def test_buffer_de_entrada_desbordado_corta_la_conexion():
    """Una línea sin '\\n' no puede crecer sin límite."""
    con = _con(_SocketGuion([b"x" * (MAX_BUFFER_ENTRADA + 1)]))
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    assert con.perdida is True
    assert not con._buffer_entrada


def test_buffer_de_salida_desbordado_corta_la_conexion():
    """Si el robot deja de leer, la cola de salida no crece sin límite."""
    class _SocketSinLeer(_SocketGuion):
        def send(self, _datos):
            raise BlockingIOError()

    con = _con(_SocketSinLeer())
    con._buffer_salida = bytearray(b"x" * MAX_BUFFER_SALIDA)

    con.enviar_mensaje({"tipo": "motor", "direccion": "arriba"})

    assert con.perdida is True
    assert not con._buffer_salida


def test_perdida_por_defecto_es_falsa():
    """perdida es False en una instancia recién creada con __new__."""
    assert Comunicacion.__new__(Comunicacion).perdida is False


def test_conexion_es_abstracta():
    """La interfaz Conexion no se puede instanciar directamente."""
    with pytest.raises(TypeError):
        Conexion()


def test_init_abre_socket_con_timeout_y_no_bloqueante(monkeypatch):
    """El constructor conecta con timeout y deja el socket en modo no bloqueante."""
    creados = []

    class _SocketConectable:
        def __init__(self, *args, **kwargs):
            self.conectado = None
            self.bloqueante = None
            self.timeout = None
            self.cerrado = False
            creados.append(self)

        def settimeout(self, valor):
            self.timeout = valor

        def connect(self, direccion):
            self.conectado = direccion

        def setblocking(self, valor):
            self.bloqueante = valor

        def close(self):
            self.cerrado = True

    monkeypatch.setattr(modulo_conexion.socket, "socket",
                        lambda *a, **k: _SocketConectable())

    con = Comunicacion("1.2.3.4", 8080)

    assert creados[0].conectado == ("1.2.3.4", 8080)
    assert creados[0].timeout == TIMEOUT_CONEXION_S
    assert creados[0].bloqueante is False
    assert con.perdida is False

    con.cerrar()
    assert creados[0].cerrado is True


def test_init_cierra_y_propaga_si_no_conecta(monkeypatch):
    """Si el ESP32 no responde, el socket se cierra y el error se propaga."""
    creados = []

    class _SocketQueFalla:
        def __init__(self, *args, **kwargs):
            self.cerrado = False
            creados.append(self)

        def settimeout(self, _valor):
            pass

        def connect(self, _direccion):
            raise TimeoutError("sin respuesta")

        def close(self):
            self.cerrado = True

    monkeypatch.setattr(modulo_conexion.socket, "socket",
                        lambda *a, **k: _SocketQueFalla())

    with pytest.raises(TimeoutError):
        Comunicacion("1.2.3.4", 8080)

    assert creados[0].cerrado is True


def test_linea_vacia_se_ignora():
    """Una línea vacía en el buffer no genera ningún mensaje."""
    con = _con(_SocketGuion([b"\n\n"]))
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    assert estado.logger.obtener_lineas() == []
    assert not con.perdida


def test_blocking_io_no_es_perdida():
    """recv sin datos (BlockingIOError) no marca la conexión como perdida."""
    con = _con(_SocketGuion(error_recv=BlockingIOError()))
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    assert not con.perdida
    assert estado.nivel_conexion == NivelConexion.NULA


def test_cerrar_limpia_los_buffers():
    """cerrar() libera el socket y no deja datos pendientes en memoria."""
    falso = _SocketGuion()
    con = _con(falso)
    con._buffer_entrada = bytearray(b"pendiente")
    con._buffer_salida = bytearray(b"pendiente")

    con.cerrar()

    assert not con._buffer_entrada
    assert not con._buffer_salida

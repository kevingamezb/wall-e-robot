# wall-e-robot/tests/test_conexion.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.comunicacion.conexion.

Cubre el simulador, la conexión offline, el parseo tolerante del protocolo y
la robustez de red, todo sin abrir sockets reales (se inyecta un socket falso
o se construye la clase con __new__).
"""


import json
import socket
import time
from typing import cast

import pytest

from app.comunicacion import conexion as modulo_conexion
from app.comunicacion.conexion import (
    Comunicacion, ComunicacionSimulada, Conexion, ConexionOffline,
    nivel_por_frescura, SEGUNDOS_SENAL_ALTA, SEGUNDOS_SENAL_MEDIA,
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


# --------------------------------------------------------------- simulador
def test_simulada_actualiza_estado():
    """Un ciclo del simulador deja el estado con valores coherentes."""
    estado = EstadoRobot()
    simulada = ComunicacionSimulada()

    simulada.actualizar_estado(estado)

    assert estado.conexion_activa is True
    assert estado.nivel_conexion in (
        NivelConexion.ALTA, NivelConexion.MEDIA, NivelConexion.BAJA)
    assert 5.0 <= estado.distancia_obstaculo_cm <= 200.0
    assert 1.2 <= estado.consumo_watts <= 4.8
    assert estado.bateria < 1.0


def test_simulada_comando_modo():
    """Un comando 'modo' cambia el modo simulado interno."""
    estado = EstadoRobot()
    simulada = ComunicacionSimulada()

    simulada.enviar_mensaje({"tipo": "modo", "modo": "manual"})
    simulada.actualizar_estado(estado)

    assert estado.modo == Modo.MANUAL


def test_simulada_multi_aplica_el_ultimo():
    """En un comando 'multi', manda el último sub-comando (como el firmware)."""
    estado = EstadoRobot()
    simulada = ComunicacionSimulada()

    simulada.enviar_mensaje({
        "tipo": "multi",
        "comandos": [
            {"tipo": "modo", "modo": "automatico"},
            {"tipo": "modo", "modo": "manual"},
        ],
    })
    simulada.actualizar_estado(estado)

    assert estado.modo == Modo.MANUAL


def test_simulada_cooldown_de_advertencia():
    """Una alerta activa se registra una sola vez, no en cada ciclo."""
    estado = EstadoRobot()
    simulada = ComunicacionSimulada()
    simulada._distancia_simulada = 8.0

    simulada.actualizar_estado(estado)
    simulada.actualizar_estado(estado)

    advertencias = [l for l in estado.logger.obtener_lineas()
                    if l.nivel == NivelLog.ADVERTENCIA]
    assert len(advertencias) == 1


def test_simulada_error_de_bateria():
    """Una batería crítica registra un error una sola vez."""
    estado = EstadoRobot()
    simulada = ComunicacionSimulada()
    simulada._distancia_simulada = 50.0
    simulada._bateria_simulada = 0.05

    simulada.actualizar_estado(estado)

    errores = [l for l in estado.logger.obtener_lineas()
               if l.nivel == NivelLog.ERROR]
    assert len(errores) == 1
    assert errores[0].origen == "BATERIA"


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


def test_comunicacion_tiene_cerrar():
    """La conexión real expone cerrar() para liberar el socket."""
    assert callable(getattr(Comunicacion, "cerrar", None))


# --------------------------------------------------------- robustez de red
class _SocketFalso:
    """Socket mínimo para inyectar datos, errores de recv o de send."""

    def __init__(self, datos=b"", error_recv=None, error_send=None):
        self._datos = datos
        self._error_recv = error_recv
        self._error_send = error_send
        self.enviado = None

    def recv(self, _n):
        if self._error_recv is not None:
            raise self._error_recv
        return self._datos

    def send(self, datos):
        if self._error_send is not None:
            raise self._error_send
        self.enviado = datos
        return len(datos)


def _con(falso):
    """Comunicacion con un socket falso ya inyectado."""
    con = Comunicacion.__new__(Comunicacion)
    con.conexion = cast(socket.socket, falso)
    con._mensaje_entrante = ""
    return con


def test_json_corrupto_no_tumba_la_linea_buena():
    """Una línea corrupta se descarta y la línea válida sí se procesa."""
    falso = _SocketFalso(datos=b'{"tipo":"estado","bateria":0.5}\n{"tipo": roto\n')
    con = _con(falso)
    estado = EstadoRobot(bateria=0.1)

    con.actualizar_estado(estado)

    assert estado.bateria == 0.5
    assert not con.perdida


def test_nivel_de_log_desconocido_degrada_a_info():
    """Un nivel de log inventado no rompe: cae a INFO."""
    falso = _SocketFalso(
        datos=b'{"tipo":"log","origen":"X","mensaje":"hola","nivel":"turbo"}\n')
    con = _con(falso)
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    ultima = estado.logger.obtener_lineas()[-1]
    assert ultima.mensaje == "hola"
    assert ultima.nivel == NivelLog.INFO


def test_recv_caido_marca_perdida():
    """Un recv que lanza OSError marca perdida=True sin propagar la excepción."""
    falso = _SocketFalso(error_recv=ConnectionResetError("el robot se reinició"))
    con = _con(falso)
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    assert con.perdida is True
    assert estado.nivel_conexion == NivelConexion.NULA


def test_send_caido_marca_perdida():
    """Un send que lanza OSError marca perdida=True sin propagar la excepción."""
    falso = _SocketFalso(error_send=OSError("socket cerrado"))
    con = _con(falso)

    con.enviar_mensaje({"tipo": "motor", "direccion": "arriba"})

    assert con.perdida is True


def test_enviar_mensaje_serializa_json_con_salto():
    """El comando se serializa a JSON UTF-8 terminado en '\\n'."""
    falso = _SocketFalso()
    con = _con(falso)

    con.enviar_mensaje({"tipo": "motor", "direccion": "arriba"})

    assert falso.enviado.endswith(b"\n")
    assert json.loads(falso.enviado.decode()) == {
        "tipo": "motor", "direccion": "arriba"}


def test_perdida_por_defecto_es_falsa():
    """perdida es False en una instancia recién creada con __new__."""
    assert Comunicacion.__new__(Comunicacion).perdida is False


def test_conexion_es_abstracta():
    """La interfaz Conexion no se puede instanciar directamente."""
    with pytest.raises(TypeError):
        Conexion()


def test_init_abre_socket_no_bloqueante(monkeypatch):
    """El constructor conecta y deja el socket en modo no bloqueante."""
    creados = []

    class _SocketConectable:
        def __init__(self, *args, **kwargs):
            self.conectado = None
            self.bloqueante = None
            self.cerrado = False
            creados.append(self)

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
    assert creados[0].bloqueante is False
    assert con.perdida is False

    con.cerrar()
    assert creados[0].cerrado is True


def test_linea_vacia_se_ignora():
    """Una línea vacía en el buffer no genera ningún mensaje."""
    falso = _SocketFalso(datos=b"\n\n")
    con = _con(falso)
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    assert estado.logger.obtener_lineas() == []
    assert not con.perdida


def test_blocking_io_no_es_perdida():
    """recv sin datos (BlockingIOError) no marca la conexión como perdida."""
    falso = _SocketFalso(error_recv=BlockingIOError())
    con = _con(falso)
    estado = EstadoRobot()

    con.actualizar_estado(estado)

    assert not con.perdida
    assert estado.nivel_conexion == NivelConexion.NULA


def test_simulada_log_periodico():
    """Pasados 10 s, el simulador deja una línea de cortesía en el logger."""
    estado = EstadoRobot()
    simulada = ComunicacionSimulada()
    simulada._ultimo_log_tiempo = time.time() - 11.0

    simulada.actualizar_estado(estado)

    del_simulador = [l for l in estado.logger.obtener_lineas()
                     if l.origen == "SIMULADOR"]
    assert len(del_simulador) == 1
    assert del_simulador[0].nivel == NivelLog.INFO

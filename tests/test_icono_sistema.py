# wall-e-robot/tests/test_icono_sistema.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.icono_sistema: activación, color y recursos."""


import pytest

from app.nucleo.estado import EstadoRobot, Modo, NivelConexion
from app.nucleo.paleta import Paleta
from app.widgets.logica.icono_sistema import IconoSistema, TipoIcono


@pytest.fixture
def entorno():
    """Estado nuevo con un icono por tipo, listos para consultar."""
    estado = EstadoRobot()
    iconos = {tipo: IconoSistema(estado, tipo) for tipo in TipoIcono}
    return estado, iconos


def test_solo_conexion_activa_al_inicio(entorno):
    """Con conexión pero sin alertas, solo CONEXION está activo."""
    estado, iconos = entorno
    estado.conexion_activa = True

    assert iconos[TipoIcono.CONEXION].activo
    assert iconos[TipoIcono.CONEXION].color == Paleta.AXIOM_CYAN
    assert not iconos[TipoIcono.ADVERTENCIA].activo
    assert iconos[TipoIcono.ADVERTENCIA].color == Paleta.GRIS
    assert not iconos[TipoIcono.MODO_MANUAL].activo


def test_advertencia_y_error(entorno):
    """Advertencia enciende naranja y error rojo."""
    estado, iconos = entorno
    estado.hay_advertencia = True
    estado.hay_error = True

    assert iconos[TipoIcono.ADVERTENCIA].activo
    assert iconos[TipoIcono.ADVERTENCIA].color == Paleta.NARANJA
    assert iconos[TipoIcono.ERROR].activo
    assert iconos[TipoIcono.ERROR].color == Paleta.ROJO


def test_manual_y_cargando(entorno):
    """Modo manual es cian y cargando verde lima."""
    estado, iconos = entorno
    estado.modo = Modo.MANUAL
    estado.cargando = True

    assert iconos[TipoIcono.MODO_MANUAL].activo
    assert iconos[TipoIcono.MODO_MANUAL].color == Paleta.AXIOM_CYAN
    assert iconos[TipoIcono.CARGANDO].activo
    assert iconos[TipoIcono.CARGANDO].color == Paleta.VERDE_LIMA


def test_modulo_inactivo_enciende_error(entorno):
    """Un módulo inactivo (config incompleta) enciende el ícono de ERROR."""
    estado, iconos = entorno
    estado.hay_error = False
    estado.modulo_inactivo = True

    assert iconos[TipoIcono.ERROR].activo
    assert iconos[TipoIcono.ERROR].color == Paleta.ROJO

    estado.modulo_inactivo = False
    assert not iconos[TipoIcono.ERROR].activo


def test_archivo_de_cada_tipo(entorno):
    """Cada icono apunta al PNG que le corresponde."""
    estado, iconos = entorno
    estado.nivel_conexion = NivelConexion.ALTA

    assert iconos[TipoIcono.ADVERTENCIA].archivo == "advertencia"
    assert iconos[TipoIcono.CARGANDO].archivo == "cargando"
    assert iconos[TipoIcono.MODO_MANUAL].archivo == "controlador"
    assert iconos[TipoIcono.ERROR].archivo == "error"
    assert iconos[TipoIcono.CONEXION].archivo == "conectividad_alta"


@pytest.mark.parametrize(
    "nivel, archivo",
    [
        (NivelConexion.ALTA,  "conectividad_alta"),
        (NivelConexion.MEDIA, "conectividad_media"),
        (NivelConexion.BAJA,  "conectividad_baja"),
        (NivelConexion.NULA,  "conectividad_alta"),
    ],
)
def test_archivo_de_conectividad_segun_nivel(entorno, nivel, archivo):
    """El icono de conexión elige el PNG según el nivel (NULA reutiliza ALTA)."""
    estado, iconos = entorno
    estado.nivel_conexion = nivel
    assert iconos[TipoIcono.CONEXION].archivo == archivo


def test_titulo_es_el_identificador(entorno):
    """titulo expone el valor del tipo."""
    _, iconos = entorno
    assert iconos[TipoIcono.ERROR].titulo == "error"

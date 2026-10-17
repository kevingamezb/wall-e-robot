# wall-e-robot/tests/test_mapeo_teclado.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.mapeo_teclado: perfil, persistencia y conflictos."""


import json

import pytest

from app.widgets.logica.mapeo_teclado import (
    ACCIONES, EJE, MapeoTeclado, accion_por_id, nombre_tecla, _teclas_por_defecto,
)


def test_perfil_por_defecto_cubre_todas_las_acciones():
    """El perfil de fábrica mapea todas las acciones con teclas únicas."""
    mapeo = MapeoTeclado()

    assert {a.id for a in ACCIONES} <= set(mapeo._mapa)
    teclas = list(mapeo._mapa.values())
    assert len(teclas) == len(set(teclas))
    assert mapeo.tecla_de("arriba") == "Up"


def test_catalogo_de_acciones():
    """Hay 11 acciones y 6 son de eje con paso positivo."""
    assert len(ACCIONES) == 11
    ejes = [a for a in ACCIONES if a.tipo == EJE]
    assert len(ejes) == 6
    assert all(a.paso > 0 for a in ejes)


def test_guardar_y_cargar_round_trip(tmp_path):
    """Guardar y volver a cargar produce un mapa idéntico."""
    ruta = tmp_path / "controles.json"
    mapeo = MapeoTeclado()
    mapeo.guardar(ruta)

    recargado = MapeoTeclado.cargar(ruta)

    assert recargado._mapa == mapeo._mapa


def test_cargar_sin_archivo_usa_defaults(tmp_path):
    """Sin archivo, la carga cae al perfil de fábrica."""
    recargado = MapeoTeclado.cargar(tmp_path / "no_existe.json")
    assert recargado.tecla_de("reposo") == "r"


def test_cargar_json_corrupto_usa_defaults(tmp_path):
    """Un JSON inválido no rompe: se usan los valores por defecto."""
    ruta = tmp_path / "roto.json"
    ruta.write_text("{ esto no es json", encoding="utf-8")

    recargado = MapeoTeclado.cargar(ruta)

    assert recargado.tecla_de("reposo") == "r"


def test_cargar_completa_acciones_faltantes(tmp_path):
    """Si el archivo omite acciones, se completan desde los defaults."""
    ruta = tmp_path / "parcial.json"
    ruta.write_text(json.dumps({"teclado": {"arriba": "Up"}}), encoding="utf-8")

    recargado = MapeoTeclado.cargar(ruta)

    assert recargado.tecla_de("arriba") == "Up"
    assert recargado.tecla_de("abajo") == "Down"
    assert {a.id for a in ACCIONES} <= set(recargado._mapa)


def test_cargar_teclado_no_dict_usa_defaults(tmp_path):
    """Si 'teclado' no es un diccionario, se cae a los valores por defecto."""
    ruta = tmp_path / "raro.json"
    ruta.write_text(json.dumps({"teclado": ["no", "es", "dict"]}),
                    encoding="utf-8")

    recargado = MapeoTeclado.cargar(ruta)

    assert recargado.tecla_de("arriba") == "Up"


def test_asignar_libera_la_accion_ocupada():
    """Asignar una tecla ya usada libera la acción anterior (una tecla = una acción)."""
    mapeo = MapeoTeclado()

    mapeo.asignar("arriba", "x")
    assert mapeo.tecla_de("arriba") == "x"

    mapeo.asignar("abajo", "x")
    assert mapeo.tecla_de("abajo") == "x"
    assert mapeo.tecla_de("arriba") is None
    assert mapeo.buscar_accion("x") == "abajo"
    assert mapeo.tecla_ocupada("x") == "abajo"


def test_limpiar_y_restaurar():
    """limpiar deja la acción sin tecla; restaurar vuelve a fábrica."""
    mapeo = MapeoTeclado()

    mapeo.limpiar("abajo")
    assert mapeo.tecla_de("abajo") is None

    mapeo.restaurar_por_defecto()
    assert mapeo.tecla_de("abajo") == "Down"


def test_tecla_desconocida_devuelve_none():
    """tecla_de de una acción no mapeada devuelve None."""
    assert MapeoTeclado({"arriba": "Up"}).tecla_de("abajo") is None


def test_tecla_de_o_por_defecto():
    """Devuelve la tecla asignada o, si no hay, la de fábrica."""
    mapeo = MapeoTeclado({"arriba": "x"})
    assert mapeo.tecla_de_o_por_defecto("arriba") == "x"
    assert mapeo.tecla_de_o_por_defecto("abajo") == "Down"


@pytest.mark.parametrize(
    "keysym, esperado",
    [
        ("Up", "\u2191"),
        ("space", "ESPACIO"),
        ("q", "Q"),
        ("F5", "F5"),
    ],
)
def test_nombre_tecla(keysym, esperado):
    """nombre_tecla traduce símbolos especiales y letras a texto legible."""
    assert nombre_tecla(keysym) == esperado


def test_accion_por_id():
    """accion_por_id devuelve la acción y lanza KeyError si no existe."""
    assert accion_por_id("arriba").tipo == "discreto"
    with pytest.raises(KeyError):
        accion_por_id("no_existe")


@pytest.mark.parametrize("metodo", ["asignar", "limpiar"])
def test_operar_sobre_accion_inexistente_lanza(metodo):
    """Asignar o limpiar una acción inexistente es un KeyError."""
    mapeo = MapeoTeclado()
    with pytest.raises(KeyError):
        if metodo == "asignar":
            mapeo.asignar("no_existe", "x")
        else:
            mapeo.limpiar("no_existe")


def test_defaults_tienen_todas_las_acciones():
    """_teclas_por_defecto cubre exactamente las acciones del catálogo."""
    assert set(_teclas_por_defecto()) == {a.id for a in ACCIONES}

import base64
import json
from unittest.mock import Mock

import pytest

from app.comunicacion import credenciales_red
from app.pantallas import modal_credenciales


def test_envia_las_nuevas_credenciales_al_portal_del_robot(monkeypatch):
    conexion = Mock()
    conexion.getresponse.return_value.status = 204
    abrir = Mock(return_value=conexion)
    monkeypatch.setattr(credenciales_red.http.client, "HTTPConnection", abrir)
    mensaje = credenciales_red.preparar_credenciales("red-nueva", "equipo", 'ota-"nueva')
    credenciales_red.guardar_por_red("walle", "wall-e-ota", mensaje)

    abrir.assert_called_once_with("192.168.4.1", timeout=5)
    args, opciones = conexion.request.call_args
    assert args == ("POST", "/credenciales")
    assert opciones["headers"]["Content-Type"] == "application/json"
    assert base64.b64decode(opciones["headers"]["Authorization"].split()[1]) == b"walle:wall-e-ota"
    assert json.loads(opciones["body"]) == {
        "wifi": "red-nueva", "usuario_ota": "equipo", "clave_ota": 'ota-"nueva',
    }
    conexion.close.assert_called_once()


@pytest.mark.parametrize("wifi, usuario, ota", [
    ("corta", "walle", "ota-valida"),
    ("wifi-valida", "u:ser", "ota-valida"),
    ("wifi-valida", "walle", "clave\nservidor"),
])
def test_rechaza_credenciales_invalidas(wifi, usuario, ota):
    with pytest.raises(ValueError):
        credenciales_red.preparar_credenciales(wifi, usuario, ota)


def test_informa_si_el_portal_rechaza_la_clave_actual(monkeypatch):
    conexion = Mock()
    conexion.getresponse.return_value.status = 401
    monkeypatch.setattr(credenciales_red.http.client, "HTTPConnection", Mock(return_value=conexion))
    with pytest.raises(OSError, match="actuales"):
        credenciales_red.guardar_por_red("equipo", "incorrecta", b"{}")
    conexion.close.assert_called_once()


def test_modal_envia_desde_la_red_sin_pedir_usb(raiz_tk, monkeypatch):
    raiz_tk.deiconify()
    raiz_tk.update()
    guardar = Mock()
    monkeypatch.setattr(modal_credenciales, "guardar_por_red", guardar)

    modal = modal_credenciales.ModalCredenciales(raiz_tk)
    for campo, valor in zip(modal._nuevas, ("red-nueva", "equipo", "ota-nueva")):
        campo.insert(0, valor)
    modal._aplicar()
    raiz_tk.wait_window(modal)

    assert modal.guardado
    usuario, clave, mensaje = guardar.call_args.args
    assert (usuario, clave) == ("walle", "wall-e-ota")
    assert json.loads(mensaje)["wifi"] == "red-nueva"

from app.nucleo.configuracion_control import CLAVES, ConfiguracionControl
from app.pantallas.modal_configuracion import ModalConfiguracion


def test_inversiones_independientes_y_persistentes(tmp_path):
    ruta = tmp_path / "control_robot.json"
    perfil = ConfiguracionControl(ruta)
    comandos = {"tipo": "multi", "comandos": [
        {"tipo": "servo", "servo": "hombro_izquierdo", "angulo": 20},
        {"tipo": "servo", "servo": "hombro_derecho", "angulo": -30},
        {"tipo": "servo", "servo": "cuello", "angulo": 40},
        {"tipo": "motor", "direccion": "arriba"},
        {"tipo": "motor", "direccion": "izquierda"},
    ]}
    assert perfil.ajustar_comando(comandos) == comandos

    perfil.aplicar({CLAVES[0]: True, CLAVES[2]: True, CLAVES[4]: True})
    perfil = ConfiguracionControl(ruta)
    ajustados = perfil.ajustar_comando(comandos)["comandos"]
    assert [comando["angulo"] for comando in ajustados[:3]] == [-20, -30, -40]
    assert [comando["direccion"] for comando in ajustados[3:]] == ["arriba", "derecha"]

    perfil.aplicar({CLAVES[1]: True, CLAVES[3]: True})
    ajustados = perfil.ajustar_comando(comandos)["comandos"]
    assert [comando["angulo"] for comando in ajustados[:3]] == [20, 30, 40]
    assert [comando["direccion"] for comando in ajustados[3:]] == ["abajo", "izquierda"]
    assert comandos["comandos"][0]["angulo"] == 20


def test_el_modal_solo_guarda_al_aplicar(raiz_tk, tmp_path):
    raiz_tk.deiconify()
    raiz_tk.update()
    perfil = ConfiguracionControl(tmp_path / "control_robot.json")

    modal = ModalConfiguracion(raiz_tk, perfil)
    modal._primer_interruptor.invoke()
    modal.destroy()
    assert not perfil.ruta.exists()

    modal = ModalConfiguracion(raiz_tk, perfil)
    assert not modal._opciones[CLAVES[0]].get()
    modal._primer_interruptor.invoke()
    modal._aplicar()
    assert ConfiguracionControl(perfil.ruta).valores[CLAVES[0]]

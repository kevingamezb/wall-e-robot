# wall-e-robot/tests/test_pantalla_principal.py
# Kevin Gámez - 16/10/2026

"""Prueba de humo de app.pantallas.pantalla_principal.

Monta la pantalla completa sobre una raíz retirada y dibuja varios ciclos con
y sin conexión, comprobando que la construcción y el render no fallan, que el
botón de modo sigue al robot y que el gamepad solo manda en manual.
"""


from app.nucleo.estado import EstadoRobot, Modo
from app.pantallas.pantalla_principal import PantallaPrincipal


def test_pantalla_se_construye_y_dibuja(raiz_tk):
    """La pantalla se construye y dibuja en conexión y en offline."""
    cambios_modo = []
    estado = EstadoRobot()
    pantalla = PantallaPrincipal(
        raiz_tk, estado,
        on_conectar=lambda: None,
        on_desconectar=lambda: None,
        on_modo=lambda: cambios_modo.append(1),
    )

    comandos = []
    pantalla.conectar_gamepad(comandos.append)
    pantalla.establecer_conexion(True, "192.168.4.1")

    for _ in range(3):
        estado.conexion_activa = True
        pantalla.dibujar()
        raiz_tk.update()

    # Conectado y en automático: el botón de modo está activo y el gamepad no.
    assert pantalla.boton_modo.habilitado is True
    assert pantalla.boton_modo.texto == "MODO: AUTOM\u00c1TICO"
    assert pantalla.gamepad.habilitado is False

    # En manual el botón lo dice, el gamepad se habilita y pulsar avisa.
    estado.modo = Modo.MANUAL
    pantalla.dibujar()
    assert pantalla.boton_modo.texto == "MODO: MANUAL"
    assert pantalla.gamepad.habilitado is True
    pantalla.boton_modo.presionar()
    assert cambios_modo == [1]

    # Sin conexión el botón queda apagado y el gamepad también.
    pantalla.establecer_conexion(False, "SIN CONEXI\u00d3N")
    estado.modo = Modo.AUTOMATICO
    pantalla.dibujar()
    raiz_tk.update()

    assert pantalla.boton_modo.habilitado is False
    assert pantalla.boton_modo.texto == "MODO: --"
    assert pantalla.gamepad.habilitado is False

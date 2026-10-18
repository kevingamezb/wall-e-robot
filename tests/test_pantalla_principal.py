# wall-e-robot/tests/test_pantalla_principal.py
# Kevin Gámez - 16/10/2026

"""Prueba de humo de app.pantallas.pantalla_principal.

Monta la pantalla completa sobre una raíz retirada y dibuja varios ciclos con
y sin conexión, comprobando que la construcción y el render no fallan.
"""


from app.nucleo.estado import EstadoRobot
from app.pantallas.pantalla_principal import PantallaPrincipal


def test_pantalla_se_construye_y_dibuja(raiz_tk):
    """La pantalla se construye y dibuja en conexión y en offline."""
    estado = EstadoRobot()
    pantalla = PantallaPrincipal(
        raiz_tk, estado,
        on_conectar=lambda: None,
        on_desconectar=lambda: None,
    )

    comandos = []
    pantalla.conectar_gamepad(comandos.append)
    pantalla.establecer_conexion(True, "192.168.4.1")

    for _ in range(3):
        estado.conexion_activa = True
        pantalla.dibujar()
        raiz_tk.update()

    estado.conexion_activa = False
    pantalla.establecer_conexion(False, "SIN CONEXI\u00d3N")
    pantalla.dibujar()
    raiz_tk.update()

    assert pantalla is not None

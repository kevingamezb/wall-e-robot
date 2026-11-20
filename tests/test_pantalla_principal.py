# wall-e-robot/tests/test_pantalla_principal.py
# Kevin Gámez - 16/10/2026

"""Prueba de humo de app.pantallas.pantalla_principal.

Monta la pantalla completa sobre una raíz retirada y dibuja varios ciclos con
y sin conexión, comprobando que la construcción y el render no fallan, que el
botón de modo sigue al robot y que el gamepad solo manda en manual.
"""


from app.nucleo.disenio import Escala, RECORTE_SUPERIOR
from app.nucleo.estado import EstadoRobot, Modo
from app.nucleo.paleta import Paleta
from app.pantallas.pantalla_principal import PantallaPrincipal
from app.widgets.renderizado import texto_render


def test_pantalla_se_construye_y_dibuja(raiz_tk):
    """La pantalla se construye y dibuja en conexión y en offline."""
    cambios_modo = []
    estado = EstadoRobot()
    estado.modo = Modo.AUTOMATICO   # comprobamos primero la rama automática
    pantalla = PantallaPrincipal(
        raiz_tk, estado, Escala(0.25),
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


def test_recorte_superior_y_navegacion_con_dos_arcos(raiz_tk):
    escala = Escala(0.40)
    estado = EstadoRobot()
    estado.distancia_obstaculo_cm = 34
    pantalla = PantallaPrincipal(raiz_tk, estado, escala)
    pantalla.dibujar()
    raiz_tk.update_idletasks()

    canvas = pantalla.canvas
    assert canvas.canvasy(0) == escala(RECORTE_SUPERIOR)
    assert canvas.winfo_reqheight() == escala.alto_panel
    radar = pantalla.render_navegacion
    colores = [
        canvas.itemcget(radar._ids[f"aro_{i}"], "outline") for i in (1, 2, 3)
    ]
    assert colores == [Paleta.NARANJA, Paleta.NARANJA, Paleta.FONDO_WIDGET]
    assert pantalla.t_navegacion._color_pastilla == Paleta.NARANJA


def test_cache_texto_conserva_las_entradas_recientes(raiz_tk, monkeypatch):
    monkeypatch.setattr(texto_render, "_MAX_CACHE", 2)

    def foto(texto):
        return texto_render.foto_texto(texto, 14, Paleta.TINTA, master=raiz_tk)

    reciente = foto("reciente")
    antigua = foto("antigua")
    assert foto("reciente") is reciente
    foto("nueva")

    assert foto("reciente") is reciente
    assert foto("antigua") is not antigua

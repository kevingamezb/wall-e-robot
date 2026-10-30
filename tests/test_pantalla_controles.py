# wall-e-robot/tests/test_pantalla_controles.py
# Kevin Gámez - 30/10/2026

"""Integración de la pestaña "Controles" incrustada en la barra lateral."""


import types

from app.nucleo.disenio import Disenio, Escala
from app.nucleo.estado import EstadoRobot
from app.pantallas.modal_controles import (
    BOTON_ANCHO, CONTROL_ALTO, FILA_ALTO, ModalControles,
)
from app.pantallas.pantalla_principal import PantallaPrincipal
from app.widgets.logica.mapeo_teclado import MapeoTeclado


def _tecla(keysym):
    """Evento de teclado mínimo."""
    return types.SimpleNamespace(keysym=keysym)


def test_pestana_controles_incrusta_el_modal(raiz_tk):
    """La pestaña muestra el modal, guarda cambios y avisa de la captura."""
    cambios = []
    capturas = []
    mapeo = MapeoTeclado()
    pantalla = PantallaPrincipal(
        raiz_tk, EstadoRobot(), Escala(0.25), mapeo=mapeo,
        on_cambio_mapeo=lambda: cambios.append(True),
        al_captura=capturas.append,
    )
    raiz_tk.update()

    assert pantalla.panel_controles is not None

    pantalla.mostrar_pagina("controles")
    assert pantalla._pagina == "controles"
    assert pantalla.canvas.itemcget(
        pantalla._ventana_controles, "state") == "normal"
    assert all(pantalla.canvas.itemcget(item, "state") == "hidden"
               for item in pantalla._items_conexion)

    modal = pantalla.panel_controles
    modal._empezar_captura("arriba")
    assert capturas[-1] is True

    modal._al_tecla(_tecla("U"))
    assert mapeo.tecla_de("arriba") == "U"
    assert capturas[-1] is False
    assert cambios == [True]

    # Volver a Conectar a mitad de captura cancela la captura y reactiva el
    # teclado (si no, escribir la IP cambiaría el mapeo).
    modal._empezar_captura("abajo")
    pantalla.mostrar_pagina("conectar")
    assert modal._capturando is None
    assert capturas[-1] is False
    assert pantalla.canvas.itemcget(
        pantalla._ventana_controles, "state") == "hidden"
    assert all(pantalla.canvas.itemcget(item, "state") == "normal"
               for item in pantalla._items_conexion)

    pantalla.dibujar()
    raiz_tk.update()


def test_panel_cabe_bajo_las_pestanas_y_dentro_de_la_barra(raiz_tk):
    """El editor no invade las pestañas ni el panel central."""
    pantalla = PantallaPrincipal(
        raiz_tk, EstadoRobot(), Escala(0.25), mapeo=MapeoTeclado(),
    )
    e = Escala(0.25)
    x1, y1 = pantalla.canvas.coords(pantalla._ventana_controles)
    x2 = x1 + e(Disenio.PANEL_CONTROLES[2] - Disenio.PANEL_CONTROLES[0])
    y2 = y1 + e(Disenio.PANEL_CONTROLES[3] - Disenio.PANEL_CONTROLES[1])

    assert y1 >= e(Disenio.SELECTOR[3]), "No debe tapar las pestañas"
    assert x1 >= e(Disenio.BARRA_LATERAL[0])
    assert x2 <= e(Disenio.BARRA_LATERAL[2])
    assert y2 <= e(Disenio.BARRA_LATERAL[3])
    assert x2 < e(Disenio.PANEL_CENTRAL[0]), "No debe invadir el panel central"


def test_filas_y_controles_tienen_el_tamano_actual(raiz_tk):
    """A escala 0.40: fila 42 px, controles 30 px de alto y × 38 px de ancho."""
    modal = ModalControles(raiz_tk, MapeoTeclado(), escala=Escala(0.40))
    raiz_tk.update()

    assert modal._px(FILA_ALTO) == 42
    assert modal._px(CONTROL_ALTO) == 30
    assert modal._px(BOTON_ANCHO) == 38

    fila = modal.marco_filas.winfo_children()[0]
    btn_tecla, btn_limpiar = modal._filas["arriba"]
    assert fila.winfo_reqheight() == 42
    assert btn_tecla.master.winfo_reqheight() == 30
    assert btn_limpiar.master.winfo_reqwidth() == 38
    assert btn_limpiar.master.winfo_reqheight() == 30
    assert btn_tecla.master.pack_info()["expand"] == 1
    modal.ventana.destroy()


def test_barra_y_rueda_desplazan_la_lista(raiz_tk):
    """La perilla dorada se sincroniza y la rueda mueve la lista."""
    modal = ModalControles(raiz_tk, MapeoTeclado(), incrustado=True)
    modal.lienzo_filas.configure(scrollregion=(0, 0, 200, 800))
    modal.barra_filas.canvas.configure(width=10, height=200)
    modal.barra_filas.set(0.0, 0.5)
    raiz_tk.update()

    assert modal.barra_filas._alto_perilla > 0, "Debe dibujarse la perilla"
    assert modal.barra_filas.canvas.itemcget(
        modal.barra_filas._perilla, "state") == "normal"

    antes = modal.lienzo_filas.yview()[0]
    modal._rueda_filas(types.SimpleNamespace(delta=-120))
    assert modal.lienzo_filas.yview()[0] > antes

    modal.lienzo_filas.yview_moveto(0.0)
    modal.barra_filas._agarre = modal.barra_filas._alto_perilla / 2
    modal.barra_filas._mover(200)
    assert modal.lienzo_filas.yview()[0] > 0.9, "Arrastrar baja la lista"

    modal.ventana.destroy()

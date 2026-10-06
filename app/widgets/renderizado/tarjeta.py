# wall-e-robot/app/widgets/renderizado/tarjeta.py
# Kevin Gámez - 13/09/2026


import tkinter as tk
from ...nucleo.paleta import Paleta


def crear_tarjeta(parent, titulo=None):
    """
    Crea un tk.Frame que se comporta como el .widget del mockup (tarjeta).

    Le da a cada bloque de la pantalla su "caja" visual: fondo oscuro, un
    borde de 1px discreto y, opcionalmente, un label de sección arriba
    (pequeño, gris tenue y en MAYÚSCULAS), igual que los <p class="label">
    de walle_demo.html ("Terminal", "Radar", ...).

    Versión SIMPLE: usa el borde nativo del Frame (highlightbackground),
    que es un rectángulo recto de 1px. Para esquinas redondeadas reales
    existe la variante borde_panel() de base_render.py (dibujada en Canvas).

    Devuelve el Frame creado; el contenido se agrega con pack()/grid()
    dentro de él. Si se pasó titulo, el label ya va empacado arriba.
    """
    marco = tk.Frame(
        parent,
        bg=Paleta.FONDO_WIDGET,
        highlightbackground=Paleta.BORDE_SUAVE,
        highlightthickness=1,
    )

    if titulo is not None:
        etiqueta = tk.Label(
            marco,
            text=titulo.upper(),
            bg=Paleta.FONDO_WIDGET,
            fg=Paleta.TEXTO_TENUE,
            font=("Segoe UI", 8),
        )
        # Espaciado del label: fracciones de la unidad (24 -> 8 / 6).
        etiqueta.pack(anchor="w", padx=Paleta.UNIDAD // 3, pady=(Paleta.UNIDAD // 4, 0))

    return marco
# wall-e-robot/app/widgets/renderizado/tarjeta.py
# Kevin Gámez - 13/09/2026


import tkinter as tk
from ...nucleo.paleta import Paleta


# Largo de cada trazo de los corchetes de esquina (px).
LARGO_CORCHETE = 12
# Desfase de cada corchete respecto al borde de la tarjeta (px).
DESFASE_CORCHETE = 3


def _corchete(parent, ancla, relx, rely, dx, dy, esquina):
    """
    Crea UNA esquina con su corchete HUD (una 'L' de 2 trazos) y la ancla
    a la esquina indicada del panel, así sobrevive a cualquier redimensión
    de la ventana (place + relx/rely la mantiene pegada al borde).

    esquina: 'sup-izq' | 'sup-der' | 'inf-izq' | 'inf-der'
    """
    can = tk.Canvas(
        parent,
        width=LARGO_CORCHETE + 2, height=LARGO_CORCHETE + 2,
        bg=parent.cget("bg"), highlightthickness=0,
    )
    can.place(anchor=ancla, relx=relx, rely=rely, x=dx, y=dy)

    i = 1
    j = LARGO_CORCHETE + 1
    # Cada 'L' apunta hacia adentro de su esquina (a = extremo vertical,
    # b = vértice, c = extremo horizontal de la polilínea).
    if esquina == "sup-izq":
        pts = (i, j, i, i, j, i)
    elif esquina == "sup-der":
        pts = (j, j, j, i, i, i)
    elif esquina == "inf-izq":
        pts = (i, i, i, j, j, j)
    else:  # inf-der
        pts = (j, i, j, j, i, j)

    can.create_line(*pts, fill=Paleta.CYAN_DIM, width=2, joinstyle="miter")
    return can


def subir_decoracion(marco):
    """
    Trae los 4 corchetes HUD de una tarjeta al FRENTE.

    Los corchetes se crean en crear_tarjeta() (antes que el contenido), y en
    Tk un hermano nuevo se apila encima de los viejos: sin este paso, los
    paneles de contenido los taparían. Se llama UNA vez al terminar de armar
    la tarjeta.
    """
    for can in getattr(marco, "_corchetes", []):
        # Nota: en un Canvas, tkraise() de Tkinter es el tag_raise (ítems);
        # para subir la VENTANA hay que invocar el 'raise' de Tcl directo.
        can.tk.call("raise", can._w)


def crear_tarjeta(parent, titulo=None):
    """
    Crea un tk.Frame que se comporta como el .widget del mockup (tarjeta).

    Le da a cada bloque de la pantalla su "caja" visual: fondo de cristal
    oscuro, un borde de 1px discreto y, opcionalmente, un label de sección
    arriba (con su glifo cian "▸" y el texto en MAYÚSCULAS tenue), más los
    4 corchetes HUD que marcan la estética de los paneles de la Nave.

    Devuelve el Frame creado; el contenido se agrega con pack()/grid()
    dentro de él. Si se pasó titulo, el label ya va empacado arriba.
    """
    marco = tk.Frame(
        parent,
        bg=Paleta.FONDO_WIDGET,
        highlightbackground=Paleta.BORDE_SUAVE,
        highlightthickness=1,
    )

    # Corchetes de esquina: se colocan con place() (no ocupan espacio en el
    # pack() del contenido) y se guardan en el frame para poder subirlos
    # después con subir_decoracion(), cuando el contenido ya esté puesto.
    marco._corchetes = [
        _corchete(marco, "nw", 0, 0, DESFASE_CORCHETE, DESFASE_CORCHETE, "sup-izq"),
        _corchete(marco, "ne", 1, 0, -DESFASE_CORCHETE, DESFASE_CORCHETE, "sup-der"),
        _corchete(marco, "sw", 0, 1, DESFASE_CORCHETE, -DESFASE_CORCHETE, "inf-izq"),
        _corchete(marco, "se", 1, 1, -DESFASE_CORCHETE, -DESFASE_CORCHETE, "inf-der"),
    ]

    if titulo is not None:
        fila = tk.Frame(marco, bg=Paleta.FONDO_WIDGET)
        # El título se indenta más allá del corchete superior-izquierdo para
        # que el glifo no lo tape (y la sangría acentúa el look HUD).
        fila.pack(anchor="w",
                  padx=(Paleta.UNIDAD // 3 + LARGO_CORCHETE, Paleta.UNIDAD // 3),
                  pady=(Paleta.UNIDAD // 4, 0))

        # El glifo en cian "enciende" la sección; el texto queda tenue.
        tk.Label(
            fila,
            text="\u25b8 ",                     # ▸
            bg=Paleta.FONDO_WIDGET,
            fg=Paleta.AXIOM_CYAN,
            font=(Paleta.FUENTE_HUD, 9, "bold"),
        ).pack(side="left")
        tk.Label(
            fila,
            text=titulo.upper(),
            bg=Paleta.FONDO_WIDGET,
            fg=Paleta.TEXTO_TENUE,
            font=(Paleta.FUENTE_TEXTO, 8),
        ).pack(side="left")

    return marco

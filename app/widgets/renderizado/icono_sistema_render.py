# wall-e-robot/app/widgets/renderizado/icono_sistema_render.py
# Kevin Gámez - 13/09/2026


import math
from ...widgets.logica.icono_sistema import TipoIcono
from .base_render import RenderizadorBase


class IconoSistemaRenderer(RenderizadorBase):
    """
    Renderer (Tkinter) de un ícono de sistema.

    Cada ícono es una caja pequeña con UN TEXTO (glifo) adentro. Según la
    técnica del mockup, la forma nunca cambia: solo cambia el color según
    si el ícono está activo o apagado (lo decide la lógica).

    Glifos de los íconos (igual que en walle_demo.html):
      ADVERTENCIA -> '!'
      CARGANDO    -> dibuja un RAYO (polygon) en vez de emoji
      MODO_MANUAL -> 'M'
      ERROR       -> 'X'
      CONEXION    -> '▂▄█'
    """

    def __init__(self, widget, canvas, x, y, lado=24):
        """
        Constructor del renderer del ícono.

        x, y, lado: zona (cuadrada) que ocupa el ícono dentro del canvas.
        """
        super().__init__(canvas)
        self.widget = widget
        self.x, self.y = x, y
        self.lado = lado

    def _crear_glifo(self):
        """Crea el ítem (texto o rayo) correspondiente al tipo de ícono."""
        cx, cy = self.x + self.lado / 2, self.y + self.lado / 2
        if self.widget.tipo == TipoIcono.CARGANDO:
            # Un rayo hecho de polígono: ni emoji, ni recurso externo.
            s = self.lado
            puntos = [
                cx + 0.28 * s, cy - 0.30 * s,
                cx - 0.05 * s, cy + 0.10 * s,
                cx + 0.10 * s, cy + 0.10 * s,
                cx - 0.10 * s, cy + 0.30 * s,
                cx + 0.18 * s, cy - 0.05 * s,
                cx + 0.03 * s, cy - 0.05 * s,
            ]
            return self.canvas.create_polygon(puntos, fill=self.widget.color,
                                              outline="")
        glifos = {
            TipoIcono.ADVERTENCIA: "!",
            TipoIcono.MODO_MANUAL: "M",
            TipoIcono.ERROR:       "X",
            TipoIcono.CONEXION:    "\u2582\u2584\u2588",
        }
        return self.canvas.create_text(
            cx, cy, text=glifos[self.widget.tipo],
            font=("Segoe UI", 10, "bold"), fill=self.widget.color,
        )

    def dibujar(self):
        """Dibuja (o actualiza) la caja y el glifo del ícono."""
        borde = self.widget.color if self.widget.activo else "#444444"

        caja = self._primera_vez(
            "caja",
            lambda: self.canvas.create_rectangle(
                self.x, self.y, self.x + self.lado, self.y + self.lado,
                outline=borde, width=1,
            ),
        )
        self.canvas.itemconfig(caja, outline=borde)

        glifo = self._primera_vez("glifo", self._crear_glifo)
        # Si el glifo es un texto (no el polígono del rayo), actualizamos color.
        if self.widget.tipo != TipoIcono.CARGANDO:
            self.canvas.itemconfig(glifo, fill=self.widget.color)
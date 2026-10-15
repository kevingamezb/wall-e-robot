# wall-e-robot/app/widgets/renderizado/icono_sistema_render.py
# Kevin Gámez - 13/09/2026


from ...nucleo.paleta import Paleta
from ...widgets.logica.icono_sistema import TipoIcono
from .base_render import RenderizadorBase, interpolar_color


class IconoSistemaRenderer(RenderizadorBase):
    """Renderer de un ícono de sistema. """
    def __init__(self, widget, canvas, x, y, lado=24):
        """x, y, lado: zona cuadrada que ocupa el ícono dentro del canvas."""
        super().__init__(canvas)
        self.widget    = widget
        self.x, self.y = x, y
        self.lado      = lado

    def _crear_glifo(self):
        """Crea el ítem (texto o rayo) correspondiente al tipo de ícono."""
        cx, cy = self.x + self.lado / 2, self.y + self.lado / 2
        if self.widget.tipo == TipoIcono.CARGANDO:
            # Un rayo hecho de polígono: sin emoji ni recurso externo.
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
            font=(Paleta.FUENTE_HUD, 10, "bold"), fill=self.widget.color,
        )

    def dibujar(self):
        """Dibuja o actualiza el halo, la caja y el glifo del ícono."""
        activo = self.widget.activo
        color = self.widget.color
        borde = color if activo else Paleta.HUD_LINE

        # Halo: relleno diluido detrás de la caja (una sola pieza).
        halo = self._primera_vez(
            "halo",
            lambda: self.canvas.create_rectangle(
                self.x - 2, self.y - 2,
                self.x + self.lado + 2, self.y + self.lado + 2,
                outline="", width=0,
            ),
        )
        caja = self._primera_vez(
            "caja",
            lambda: self.canvas.create_rectangle(
                self.x, self.y, self.x + self.lado, self.y + self.lado,
                outline=borde, width=1,
            ),
        )
        glifo = self._primera_vez("glifo", self._crear_glifo)

        # El ícono solo cambia de color (recoloreo)
        if not self._hay_cambio("estado", (color, activo)):
            return

        self.canvas.itemconfig(halo, fill=interpolar_color(
            color, Paleta.FONDO_WIDGET, 0.80) if activo else Paleta.FONDO_WIDGET)
        self.canvas.itemconfig(caja, outline=borde)
        # El rayo (polígono) conserva el color con que se creó;
        if self.widget.tipo != TipoIcono.CARGANDO:
            self.canvas.itemconfig(glifo, fill=color)

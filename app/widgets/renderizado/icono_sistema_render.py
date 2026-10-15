# wall-e-robot/app/widgets/renderizado/icono_sistema_render.py
# Kevin Gámez - 13/09/2026

# Dibuja un ícono de sistema. Si el PNG de app/recursos/ está exportado se usa
# la imagen (teñida con el color del estado); si no, se cae al glifo procedural
# de siempre (texto o el rayo hecho de polígono).


from ...nucleo.paleta import Paleta
from ...widgets.logica.icono_sistema import TipoIcono
from .base_render import RenderizadorBase, interpolar_color
from . import carga_recursos


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

    def _dibujar_imagen(self, color):
        """Dibuja (o recolorea) el PNG del ícono y oculta el glifo procedural."""
        cx, cy = self.x + self.lado / 2, self.y + self.lado / 2
        foto = carga_recursos.cargar(self.widget.archivo, color, self.lado - 4)

        imagen = self._primera_vez(
            "imagen",
            lambda: self.canvas.create_image(cx, cy, image=foto, anchor="center"),
        )
        self.canvas.coords(imagen, cx, cy)
        self.canvas.itemconfig(imagen, image=foto, state="normal")
        self._ocultar("glifo")

    def _dibujar_glifo(self, color):
        """Dibuja el glifo procedural y oculta la imagen si ya existía."""
        glifo = self._primera_vez("glifo", self._crear_glifo)
        self._ocultar("imagen")
        self.canvas.itemconfig(glifo, state="normal")
        # El rayo (polígono) conserva el color con que se creó.
        if self.widget.tipo != TipoIcono.CARGANDO:
            self.canvas.itemconfig(glifo, fill=color)

    def _ocultar(self, nombre):
        """Oculta un ítem si ya existe."""
        if nombre in self._ids:
            self.canvas.itemconfig(self._ids[nombre], state="hidden")

    def dibujar(self):
        """Dibuja o actualiza el halo, la caja y el glifo/imagen del ícono."""
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

        # Contenido: PNG si existe, si no el glifo procedural.
        if carga_recursos.existe(self.widget.archivo):
            self._dibujar_imagen(color)
        else:
            self._dibujar_glifo(color)

        # El ícono solo cambia de color (recoloreo)
        if not self._hay_cambio("estado", (color, activo)):
            return

        self.canvas.itemconfig(halo, fill=interpolar_color(
            color, Paleta.FONDO_WIDGET, 0.80) if activo else Paleta.FONDO_WIDGET)
        self.canvas.itemconfig(caja, outline=borde)

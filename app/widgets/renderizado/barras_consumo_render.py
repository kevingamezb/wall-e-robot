# wall-e-robot/app/widgets/renderizado/barras_consumo_render.py
# Kevin Gámez - 13/09/2026


from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase


class BarrasConsumoRenderer(RenderizadorBase):
    """
    Renderer (Tkinter) de las barritas de consumo apiladas.

    Recrea el mockup: una columna de 10 barritas horizontales. Se encienden
    desde abajo hacia arriba (column-reverse del HTML). Las apagadas son de
    un gris oscuro y el color de las encendidas lo decide la lógica (más
    consumo = color más caliente: dorado -> naranja -> rojo).

    Parámetros típicos: un canvas de ~40x130 con la columna arriba.
    """

    def __init__(self, widget, canvas, x, y, ancho_barra=26,
                 alto_barra=4, separacion=3):
        """
        Constructor del renderer de barras.

        x, y: esquina inferior-izquierda (las barras crecen hacia arriba).
        """
        super().__init__(canvas)
        self.widget = widget
        self.x, self.y = x, y
        self.ancho_barra = ancho_barra
        self.alto_barra = alto_barra
        self.separacion = separacion

    def dibujar(self):
        """Dibuja (o actualiza) las 10 barritas apiladas de abajo hacia arriba."""
        total = self.widget.TOTAL_BARRISTAS
        encendidas = self.widget.barritas_encendidas
        color = self.widget.color
        apagado = "#2a2a2a"

        for i in range(total):
            # i=0 es la barra de abajo (y crecen hacia arriba).
            base_y = self.y - i * (self.alto_barra + self.separacion)
            barrita = self._primera_vez(
                f"barrita_{i}",
                lambda base_y=base_y: self.canvas.create_rectangle(
                    self.x, base_y - self.alto_barra,
                    self.x + self.ancho_barra, base_y,
                    outline="", width=0,
                ),
            )
            debe_encenderse = i < encendidas
            self.canvas.itemconfig(barrita, fill=color if debe_encenderse else apagado)
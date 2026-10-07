# wall-e-robot/app/widgets/renderizado/barras_consumo_render.py
# Kevin Gámez - 13/09/2026


from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase, interpolar_color


class BarrasConsumoRenderer(RenderizadorBase):
    """
    Renderer (Tkinter) de las barritas de consumo apiladas.

    Recrea el mockup: una columna de 10 barritas horizontales. Se encienden
    desde abajo hacia arriba (column-reverse del HTML). Las apagadas son de
    un azul-estructural tenue y las encendidas llevan un "brillo" superior
    (una línea más clara arriba de cada barrita) que les da relieve sin
    blur real. El color de las encendidas lo decide la lógica (más consumo
    = color más caliente: dorado -> naranja -> rojo).

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
        """Dibuja (o actualiza) las 10 barritas apiladas de abajo hacia arriba.

        La geometría se crea una sola vez; el coloreo se repite solo cuando
        cambia (encendidas, color), para no gastar `itemconfig` en cada ciclo.
        """
        total = self.widget.TOTAL_BARRISTAS
        encendidas = self.widget.barritas_encendidas
        color = self.widget.color
        apagado = Paleta.HUD_LINE

        # Primera vez: crear la geometría de las 10 barritas y su brillo.
        for i in range(total):
            base_y = self.y - i * (self.alto_barra + self.separacion)
            self._primera_vez(
                f"barrita_{i}",
                lambda base_y=base_y: self.canvas.create_rectangle(
                    self.x, base_y - self.alto_barra,
                    self.x + self.ancho_barra, base_y,
                    outline="", width=0,
                ),
            )
            self._primera_vez(
                f"brillo_{i}",
                lambda base_y=base_y: self.canvas.create_rectangle(
                    self.x, base_y - self.alto_barra,
                    self.x + self.ancho_barra, base_y - self.alto_barra + 2,
                    outline="", width=0,
                ),
            )

        # El valor derivado no cambió: no hay nada que repintar.
        if not self._hay_cambio("estado", (encendidas, color)):
            return

        # i=0 es la barra de abajo (y crecen hacia arriba).
        brillo = interpolar_color(color, Paleta.TEXTO_LOG, 0.30)
        for i in range(total):
            base_y = self.y - i * (self.alto_barra + self.separacion)
            barrita = self._ids[f"barrita_{i}"]
            destello = self._ids[f"brillo_{i}"]
            debe_encenderse = i < encendidas
            self.canvas.itemconfig(barrita, fill=color if debe_encenderse else apagado)
            self.canvas.itemconfig(
                destello,
                fill=brillo if debe_encenderse else Paleta.FONDO_WIDGET,
            )
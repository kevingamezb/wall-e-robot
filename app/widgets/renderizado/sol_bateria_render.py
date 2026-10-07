# wall-e-robot/app/widgets/renderizado/sol_bateria_render.py
# Kevin Gámez - 13/09/2026


import math
from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase, interpolar_color


class SolBateriaRenderer(RenderizadorBase):
    """
    Renderer (Tkinter) del Sol de batería.

    Recrea el dibujo del mockup (walle_demo.html): un sol de 12 rayos con
    un círculo en el centro. Los rayos encendidos son MÁS LARGOS (llegan
    más lejos del centro) y del color del estado; los apagados son cortos
    y azul-estructurales. Así "ver" cuánta energía queda es instantáneo.

    Cada rayo encendido lleva UNA capa de halo detrás (más ancha y más
    tenue) que da el "glow" del holograma sin blur real (Tk no lo tiene):
    dos líneas superpuestas, creadas una sola vez.

    Parámetros típicos: un canvas de ~100x100 con centro en (50, 50).
    """

    TOTAL_RAYOS = 12

    def __init__(self, widget, canvas, cx, cy, radio_interior=16,
                 radio_rayo_encendido=44, radio_rayo_apagado=30):
        """
        Constructor del renderer del sol.

        widget               : el SolBateria lógico.
        cx, cy               : centro del sol dentro del canvas.
        radio_interior       : radio del círculo central.
        radio_rayo_encendido : longitud de los rayos encendidos.
        radio_rayo_apagado   : longitud de los rayos apagados.
        """
        super().__init__(canvas)
        self.widget = widget
        self.cx, self.cy = cx, cy
        self.r_in = radio_interior
        self.r_on = radio_rayo_encendido
        self.r_off = radio_rayo_apagado

    def _punto_rayo(self, indice, radio):
        """Devuelve (x1, y1, x2, y2) de una línea de rayo en 'radio'."""
        angulo = (indice / self.TOTAL_RAYOS) * 2 * math.pi - math.pi / 2  # empieza arriba
        vx, vy = math.cos(angulo), math.sin(angulo)
        return (self.cx + vx * (self.r_in + 3),
                self.cy + vy * (self.r_in + 3),
                self.cx + vx * radio,
                self.cy + vy * radio)

    def dibujar(self):
        """Dibuja (o actualiza) los 12 rayos (con halo), el anillo y el núcleo.

        La geometría se crea una sola vez; el estado se repinta solo cuando
        cambia (encendidos, color), para no gastar coords/itemconfig de más.
        """
        encendidos = self.widget.rayos_encendidos
        color = self.widget.color
        apagado = Paleta.HUD_LINE

        # Primera vez: crear los rayos, sus halos y el núcleo central.
        for i in range(self.TOTAL_RAYOS):
            self._primera_vez(
                f"rayo_{i}",
                lambda i=i: self.canvas.create_line(
                    *self._punto_rayo(i, self.r_off),
                    width=5, capstyle="round",
                ),
            )
            self._primera_vez(
                f"halo_{i}",
                lambda i=i: self.canvas.create_line(
                    *self._punto_rayo(i, self.r_off),
                    width=11, capstyle="round",
                ),
            )
        self._primera_vez(
            "circulo",
            lambda: self.canvas.create_oval(
                self.cx - self.r_in, self.cy - self.r_in,
                self.cx + self.r_in, self.cy + self.r_in,
                outline="", width=3,
            ),
        )
        self._primera_vez(
            "nucleo",
            lambda: self.canvas.create_oval(
                self.cx - 8, self.cy - 8, self.cx + 8, self.cy + 8,
                fill="", outline="",
            ),
        )

        # El valor derivado no cambió: no hay nada que repintar.
        if not self._hay_cambio("estado", (encendidos, color)):
            return

        color_halo = interpolar_color(color, Paleta.FONDO_WIDGET, 0.7)
        for i in range(self.TOTAL_RAYOS):
            rayo = self._ids[f"rayo_{i}"]
            halo = self._ids[f"halo_{i}"]
            encendido = i < encendidos
            coords = self._punto_rayo(i, self.r_on if encendido else self.r_off)
            self.canvas.coords(rayo, *coords)
            self.canvas.itemconfig(rayo, fill=color if encendido else apagado)
            # El halo solo aparece "encendido": detrás de cada rayo vivo.
            self.canvas.coords(halo, *coords)
            self.canvas.itemconfig(
                halo,
                fill=color_halo if encendido else Paleta.FONDO_WIDGET,
            )

        # Anillo central: todo encendido si hay energía/carga, tenue si no.
        circulo = self._ids["circulo"]
        color_circulo = color if encendidos > 0 else Paleta.GRIS
        self.canvas.itemconfig(circulo, outline=color_circulo)

        # Núcleo: disco relleno con el color de estado (o apagado).
        nucleo = self._ids["nucleo"]
        self.canvas.itemconfig(
            nucleo,
            fill=color_circulo if encendidos > 0 else Paleta.FONDO_WIDGET,
            outline="",
        )
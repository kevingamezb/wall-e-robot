# wall-e-robot/app/widgets/renderizado/sol_bateria_render.py
# Kevin Gámez - 13/09/2026


import math
from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase


class SolBateriaRenderer(RenderizadorBase):
    """
    Renderer (Tkinter) del Sol de batería.

    Recrea el dibujo del mockup (walle_demo.html): un sol de 12 rayos con
    un círculo en el centro. Los rayos encendidos son MÁS LARGOS (llegan
    más lejos del centro) y del color del estado; los apagados son cortos
    y grises. Así "ver" cuánta energía queda es instantáneo.

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
        """Dibuja (o actualiza) los 12 rayos y el círculo central."""
        encendidos = self.widget.rayos_encendidos
        color = self.widget.color
        apagado = "#333333"

        for i in range(self.TOTAL_RAYOS):
            rayo = self._primera_vez(
                f"rayo_{i}",
                lambda i=i: self.canvas.create_line(
                    *self._punto_rayo(i, self.r_off),
                    width=5, capstyle="round",
                ),
            )
            encendido = i < encendidos
            self.canvas.coords(rayo, *self._punto_rayo(i, self.r_on if encendido else self.r_off))
            self.canvas.itemconfig(rayo, fill=color if encendido else apagado)

        # Círculo central: todo encendido si hay energía/carga, gris si no.
        circulo = self._primera_vez(
            "circulo",
            lambda: self.canvas.create_oval(
                self.cx - self.r_in, self.cy - self.r_in,
                self.cx + self.r_in, self.cy + self.r_in,
                outline="", width=3,
            ),
        )
        color_circulo = color if encendidos > 0 else Paleta.GRIS
        self.canvas.itemconfig(circulo, outline=color_circulo)
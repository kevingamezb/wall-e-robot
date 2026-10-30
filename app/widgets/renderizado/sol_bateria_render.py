# wall-e-robot/app/widgets/renderizado/sol_bateria_render.py
# Kevin Gámez - 13/09/2026
# Rediseño: sol de 8 rayos con contorno, como en el diseño.


import math
from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase
from .recoloreo import Recoloreo


class SolBateriaRenderer(RenderizadorBase):
    """Renderer del Sol de batería."""

    def __init__(self, widget, canvas, e, cx, cy, radio=183):
        """cx, cy, radio: centro y radio exterior del sol, en unidades de diseño."""
        super().__init__(canvas)
        self.widget = widget
        self.e = e
        self.cx, self.cy, self.radio = cx, cy, radio
        self.total = widget.TOTAL_RAYOS

    def _extremos_rayo(self, indice):
        """(x1, y1, x2, y2) en píxeles del rayo 'indice' (el 0 apunta arriba)."""
        e = self.e
        angulo = (indice / self.total) * 2 * math.pi - math.pi / 2
        vx, vy = math.cos(angulo), math.sin(angulo)
        r_ini, r_fin = self.radio * 0.60, self.radio - 17
        return (e(self.cx + vx * r_ini), e(self.cy + vy * r_ini),
                e(self.cx + vx * r_fin), e(self.cy + vy * r_fin))

    def dibujar(self):
        """Dibuja o actualiza los rayos, el anillo y el núcleo."""
        e = self.e
        cx, cy = e(self.cx), e(self.cy)
        grosor = max(3, e(36))
        borde = max(2, e(10))

        for i in range(self.total):
            coords = self._extremos_rayo(i)
            self._primera_vez(
                f"contorno_{i}",
                lambda c=coords: self.canvas.create_line(
                    *c, width=grosor + 2 * borde, capstyle="round"))
            self._primera_vez(
                f"rayo_{i}",
                lambda c=coords: self.canvas.create_line(
                    *c, width=grosor, capstyle="round"))
        r_anillo = e(self.radio * 0.40)
        self._primera_vez(
            "anillo",
            lambda: self.canvas.create_oval(
                cx - r_anillo, cy - r_anillo, cx + r_anillo, cy + r_anillo,
                width=borde))
        r_hueco = e(self.radio * 0.26)
        self._primera_vez(
            "hueco",
            lambda: self.canvas.create_oval(
                cx - r_hueco, cy - r_hueco, cx + r_hueco, cy + r_hueco,
                fill=Paleta.FONDO_WIDGET, width=borde))

        encendidos = self.widget.rayos_encendidos
        color = self.widget.color
        if not self._hay_cambio("estado", (encendidos, color)):
            return

        oscuro = Recoloreo.interpolar(color, "#000000", 0.62)
        for i in range(self.total):
            vivo = i < encendidos
            self.canvas.itemconfig(
                self._ids[f"contorno_{i}"],
                fill=oscuro if vivo else Paleta.FONDO_CANVAS)
            self.canvas.itemconfig(
                self._ids[f"rayo_{i}"],
                fill=color if vivo else Paleta.HUD_LINE)
        self.canvas.itemconfig(
            self._ids["anillo"], fill=color if encendidos > 0 else Paleta.HUD_LINE,
            outline=oscuro if encendidos > 0 else Paleta.FONDO_CANVAS)
        self.canvas.itemconfig(self._ids["hueco"], outline=oscuro
                               if encendidos > 0 else Paleta.FONDO_CANVAS)

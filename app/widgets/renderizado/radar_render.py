# wall-e-robot/app/widgets/renderizado/radar_render.py
# Kevin Gámez - 13/09/2026


import math
from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase


# Rango máximo de lectura (en cm) para mapear la distancia a la pantalla.
RANGO_MAX_CM = 200
# Ángulo (grados) que "lleva" el punto de detección detrás del borde activo.
RETRASO_PUNTO = 10


class RadarRenderer(RenderizadorBase):
    """
    Renderer (Tkinter) del radar de barrido.

    Dibuja el radar del mockup: tres aros de media circunferencia, líneas
    radiales cada 30°, una "cuña" radiante que barre de 0° a 180° y un
    punto que marca dónde se detecta el objeto (más cerca del centro =
    más lejos; en el borde = muy cerca).

    El barrido se anima en cada dibujar(): se llama a widget.avanzar(),
    que mueve el ángulo lógico, y con ese ángulo se reconstruye la cuña.
    """

    def __init__(self, widget, canvas, cx, cy, radio):
        """
        Constructor del renderer.

        cx, cy: centro del radar (en la base, hacia abajo).
        radio : radio del semicírculo.
        """
        super().__init__(canvas)
        self.widget = widget
        self.cx, self.cy = cx, cy
        self.radio = radio

    def _punto(self, angulo_grados, radio):
        """Devuelve (x, y) en el semiplano superior para un ángulo en grados."""
        rad = math.radians(angulo_grados)
        return (self.cx - math.cos(rad) * radio,
                self.cy - math.sin(rad) * radio)

    def _dibujar_fondo(self):
        """Dibuja aros y líneas radiales (todo estático, se crea 1 vez)."""
        # Tres aros concéntricos de media circunferencia.
        for i in range(1, 4):
            r = (self.radio / 3) * i
            self._primera_vez(
                f"aro_{i}",
                lambda r=r: self.canvas.create_arc(
                    self.cx - r, self.cy - r, self.cx + r, self.cy + r,
                    start=0, extent=180, style="arc",
                    outline="#2a2a2a", width=1,
                ),
            )

        # Líneas radiales cada 30°.
        for a in range(0, 181, 30):
            x, y = self._punto(a, self.radio)
            self._primera_vez(
                f"linea_{a}",
                lambda x=x, y=y: self.canvas.create_line(
                    self.cx, self.cy, x, y, fill="#2a2a2a", width=1,
                ),
            )

    def _dibujar_barrido(self):
        """Dibuja (o actualiza) la cuña radiante con el ángulo actual."""
        self.widget.avanzar()
        angulo = self.widget.angulo

        # La cuña cubre desde (angulo - 22°) hasta (angulo).
        a1, a2 = angulo - 22, angulo
        # Puntos a lo largo del arco para que el polígono siga la curva.
        puntos = [self.cx, self.cy]
        for a in range(int(a1), int(a2) + 1):
            px, py = self._punto(float(a), self.radio)
            puntos.extend([px, py])

        cuna = self._primera_vez(
            "cuna",
            lambda: self.canvas.create_polygon(
                puntos, fill=Paleta.DORADO_DIM, outline="", width=0,
            ),
        )
        self.canvas.coords(cuna, *puntos)
        self.canvas.itemconfig(cuna, state="normal")

    def _dibujar_punto(self):
        """Dibuja (o actualiza) el punto rojo del objeto detectado."""
        tiene_objeto = self.widget.hay_obstaculo
        distancia = self.widget.distancia_cm if tiene_objeto else None

        punto = self._primera_vez(
            "punto",
            lambda: self.canvas.create_oval(
                0, 0, 8, 8, fill=Paleta.NARANJA, outline="",
            ),
        )

        if not tiene_objeto:
            self.canvas.itemconfig(punto, state="hidden")
            return

        # Más lejos = más cerca del centro; muy cerca = pegado al borde.
        fraccion = 1 - min(distancia, RANGO_MAX_CM) / RANGO_MAX_CM
        radio_punto = self.radio * (0.12 + 0.55 * fraccion)

        angulo_punto = self.widget.angulo - RETRASO_PUNTO
        px, py = self._punto(angulo_punto, radio_punto)

        self.canvas.coords(punto, px - 4, py - 4, px + 4, py + 4)
        self.canvas.itemconfig(punto, state="normal")

    def dibujar(self):
        """Redibuja el radar completo (fondo una vez, barrido y punto cada ciclo)."""
        self._dibujar_fondo()
        self._dibujar_barrido()
        self._dibujar_punto()
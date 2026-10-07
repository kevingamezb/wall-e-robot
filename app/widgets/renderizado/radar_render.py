# wall-e-robot/app/widgets/renderizado/radar_render.py
# Kevin Gámez - 13/09/2026


import math
from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase, interpolar_color, scanlines, texto_hud


# Rango máximo de lectura (en cm) para mapear la distancia a la pantalla.
RANGO_MAX_CM = 200
# Ángulo (grados) que "lleva" el punto de detección detrás del borde activo.
RETRASO_PUNTO = 10
# Ancho (grados) del "filo" brillante que lidera el barrido.
ANCHO_FILO = 4

# Color de los radios y arcos estáticos de la retícula (línea estructural).
COLOR_RETICULA = Paleta.HUD_LINE
# Color del sector ya barrido (estela tenue del holograma).
COLOR_ESTELA = interpolar_color(Paleta.AXIOM_CYAN, Paleta.FONDO_WIDGET, 0.78)
# Tres capas del punto detectado: halo tenue, cuerpo y núcleo intenso.
CAPAS_PUNTO = (
    (13, interpolar_color(Paleta.NARANJA, Paleta.FONDO_WIDGET, 0.72)),
    (8,  interpolar_color(Paleta.NARANJA, Paleta.FONDO_WIDGET, 0.35)),
    (4,  Paleta.NARANJA),
)


class RadarRenderer(RenderizadorBase):
    """
    Renderer (Tkinter) del radar de barrido.

    Estética holograma de la Nave: retícula azul-espacia, una "cuña" cian
    que barre de 0° a 180° con un filo brillante al frente y un punto
    naranja con halo donde se detecta el objeto (más cerca del centro =
    más lejos; en el borde = muy cerca).

    El barrido se anima en cada dibujar(): se llama a widget.avanzar(),
    que mueve el ángulo lógico, y con ese ángulo se reconstruye la cuña.
    Todo lo estático (retícula, scanlines, etiquetas) se crea 1 vez.
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
        """Dibuja scanlines, arcos, radios, regla base y etiquetas (1 vez)."""
        # Pantalla de barrido: líneas horizontales tenues de fondo.
        self._primera_vez(
            "scanlines",
            lambda: scanlines(self.canvas, 0, 0, self.cx * 2, self.cy,
                              separacion=6),
        )

        # Tres aros concéntricos de media circunferencia + aro-lente.
        for i in range(1, 4):
            r = (self.radio / 3) * i
            self._primera_vez(
                f"aro_{i}",
                lambda r=r: self.canvas.create_arc(
                    self.cx - r, self.cy - r, self.cx + r, self.cy + r,
                    start=0, extent=180, style="arc",
                    outline=COLOR_RETICULA, width=1,
                ),
            )
        self._primera_vez(
            "lente",
            lambda: self.canvas.create_arc(
                self.cx - self.radio, self.cy - self.radio,
                self.cx + self.radio, self.cy + self.radio,
                start=0, extent=180, style="arc",
                outline=Paleta.CYAN_DIM, width=2,
            ),
        )

        # Regla base: la línea de suelo del radar con marcas cada 15°.
        self._primera_vez(
            "base",
            lambda: self.canvas.create_line(
                self.cx - self.radio, self.cy,
                self.cx + self.radio, self.cy,
                fill=Paleta.CYAN_DIM, width=2,
            ),
        )
        for a in range(15, 180, 15):
            largo = 7 if a % 45 == 0 else 4
            x0, y0 = self._punto(a, self.radio)
            x1, y1 = self._punto(a, self.radio - largo)
            self._primera_vez(
                f"marca_{a}",
                lambda x0=x0, y0=y0, x1=x1, y1=y1: self.canvas.create_line(
                    x0, y0, x1, y1, fill=COLOR_RETICULA, width=1,
                ),
            )

        # Líneas radiales cada 30°.
        for a in range(0, 181, 30):
            x, y = self._punto(a, self.radio)
            self._primera_vez(
                f"linea_{a}",
                lambda x=x, y=y: self.canvas.create_line(
                    self.cx, self.cy, x, y, fill=COLOR_RETICULA, width=1,
                ),
            )

        # Etiquetas de grados en los extremos y el cenit (0 / 90 / 180).
        for a, ancla in ((0, "se"), (90, "n"), (180, "sw")):
            x, y = self._punto(a, self.radio - 16)
            self._primera_vez(
                f"grado_{a}",
                lambda x=x, y=y, a=a, ancla=ancla: texto_hud(
                    self.canvas, x, y, f"{a}\u00b0", ancla=ancla,
                    color=Paleta.CYAN_DIM, tamano=7, negrita=False,
                ),
            )

    def _dibujar_barrido(self):
        """Dibuja (o actualiza) la cuña radiante y su filo brillante."""
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
                puntos, fill=COLOR_ESTELA, outline="", width=0,
            ),
        )
        self.canvas.coords(cuna, *puntos)
        self.canvas.itemconfig(cuna, state="normal")

        # Filo: línea viva desde el centro al frente del barrido + punto
        # luminoso en el rim (lo que hace que se sienta "encendido").
        xf, yf = self._punto(a2, self.radio)
        filo = self._primera_vez(
            "filo",
            lambda: self.canvas.create_line(
                self.cx, self.cy, xf, yf,
                fill=Paleta.AXIOM_CYAN, width=2,
            ),
        )
        self.canvas.coords(filo, self.cx, self.cy, xf, yf)

        punta = self._primera_vez(
            "punta",
            lambda: self.canvas.create_oval(
                xf - 3, yf - 3, xf + 3, yf + 3,
                fill=Paleta.AXIOM_CYAN, outline="",
            ),
        )
        self.canvas.coords(punta, xf - 3, yf - 3, xf + 3, yf + 3)

    def _dibujar_punto(self):
        """Dibuja (o actualiza) el punto naranja con halo del obstáculo."""
        tiene_objeto = self.widget.hay_obstaculo
        distancia = self.widget.distancia_cm if tiene_objeto else None

        # El halo completo se crea una vez (3 capas apiladas).
        puntos = self._primera_vez(
            "punto",
            lambda: [
                self.canvas.create_oval(
                    0, 0, 2 * r, 2 * r, fill=color, outline="", width=0,
                )
                for r, color in CAPAS_PUNTO
            ],
        )

        if not tiene_objeto:
            for pid in puntos:
                self.canvas.itemconfig(pid, state="hidden")
            return

        # Más lejos = más cerca del centro; muy cerca = pegado al borde.
        fraccion = 1 - min(distancia, RANGO_MAX_CM) / RANGO_MAX_CM
        radio_punto = self.radio * (0.12 + 0.55 * fraccion)

        angulo_punto = self.widget.angulo - RETRASO_PUNTO
        px, py = self._punto(angulo_punto, radio_punto)

        for pid, (r, _color) in zip(puntos, CAPAS_PUNTO):
            self.canvas.coords(pid, px - r, py - r, px + r, py + r)
            self.canvas.itemconfig(pid, state="normal")

    def dibujar(self):
        """Redibuja el radar completo (fondo una vez, barrido y punto cada ciclo)."""
        self._dibujar_fondo()
        self._dibujar_barrido()
        self._dibujar_punto()

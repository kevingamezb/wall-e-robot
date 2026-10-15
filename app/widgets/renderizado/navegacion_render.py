# wall-e-robot/app/widgets/renderizado/navegacion_render.py
# Kevin Gámez - 13/09/2026


from ...nucleo.paleta import Paleta, color_por_umbral
from .base_render import RenderizadorBase, scanlines, texto_hud


# Cantidad de aros concéntricos del medidor de proximidad.
AROS = 4
# Separación (px) entre la línea base del medidor y la banda de maniobra.
SEPARADOR_MANIOBRA = 48


class NavegacionRenderer(RenderizadorBase):
    """Renderer de la tarjeta Navegación: medidor de proximidad + maniobra."""
    def __init__(self, proximidad, navegacion, canvas, cx, cy, radio):
        super().__init__(canvas)
        self.proximidad  = proximidad
        self.navegacion  = navegacion
        self.cx, self.cy = cx, cy
        self.radio       = radio

    def _dibujar_fondo(self):
        """Dibuja scanlines, aros, base, robot y textos fijos (una sola vez)."""
        self._primera_vez(
            "scanlines",
            lambda: scanlines(self.canvas, 0, 0, self.cx * 2, self.cy,
                              separacion=6),
        )

        # Aros concéntricos de la retícula (apagados hasta que un objeto se
        # acerque). Se indexan de 1 (exterior) a AROS (interior).
        for i in range(1, AROS + 1):
            r = (self.radio / AROS) * i
            self._primera_vez(
                f"aro_{i}",
                lambda r=r: self.canvas.create_arc(
                    self.cx - r, self.cy - r, self.cx + r, self.cy + r,
                    start=0, extent=180, style="arc",
                    outline=Paleta.HUD_LINE, width=1,
                ),
            )

        # Línea base del medidor y eje central (orientación del robot).
        self._primera_vez(
            "base",
            lambda: self.canvas.create_line(
                self.cx - self.radio, self.cy,
                self.cx + self.radio, self.cy,
                fill=Paleta.CYAN_DIM, width=2,
            ),
        )
        self._primera_vez(
            "eje",
            lambda: self.canvas.create_line(
                self.cx, self.cy, self.cx, self.cy - self.radio,
                fill=Paleta.HUD_LINE, width=1,
            ),
        )

        # Punto del robot (centro del medidor).
        self._primera_vez(
            "robot",
            lambda: self.canvas.create_oval(
                self.cx - 6, self.cy - 6, self.cx + 6, self.cy + 6,
                fill=Paleta.CYAN_DIM, outline="",
            ),
        )

        # Etiqueta de distancia, centrada sobre el medidor.
        self._primera_vez(
            "distancia",
            lambda: self.canvas.create_text(
                self.cx, self.cy - self.radio + 12, text="",
                anchor="n", fill=Paleta.TEXTO_TENUE,
                font=(Paleta.FUENTE_HUD, 14, "bold"),
            ),
        )

        # Separador y banda de maniobra (abajo).
        y_sep = self.cy + SEPARADOR_MANIOBRA
        self._primera_vez(
            "separador",
            lambda: self.canvas.create_line(
                40, y_sep, self.cx * 2 - 40, y_sep, fill=Paleta.HUD_LINE, width=1,
            ),
        )
        self._primera_vez(
            "caption",
            lambda: texto_hud(self.canvas, self.cx, y_sep + 12, "MANIOBRA",
                              ancla="n", color=Paleta.TEXTO_TENUE, tamano=8),
        )
        self._primera_vez(
            "maniobra",
            lambda: self.canvas.create_text(
                self.cx, y_sep + 40, text="", anchor="center",
                font=(Paleta.FUENTE_HUD, 15, "bold"),
            ),
        )

    def dibujar(self):
        """Redibuja el medidor y la maniobra solo si cambió su estado."""
        self._dibujar_fondo()

        cercania = self.proximidad.cercania
        hay_obstaculo = self.proximidad.hay_obstaculo
        etiqueta_dist = self.proximidad.etiqueta
        simbolo = self.navegacion.simbolo
        etiqueta_nav = self.navegacion.etiqueta
        color_nav = self.navegacion.color
        color_obstaculo = color_por_umbral(cercania, invertido=True)
        if color_obstaculo == Paleta.GRIS:
            color_obstaculo = Paleta.DORADO

        if not self._hay_cambio("estado", (cercania, hay_obstaculo, etiqueta_dist,
                                           simbolo, etiqueta_nav, color_nav)):
            return

        # Aros: se encienden del exterior hacia el centro a medida que el objeto
        # se acerca. Como mínimo uno si hay lectura.
        encendidos = round(cercania * AROS)
        if hay_obstaculo:
            encendidos = max(1, encendidos)
        for i in range(1, AROS + 1):
            aro = self._ids[f"aro_{i}"]
            # i=1 es el aro exterior: se enciende primero.
            vivo = i <= encendidos
            self.canvas.itemconfig(
                aro,
                outline=color_obstaculo if vivo else Paleta.HUD_LINE,
                width=3 if vivo else 1,
            )

        color_robot = color_obstaculo if hay_obstaculo else Paleta.CYAN_DIM
        self.canvas.itemconfig(self._ids["robot"], fill=color_robot)

        self.canvas.itemconfig(
            self._ids["distancia"],
            text=etiqueta_dist,
            fill=color_obstaculo if hay_obstaculo else Paleta.TEXTO_TENUE,
        )

        self.canvas.itemconfig(
            self._ids["maniobra"],
            text=f"{simbolo}   {etiqueta_nav}",
            fill=color_nav,
        )

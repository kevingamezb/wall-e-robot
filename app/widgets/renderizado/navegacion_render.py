# wall-e-robot/app/widgets/renderizado/navegacion_render.py
# Kevin Gámez - 13/09/2026
# Rediseño: medidor de arcos tipo "señal" a la izquierda y, a la derecha, la
# distancia y el movimiento decidido por el robot.


import math
from ...nucleo.paleta import Paleta, color_por_umbral
from ...nucleo.disenio import Disenio
from ...nucleo.estado import Maniobra
from .base_render import RenderizadorBase
from .texto_render import Texto


# Cantidad de arcos del medidor de proximidad.
AROS = 3
# Por encima de esta distancia (cm) la tarjeta muestra ">100 cm".
DISTANCIA_LEJOS_CM = 100


class NavegacionRenderer(RenderizadorBase):
    """Renderer de la tarjeta Navegación: medidor de proximidad + maniobra."""

    def __init__(self, proximidad, navegacion, canvas, e):
        super().__init__(canvas)
        self.proximidad = proximidad
        self.navegacion = navegacion
        self.e = e
        self._textos = {}

    # Construcción (una sola vez)
    def _construir(self):
        e, c = self.e, self.canvas
        cx, cy = Disenio.RADAR_CENTRO
        grosor = max(3, e(Disenio.RADAR_GROSOR))
        radios = Disenio.RADAR_RADIOS[::-1]          # 1 = exterior
        for i, r in enumerate(radios, start=1):
            self._primera_vez(
                f"aro_{i}",
                lambda r=r: c.create_arc(
                    e(cx - r), e(cy - r), e(cx + r), e(cy + r),
                    start=45, extent=90, style="arc", width=grosor))
            # Extremos redondeados (el arco de Tk termina recto).
            for lado, ang in (("a", 45), ("b", 135)):
                px = cx + r * math.cos(math.radians(ang))
                py = cy - r * math.sin(math.radians(ang))
                rr = Disenio.RADAR_GROSOR / 2
                self._primera_vez(
                    f"punta_{i}{lado}",
                    lambda px=px, py=py, rr=rr: c.create_oval(
                        e(px - rr), e(py - rr), e(px + rr), e(py + rr), width=0))
        rd = 29
        self._primera_vez(
            "robot",
            lambda: c.create_oval(
                e(cx - rd), e(cy - rd), e(cx + rd), e(cy + rd),
                fill=Paleta.DORADO, outline=Paleta.TINTA, width=max(2, e(7))))

        px = e.fuente(68)
        self._textos["dist_t"] = Texto(c, e(Disenio.DISTANCIA_TITULO[0]),
                                       e(Disenio.DISTANCIA_TITULO[1]), "Distancia",
                                       px, Paleta.TINTA, ancla="w",
                                       contorno=Paleta.TINTA, grosor=1)
        self._textos["dist_v"] = Texto(c, e(Disenio.DISTANCIA_VALOR[0]),
                                       e(Disenio.DISTANCIA_VALOR[1]), "",
                                       e.fuente(60), Paleta.TINTA, ancla="w",
                                       contorno=Paleta.TINTA, grosor=1)
        self._textos["mov_t"] = Texto(c, e(Disenio.MOVIMIENTO_TITULO[0]),
                                      e(Disenio.MOVIMIENTO_TITULO[1]), "Movimiento",
                                      px, Paleta.TINTA, ancla="w",
                                      contorno=Paleta.TINTA, grosor=1)
        self._textos["mov_d"] = Texto(c, e(Disenio.MOVIMIENTO_TEXTO[0]),
                                      e(Disenio.MOVIMIENTO_TEXTO[1] + 40), "",
                                      e.fuente(40), Paleta.AZUL, ancla="w",
                                      contorno=Paleta.AZUL, grosor=1)
        self._construir_simbolo()

    def _construir_simbolo(self):
        """Corchetes [ ] fijos y, dentro, el glifo de la maniobra."""
        e, c = self.e, self.canvas
        x1, y1, x2, y2 = Disenio.MOVIMIENTO_SIMBOLO
        w = max(3, e(10))
        t = 20   # largo de los remates del corchete
        self._corchetes = [
            c.create_line(e(x1 + t), e(y1), e(x1), e(y1), e(x1), e(y2), e(x1 + t), e(y2),
                          width=w, joinstyle="miter"),
            c.create_line(e(x2 - t), e(y1), e(x2), e(y1), e(x2), e(y2), e(x2 - t), e(y2),
                          width=w, joinstyle="miter"),
        ]
        self._glifo = c.create_line(0, 0, 0, 0, width=w, joinstyle="miter",
                                    capstyle="projecting")
        self._glifo_caja = c.create_rectangle(0, 0, 0, 0, width=0, state="hidden")

    def _poner_glifo(self, maniobra, manual, color):
        """Dibuja dentro de los corchetes el glifo de la maniobra."""
        e, c = self.e, self.canvas
        x1, y1, x2, y2 = Disenio.MOVIMIENTO_SIMBOLO
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        a = 17   # medio tamaño del glifo
        if manual:
            puntos, caja = (cx - a, cy, cx + a, cy), None
        elif maniobra == Maniobra.DERECHA:
            puntos, caja = (cx - a * .6, cy - a, cx + a * .6, cy, cx - a * .6, cy + a), None
        elif maniobra == Maniobra.IZQUIERDA:
            puntos, caja = (cx + a * .6, cy - a, cx - a * .6, cy, cx + a * .6, cy + a), None
        elif maniobra == Maniobra.RECTO:
            puntos, caja = (cx - a, cy + a * .6, cx, cy - a * .6, cx + a, cy + a * .6), None
        else:   # ALTO: cuadrado
            puntos, caja = None, (cx - a * .8, cy - a * .8, cx + a * .8, cy + a * .8)
        if puntos is not None:
            c.coords(self._glifo, *[e(v) for v in puntos])
            c.itemconfig(self._glifo, fill=color, state="normal")
            c.itemconfig(self._glifo_caja, state="hidden")
        else:
            c.coords(self._glifo_caja, *[e(v) for v in caja])
            c.itemconfig(self._glifo_caja, fill=color, state="normal")
            c.itemconfig(self._glifo, state="hidden")
        for corchete in self._corchetes:
            c.itemconfig(corchete, fill=color)

    @staticmethod
    def _texto_distancia(proximidad):
        """'>100 cm' si está lejos, 'Sin lectura' si no hay dato."""
        if not proximidad.hay_obstaculo:
            return "Sin lectura"
        cm = proximidad.distancia_cm
        return f">{DISTANCIA_LEJOS_CM} cm" if cm > DISTANCIA_LEJOS_CM else f"{cm:.0f} cm"

    def dibujar(self):
        """Redibuja el medidor y la maniobra solo si cambió su estado."""
        if "aro_1" not in self._ids:
            self._construir()

        cercania = self.proximidad.cercania
        hay_obstaculo = self.proximidad.hay_obstaculo
        texto_dist = self._texto_distancia(self.proximidad)
        maniobra = self.navegacion.maniobra
        manual = self.navegacion.en_manual
        descripcion = self.navegacion.descripcion
        color_nav = self.navegacion.color
        color_obstaculo = color_por_umbral(cercania, invertido=True)
        if color_obstaculo == Paleta.GRIS:
            color_obstaculo = Paleta.DORADO

        if not self._hay_cambio("estado", (cercania, hay_obstaculo, texto_dist,
                                           maniobra, manual, descripcion, color_nav)):
            return
        c = self.canvas

        # Arcos: se encienden del exterior hacia el centro al acercarse un objeto.
        encendidos = round(cercania * AROS)
        if hay_obstaculo:
            encendidos = max(1, encendidos)
        for i in range(1, AROS + 1):
            color = color_obstaculo if i <= encendidos else Paleta.FONDO_WIDGET
            c.itemconfig(self._ids[f"aro_{i}"], outline=color)
            for lado in "ab":
                c.itemconfig(self._ids[f"punta_{i}{lado}"], fill=color)

        c.itemconfig(self._ids["robot"],
                     fill=color_obstaculo if hay_obstaculo else Paleta.DORADO)
        self._textos["dist_v"].poner(
            texto=texto_dist,
            color=color_obstaculo if hay_obstaculo and cercania > 0.4 else Paleta.TINTA)
        self._textos["mov_d"].poner(texto=descripcion, color=color_nav)
        self._poner_glifo(maniobra, manual, color_nav)

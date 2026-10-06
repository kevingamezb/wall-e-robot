# wall-e-robot/app/widgets/renderizado/ojos_render.py
# Kevin Gámez - 13/09/2026


from ...nucleo.paleta import Paleta
from ...widgets.logica.ojos import ExpresionOjos
from .base_render import RenderizadorBase


# Geometría base de los ojos (silueta "caja" estilo Wall-E, mientras la
# mejora realista de los ojos queda pendiente).
OJO_ANCHO = 44
SEP_ENTRE_OJOS = 12
OJO_ALTO_ABIERTO = 30
OJO_ALTO_OBSTACULO = 12
PUPILA_ABIERTA = 9
PUPILA_OBSTACULO = 6


class OjosRenderer(RenderizadorBase):
    """
    Renderer (Tkinter) de los ojos de Wall-E.

    Los ojos son el único widget que cambia de SILUETA además de color
    (los planos lo explican: normal/manual/obstáculo/sin datos). Por eso
    este renderer no solo pinta un color distinto: ajusta el alto de la
    "caja" del ojo, la posición de la pupila y si la pupila se ve o no.

    Expresiones:
      NORMAL    -> caja abierta, pupila centrada (DORADO)
      MANUAL    -> pupila mirando "al operador" (hacia adentro, NARANJA)
      OBSTACULO -> caja entrecerrada (ROJO)
      SIN_DATOS -> caja vacía: sin pupila (GRIS)
    """

    def __init__(self, widget, canvas, x=20, y=8):
        """
        Constructor del renderer de los ojos.

        x, y: origen de la caja de dibujo (el ancho total necesario es
        2*OJO_ANCHO + SEP_ENTRE_OJOS = 100px; el alto ~46px).
        """
        super().__init__(canvas)
        self.widget = widget
        self.x = x
        self.y = y
        self.alto_total = OJO_ALTO_ABIERTO + 16  # margen arriba/abajo

    def _coords_caja(self, cx, alto, y_superior):
        """Devuelve (x1, y1, x2, y2) para la caja de un ojo centrada en cx."""
        return (cx - OJO_ANCHO / 2, y_superior,
                cx + OJO_ANCHO / 2, y_superior + alto)

    def _coords_pupila(self, cx, cy, tamano):
        """Devuelve (x1, y1, x2, y2) para la pupila centrada en (cx, cy)."""
        return (cx - tamano / 2, cy - tamano / 2,
                cx + tamano / 2, cy + tamano / 2)

    def dibujar(self):
        """Dibuja (o actualiza) los dos ojos según la expresión lógica."""
        expresion = self.widget.expresion
        color = self.widget.color

        # Posiciones horizontales de cada ojo (izquierdo y derecho).
        cx_izq = self.x + OJO_ANCHO / 2
        cx_der = self.x + 2 * OJO_ANCHO / 2 + SEP_ENTRE_OJOS + OJO_ANCHO / 2

        # Alto de la caja según la expresión.
        alto = OJO_ALTO_ABIERTO if expresion != ExpresionOjos.OBSTACULO else OJO_ALTO_OBSTACULO

        # Desplazamiento horizontal de la pupila: en MANUAL mira hacia
        # adentro (izquierdo a la derecha, derecho a la izquierda).
        desplazamiento = 0
        if expresion == ExpresionOjos.MANUAL:
            desplazamiento = 6

        # Tamaño de la pupila (y si se ve o no).
        if expresion == ExpresionOjos.SIN_DATOS:
            tamano = 0          # no se dibuja pupila
            ver_pupila = False
        elif expresion == ExpresionOjos.OBSTACULO:
            tamano = PUPILA_OBSTACULO
            ver_pupila = True
        else:
            tamano = PUPILA_ABIERTA
            ver_pupila = True

        # Primera vez: crear las cajas y pupilas con su geometría base.
        for lado, cx in (("izq", cx_izq), ("der", cx_der)):
            self._primera_vez(
                f"caja_{lado}",
                lambda cx=cx: self.canvas.create_rectangle(
                    *self._coords_caja(cx, OJO_ALTO_ABIERTO, self.y + 8),
                    fill="", outline=color, width=2,
                ),
            )
            self._primera_vez(
                f"pupila_{lado}",
                lambda cx=cx: self.canvas.create_oval(
                    *self._coords_pupila(cx, self.y + 23, PUPILA_ABIERTA),
                    fill=color, outline="",
                ),
            )

        # La silueta solo cambia con la expresión (y su color): repintar
        # solo entonces, en vez de re-coords en cada ciclo.
        if not self._hay_cambio("estado", (expresion, color)):
            return

        for lado, cx in (("izq", cx_izq), ("der", cx_der)):
            # Caja del ojo (rectángulo gris oscuro sin relleno + borde de color).
            caja = self._ids[f"caja_{lado}"]
            self.canvas.coords(caja, *self._coords_caja(cx, alto, self.y + 8))
            self.canvas.itemconfig(caja, outline=color)

            # Pupila (evita dibujarla si no corresponde).
            pupila = self._ids[f"pupila_{lado}"]
            cx_pupila = cx + (desplazamiento if lado == "izq" else -desplazamiento)
            cy_pupila = self.y + 8 + alto / 2
            self.canvas.coords(pupila, *self._coords_pupila(cx_pupila, cy_pupila, tamano))
            self.canvas.itemconfig(pupila, fill=color)
            self.canvas.itemconfig(
                pupila,
                state="normal" if ver_pupila else "hidden",
            )
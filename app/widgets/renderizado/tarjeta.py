# wall-e-robot/app/widgets/renderizado/tarjeta.py
# Rediseño de la GUI según el diseño
#
# Tarjetas claras con doble contorno, pastilla de alerta y título (Quadrillion),
# más las pantallas oscuras que van dentro de ellas.


from ...nucleo.paleta import Paleta
from ...nucleo.disenio import Disenio
from .base_render import rectangulo_redondeado
from .recoloreo import Recoloreo
from .texto_render import Texto
from . import carga_recursos


def pantalla_oscura(canvas, e, caja, radio=48):
    """Pantalla oscura con contorno negro (p. ej. donde van los ojos o el sol)."""
    x1, y1, x2, y2 = e.caja(caja)
    return rectangulo_redondeado(
        canvas, x1, y1, x2, y2, e(radio),
        fill=Paleta.FONDO_WIDGET, outline=Paleta.TINTA, width=max(2, e(11)))


def linea_vertical(canvas, e, x, y1, y2, grosor):
    """Separador vertical entre zonas de una tarjeta."""
    ancho = max(2, e(grosor))
    return canvas.create_line(e(x), e(y1), e(x), e(y2), fill=Paleta.TINTA,
                              width=ancho, capstyle="round")


class Tarjeta:
    """Una tarjeta del panel: cara, línea interior, pastilla y título."""

    def __init__(self, canvas, e, caja, linea, clave, titulo):
        """
        caja   : caja exterior de la tarjeta (unidades de diseño); None si la cara
                 ya la dibujó otra tarjeta (Consumo y Batería comparten una).
        linea  : caja de la línea interior; None si la tarjeta no la lleva.
        clave  : nombre de la pastilla en Disenio.PASTILLA.
        titulo : texto del rótulo.
        """
        self.canvas = canvas
        self.e = e
        self.cara = None
        if caja is not None:
            x1, y1, x2, y2 = e.caja(caja)
            self.cara = rectangulo_redondeado(
                canvas, x1, y1, x2, y2, e(52),
                fill=Paleta.TARJETA, outline=Paleta.TINTA, width=max(2, e(8)))
        self.linea = None
        if linea is not None:
            lx1, ly1, lx2, ly2 = e.caja(linea)
            self.linea = rectangulo_redondeado(
                canvas, lx1, ly1, lx2, ly2, e(60),
                fill="", outline=Paleta.TINTA, width=max(2, e(9)))

        px, py = Disenio.PASTILLA[clave]
        self._pastilla_xy = (e(px), e(py))
        self._pastilla = None
        self._color_pastilla = None
        self.alertar(Paleta.DORADO)

        self.titulo = Texto(
            canvas, e(px + Disenio.PASTILLA_ANCHO + 18),
            e(py + Disenio.PASTILLA_ALTO / 2), titulo, e.fuente(70),
            Paleta.TINTA, ancla="w", contorno=Paleta.TINTA, grosor=1)

    def alertar(self, color):
        """Pinta la pastilla de alerta del rótulo con 'color'."""
        if color == self._color_pastilla:
            return
        self._color_pastilla = color
        foto = carga_recursos.cargar_ancho(
            "bombillito_alertor", max(8, self.e(Disenio.PASTILLA_ALTO * 0.34)),
            sustituciones=[
                (Paleta.DORADO_BORDE, Recoloreo.interpolar(color, "#000000", 0.62)),
                (Paleta.DORADO, color),
            ])
        if self._pastilla is None:
            self._pastilla = self.canvas.create_image(
                *self._pastilla_xy, image=foto, anchor="nw")
        else:
            self.canvas.itemconfig(self._pastilla, image=foto)

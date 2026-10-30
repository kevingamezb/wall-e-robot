# wall-e-robot/app/widgets/renderizado/texto_render.py
# Kevin Gámez - 29/10/2026

from PIL import Image, ImageDraw, ImageFont, ImageTk

from ... import rutas


ARCHIVO_FUENTE = "Quadrillion Sb.otf"
_FUENTES = {}
_CACHE = {}
_MAX_CACHE = 600


def fuente(px: int):
    """Fuente Quadrillion a 'px' píxeles (cae a la de Pillow si no se halla)."""
    px = max(6, int(px))
    if px not in _FUENTES:
        try:
            _FUENTES[px] = ImageFont.truetype(
                str(rutas.directorio_recursos() / ARCHIVO_FUENTE), px)
        except OSError:
            _FUENTES[px] = ImageFont.load_default(px)
    return _FUENTES[px]


def imagen_texto(texto: str, px: int, color: str, contorno: str | None = None,
                 grosor: int = 0, interlineado: float = 1.1,
                 alinear: str = "left") -> Image.Image:
    """Imagen RGBA (fondo transparente) con 'texto' ya dibujado."""
    tipo = fuente(px)
    grosor = grosor if contorno else 0
    relleno = max(2, grosor + 1)
    medidor = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    izq, arr, der, aba = medidor.multiline_textbbox(
        (0, 0), texto, font=tipo, stroke_width=grosor,
        spacing=round(px * (interlineado - 1)), align=alinear)
    lienzo = Image.new("RGBA", (der - izq + 2 * relleno, aba - arr + 2 * relleno),
                       (0, 0, 0, 0))
    ImageDraw.Draw(lienzo).multiline_text(
        (relleno - izq, relleno - arr), texto, font=tipo, fill=color,
        stroke_width=grosor, stroke_fill=contorno or color,
        spacing=round(px * (interlineado - 1)), align=alinear)
    return lienzo


def foto_texto(texto, px, color, contorno=None, grosor=0, alinear="left"):
    """PhotoImage cacheado del texto pedido."""
    clave = (texto, px, color, contorno, grosor, alinear)
    if clave not in _CACHE:
        if len(_CACHE) >= _MAX_CACHE:
            _CACHE.clear()
        _CACHE[clave] = ImageTk.PhotoImage(
            imagen_texto(texto, px, color, contorno, grosor, alinear=alinear))
    return _CACHE[clave]


class Texto:
    """Un texto en el canvas que solo se redibuja cuando algo cambia."""

    def __init__(self, canvas, x, y, texto, px, color, ancla="nw",
                 contorno=None, grosor=0, alinear="left", estado="normal"):
        self.canvas = canvas
        self.px = px
        self.contorno = contorno
        self.grosor = grosor
        self.alinear = alinear
        self._texto = texto
        self._color = color
        self._foto = foto_texto(texto, px, color, contorno, grosor, alinear)
        self.id = canvas.create_image(x, y, image=self._foto, anchor=ancla,
                                      state=estado)

    def poner(self, texto=None, color=None, px=None, contorno=None):
        """Cambia el texto, el color, el tamaño y/o el contorno (no hace nada
        si no cambió nada)."""
        texto = self._texto if texto is None else texto
        color = self._color if color is None else color
        px = self.px if px is None else px
        contorno = self.contorno if contorno is None else contorno
        if (texto == self._texto and color == self._color and px == self.px
                and contorno == self.contorno):
            return
        self._texto, self._color = texto, color
        self.px, self.contorno = px, contorno
        self._foto = foto_texto(texto, self.px, color, self.contorno,
                                self.grosor, self.alinear)
        self.canvas.itemconfig(self.id, image=self._foto)

    def mover(self, x, y):
        self.canvas.coords(self.id, x, y)

    def mostrar(self, visible=True):
        self.canvas.itemconfig(self.id, state="normal" if visible else "hidden")

    @property
    def texto(self):
        return self._texto

    def caja(self):
        """(x1, y1, x2, y2) actual del texto en el canvas."""
        return self.canvas.bbox(self.id)

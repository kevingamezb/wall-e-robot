# wall-e-robot/app/widgets/renderizado/texto_render.py
# Kevin Gámez - 29/10/2026

from PIL import Image, ImageDraw, ImageFont, ImageTk

from ... import rutas


ARCHIVO_FUENTE = "Quadrillion Sb.otf"
# Quadrillion no trae flechas (↑ ↓ ← →) ni otros signos: para esas teclas se
# usa una fuente del sistema que sí los tenga.
RUTAS_RESPALDO = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
)
_FUENTES = {}
_FUENTES_RESPALDO = {}
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


def fuente_respaldo(px: int):
    """Fuente del sistema para los glifos que Quadrillion no incluye."""
    px = max(6, int(px))
    if px not in _FUENTES_RESPALDO:
        for ruta in RUTAS_RESPALDO:
            try:
                _FUENTES_RESPALDO[px] = ImageFont.truetype(ruta, px)
                break
            except OSError:
                continue
        else:
            _FUENTES_RESPALDO[px] = ImageFont.load_default(px)
    return _FUENTES_RESPALDO[px]


def faltan_glifos(texto: str, tipo) -> bool:
    """True si 'tipo' no dibuja alguno de los caracteres de 'texto'."""
    referencia = tipo.getmask("\U0010FFFF")
    firma = (referencia.size, bytes(referencia))
    for caracter in texto:
        if caracter.isspace():
            continue
        mascara = tipo.getmask(caracter)
        if (mascara.size, bytes(mascara)) == firma:
            return True
    return False


def imagen_texto(texto: str, px: int, color: str, contorno: str | None = None,
                 grosor: int = 0, interlineado: float = 1.1,
                 alinear: str = "left", tipo=None) -> Image.Image:
    """Imagen RGBA (fondo transparente) con 'texto' ya dibujado."""
    tipo = tipo or fuente(px)
    grosor = grosor if contorno else 0
    relleno = max(2, grosor + 1)
    medidor = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    izq, arr, der, aba = medidor.multiline_textbbox(
        (0, 0), texto, font=tipo, stroke_width=grosor,
        spacing=round(px * (interlineado - 1)), align=alinear)
    lienzo = Image.new("RGBA",
                       (int(der - izq + 2 * relleno),
                        int(aba - arr + 2 * relleno)),
                       (0, 0, 0, 0))
    ImageDraw.Draw(lienzo).multiline_text(
        (relleno - izq, relleno - arr), texto, font=tipo, fill=color,
        stroke_width=grosor, stroke_fill=contorno or color,
        spacing=round(px * (interlineado - 1)), align=alinear)
    return lienzo


def foto_texto(texto, px, color, contorno=None, grosor=0, alinear="left",
               respaldo=False, master=None):
    """PhotoImage cacheado del texto pedido.

    respaldo=True usa una fuente del sistema cuando Quadrillion no tiene
    alguno de los glifos (p. ej. las flechas del teclado). 'master' fija el
    intérprete de Tk y la caché (una por raíz, para que dos intérpretes no
    compartan la misma PhotoImage).
    """
    tipo = fuente(px)
    if respaldo and faltan_glifos(texto, tipo):
        tipo = fuente_respaldo(px)
    # La caché vive en la raíz de Tk: al destruirla se liberan sus imágenes y
    # dos raíces distintas (como en las pruebas) nunca comparten PhotoImage.
    if master is not None:
        raiz = master.winfo_toplevel()
        cache = getattr(raiz, "_cache_texto_quadrillion", None)
        if cache is None:
            cache = {}
            raiz._cache_texto_quadrillion = cache
    else:
        cache = _CACHE
    clave = (texto, px, color, contorno, grosor, alinear, tipo)
    if clave not in cache:
        if len(cache) >= _MAX_CACHE:
            cache.clear()
        cache[clave] = ImageTk.PhotoImage(
            imagen_texto(texto, px, color, contorno, grosor, alinear=alinear,
                         tipo=tipo), master=master)
    return cache[clave]


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
        self._foto = foto_texto(texto, px, color, contorno, grosor, alinear,
                                master=canvas)
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
                                self.grosor, self.alinear, master=self.canvas)
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

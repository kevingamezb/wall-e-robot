# wall-e-robot/app/widgets/renderizado/boton_imagen_render.py
# Kevin Gámez - 30/10/2026


import math
from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase
from .texto_render import Texto, imagen_texto
from . import carga_recursos


def sector_circular(cx, cy, r_min, r_max, direccion):
    """Función 'está dentro' de un sector de corona circular.

    direccion: 'arriba' | 'abajo' | 'izquierda' | 'derecha'. El sector abarca
    ±45° alrededor de esa dirección. Sirve para que cada flecha del mando solo
    reaccione dentro de su forma y no en toda su caja rectangular.
    """
    angulos = {"derecha": 0, "abajo": 90, "izquierda": 180, "arriba": 270}
    centro = angulos[direccion]

    def dentro(x, y):
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy)
        if not (r_min <= r <= r_max):
            return False
        ang = math.degrees(math.atan2(dy, dx)) % 360
        return abs((ang - centro + 180) % 360 - 180) <= 45
    return dentro


class BotonImagenRenderer(RenderizadorBase):
    """Renderer de un Boton lógico con aspecto de imagen."""

    def __init__(self, widget, canvas, x, y, ancho, recurso, rotar=0,
                 variantes=None, texto=None, texto_px=0, texto_color=None,
                 dentro=None):
        """
        x, y      : esquina superior-izquierda (px).
        ancho     : ancho final en px (ya rotado).
        recurso   : nombre del PNG en recursos.
        variantes : {'reposo'|'hover'|'presionado'|'apagado': [(origen, destino)]}
                    sustituciones de color para cada estado.
        texto     : etiqueta centrada sobre la imagen (opcional).
        dentro    : función (x, y) -> bool para acotar la zona sensible.
        """
        super().__init__(canvas)
        self.widget = widget
        self.x, self.y = x, y
        self.ancho = ancho
        self.recurso = recurso
        self.rotar = rotar
        self.variantes = variantes or {}
        self.dentro = dentro
        self._texto_def = (texto, texto_px, texto_color)
        self._texto = None

    @staticmethod
    def _px_que_cabe(texto, px, ancho_boton):
        """Tamaño de letra (<= px) con que 'texto' cabe en el 82% del botón."""
        while px > 8 and imagen_texto(texto, px, "#000000").width > ancho_boton * 0.82:
            px -= 2
        return px

    def _foto(self, estado):
        return carga_recursos.cargar_ancho(
            self.recurso, self.ancho, rotar=self.rotar,
            sustituciones=self.variantes.get(estado, ()), master=self.canvas)

    def _estado(self):
        if not self.widget.habilitado:
            return "apagado"
        if self.widget.presionado:
            return "presionado"
        if self.widget.en_hover:
            return "hover"
        return "reposo"

    # Eventos (se filtran con 'dentro' si la forma no es rectangular)
    def _acepta(self, evento):
        return self.dentro is None or self.dentro(evento.x, evento.y)

    def _al_presionar(self, evento):
        if self._acepta(evento):
            self.widget.presionar()

    def _al_soltar(self, _evento):
        self.widget.soltar()

    def _al_mover(self, evento):
        dentro = self._acepta(evento)
        if dentro and not self.widget.en_hover:
            self.widget.entrar_hover()
            self.canvas.configure(cursor="hand2")
        elif not dentro and self.widget.en_hover:
            self._al_salir(evento)

    def _al_salir(self, _evento):
        self.widget.salir_hover()
        if self.widget.presionado:
            self.widget.soltar()
        self.canvas.configure(cursor="")

    def mostrar(self, visible: bool):
        """Muestra u oculta el botón (imagen y etiqueta)."""
        estado = "normal" if visible else "hidden"
        if "imagen" in self._ids:
            self.canvas.itemconfig(self._ids["imagen"], state=estado)
        if self._texto is not None:
            self._texto.mostrar(visible)

    def dibujar(self):
        """Dibuja (o actualiza) la imagen del estado actual y su etiqueta."""
        estado = self._estado()
        foto = self._foto(estado)
        imagen = self._primera_vez(
            "imagen",
            lambda: self.canvas.create_image(self.x, self.y, image=foto,
                                             anchor="nw"))

        # Texto centrado (la etiqueta del botón lógico puede cambiar en vivo).
        _, px, color = self._texto_def
        if px:
            texto = self.widget.texto
            px_ajustado = self._px_que_cabe(texto, px, foto.width())
            if self._texto is None:
                self._texto = Texto(
                    self.canvas, self.x + foto.width() / 2,
                    self.y + foto.height() / 2, texto, px_ajustado,
                    color or Paleta.TINTA, ancla="center")
            self._texto.poner(texto=texto, px=px_ajustado)

        if self._hay_cambio("estado", estado):
            self.canvas.itemconfig(imagen, image=foto)
            self._foto_actual = foto   # evita que Tk libere la imagen

        # Enlaces idempotentes de eventos.
        self.canvas.tag_bind(imagen, "<ButtonPress-1>", self._al_presionar)
        self.canvas.tag_bind(imagen, "<ButtonRelease-1>", self._al_soltar)
        self.canvas.tag_bind(imagen, "<Motion>", self._al_mover)
        self.canvas.tag_bind(imagen, "<Leave>", self._al_salir)
        if self._texto is not None:
            for evento, accion in (("<ButtonPress-1>", self._al_presionar),
                                   ("<ButtonRelease-1>", self._al_soltar),
                                   ("<Motion>", self._al_mover)):
                self.canvas.tag_bind(self._texto.id, evento, accion)

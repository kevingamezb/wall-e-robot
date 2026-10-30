# wall-e-robot/app/widgets/renderizado/deslizador_render.py
# Kevin Gámez - 13/09/2026
# Rediseño: pista oscura redondeada y perilla gris con centro dorado.


from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase, rectangulo_redondeado
from .recoloreo import Recoloreo


class DeslizadorRenderer(RenderizadorBase):
    """Renderer de un Deslizador lógico."""
    def __init__(self, widget, canvas, x, y, largo,
                 orientacion="horizontal", alto_pista=6, radio_thumb=10):
        """Inicializa la pista y el estado de interacción.

        x, y        : extremo de la pista (horizontal: izquierdo; vertical:
                      superior), sobre su eje central.
        largo       : longitud de la pista (horizontal: ancho, vertical: alto).
        orientacion : 'horizontal' | 'vertical'.
        alto_pista  : grosor de la pista (px).
        radio_thumb : radio de la perilla (px).
        """
        super().__init__(canvas)
        self.widget = widget
        self.x, self.y = x, y
        self.largo = largo
        self.orientacion = orientacion
        self.alto_pista = alto_pista
        self.radio_thumb = radio_thumb
        self._ultimo_enviado = None  # evita reenviar el mismo valor y saturar avisos
        self._arrastrando = False
        self._en_hover = False

    # Conversiones de coordenadas
    def _minimo(self):
        return min(self.widget.rango)

    def _maximo(self):
        return max(self.widget.rango)

    def _valor_a_pixel(self, valor):
        """Devuelve (px, py) del centro del thumb para un valor dado."""
        factor = (valor - self._minimo()) / (self._maximo() - self._minimo())
        if self.orientacion == "horizontal":
            return self.x + factor * self.largo, self.y
        # vertical: el valor máximo queda arriba (1-factor)
        return self.x, self.y + (1 - factor) * self.largo

    def _pixel_a_valor(self, px, py):
        """Convierte una coordenada del mouse al valor de deslizador más cercano."""
        if self.orientacion == "horizontal":
            factor = max(0.0, min(1.0, (px - self.x) / self.largo))
        else:
            factor = max(0.0, min(1.0, (self.y + self.largo - py) / self.largo))
        return self._minimo() + factor * (self._maximo() - self._minimo())

    # Eventos del mouse
    def _al_presionar(self, evento):
        """Mueve el thumb hasta el mouse y habilita el arrastre."""
        self._arrastrando = True
        self._aplicar_posicion(evento.x, evento.y)

    def _al_arrastrar(self, evento):
        if self._arrastrando:
            self._aplicar_posicion(evento.x, evento.y)

    def _al_soltar(self, _evento):
        self._arrastrando = False

    def _al_entrar(self, _evento):
        """Activa el cursor de agarre y el estado hover del thumb."""
        self._en_hover = True
        self.canvas.configure(cursor="hand2")

    def _al_salir(self, _evento):
        self._en_hover = False
        self.canvas.configure(cursor="")

    def _aplicar_posicion(self, px, py):
        """Entrega al deslizador lógico el valor bajo el mouse, solo si cambió.

        Así no se repite el mismo aviso en cada píxel.
        """
        valor = round(self._pixel_a_valor(px, py))
        if valor != self._ultimo_enviado:
            self._ultimo_enviado = valor
            self.widget.mover(valor)

    # Dibujo
    def _centro_thumb(self):
        return self._valor_a_pixel(self.widget.posicion)

    def dibujar(self):
        """Dibuja o actualiza la pista y la perilla."""
        mitad = self.alto_pista / 2
        if self.orientacion == "horizontal":
            caja = (self.x - mitad, self.y - mitad,
                    self.x + self.largo + mitad, self.y + mitad)
        else:
            caja = (self.x - mitad, self.y - mitad,
                    self.x + mitad, self.y + self.largo + mitad)
        pista = self._primera_vez(
            "pista",
            lambda: rectangulo_redondeado(
                self.canvas, *caja, mitad,
                fill=Paleta.FONDO_WIDGET, outline=Paleta.TINTA,
                width=max(1, round(self.alto_pista * 0.18))),
        )

        activo = self._arrastrando or self._en_hover
        r = self.radio_thumb + (2 if self._arrastrando else 0)
        px, py = self._centro_thumb()
        grosor = max(1, round(self.radio_thumb * 0.14))

        thumb = self._primera_vez(
            "thumb",
            lambda: self.canvas.create_oval(
                px - r, py - r, px + r, py + r,
                fill="#9a9a9a", outline=Paleta.TINTA, width=grosor),
        )
        r_in = r * 0.42
        centro = self._primera_vez(
            "centro",
            lambda: self.canvas.create_oval(
                px - r_in, py - r_in, px + r_in, py + r_in,
                fill=Paleta.DORADO, outline=Paleta.DORADO_BORDE, width=grosor),
        )
        self.canvas.coords(thumb, px - r, py - r, px + r, py + r)
        self.canvas.coords(centro, px - r_in, py - r_in, px + r_in, py + r_in)
        self.canvas.itemconfig(thumb, fill="#c9c9c9" if activo else "#9a9a9a")

        # Enlaza la interacción sobre pista y perilla (idempotente).
        for item in (pista, thumb, centro):
            self.canvas.tag_bind(item, "<ButtonPress-1>", self._al_presionar)
            self.canvas.tag_bind(item, "<B1-Motion>", self._al_arrastrar)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self._al_soltar)
            self.canvas.tag_bind(item, "<Enter>", self._al_entrar)
            self.canvas.tag_bind(item, "<Leave>", self._al_salir)

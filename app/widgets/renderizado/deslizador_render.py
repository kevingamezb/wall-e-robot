# wall-e-robot/app/widgets/renderizado/deslizador_render.py
# Kevin Gámez - 13/09/2026


from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase, interpolar_color


class DeslizadorRenderer(RenderizadorBase):
    """Renderer de un Deslizador lógico."""

    def __init__(self, widget, canvas, x, y, largo,
                 orientacion="horizontal", alto_pista=6, radio_thumb=10):
        """
        x, y        : esquina superior-izquierda de la pista.
        largo       : longitud de la pista (horizontal: ancho, vertical: alto).
        orientacion : 'horizontal' | 'vertical'.
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
        """
        Entrega al deslizador lógico el valor bajo el mouse, solo si cambió,
        para no repetir el mismo aviso en cada píxel.
        """
        valor = round(self._pixel_a_valor(px, py))
        if valor != self._ultimo_enviado:
            self._ultimo_enviado = valor
            self.widget.mover(valor)

    # Dibujo
    def dibujar(self):
        """Dibuja o actualiza la pista, sus marcas, el halo y el thumb."""
        # Pista: banda fina que representa el recorrido, centrada en la
        # posición (x, y) y orientada según el eje.
        if self.orientacion == "horizontal":
            pista1 = (self.x, self.y - self.alto_pista / 2,
                      self.x + self.largo, self.y + self.alto_pista / 2)
        else:
            pista1 = (self.x - self.alto_pista / 2, self.y,
                      self.x + self.alto_pista / 2, self.y + self.largo)

        pista = self._primera_vez(
            "pista",
            lambda: self.canvas.create_rectangle(
                *pista1, fill=Paleta.HUD_LINE, outline="",
            ),
        )
        self._dibujar_ticks()

        # El thumb cambia de tamaño y color según el estado, igual que el
        # control del mockup: apagado en reposo, más claro con el mouse encima,
        # y grande y brillante al arrastrar.
        activo = self._arrastrando or self._en_hover
        thumb_radio = self.radio_thumb + (2 if self._arrastrando else 0)
        color_thumb = Paleta.DORADO if activo else Paleta.DORADO_DIM
        px, py = self._valor_a_pixel(self.widget.posicion)

        # Halo del thumb: un disco tenue detrás que acompaña el agarre.
        halo = self._primera_vez(
            "halo",
            lambda: self.canvas.create_oval(
                px - thumb_radio - 5, py - thumb_radio - 5,
                px + thumb_radio + 5, py + thumb_radio + 5,
                fill=interpolar_color(color_thumb, Paleta.FONDO_WIDGET, 0.75),
                outline="",
            ),
        )
        self.canvas.coords(
            halo,
            px - thumb_radio - 5, py - thumb_radio - 5,
            px + thumb_radio + 5, py + thumb_radio + 5,
        )
        self.canvas.itemconfig(
            halo, fill=interpolar_color(color_thumb, Paleta.FONDO_WIDGET, 0.75),
        )
        self.canvas.itemconfig(halo, state="normal" if activo else "hidden")

        thumb = self._primera_vez(
            "thumb",
            lambda: self.canvas.create_oval(
                px - thumb_radio, py - thumb_radio,
                px + thumb_radio, py + thumb_radio,
                fill=color_thumb, outline="",
            ),
        )
        self.canvas.coords(
            thumb,
            px - thumb_radio, py - thumb_radio,
            px + thumb_radio, py + thumb_radio,
        )
        self.canvas.itemconfig(thumb, fill=color_thumb)

        # Enlaza la interacción sobre pista y thumb. Es idempotente: volver a
        # enlazar sobrescribe los manejadores anteriores. El cursor pertenece
        # al canvas porque Tk no lo define por ítem.
        for item in (pista, thumb):
            self.canvas.tag_bind(item, "<ButtonPress-1>", self._al_presionar)
            self.canvas.tag_bind(item, "<B1-Motion>", self._al_arrastrar)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self._al_soltar)
            self.canvas.tag_bind(item, "<Enter>", self._al_entrar)
            self.canvas.tag_bind(item, "<Leave>", self._al_salir)

    def _dibujar_ticks(self):
        """Dibuja las marcas de los extremos y del centro (0° si cae en el rango)."""
        # La marca es perpendicular a la pista: vertical en un deslizador
        # horizontal y horizontal en uno vertical.
        es_horizontal = self.orientacion == "horizontal"

        def _crear_marca(px, py):
            if es_horizontal:
                return self.canvas.create_line(
                    px, self.y - 5, px, self.y + 5,
                    fill=Paleta.CYAN_DIM, width=1,
                )
            return self.canvas.create_line(
                self.x - 5, py, self.x + 5, py,
                fill=Paleta.CYAN_DIM, width=1,
            )

        # Extremos y centro: min, max y 0° (o el punto medio si 0 no cae
        # dentro del rango del eje).
        extremos = (self._minimo(), self._maximo())
        centro = 0.0 if extremos[0] <= 0 <= extremos[1] else \
            sum(extremos) / 2
        marcas = {
            "marca_min":  self._valor_a_pixel(extremos[0]),
            "marca_max":  self._valor_a_pixel(extremos[1]),
            "marca_cero": self._valor_a_pixel(centro),
        }
        for clave, (px, py) in marcas.items():
            self._primera_vez(clave, lambda px=px, py=py: _crear_marca(px, py))

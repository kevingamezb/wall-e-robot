# wall-e-robot/app/widgets/renderizado/deslizador_render.py
# Kevin Gámez - 13/09/2026


from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase


class DeslizadorRenderer(RenderizadorBase):
    """
    El renderer (Tkinter) de un Deslizador lógico.

    A diferencia del botón, este renderer es INTERACTIVO de verdad: mapea
    la posición del mouse dentro de la pista a un valor dentro del rango
    del deslizador, y se lo pasa a widget.mover() mientras el usuario
    presiona/arrastra (eso es lo que dispara los avisos a los suscriptores).

    Puede dibujarse horizontal o vertical (para el cuello y los hombros).

    Convención de eje:
      - horizontal: los valores crecen de izquierda a derecha.
      - vertical:   los valores crecen de abajo hacia arriba (como una regla).
    """

    def __init__(self, widget, canvas, x, y, largo,
                 orientacion="horizontal", alto_pista=6, radio_thumb=10):
        """
        Constructor del renderer del deslizador.

        widget      : el Deslizador lógico.
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
        self._ultimo_enviado = None  # evita reenviar el mismo ángulo y "spamear"
        self._arrastrando = False
        self._en_hover = False

    # --- Conversiones de coordenadas ---

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

    # --- Eventos del mouse ---

    def _al_presionar(self, evento):
        """Agarra la pista: mueve el thumb hasta el mouse y habilita arrastre."""
        self._arrastrando = True
        self._aplicar_posicion(evento.x, evento.y)

    def _al_arrastrar(self, evento):
        """Mientras se arrastra, sigue moviendo el thumb."""
        if self._arrastrando:
            self._aplicar_posicion(evento.x, evento.y)

    def _al_soltar(self, _evento):
        """Suelta la pista: termina el arrastre."""
        self._arrastrando = False

    def _al_entrar(self, _evento):
        """El mouse entró sobre la pista: cursor de "agarre" y thumb iluminado."""
        self._en_hover = True
        self.canvas.configure(cursor="hand2")

    def _al_salir(self, _evento):
        """El mouse salió de la pista: se restaura cursor y thumb."""
        self._en_hover = False
        self.canvas.configure(cursor="")

    def _aplicar_posicion(self, px, py):
        """
        Pasa al deslizador lógico el valor bajo el mouse (solo si cambió)
        para no bombardear al robot con el mismo ángulo en cada píxel.
        """
        valor = round(self._pixel_a_valor(px, py))
        if valor != self._ultimo_enviado:
            self._ultimo_enviado = valor
            self.widget.mover(valor)

    # --- Dibujo ---

    def dibujar(self):
        """Dibuja (o actualiza) la pista y el thumb del deslizador."""
        # Pista: banda fina que indica el recorrido. Según la orientación,
        # la banda es un rectángulo horizontal o vertical centrado en (x, y).
        if self.orientacion == "horizontal":
            pista1 = (self.x, self.y - self.alto_pista / 2,
                      self.x + self.largo, self.y + self.alto_pista / 2)
        else:
            pista1 = (self.x - self.alto_pista / 2, self.y,
                      self.x + self.alto_pista / 2, self.y + self.largo)

        pista = self._primera_vez(
            "pista",
            lambda: self.canvas.create_rectangle(
                *pista1, fill="#333333", outline="",
            ),
        )
        # El thumb cambia de tamaño/color según el estado, como el
        # ::-webkit-slider-thumb del mockup: reposo apagado, con el mouse
        # encima más claro, y al arrastrar grande y brillante.
        thumb_radio = self.radio_thumb + (2 if self._arrastrando else 0)
        color_thumb = (Paleta.DORADO
                       if (self._arrastrando or self._en_hover)
                       else Paleta.DORADO_DIM)
        px, py = self._valor_a_pixel(self.widget.posicion)
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

        # Bindings de interacción sobre pista y thumb (idempotente: los
        # re-anotamos cada vez, los eventos viejos se sobrescriben). El
        # cursor no existe por ítem en Tk, así que se cambia el del canvas.
        for item in (pista, thumb):
            self.canvas.tag_bind(item, "<ButtonPress-1>", self._al_presionar)
            self.canvas.tag_bind(item, "<B1-Motion>", self._al_arrastrar)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self._al_soltar)
            self.canvas.tag_bind(item, "<Enter>", self._al_entrar)
            self.canvas.tag_bind(item, "<Leave>", self._al_salir)
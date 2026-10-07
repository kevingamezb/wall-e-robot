# wall-e-robot/app/widgets/renderizado/boton_render.py
# Kevin Gámez - 13/09/2026


import tkinter as tk
from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase, rectangulo_redondeado, interpolar_color


# La transición de color del botón: un "fade" corto en vez de un salto seco.
PASOS_TRANSICION = 6
INTERVALO_TRANSICION_MS = 16


class BotonRenderer(RenderizadorBase):
    """
    El renderer (Tkinter) de un Boton lógico.

    Recibe:
      - widget: el Boton lógico (widgets/logica/boton.py), que NO sabe nada
        de Tkinter. Aquí es donde Tkinter finalmente sí existe.
      - canvas: el Canvas donde dibujar.
      - x, y, ancho, alto: la zona que ocupa el botón (en píxeles).

    Su trabajo es triple:
      1. DIBUJAR el botón según el estado lógico (fondo, borde y texto).
      2. CONECTAR los eventos reales del framework (clic y hover del mouse)
         al widget lógico (widget.presionar()/soltar()/entrar_hover()/salir_hover()).
      3. SUAVIZAR el cambio de color con una mini-animación (fallo corto con
         canvas.after), para que presionar se sienta táctil y no como un
         interruptor de luz.
    """

    def __init__(self, widget, canvas, x, y, ancho, alto,
                 texto=None, radio_esquinas=Paleta.RADIO_BOTON, tamano_fuente=9):
        """
        Constructor del renderer del botón.

        texto: etiqueta a mostrar (si se omite, usa widget.texto). Permite
        que el gamepad muestre flechas (▲◀▶▼) en lugar de "ARRIBA"/"ABAJO".

        radio_esquinas: por defecto usa Paleta.RADIO_BOTON para que todos
        los botones compartan el mismo lenguaje visual.

        tamano_fuente: las flechas del d-pad piden una fuente grande (16),
        los botones de texto una mediana (9-10). Como el mockup.
        """
        super().__init__(canvas)
        self.widget = widget
        self.x, self.y = x, y
        self.ancho, self.alto = ancho, alto
        self.texto = texto if texto is not None else widget.texto
        self.radio_esquinas = radio_esquinas
        self.tamano_fuente = tamano_fuente

        # Estado interno de la animación de color.
        self._color_visual = None   # el color aplicado HOY (lo que se ve)
        self._color_origen = None   # desde dónde parte la animación actual
        self._color_destino = None  # hacia dónde va (None = sin animar)
        self._paso = 0

    # --- Traducción de eventos del mouse a estados lógicos ---

    def _al_presionar(self, _evento):
        """El clic del mouse se traduce a 'presionado' en la lógica."""
        self.widget.presionar()

    def _al_soltar(self, _evento):
        """Soltar el botón del mouse se traduce a 'soltado'."""
        self.widget.soltar()

    def _al_entrar(self, _evento):
        """El mouse entró: el botón pasa a estado de hover (y cursor de mano)."""
        self.widget.entrar_hover()
        self.canvas.configure(cursor="hand2")

    def _al_salir(self, _evento):
        """El mouse salió: se apaga el hover (y si estaba presionado, se suelta)."""
        self.widget.salir_hover()
        if self.widget.presionado:
            self.widget.soltar()
        self.canvas.configure(cursor="")

    # --- Mini-animación de color (fade) ---

    def _aplicar_color(self, color):
        """Pinta el fondo del botón y recuerda ese color como el visible."""
        self.canvas.itemconfig(self._ids["fondo"], fill=color)
        self._color_visual = color

    def _animar_hacia(self):
        """Un "paso" de la animación: interpola entre origen y destino."""
        try:
            if self._color_destino is None:
                return  # el viaje ya terminó
            self._paso += 1
            t = min(1.0, self._paso / PASOS_TRANSICION)
            self._aplicar_color(
                interpolar_color(self._color_origen, self._color_destino, t),
            )
            if t < 1.0:
                self.canvas.after(INTERVALO_TRANSICION_MS, self._animar_hacia)
            else:
                self._color_destino = None
        except tk.TclError:
            # El canvas ya fue destruido (se cambió de pantalla): no hay
            # nada más que animar y el after pendiente se desvanece solo.
            self._color_destino = None

    def dibujar(self):
        """Dibuja (o actualiza) el botón y regenera sus bindings si hace falta."""
        # --- Bezel (placa metálica) y halo, detrás del fondo animado ---
        # La placa es un borde metálico fijo que le da aspecto de "tapa de
        # deck"; el halo es el brillo que se prende al presionar (dibujado
        # detrás del fondo, así el fade del estado lo cubre con elegancia).
        self._primera_vez(
            "bezel",
            lambda: rectangulo_redondeado(
                self.canvas, self.x - 2, self.y - 2,
                self.x + self.ancho + 2, self.y + self.alto + 2,
                self.radio_esquinas + 1,
                fill=Paleta.HUD_LINE, outline="", width=0,
            ),
        )
        self._primera_vez(
            "halo",
            lambda: rectangulo_redondeado(
                self.canvas, self.x - 4, self.y - 4,
                self.x + self.ancho + 4, self.y + self.alto + 4,
                self.radio_esquinas + 2,
                fill=interpolar_color(Paleta.DORADO, Paleta.FONDO_WIDGET, 0.75),
                outline="", width=0,
            ),
        )

        # --- Fondo del botón (rectángulo redondeado, color según estado) ---
        fondo = self._primera_vez(
            "fondo",
            lambda: rectangulo_redondeado(
                self.canvas, self.x, self.y,
                self.x + self.ancho, self.y + self.alto,
                self.radio_esquinas,
                outline="", width=1,
            ),
        )

        # Color de fondo: si cambió el estado lógico, arranca la transición.
        objetivo = self.widget.color_fondo
        if self._color_visual is None:
            self._aplicar_color(objetivo)
        elif objetivo != self._color_visual and objetivo != self._color_destino:
            # Estado nuevo (o cambió a mitad del viaje): se re-orienta la animación.
            self._color_origen = self._color_visual
            self._color_destino = objetivo
            self._paso = 0
            self.canvas.after(INTERVALO_TRANSICION_MS, self._animar_hacia)

        # (Re)conectar los eventos sobre el fondo: clic y hover + cursor de mano.
        # El hover se bindea solo al fondo (no a la etiqueta) para que
        # cruzar por encima del texto no haga pestañear al botón. Como el
        # cursor no existe por ítem en Tk, se cambia el del canvas entero.
        self.canvas.tag_bind(fondo, "<ButtonPress-1>", self._al_presionar)
        self.canvas.tag_bind(fondo, "<ButtonRelease-1>", self._al_soltar)
        self.canvas.tag_bind(fondo, "<Enter>", self._al_entrar)
        self.canvas.tag_bind(fondo, "<Leave>", self._al_salir)

        # --- Texto del botón ---
        etiqueta = self._primera_vez(
            "etiqueta",
            lambda: self.canvas.create_text(
                self.x + self.ancho / 2, self.y + self.alto / 2,
                text=self.texto,
                font=(Paleta.FUENTE_TEXTO, self.tamano_fuente, "bold"),
            ),
        )

        # Borde y color del texto dependen solo de presionado; no se repintan
        # en cada ciclo si el estado lógico no cambió (el fondo sí se anima).
        if self._hay_cambio("estado", self.widget.presionado):
            # El halo "se enciende" con la presión (y se apaga al soltar).
            halo = self._ids["halo"]
            self.canvas.itemconfig(
                halo, state="normal" if self.widget.presionado else "hidden",
            )

            # Color de borde: DORADO si está presionado, gris oscuro si no.
            borde = Paleta.DORADO if self.widget.presionado else Paleta.GRIS
            self.canvas.itemconfig(fondo, outline=borde)

            color_texto = Paleta.DORADO if self.widget.presionado else Paleta.TEXTO_LOG
            self.canvas.itemconfig(etiqueta, fill=color_texto)

        # Permitir presionar también haciendo clic sobre el texto (sin hover).
        self.canvas.tag_bind(etiqueta, "<ButtonPress-1>", self._al_presionar)
        self.canvas.tag_bind(etiqueta, "<ButtonRelease-1>", self._al_soltar)
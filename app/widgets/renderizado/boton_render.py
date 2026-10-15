# wall-e-robot/app/widgets/renderizado/boton_render.py
# Kevin Gámez - 13/09/2026


import tkinter as tk
from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase, rectangulo_redondeado, interpolar_color


# Parámetros de la transición de color
PASOS_TRANSICION = 6
INTERVALO_TRANSICION_MS = 16


class BotonRenderer(RenderizadorBase):
    """Renderer de un Boton lógico."""
    def __init__(self, widget, canvas, x, y, ancho, alto,
                 texto=None, radio_esquinas=Paleta.RADIO_BOTON, tamano_fuente=9):
        super().__init__(canvas)
        
        self.widget           = widget
        self.x, self.y        = x, y
        self.ancho, self.alto = ancho, alto
        self.texto            = texto if texto is not None else widget.texto
        self.radio_esquinas   = radio_esquinas
        self.tamano_fuente    = tamano_fuente

        # Estado de la animación de color.
        self._color_visual = None   # color aplicado actualmente (lo que se ve)
        self._color_origen = None   # punto de partida de la animación en curso
        self._color_destino = None  # destino (None = sin animación activa)
        self._paso = 0

    # Traducción de eventos del mouse a estados lógicos
    def _al_presionar(self, _evento):
        self.widget.presionar()

    def _al_soltar(self, _evento):
        self.widget.soltar()

    def _al_entrar(self, _evento):
        """Activa el hover y el cursor de mano del canvas."""
        self.widget.entrar_hover()
        self.canvas.configure(cursor="hand2")

    def _al_salir(self, _evento):
        """Desactiva el hover; si el botón quedó presionado, lo suelta."""
        self.widget.salir_hover()
        if self.widget.presionado:
            self.widget.soltar()
        self.canvas.configure(cursor="")


    def _aplicar_color(self, color):
        self.canvas.itemconfig(self._ids["fondo"], fill=color)
        self._color_visual = color

    def _animar_hacia(self):
        try:
            if self._color_destino is None:
                return  # la animación ya terminó
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
            # El canvas ya fue destruido
            self._color_destino = None

    def dibujar(self):
        """Dibuja o actualiza el botón y reenlaza sus eventos."""
        # Bezel (placa metálica) y halo, detrás del fondo animado
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

        # Fondo del botón
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
            # Estado nuevo (o cambio a mitad de la transición): se reorienta.
            self._color_origen = self._color_visual
            self._color_destino = objetivo
            self._paso = 0
            self.canvas.after(INTERVALO_TRANSICION_MS, self._animar_hacia)

        # (Re)enlaza los eventos sobre el fondo. El hover se enlaza solo al
        # fondo (no a la etiqueta) para evitar parpadeos al cruzar el texto;
        self.canvas.tag_bind(fondo, "<ButtonPress-1>", self._al_presionar)
        self.canvas.tag_bind(fondo, "<ButtonRelease-1>", self._al_soltar)
        self.canvas.tag_bind(fondo, "<Enter>", self._al_entrar)
        self.canvas.tag_bind(fondo, "<Leave>", self._al_salir)

        # Texto del botón
        etiqueta = self._primera_vez(
            "etiqueta",
            lambda: self.canvas.create_text(
                self.x + self.ancho / 2, self.y + self.alto / 2,
                text=self.texto,
                font=(Paleta.FUENTE_TEXTO, self.tamano_fuente, "bold"),
            ),
        )

        # Borde y color del texto dependen solo de presionado; se repintan
        # únicamente cuando ese estado cambia (el fondo sí se anima aparte).
        if self._hay_cambio("estado", self.widget.presionado):
            # El halo se enciende con la presión y se apaga al soltar.
            halo = self._ids["halo"]
            self.canvas.itemconfig(
                halo, state="normal" if self.widget.presionado else "hidden",
            )

            borde = Paleta.DORADO if self.widget.presionado else Paleta.GRIS
            self.canvas.itemconfig(fondo, outline=borde)

            color_texto = Paleta.DORADO if self.widget.presionado else Paleta.TEXTO_LOG
            self.canvas.itemconfig(etiqueta, fill=color_texto)

        # Permite presionar también haciendo clic sobre el texto (sin hover).
        self.canvas.tag_bind(etiqueta, "<ButtonPress-1>", self._al_presionar)
        self.canvas.tag_bind(etiqueta, "<ButtonRelease-1>", self._al_soltar)

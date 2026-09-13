# wall-e-robot/app/widgets/renderizado/boton_render.py
# Kevin Gámez - 13/09/2026


from ...nucleo.paleta import Paleta
from .base_render import RenderizadorBase, rectangulo_redondeado


class BotonRenderer(RenderizadorBase):
    """
    El renderer (Tkinter) de un Boton lógico.

    Recibe:
      - widget: el Boton lógico (widgets/logica/boton.py), que NO sabe nada
        de Tkinter. Aquí es donde Tkinter finalmente sí existe.
      - canvas: el Canvas donde dibujar.
      - x, y, ancho, alto: la zona que ocupa el botón (en píxeles).

    Su trabajo es doble:
      1. DIBUJAR el botón según el estado lógico (fondo, borde y texto).
      2. CONECTAR los eventos reales del framework (clic del mouse) al
         widget lógico (widget.presionar() / widget.soltar()).
    """

    def __init__(self, widget, canvas, x, y, ancho, alto,
                 texto=None, radio_esquinas=8):
        """
        Constructor del renderer del botón.

        texto: etiqueta a mostrar (si se omite, usa widget.texto). Permite
        que el gamepad muestre flechas (▲◀▶▼) en lugar de "ARRIBA"/"ABAJO".
        """
        super().__init__(canvas)
        self.widget = widget
        self.x, self.y = x, y
        self.ancho, self.alto = ancho, alto
        self.texto = texto if texto is not None else widget.texto
        self.radio_esquinas = radio_esquinas

    def _al_presionar(self, _evento):
        """El clic del mouse se traduce a 'presionado' en la lógica."""
        self.widget.presionar()

    def _al_soltar(self, _evento):
        """Soltar el botón del mouse se traduce a 'soltado'."""
        self.widget.soltar()

    def dibujar(self):
        """Dibuja (o actualiza) el botón y regenera sus bindings si hace falta."""
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
        # Color de borde: DORADO si está presionado, gris oscuro si no.
        borde = Paleta.DORADO if self.widget.presionado else "#333333"
        self.canvas.itemconfig(
            fondo,
            fill=self.widget.color_fondo,
            outline=borde,
        )

        # (Re)conectar el evento de clic sobre el fondo, por si la primera vez.
        self.canvas.tag_bind(fondo, "<ButtonPress-1>", self._al_presionar)
        self.canvas.tag_bind(fondo, "<ButtonRelease-1>", self._al_soltar)

        # --- Texto del botón ---
        etiqueta = self._primera_vez(
            "etiqueta",
            lambda: self.canvas.create_text(
                self.x + self.ancho / 2, self.y + self.alto / 2,
                text=self.texto, font=("Segoe UI", 9, "bold"),
            ),
        )
        color_texto = Paleta.DORADO if self.widget.presionado else Paleta.TEXTO_LOG
        self.canvas.itemconfig(etiqueta, fill=color_texto)

        # Permitir presionar también haciendo clic sobre el texto.
        self.canvas.tag_bind(etiqueta, "<ButtonPress-1>", self._al_presionar)
        self.canvas.tag_bind(etiqueta, "<ButtonRelease-1>", self._al_soltar)
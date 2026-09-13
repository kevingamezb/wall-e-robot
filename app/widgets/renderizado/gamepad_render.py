# wall-e-robot/app/widgets/renderizado/gamepad_render.py
# Kevin Gámez - 13/09/2026


from ...nucleo.paleta import Paleta
from .boton_render import BotonRenderer
from .deslizador_render import DeslizadorRenderer


class GamepadRenderer:
    """
    Renderer (Tkinter) del gamepad, hecho por COMPOSICIÓN.

    Igual que la lógica del Gamepad reutiliza piezas (Boton, Deslizador),
    este renderer reutiliza sus renderers correspondientes sobre un mismo
    canvas. Agrupa:
        - cruceta (4 botones, con flechas ▲◀▶▼)
        - deslizador horizontal del cuello
        - dos deslizadores verticales de hombros (Izq / Der)
        - botón de reposo
        - dos botones de manos (ABRIR / CERRAR)

    Cada pieza se ubica en una zona del canvas definida por fracciones del
    ancho/alto (para que las proporciones sobrevivan a distintos tamaños).
    """

    def __init__(self, gamepad, canvas, ancho, alto):
        """
        Constructor del renderer del gamepad.

        gamepad : el Gamepad lógico (ya trae cableados los comandos).
        canvas  : canvas donde se dibuja todo el control.
        """
        self.gamepad = gamepad
        self.canvas = canvas
        self.ancho, self.alto = ancho, alto
        self._textos = {}  # etiquetas auxiliares (valores, nombres de ejes)

        # --- Geometría base (fracciones del canvas) ---
        cx = 0.26 * ancho          # centro de la cruceta
        cy = 0.32 * alto
        lado_boton = 44
        sep = 52                   # distancia entre centros de la cruceta

        # Cruceta de 4 direcciones.
        self._arriba = BotonRenderer(
            gamepad.direccion_arriba, canvas,
            cx - lado_boton / 2, cy - sep - lado_boton / 2,
            lado_boton, lado_boton, texto="\u25b2")     # ▲
        self._abajo = BotonRenderer(
            gamepad.direccion_abajo, canvas,
            cx - lado_boton / 2, cy + sep - lado_boton / 2,
            lado_boton, lado_boton, texto="\u25bc")     # ▼
        self._izquierda = BotonRenderer(
            gamepad.direccion_izquierda, canvas,
            cx - sep - lado_boton / 2, cy - lado_boton / 2,
            lado_boton, lado_boton, texto="\u25c0")     # ◀
        self._derecha = BotonRenderer(
            gamepad.direccion_derecha, canvas,
            cx + sep - lado_boton / 2, cy - lado_boton / 2,
            lado_boton, lado_boton, texto="\u25b6")     # ▶

        # Deslizador del cuello (horizontal), debajo de la cruceta.
        self._cuello = DeslizadorRenderer(
            gamepad.cuello, canvas,
            cx - 0.16 * ancho, cy + sep + 40,
            0.34 * ancho, orientacion="horizontal",
        )

        # Hombros: dos deslizadores verticales a la derecha.
        y_hombros = 0.30 * alto
        self._hombro_izq = DeslizadorRenderer(
            gamepad.hombro_izquierdo, canvas,
            0.55 * ancho, y_hombros,
            0.55 * alto, orientacion="vertical",
        )
        self._hombro_der = DeslizadorRenderer(
            gamepad.hombro_derecho, canvas,
            0.76 * ancho, y_hombros,
            0.55 * alto, orientacion="vertical",
        )

        # Reposo: sobre los hombros, entre ambos deslizadores.
        self._reposo = BotonRenderer(
            gamepad.reposo, canvas,
            0.645 * ancho - 36, 0.07 * alto,
            72, 26, texto="REPOSO",
        )

        # Manos: dos botones apilados en la columna derecha.
        self._mano_abrir = BotonRenderer(
            gamepad.mano_abrir, canvas,
            0.885 * ancho, 0.28 * alto,
            46, 34, texto="ABRIR",
        )
        self._mano_cerrar = BotonRenderer(
            gamepad.mano_cerrar, canvas,
            0.885 * ancho, 0.28 * alto + 60,
            46, 34, texto="CERRAR",
        )

    # --- Etiquetas auxiliares (texto que cambia con el estado) ---

    def _texto(self, clave, contenido, x, y, fill=Paleta.TEXTO_LOG, tamano=8):
        """Crea (o actualiza) una etiqueta de texto en el canvas."""
        if clave not in self._textos:
            self._textos[clave] = self.canvas.create_text(
                x, y, text=contenido, font=("Segoe UI", tamano),
                fill=fill, anchor="nw",
            )
        else:
            self.canvas.itemconfig(self._textos[clave], text=contenido, fill=fill)

    def dibujar(self):
        """Dibuja (o actualiza) todas las piezas y sus etiquetas."""
        # Piezas interactivas (sus propios renderers se encargan de su estado).
        for pieza in (self._arriba, self._abajo, self._izquierda, self._derecha,
                      self._reposo, self._mano_abrir, self._mano_cerrar):
            pieza.dibujar()
        self._cuello.dibujar()
        self._hombro_izq.dibujar()
        self._hombro_der.dibujar()

        # Nombres de los ejes y valores actuales (anclados a la geometría
        # real de cada deslizador, para que no se desalineen).
        x_cuello, y_cuello = self._cuello.x, self._cuello.y
        self._texto("lbl_cuello", "CUELLO", x_cuello, y_cuello - 14, tamano=7)
        self._texto("val_cuello", f"{int(self.gamepad.cuello.posicion)}\u00b0",
                    x_cuello + self._cuello.largo + 6, y_cuello - 8, tamano=8)

        for (clave_lbl, clave_val, slider, txt) in (
            ("lbl_izq", "val_izq", self._hombro_izq, "IZQ"),
            ("lbl_der", "val_der", self._hombro_der, "DER"),
        ):
            self._texto(clave_lbl, txt, slider.x - 14, slider.y - 16, tamano=7)
            self._texto(clave_val, f"{int(slider.widget.posicion)}\u00b0",
                        slider.x + 10, slider.y + slider.largo + 4, tamano=8)
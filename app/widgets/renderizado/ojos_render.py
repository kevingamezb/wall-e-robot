# wall-e-robot/app/widgets/renderizado/ojos_render.py
# Kevin Gámez - 13/09/2026


from ...nucleo.paleta import Paleta
from ...widgets.logica.ojos import ExpresionOjos
from .base_render import RenderizadorBase, rectangulo_redondeado
from .recoloreo import Recoloreo
from . import carga_recursos


# Geometría base de los ojos (fallback procedural).
OJO_ANCHO = 44
OJO_ALTO_ABIERTO = 30
OJO_ALTO_OBSTACULO = 12
PUPILA_ABIERTA = 9
PUPILA_OBSTACULO = 6

# Alto con que se dibujan las imágenes de los ojos.
ALTO_OJO_IMAGEN = 40

# PNG de cada expresión.
RECURSOS = {
    ExpresionOjos.NORMAL:    "ojo_normal",
    ExpresionOjos.MANUAL:    "ojo_manual",
    ExpresionOjos.OBSTACULO: "ojo_obstaculo",
    ExpresionOjos.SIN_DATOS: "ojo_desconectado",
    ExpresionOjos.ERROR:     "ojo_error",
}


class OjosRenderer(RenderizadorBase):
    """Renderer de los ojos de Wall-E."""
    def __init__(self, widget, canvas, x=20, y=8, alto_imagen=ALTO_OJO_IMAGEN):
        """x, y: esquina superior-izquierda del bloque de ojos.

        alto_imagen: alto (px) con que se dibuja cada PNG de ojo. Los dos
        PNG se colocan pegados (el puente de la nariz de cada uno se une).
        """
        super().__init__(canvas)
        self.widget = widget
        self.x = x
        self.y = y
        self.alto_imagen = alto_imagen
        self.alto_total = OJO_ALTO_ABIERTO + 16  # margen arriba/abajo

    @property
    def ancho_bloque(self) -> float:
        """Ancho total del bloque de ojos en px (los PNG son cuadrados)."""
        return 2 * self.alto_imagen

    # Geometría
    def _coords_caja(self, cx, alto, y_superior):
        """Devuelve (x1, y1, x2, y2) para la caja de un ojo centrada en cx."""
        return (cx - OJO_ANCHO / 2, y_superior,
                cx + OJO_ANCHO / 2, y_superior + alto)

    def _coords_pupila(self, cx, cy, tamano):
        """Devuelve (x1, y1, x2, y2) para la pupila centrada en (cx, cy)."""
        return (cx - tamano / 2, cy - tamano / 2,
                cx + tamano / 2, cy + tamano / 2)

    def _centros(self):
        """Centros (cx) del ojo izquierdo y derecho."""
        ancho = self.ancho_bloque / 2
        return self.x + ancho / 2, self.x + ancho + ancho / 2

    # Selección de modo (imágenes vs. procedural)
    def _usa_imagenes(self, expresion):
        """True si el PNG de esta expresión está exportado."""
        return carga_recursos.existe(RECURSOS[expresion])

    def dibujar(self):
        """Dibuja o actualiza los dos ojos según la expresión lógica."""
        expresion = self.widget.expresion
        color = self.widget.color
        cx_izq, cx_der = self._centros()

        if self._usa_imagenes(expresion):
            self._dibujar_imagenes(expresion, color, cx_izq, cx_der)
        else:
            self._dibujar_procedural(expresion, color, cx_izq, cx_der)

    def _ocultar(self, nombre):
        """Oculta un ítem si ya existe."""
        if nombre in self._ids:
            self.canvas.itemconfig(self._ids[nombre], state="hidden")

    def _mostrar(self, nombre):
        """Muestra un ítem si ya existe."""
        if nombre in self._ids:
            self.canvas.itemconfig(self._ids[nombre], state="normal")

    # Modo imágenes
    def _dibujar_imagenes(self, expresion, color, cx_izq, cx_der):
        """Dibuja el PNG del ojo (derecho espejado) y oculta lo procedural."""
        for nombre in ("caja_izq", "caja_der", "pupila_izq", "pupila_der"):
            self._ocultar(nombre)

        cy = self.y + self.alto_imagen / 2
        archivo = RECURSOS[expresion]
        izquierda = carga_recursos.cargar(archivo, color, self.alto_imagen,
                                          master=self.canvas)
        derecha = carga_recursos.cargar(archivo, color, self.alto_imagen,
                                        espejo=True, master=self.canvas)

        ojo_izq = self._primera_vez(
            "img_izq",
            lambda: self.canvas.create_image(
                cx_izq, cy, image=izquierda, anchor="center"),
        )
        ojo_der = self._primera_vez(
            "img_der",
            lambda: self.canvas.create_image(
                cx_der, cy, image=derecha, anchor="center"),
        )

        self.canvas.coords(ojo_izq, cx_izq, cy)
        self.canvas.coords(ojo_der, cx_der, cy)
        self.canvas.itemconfig(ojo_izq, image=izquierda, state="normal")
        self.canvas.itemconfig(ojo_der, image=derecha, state="normal")

    # Modo procedural (fallback)
    def _dibujar_procedural(self, expresion, color, cx_izq, cx_der):
        """Dibuja el fallback procedural a mano con el Canvas."""
        if "img_izq" in self._ids:
            self._ocultar("img_izq")
            self._ocultar("img_der")

        # Alto de la caja según la expresión.
        alto = OJO_ALTO_ABIERTO if expresion != ExpresionOjos.OBSTACULO else OJO_ALTO_OBSTACULO

        # Desplazamiento horizontal de la pupila: en MANUAL mira hacia adentro
        # (el ojo izquierdo a la derecha y el derecho a la izquierda).
        desplazamiento = 0
        if expresion == ExpresionOjos.MANUAL:
            desplazamiento = 6

        # Tamaño de la pupila y si se muestra o no.
        if expresion == ExpresionOjos.SIN_DATOS:
            tamano = 0          # no se dibuja pupila
            ver_pupila = False
        elif expresion == ExpresionOjos.OBSTACULO:
            tamano = PUPILA_OBSTACULO
            ver_pupila = True
        else:
            tamano = PUPILA_ABIERTA
            ver_pupila = True

        # Primera vez: crear las cajas y pupilas con su geometría base.
        for lado, cx in (("izq", cx_izq), ("der", cx_der)):
            self._primera_vez(
                f"caja_{lado}",
                lambda cx=cx: self.canvas.create_rectangle(
                    *self._coords_caja(cx, OJO_ALTO_ABIERTO, self.y + 8),
                    fill="", outline=color, width=2,
                ),
            )
            self._primera_vez(
                f"pupila_{lado}",
                lambda cx=cx: self.canvas.create_oval(
                    *self._coords_pupila(cx, self.y + 23, PUPILA_ABIERTA),
                    fill=color, outline="",
                ),
            )

        # La silueta solo cambia con la expresión (y su color): repintar solo
        # entonces, en vez de recalcular coords en cada ciclo.
        if not self._hay_cambio("estado", (expresion, color)):
            return

        for lado, cx in (("izq", cx_izq), ("der", cx_der)):
            # Caja del ojo: rectángulo sin relleno con borde de color.
            caja = self._ids[f"caja_{lado}"]
            self.canvas.coords(caja, *self._coords_caja(cx, alto, self.y + 8))
            self.canvas.itemconfig(caja, outline=color, state="normal")

            # La pupila se oculta cuando la expresión es SIN_DATOS.
            pupila = self._ids[f"pupila_{lado}"]
            cx_pupila = cx + (desplazamiento if lado == "izq" else -desplazamiento)
            cy_pupila = self.y + 8 + alto / 2
            self.canvas.coords(pupila, *self._coords_pupila(cx_pupila, cy_pupila, tamano))
            self.canvas.itemconfig(pupila, fill=color)
            self.canvas.itemconfig(
                pupila,
                state="normal" if ver_pupila else "hidden",
            )

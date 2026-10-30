# wall-e-robot/app/widgets/renderizado/gamepad_render.py
# Kevin Gámez - 13/09/2026
# Rediseño: cruceta de flechas con perilla de reposo central y deslizadores
# del diseño (cuello horizontal y brazos L/R verticales).


from PIL import Image, ImageDraw, ImageTk
from ...nucleo.paleta import Paleta
from ...nucleo.disenio import Disenio
from .base_render import rectangulo_redondeado
from .boton_imagen_render import BotonImagenRenderer, sector_circular
from .deslizador_render import DeslizadorRenderer
from .texto_render import Texto


CUERPO = "#2b2d42"        # color del cuerpo de las flechas en el PNG
FLECHA = "#edf2f4"        # color del triángulo en el PNG
TOL = 20                  # tolerancia: el contorno (#1b1b29) está muy cerca


class GamepadRenderer:
    """Renderer del gamepad, construido por composición."""

    def __init__(self, gamepad, canvas, e):
        """
        gamepad : instancia de Gamepad (lógica).
        canvas  : canvas donde se dibuja todo.
        e       : Escala (unidades de diseño -> píxeles).
        """
        self.gamepad = gamepad
        self.canvas = canvas
        self.e = e
        self._etiquetas = {}

        variantes_flecha = {
            "hover":      [(CUERPO, "#3f4263", TOL)],
            "presionado": [(CUERPO, Paleta.DORADO, TOL), (FLECHA, Paleta.TINTA, 40)],
        }
        centro_x = (Disenio.FLECHA_IZQUIERDA[0] + Disenio.FLECHA_DERECHA[2]) / 2
        centro_y = (Disenio.FLECHA_ARRIBA[1] + Disenio.FLECHA_ABAJO[3]) / 2
        r_min, r_max = e(100), e(252)

        def flecha(boton, caja, rotar, direccion):
            x1, y1, x2, _ = e.caja(caja)
            return BotonImagenRenderer(
                boton, canvas, x1, y1, e(caja[2] - caja[0]) if rotar % 180 == 0
                else e(caja[2] - caja[0]),
                "boton", rotar=rotar, variantes=variantes_flecha,
                dentro=sector_circular(e(centro_x), e(centro_y), r_min, r_max,
                                       direccion))

        self._arriba = flecha(gamepad.direccion_arriba, Disenio.FLECHA_ARRIBA, 0, "arriba")
        self._derecha = flecha(gamepad.direccion_derecha, Disenio.FLECHA_DERECHA, 90, "derecha")
        self._abajo = flecha(gamepad.direccion_abajo, Disenio.FLECHA_ABAJO, 180, "abajo")
        self._izquierda = flecha(gamepad.direccion_izquierda, Disenio.FLECHA_IZQUIERDA, 270, "izquierda")

        # Perilla central: reposo de todos los servos.
        rx1, ry1, rx2, ry2 = e.caja(Disenio.REPOSO)
        r_perilla = (rx2 - rx1) / 2
        cx_p, cy_p = (rx1 + rx2) / 2, (ry1 + ry2) / 2
        self._reposo = BotonImagenRenderer(
            gamepad.reposo, canvas, rx1, ry1, rx2 - rx1, "boton_reposo",
            variantes={
                "hover":      [(Paleta.DORADO, "#f3cd5a", 50)],
                "presionado": [(CUERPO, "#3f4263", TOL)],
            },
            dentro=lambda x, y: (x - cx_p) ** 2 + (y - cy_p) ** 2 <= r_perilla ** 2)

        # Deslizadores
        cx0, cy0, largo_c = Disenio.CUELLO_PISTA
        grosor = e(Disenio.PISTA_GROSOR)
        radio = e(Disenio.THUMB_RADIO)
        self._cuello = DeslizadorRenderer(
            gamepad.cuello, canvas, e(cx0), e(cy0), e(largo_c),
            orientacion="horizontal", alto_pista=grosor, radio_thumb=radio)
        lx, ly, largo_b = Disenio.BRAZO_L_PISTA
        self._hombro_izq = DeslizadorRenderer(
            gamepad.hombro_izquierdo, canvas, e(lx), e(ly), e(largo_b),
            orientacion="vertical", alto_pista=grosor, radio_thumb=radio)
        rx, ry, _ = Disenio.BRAZO_R_PISTA
        self._hombro_der = DeslizadorRenderer(
            gamepad.hombro_derecho, canvas, e(rx), e(ry), e(largo_b),
            orientacion="vertical", alto_pista=grosor, radio_thumb=radio)

        # Se dibujan una vez para fijar el orden de las capas (la capa
        # "apagado" debe quedar por encima de todas las piezas).
        self._dibujar_piezas()

        px = e.fuente(30)
        for clave, texto, (x, y) in (
            ("cuello", "CUELLO", Disenio.ETIQUETA_CUELLO),
            ("brazos", "BRAZOS", Disenio.ETIQUETA_BRAZOS),
            ("L", "L", Disenio.ETIQUETA_L),
            ("R", "R", Disenio.ETIQUETA_R),
        ):
            self._etiquetas[clave] = Texto(canvas, e(x), e(y), texto, px,
                                           Paleta.TINTA, ancla="center",
                                           contorno=Paleta.TINTA, grosor=1)
        for clave in ("grados_cuello", "grados_izq", "grados_der"):
            self._etiquetas[clave] = Texto(canvas, 0, 0, "0°", px,
                                           Paleta.FONDO_WIDGET, ancla="center",
                                           contorno=Paleta.FONDO_WIDGET, grosor=1)

        # Capa "apagado": velo sobre la zona del mando + aviso.
        x1, y1, x2, y2 = e.caja(Disenio.LINEA_CONTROL)
        m = e(26)
        ancho_v, alto_v = x2 - x1 - 2 * m, y2 - y1 - 2 * m - e(110)
        veles = Image.new("RGBA", (ancho_v, alto_v), (0, 0, 0, 0))
        ImageDraw.Draw(veles).rounded_rectangle(
            (0, 0, ancho_v - 1, alto_v - 1), radius=e(40),
            fill=(237, 242, 244, 205))
        self._foto_velo = ImageTk.PhotoImage(veles)
        self._velo = canvas.create_image(x1 + m, y1 + m + e(110),
                                         image=self._foto_velo, anchor="nw")
        cx = (x1 + x2) / 2
        self._aviso = Texto(canvas, cx, e(1640), "SIN CONEXIÓN", e.fuente(86),
                            Paleta.ROJO, ancla="center",
                            contorno=Paleta.TARJETA, grosor=max(2, e(8)))
        self._nota = Texto(canvas, cx, e(1760),
                           "Presiona Conectar para usar el control",
                           e.fuente(40), Paleta.TINTA, ancla="center")

    def _dibujar_piezas(self):
        for pieza in (self._arriba, self._abajo, self._izquierda, self._derecha,
                      self._reposo, self._cuello, self._hombro_izq,
                      self._hombro_der):
            pieza.dibujar()

    def _grados(self, clave, deslizador):
        """Mueve el rótulo de grados junto a la perilla y actualiza su valor."""
        e = self.e
        px, py = deslizador._centro_thumb()
        texto = f"{int(deslizador.widget.posicion)}°"
        etiqueta = self._etiquetas[clave]
        etiqueta.poner(texto=texto)
        if clave == "grados_cuello":
            etiqueta.mover(px, e(1474))
        elif clave == "grados_izq":
            etiqueta.mover(e(3216), py)
        else:
            etiqueta.mover(e(3553), py)

    def dibujar(self):
        """Dibuja o actualiza todas las piezas y sus etiquetas."""
        self._dibujar_piezas()
        self._grados("grados_cuello", self._cuello)
        self._grados("grados_izq", self._hombro_izq)
        self._grados("grados_der", self._hombro_der)

        apagado = not self.gamepad.habilitado
        estado = "normal" if apagado else "hidden"
        self.canvas.itemconfig(self._velo, state=estado)
        self._aviso.mostrar(apagado)
        self._nota.mostrar(apagado)
        if apagado:
            for item in (self._velo, self._aviso.id, self._nota.id):
                self.canvas.tag_raise(item)

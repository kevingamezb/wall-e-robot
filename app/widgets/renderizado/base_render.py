# wall-e-robot/app/widgets/renderizado/base_render.py
# Kevin Gámez - 13/09/2026


from ...nucleo.paleta import Paleta


def rectangulo_redondeado(canvas, x1, y1, x2, y2, radio, **opciones):
    """
    Dibuja un rectángulo con esquinas redondeadas en un canvas de Tkinter.

    Tkinter no tiene una primitiva de "rectángulo redondeado": se simula con
    un polígono con suavizado (smooth=True) cuyos puntos recorren el borde
    cortando las 4 esquinas a 'radio' píxeles de la esquina exacta.

    Devuelve el id del ítem creado (como cualquier create_*).
    """
    puntos = [
        x1 + radio, y1,
        x2 - radio, y1,
        x2, y1 + radio,
        x2, y2 - radio,
        x2 - radio, y2,
        x1 + radio, y2,
        x1, y2 - radio,
        x1, y1 + radio,
    ]
    return canvas.create_polygon(puntos, smooth=True, **opciones)


def interpolar_color(hex1, hex2, t):
    """
    Interpola linealmente entre dos colores hex (#rrggbb) según t (0.0 a 1.0).

    Tkinter no anima colores solo: cualquier "fade" hay que construirlo a
    mano. Esta función calcula el color intermedio entre hex1 (t=0) y
    hex2 (t=1), pasando por todos los tonos del medio.
    """
    t = max(0.0, min(1.0, t))
    c1 = tuple(int(hex1[i:i + 2], 16) for i in (1, 3, 5))
    c2 = tuple(int(hex2[i:i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(a + (b - a) * t) for a, b in zip(c1, c2))
    return f"#{r:02x}{g:02x}{b:02x}"


def borde_panel(canvas, radio=Paleta.RADIO_TARJETA, margen=2, color=Paleta.BORDE_SUAVE):
    """
    Dibuja el marco sutil de un panel (una "tarjeta") sobre su canvas.

    Es la variante FIEL al mockup: esquinas redondeadas reales (a diferencia
    de la tarjeta básica de tarjeta.py, que usa un borde recto de 1px).
    Se usa dibujando encima del canvas; para el borde recto, prefiere
    crear_tarjeta() de tarjeta.py.
    """
    ancho = int(canvas.cget("width"))
    alto = int(canvas.cget("height"))
    return rectangulo_redondeado(
        canvas,
        margen, margen, ancho - margen, alto - margen,
        radio,
        outline=color, width=1,
    )


class RenderizadorBase:
    """
    Base común de todos los renderers: la "memoria" de los ítems dibujados.

    En lugar de borrar y redibujar todo el canvas en cada ciclo (lo que
    parpadearía), cada renderer guarda los ids de sus ítems en _ids y solo
    los ACTUALIZA (canvas.itemconfig / canvas.coords) cuando dibuja de nuevo.
    """

    def __init__(self, canvas):
        """
        Constructor base.

        canvas: el canvas de Tkinter sobre el que dibujará este renderer.
        """
        self.canvas = canvas
        self._ids = {}
        self._valores = {}

    def _primera_vez(self, nombre, creador):
        """
        Crea un ítem la primera vez y devuelve su id; si ya existía, lo
        devuelve sin recrearlo.

        nombre :  clave única de este ítem dentro del renderer (un string).
        creador: función sin argumentos que crea el ítem (ej. lambda:
                 self.canvas.create_line(...)).
        """
        if nombre not in self._ids:
            self._ids[nombre] = creador()
        return self._ids[nombre]

    def _hay_cambio(self, clave, valor):
        """
        Devuelve True si 'valor' cambió respecto a la última vez con 'clave'.

        Es el "interruptor de suciedad" de los renderers: en vez de repintar
        el canvas en cada ciclo (lo que gasta CPU de miembro en periféricos),
        cada renderer compara el valor derivado de su lógica y salta el
        repintado si no cambió. La clave es un string propio del renderer.
        """
        if clave in self._valores and self._valores[clave] == valor:
            return False
        self._valores[clave] = valor
        return True
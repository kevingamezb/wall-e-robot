# wall-e-robot/app/widgets/renderizado/base_render.py
# Kevin Gámez - 13/09/2026


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
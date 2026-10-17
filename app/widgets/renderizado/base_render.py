# wall-e-robot/app/widgets/renderizado/base_render.py
# Kevin Gámez - 13/09/2026


from ...nucleo.paleta import Paleta


def rectangulo_redondeado(canvas, x1, y1, x2, y2, radio, **opciones):
    """Dibuja un rectángulo de esquinas redondeadas y devuelve su id."""
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
    """Devuelve el color intermedio entre hex1 (t=0) y hex2 (t=1), recortando t a [0, 1]."""
    t = max(0.0, min(1.0, t))
    c1 = tuple(int(hex1[i:i + 2], 16) for i in (1, 3, 5))
    c2 = tuple(int(hex2[i:i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(a + (b - a) * t) for a, b in zip(c1, c2))
    return f"#{r:02x}{g:02x}{b:02x}"


def borde_panel(canvas, radio=Paleta.RADIO_TARJETA, margen=2, color=Paleta.BORDE_SUAVE):
    """Dibuja el marco redondeado de un panel y devuelve su id."""
    ancho = int(canvas.cget("width"))
    alto = int(canvas.cget("height"))
    return rectangulo_redondeado(
        canvas,
        margen, margen, ancho - margen, alto - margen,
        radio,
        outline=color, width=1,
    )


# Primitivas de "holograma"
def fulgor_radial(canvas, cx, cy, radio, color, capas=4):
    """Dibuja un brillo radial tipo holograma y devuelve sus ids."""
    ids = []
    for i in range(capas, 0, -1):
        r = radio * (i / capas)
        t = (capas - i) / capas          # 0 en el centro -> 1 en el borde
        ids.append(canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=interpolar_color(color, Paleta.FONDO_WIDGET, t * 0.85),
            outline="",
        ))
    return ids


def anillo_con_halo(canvas, cx, cy, radio, grosor, color, capas=3):
    """Dibuja un círculo con halo concéntrico y devuelve sus ids."""
    ids = []
    for i in range(capas, 0, -1):
        desfase = (capas - i) * grosor
        ids.append(canvas.create_oval(
            cx - radio - desfase, cy - radio - desfase,
            cx + radio + desfase, cy + radio + desfase,
            outline=interpolar_color(color, Paleta.FONDO_WIDGET,
                                     (capas - i) / capas),
            width=grosor,
        ))
    return ids


def banda_gradiente(canvas, x1, y1, x2, y2, color_a, color_b,
                    tiras=16, orientacion="vertical"):
    """Dibuja un degradado rectangular y devuelve sus ids."""
    ids = []
    for i in range(tiras):
        t = i / max(1, tiras - 1)
        color = interpolar_color(color_a, color_b, t)
        if orientacion == "vertical":
            ya = y1 + (y2 - y1) * (i / tiras)
            yb = y1 + (y2 - y1) * ((i + 1) / tiras)
            rect = (x1, ya, x2, yb)
        else:
            xa = x1 + (x2 - x1) * (i / tiras)
            xb = x1 + (x2 - x1) * ((i + 1) / tiras)
            rect = (xa, y1, xb, y2)
        ids.append(canvas.create_rectangle(
            *rect, fill=color, outline="", width=0,
        ))
    return ids


def corchetes_hud(canvas, x1, y1, x2, y2, largo=12, color=None,
                  grosor=2, nivel=1):
    """Dibuja corchetes HUD en las 4 esquinas de un rectángulo."""
    if color is None:
        color = Paleta.CYAN_DIM
    ids = []
    for n in range(nivel):
        d = n * (grosor + 1)
        x1n, y1n, x2n, y2n = x1 + d, y1 + d, x2 - d, y2 - d
        col = interpolar_color(color, Paleta.FONDO_WIDGET, n * 0.5)
        esquinas = (
            ((x1n, y1n + largo), (x1n, y1n), (x1n + largo, y1n)),  # sup-izq
            ((x2n, y1n + largo), (x2n, y1n), (x2n - largo, y1n)),  # sup-der
            ((x1n, y2n - largo), (x1n, y2n), (x1n + largo, y2n)),  # inf-izq
            ((x2n, y2n - largo), (x2n, y2n), (x2n - largo, y2n)),  # inf-der
        )
        for (a, b, c) in esquinas:
            ids.append(canvas.create_line(
                a[0], a[1], b[0], b[1], c[0], c[1],
                fill=col, width=grosor, joinstyle="miter",
            ))
    return ids


def scanlines(canvas, x1, y1, x2, y2, separacion=4, color=None):
    """Dibuja una rejilla de líneas horizontales."""
    if color is None:
        color = Paleta.ESCANEO
    return [
        canvas.create_line(x1, y, x2, y, fill=color, width=1)
        for y in range(int(y1), int(y2), separacion)
    ]


def texto_hud(canvas, x, y, contenido, ancla="nw", color=None,
              tamano=9, negrita=True):
    """Dibuja una etiqueta de texto monoespaciada en mayúsculas."""
    if color is None:
        color = Paleta.AXIOM_CYAN
    return canvas.create_text(
        x, y, text=contenido, anchor=ancla,
        font=(Paleta.FUENTE_HUD, tamano, "bold" if negrita else "normal"),
        fill=color,
    )


class RenderizadorBase:
    """Base de todos los renderers: cachea los ids de los ítems dibujados."""

    def __init__(self, canvas):
        """Asocia el renderer a 'canvas' e inicializa sus cachés de estado."""
        self.canvas = canvas
        self._ids = {}
        self._valores = {}

    def _primera_vez(self, nombre, creador):
        """Crea el ítem la primera vez y devuelve su id; si ya existe, reutiliza el id cacheado."""
        if nombre not in self._ids:
            self._ids[nombre] = creador()
        return self._ids[nombre]

    def _hay_cambio(self, clave, valor):
        """Devuelve True si 'valor' cambió respecto al último registrado con 'clave'."""
        if clave in self._valores and self._valores[clave] == valor:
            return False
        self._valores[clave] = valor
        return True


# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.renderizado.base_render

# Usa una raíz de Tkinter retirada para ejecutarse sin mostrar
# ninguna ventana.

if __name__ == "__main__":
    import sys
    import tkinter as tk

    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")  # evita errores en consolas cp1252
    print("Prueba base_render.py (helpers HUD)\n")

    print("rectangulo_redondeado")
    raiz = tk.Tk()
    raiz.withdraw()
    lienzo = tk.Canvas(raiz, width=320, height=220, bg=Paleta.FONDO_WIDGET)
    lienzo.pack()
    rid = rectangulo_redondeado(lienzo, 10, 10, 310, 210, Paleta.RADIO_TARJETA,
                                outline=Paleta.BORDE_SUAVE, width=1)
    assert isinstance(rid, int) and rid > 0, "El rectángulo redondeado debe devolver un id"
    print("OK: ítem creado\n")

    print("interpolar_color")
    assert interpolar_color("#000000", "#ffffff", 0.0) == "#000000", "t=0 da el color inicial"
    assert interpolar_color("#000000", "#ffffff", 1.0) == "#ffffff", "t=1 da el color final"
    assert interpolar_color("#000000", "#ffffff", 0.5) == "#808080", "t=0.5 da el gris medio"
    print("OK: extremos y punto medio\n")

    print("fulgor_radial")
    ids_fulgor = fulgor_radial(lienzo, 60, 170, 24, Paleta.AXIOM_CYAN, capas=4)
    assert len(ids_fulgor) == 4, "Debe crear el número de capas pedido"
    print(f"OK: {len(ids_fulgor)} anillos de brillo\n")

    print("anillo_con_halo")
    ids_halo = anillo_con_halo(lienzo, 150, 170, 8, 2, Paleta.NARANJA, capas=3)
    assert len(ids_halo) == 3, "Halo = aro central + capas"
    print(f"OK: {len(ids_halo)} aros concéntricos\n")

    print("banda_gradiente")
    ids_v = banda_gradiente(lienzo, 200, 150, 230, 200,
                            Paleta.AXIOM_CYAN, Paleta.FONDO_WIDGET, tiras=8)
    ids_h = banda_gradiente(lienzo, 240, 150, 310, 170,
                            Paleta.DORADO, Paleta.FONDO_WIDGET, tiras=8,
                            orientacion="horizontal")
    assert len(ids_v) == 8 and len(ids_h) == 8, "Cada orientación debe crear sus tiras"
    print("OK: degradados vertical y horizontal\n")

    print("corchetes_hud")
    ids_c = corchetes_hud(lienzo, 20, 20, 300, 130, largo=14, nivel=2)
    assert len(ids_c) == 8, "2 niveles x 4 esquinas x 1 polilínea = 8"
    print("OK: corchetes de las 4 esquinas\n")

    print("scanlines")
    ids_s = scanlines(lienzo, 20, 20, 300, 130, separacion=4)
    assert len(ids_s) == 28, f"Se esperaban 28 scanlines, llegaron {len(ids_s)}"
    print(f"OK: {len(ids_s)} líneas de barrido\n")

    print("texto_hud")
    tid = texto_hud(lienzo, 20, 140, "MODO MANUAL", tamano=9)
    assert isinstance(tid, int) and tid > 0, "El texto HUD debe devolver un id"
    print("OK: etiqueta monoespaciada creada\n")

    raiz.update()
    raiz.destroy()
    print("Pruebas OK")

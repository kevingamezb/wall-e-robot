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


# --- Primitivas de "holograma" (sistema visual Axiom + Wall-E) ---
#
# Tkinter no tiene blur, sombras, translucidez ni degradados: todo esto se
# SIMULA con primitivas opacas apiladas. Se crean una sola vez
# (RenderizadorBase._primera_vez) y solo se repintan si su estado cambia,
# igual que el resto de la GUI (regla de performance del dirty-check).

def fulgor_radial(canvas, cx, cy, radio, color, capas=4):
    """
    Brillo radial tipo holograma: anillos rellenos desde el color (centro)
    hasta el fondo del panel (borde), que dan la sensación de "glow".

    Devuelve la lista de ids creados, de mayor (tenue) a menor (intenso),
    para poder moverlos/esconderlos después.
    """
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
    """
    Un círculo con halo: los mismos aros concéntricos (cada uno más ancho
    y más tenue) alrededor del aro central. Ideal para el punto del radar,
    el thumb del deslizador o el "LED" de un ícono.
    """
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
    """
    Degradado rectangular: tira de rectángulos apilados interpolando entre
    color_a y color_b. Orientación 'vertical' (de arriba a abajo) o
    'horizontal' (de izquierda a derecha).
    """
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
    """
    Corchetes HUD en las 4 esquinas de un rectángulo: el "sello" visual de
    los paneles de la Nave. 'nivel' apila corchetes concéntricos (el
    exterior más tenue) para dar profundidad sin blur.
    """
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
    """
    Rejilla de scanlines (líneas finas horizontales) de la estética de
    "pantalla de la nave". Se dibuja UNA vez y no se repinta jamás.
    """
    if color is None:
        color = Paleta.ESCANEO
    return [
        canvas.create_line(x1, y, x2, y, fill=color, width=1)
        for y in range(int(y1), int(y2), separacion)
    ]


def texto_hud(canvas, x, y, contenido, ancla="nw", color=None,
              tamano=9, negrita=True):
    """
    Etiqueta de texto con cara de HUD: monoespaciada y en MAYÚSCULAS.
    Centraliza la fuente para que toda la app lea datos igual.
    """
    if color is None:
        color = Paleta.AXIOM_CYAN
    return canvas.create_text(
        x, y, text=contenido, anchor=ancla,
        font=(Paleta.FUENTE_HUD, tamano, "bold" if negrita else "normal"),
        fill=color,
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


# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.widgets.renderizado.base_render
#
# Abre una raíz de Tkinter CON LA VENTANA RETIRADA (withdraw), así el
# runner puede ejecutarlo sin que aparezca ningún cuadro en pantalla.

if __name__ == "__main__":
    import sys
    import tkinter as tk

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # consola cp1252 y flechas
    print("Prueba base_render.py (helpers HUD)\n")

    # --- 1. rectangulo_redondeado ---
    print("=== rectangulo_redondeado ===")
    raiz = tk.Tk()
    raiz.withdraw()
    lienzo = tk.Canvas(raiz, width=320, height=220, bg=Paleta.FONDO_WIDGET)
    lienzo.pack()
    rid = rectangulo_redondeado(lienzo, 10, 10, 310, 210, Paleta.RADIO_TARJETA,
                                outline=Paleta.BORDE_SUAVE, width=1)
    assert isinstance(rid, int) and rid > 0, "El rectángulo redondeado debe devolver un id"
    print("OK: ítem creado\n")

    # --- 2. interpolar_color ---
    print("=== interpolar_color ===")
    assert interpolar_color("#000000", "#ffffff", 0.0) == "#000000", "t=0 da el color inicial"
    assert interpolar_color("#000000", "#ffffff", 1.0) == "#ffffff", "t=1 da el color final"
    assert interpolar_color("#000000", "#ffffff", 0.5) == "#808080", "t=0.5 da el gris medio"
    print("OK: extremos y punto medio\n")

    # --- 3. fulgor_radial ---
    print("=== fulgor_radial ===")
    ids_fulgor = fulgor_radial(lienzo, 60, 170, 24, Paleta.AXIOM_CYAN, capas=4)
    assert len(ids_fulgor) == 4, "Debe crear el número de capas pedido"
    print(f"OK: {len(ids_fulgor)} anillos de brillo\n")

    # --- 4. anillo_con_halo ---
    print("=== anillo_con_halo ===")
    ids_halo = anillo_con_halo(lienzo, 150, 170, 8, 2, Paleta.NARANJA, capas=3)
    assert len(ids_halo) == 3, "Halo = aro central + capas"
    print(f"OK: {len(ids_halo)} aros concéntricos\n")

    # --- 5. banda_gradiente ---
    print("=== banda_gradiente ===")
    ids_v = banda_gradiente(lienzo, 200, 150, 230, 200,
                            Paleta.AXIOM_CYAN, Paleta.FONDO_WIDGET, tiras=8)
    ids_h = banda_gradiente(lienzo, 240, 150, 310, 170,
                            Paleta.DORADO, Paleta.FONDO_WIDGET, tiras=8,
                            orientacion="horizontal")
    assert len(ids_v) == 8 and len(ids_h) == 8, "Cada orientación debe crear sus tiras"
    print("OK: degradados vertical y horizontal\n")

    # --- 6. corchetes_hud ---
    print("=== corchetes_hud ===")
    ids_c = corchetes_hud(lienzo, 20, 20, 300, 130, largo=14, nivel=2)
    assert len(ids_c) == 8, "2 niveles x 4 esquinas x 1 polilínea = 8"
    print("OK: corchetes de las 4 esquinas\n")

    # --- 7. scanlines ---
    print("=== scanlines ===")
    ids_s = scanlines(lienzo, 20, 20, 300, 130, separacion=4)
    assert len(ids_s) == 28, f"Se esperaban 28 scanlines, llegaron {len(ids_s)}"
    print(f"OK: {len(ids_s)} líneas de barrido\n")

    # --- 8. texto_hud ---
    print("=== texto_hud ===")
    tid = texto_hud(lienzo, 20, 140, "MODO MANUAL", tamano=9)
    assert isinstance(tid, int) and tid > 0, "El texto HUD debe devolver un id"
    print("OK: etiqueta monoespaciada creada\n")

    raiz.update()
    raiz.destroy()
    print("Pruebas OK")
# wall-e-robot/app/widgets/renderizado/carga_recursos.py
# Kevin Gámez - 15/10/2026
#
# Carga los PNG de app/recursos/, los tiñe (vía Recoloreo) con un color de la
# Paleta y los entrega como PhotoImage de Tk.


from pathlib import Path
from PIL import Image, ImageTk, ImageOps

from ... import rutas
from .recoloreo import Recoloreo


# Carpeta de assets (app/recursos). El cajón y las pruebas la reemplazan por
# un temp dir; congelado, apunta dentro del bundle.
DIRECTORIO = rutas.directorio_recursos()

# Cache de PhotoImage ya construidos: (nombre, color, alto, espejo) -> foto.
# Mantener las referencias evita que el recolector de basura libere las imágenes.
_CACHE = {}


def ruta_asset(nombre: str, extension: str = "png") -> Path:
    """Ruta completa del asset 'nombre' (sin extensión)."""
    return DIRECTORIO / f"{nombre}.{extension}"


def existe(nombre: str) -> bool:
    """True si el PNG del asset existe (para decidir el fallback procedural)."""
    return ruta_asset(nombre).is_file()


def cargar(nombre: str, color: str, alto: int, espejo: bool = False):
    """Carga, tiñe con 'color' y escala a 'alto' (conservando aspecto).

    'espejo=True' devuelve la imagen reflejada (para el ojo derecho).
    """
    clave = (nombre, color, alto, espejo)
    if clave in _CACHE:
        return _CACHE[clave]

    with Image.open(ruta_asset(nombre)) as abierta:
        imagen = abierta.convert("RGBA")

    imagen = Recoloreo.tenir(imagen, color)
    ancho = max(1, round(alto * imagen.width / imagen.height))
    imagen = imagen.resize((ancho, alto), Image.LANCZOS)
    if espejo:
        imagen = ImageOps.mirror(imagen)

    foto = ImageTk.PhotoImage(imagen)
    _CACHE[clave] = foto
    return foto


def cargar_ancho(nombre: str, ancho: int, rotar: int = 0, sustituciones=(),
                 espejo: bool = False):
    """Carga el PNG 'nombre' escalado a 'ancho' px, conservando sus colores.

    rotar         : grados en sentido horario (0, 90, 180, 270).
    sustituciones : pares (color_origen, color_destino) que se cambian dentro
                    de la imagen (ver Recoloreo.sustituir). Sirve para variar
                    el estado de una pieza sin exportar un PNG por estado.
    """
    sustituciones = tuple(sustituciones)
    clave = ("ancho", nombre, ancho, rotar, sustituciones, espejo)
    if clave in _CACHE:
        return _CACHE[clave]

    with Image.open(ruta_asset(nombre)) as abierta:
        imagen = abierta.convert("RGBA")

    for par in sustituciones:
        origen, destino = par[0], par[1]
        tolerancia = par[2] if len(par) > 2 else 70
        imagen = Recoloreo.sustituir(imagen, origen, destino, tolerancia)
    if rotar % 360:
        imagen = imagen.rotate(-rotar, expand=True, resample=Image.BICUBIC)
    alto = max(1, round(ancho * imagen.height / imagen.width))
    imagen = imagen.resize((max(1, ancho), alto), Image.LANCZOS)
    if espejo:
        imagen = ImageOps.mirror(imagen)

    foto = ImageTk.PhotoImage(imagen)
    _CACHE[clave] = foto
    return foto


def cargar_fondo(nombre: str, ancho: int, alto: int):
    """Carga el PNG 'nombre' estirado exactamente a ancho x alto (fondo)."""
    clave = ("fondo", nombre, ancho, alto)
    if clave in _CACHE:
        return _CACHE[clave]
    with Image.open(ruta_asset(nombre)) as abierta:
        imagen = abierta.convert("RGBA").resize((ancho, alto), Image.LANCZOS)
    foto = ImageTk.PhotoImage(imagen)
    _CACHE[clave] = foto
    return foto


# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.renderizado.carga_recursos

# Usa una raíz de Tkinter retirada y PNG generados en un temp dir, para no
# depender de que los assets reales estén exportados.

if __name__ == "__main__":
    import sys
    import tempfile
    import tkinter as tk
    from ...nucleo.paleta import Paleta

    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")  # evita errores en consolas cp1252
    print("Prueba carga_recursos.py\n")

    raiz = tk.Tk()
    raiz.withdraw()

    with tempfile.TemporaryDirectory() as temporal:
        DIRECTORIO = Path(temporal)

        # PNG de prueba: mitad opaca, fondo transparente (20x10).
        muestra = Image.new("RGBA", (20, 10), (255, 255, 255, 0))
        for x in range(10):
            for y in range(10):
                muestra.putpixel((x, y), (255, 255, 255, 255))
        muestra.save(DIRECTORIO / "prueba.png")

        print("existe()")
        assert existe("prueba") is True
        assert existe("no_existe") is False
        print("OK: distingue presente/ausente\n")

        print("tinte conservando alfa (vía Recoloreo)")
        teñida = Recoloreo.tenir(muestra, Paleta.DORADO)
        assert teñida.size == (20, 10)
        assert teñida.getpixel((2, 2)) == Recoloreo.a_rgb(Paleta.DORADO) + (255,), \
            "El píxel opaco toma el color pedido"
        assert teñida.getpixel((15, 5))[3] == 0, "El fondo sigue transparente"
        print("OK: colores del dibujo sí, fondo no\n")

        print("cargar() escala por alto conservando aspecto")
        foto = cargar("prueba", Paleta.DORADO, 30)
        assert foto.height() == 30, "El alto pedido se respeta"
        assert foto.width() == 60, "El ancho conserva el aspecto (20x10 -> 60x30)"
        print(f"OK: {foto.width()}x{foto.height()}\n")

        print("cache y espejo")
        assert cargar("prueba", Paleta.DORADO, 30) is foto, "El mismo pedido reutiliza la foto"
        foto_espejo = cargar("prueba", Paleta.DORADO, 30, espejo=True)
        assert foto_espejo is not foto, "El espejo es una foto distinta"
        print("OK: cache y variante espejada\n")

    raiz.destroy()
    print("Pruebas OK")

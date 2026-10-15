# wall-e-robot/app/widgets/renderizado/carga_recursos.py
# Kevin Gámez - 15/10/2026

# Carga los PNG de app/recursos/, los tiñe con un color de la Paleta y los
# entrega como PhotoImage de Tk. Así los assets se dibujan por imágenes pero
# el color sigue saliendo de un único lugar (Paleta).


from pathlib import Path
from PIL import Image, ImageTk, ImageOps


# Carpeta de assets (app/recursos). El cajón la reemplaza por un temp dir.
DIRECTORIO = Path(__file__).resolve().parents[2] / "recursos"

# Cache de PhotoImage ya construidos: (nombre, color, alto, espejo) -> foto.
# Mantener las referencias evita que el recolector de basura libere las imágenes.
_CACHE = {}


def ruta_asset(nombre: str, extension: str = "png") -> Path:
    """Ruta completa del asset 'nombre' (sin extensión)."""
    return DIRECTORIO / f"{nombre}.{extension}"


def existe(nombre: str) -> bool:
    """True si el PNG del asset existe (para decidir el fallback procedural)."""
    return ruta_asset(nombre).is_file()


def _tenido(imagen: Image.Image, color: str) -> Image.Image:
    """Copia de 'imagen' (RGBA) pintada con 'color', conservando su alfa."""
    color_rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    solido = Image.new("RGBA", imagen.size, color_rgb + (255,))
    solido.putalpha(imagen.getchannel("A"))
    return solido


def cargar(nombre: str, color: str, alto: int, espejo: bool = False):
    """Carga, tiñe con 'color' y escala a 'alto' (conservando aspecto).

    'espejo=True' devuelve la imagen reflejada (para el ojo derecho).
    """
    clave = (nombre, color, alto, espejo)
    if clave in _CACHE:
        return _CACHE[clave]

    with Image.open(ruta_asset(nombre)) as abierta:
        imagen = abierta.convert("RGBA")

    imagen = _tenido(imagen, color)
    ancho = max(1, round(alto * imagen.width / imagen.height))
    imagen = imagen.resize((ancho, alto), Image.LANCZOS)
    if espejo:
        imagen = ImageOps.mirror(imagen)

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

        print("tinte conservando alfa")
        teñida = _tenido(muestra, Paleta.DORADO)
        assert teñida.size == (20, 10)
        assert teñida.getpixel((2, 2)) == (0xcb, 0xa1, 0x35, 255), \
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

# wall-e-robot/app/widgets/renderizado/recoloreo.py
# Kevin Gámez - 15/10/2026


from PIL import Image, ImageChops


class Recoloreo:
    """Matemáticas y transformación de color (code tinting).

    Único origen del recoloreo: conversiones hex <-> RGB, interpolación entre
    dos colores y tinte de imágenes RGBA conservando el alfa. El resto del
    código pide el color por aquí en vez de parsear hex a mano.
    """

    @staticmethod
    def a_rgb(hexadecimal: str) -> tuple:
        """(r, g, b) de un color '#rrggbb'."""
        return tuple(int(hexadecimal[i:i + 2], 16) for i in (1, 3, 5))

    @staticmethod
    def a_hex(rgb) -> str:
        """Color '#rrggbb' a partir de una tupla (r, g, b)."""
        r, g, b = rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def interpolar(hex1: str, hex2: str, t: float) -> str:
        """Color intermedio entre hex1 (t=0) y hex2 (t=1), recortando t a [0, 1]."""
        t = max(0.0, min(1.0, t))
        c1 = Recoloreo.a_rgb(hex1)
        c2 = Recoloreo.a_rgb(hex2)
        return Recoloreo.a_hex(
            round(a + (b - a) * t) for a, b in zip(c1, c2))

    @staticmethod
    def tenir(imagen: Image.Image, color: str) -> Image.Image:
        """Copia de 'imagen' (RGBA) pintada con 'color', conservando su alfa.

        Si la imagen no está en RGBA se convierte antes: el tinte se apoya en
        el canal alfa original para que el fondo transparente siga siéndolo.
        """
        if imagen.mode != "RGBA":
            imagen = imagen.convert("RGBA")
        solido = Image.new("RGBA", imagen.size, Recoloreo.a_rgb(color) + (255,))
        solido.putalpha(imagen.getchannel("A"))
        return solido


    @staticmethod
    def sustituir(imagen: Image.Image, origen: str, destino: str,
                  tolerancia: int = 70) -> Image.Image:
        """Copia de 'imagen' donde los píxeles parecidos a 'origen' pasan a
        'destino'. Los píxeles intermedios (bordes suavizados) se mezclan en
        proporción a su parecido, de modo que no queda un halo del color viejo.
        El alfa original se conserva."""
        imagen = imagen.convert("RGBA")
        rgb = imagen.convert("RGB")
        solido_origen = Image.new("RGB", imagen.size, Recoloreo.a_rgb(origen))
        dif = ImageChops.difference(rgb, solido_origen)
        r, g, b = dif.split()
        distancia = ImageChops.lighter(ImageChops.lighter(r, g), b)
        peso = distancia.point(
            lambda v: max(0, min(255, round(255 * (1 - v / tolerancia)))))
        solido_destino = Image.new("RGB", imagen.size, Recoloreo.a_rgb(destino))
        mezcla = Image.composite(solido_destino, rgb, peso).convert("RGBA")
        mezcla.putalpha(imagen.getchannel("A"))
        return mezcla


# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.renderizado.recoloreo

# Solo depende de Pillow (sin Tkinter): puede ejecutarse sin display.

if __name__ == "__main__":
    import sys
    from ...nucleo.paleta import Paleta

    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")  # evita errores en consolas cp1252
    print("Prueba recoloreo.py\n")

    print("a_rgb / a_hex")
    assert Recoloreo.a_rgb("#cba135") == (0xCB, 0xA1, 0x35), \
        "hex -> tupla RGB"
    assert Recoloreo.a_hex((0xCB, 0xA1, 0x35)) == "#cba135", \
        "tupla RGB -> hex"
    assert Recoloreo.a_hex(Recoloreo.a_rgb(Paleta.ROJO)) == Paleta.ROJO, \
        "ida y vuelta sin perdida"
    print("OK: conversiones hex <-> RGB\n")

    print("interpolar")
    assert Recoloreo.interpolar("#000000", "#ffffff", 0.0) == "#000000", \
        "t=0 da el color inicial"
    assert Recoloreo.interpolar("#000000", "#ffffff", 1.0) == "#ffffff", \
        "t=1 da el color final"
    assert Recoloreo.interpolar("#000000", "#ffffff", 0.5) == "#808080", \
        "t=0.5 da el gris medio"
    assert Recoloreo.interpolar("#000000", "#ffffff", -3.0) == "#000000", \
        "t<0 se recorta al inicial"
    assert Recoloreo.interpolar("#000000", "#ffffff", 9.0) == "#ffffff", \
        "t>1 se recorta al final"
    print("OK: extremos, punto medio y recorte de t\n")

    print("tenir conservando alfa")
    muestra = Image.new("RGBA", (20, 10), (255, 255, 255, 0))
    for x in range(10):
        for y in range(10):
            muestra.putpixel((x, y), (255, 255, 255, 255))
    tenida = Recoloreo.tenir(muestra, Paleta.DORADO)
    assert tenida.size == (20, 10), "El tamaño no cambia"
    assert tenida.getpixel((2, 2)) == Recoloreo.a_rgb(Paleta.DORADO) + (255,), \
        "El píxel opaco toma el color pedido"
    assert tenida.getpixel((15, 5))[3] == 0, "El fondo sigue transparente"
    assert muestra.getpixel((2, 2)) == (255, 255, 255, 255), \
        "La imagen original no se toca (se devuelve una copia)"
    print("OK: colores del dibujo sí, fondo no, y original intacta\n")

    print("tenir convierte a RGBA si hace falta")
    rgb = Image.new("RGB", (4, 4), (255, 255, 255))
    rgb_tenida = Recoloreo.tenir(rgb, Paleta.AXIOM_CYAN)
    assert rgb_tenida.mode == "RGBA"
    assert rgb_tenida.getpixel((0, 0))[:3] == Recoloreo.a_rgb(Paleta.AXIOM_CYAN)
    print("OK: imagen sin alfa -> opaca con el color pedido\n")

    print("Pruebas OK")

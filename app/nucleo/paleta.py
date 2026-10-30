# wall-e-robot/app/nucleo/paleta.py
# Kevin Gámez - 26/08/2026


class Paleta:
    """Paleta de colores y sistema visual de la GUI."""

    # Fondos
    FONDO_APP    = "#191b27"   # fondo general de la ventana
    FONDO_NEGRO  = "#16181b"   # paneles negros (barra lateral y panel central)
    FONDO_WIDGET = "#2b2d42"   # pantallas oscuras dentro de las tarjetas
    FONDO_CANVAS = "#1b1b29"   # lienzo/entradas aún más oscuros
    PLATA        = "#6b6d76"   # marco plateado de la ventana

    # Tarjetas claras
    TARJETA      = "#edf2f4"   # cara de las tarjetas
    TINTA        = "#1b1b29"   # trazos y texto sobre las tarjetas

    # Acentos del robot
    DORADO       = "#e1b12c"   # chassis/ojos del robot
    DORADO_DIM   = "#96701c"   # variante tenue del dorado
    DORADO_BORDE = "#58420d"   # contorno oscuro de las piezas doradas
    NARANJA      = "#c37609"   # advertencias / ojos en manual

    # Acentos de información
    AZUL         = "#1e5ea0"   # texto informativo sobre tarjetas claras
    AXIOM_CYAN   = "#7fb2e5"   # información activa sobre pantallas oscuras
    CYAN_DIM     = "#4a4a6f"   # bordes y brillos tenues
    HUD_LINE     = "#3a3c5a"   # líneas estructurales sobre pantallas oscuras
    ESCANEO      = "#252546"   # (reservado)

    # Texto
    TEXTO_LOG    = "#edf2f4"   # general (blanco-hielo)
    TEXTO_TENUE  = "#9a9cc0"   # etiquetas de sección e inactivo
    GRIS         = "#4a4a6f"   # "apagado"/sin datos (violeta grisáceo)
    VERDE_LIMA   = "#8fd82a"   # carga / OK
    ROJO         = "#d64545"   # error / obstáculo

    # Borde de los paneles
    BORDE_SUAVE  = "#252546"

    # Fuentes. Los textos del diseño se dibujan con Quadrillion (ver
    # widgets/renderizado/texto_render.py); estas familias son para los
    # widgets nativos de Tk (campos de texto, terminal, ventanas modales).
    FUENTE_TEXTO = "Segoe UI"
    FUENTE_HUD   = "Consolas"

    # Sistema de espaciado
    UNIDAD        = 24             # --unit: la base de todos los gaps
    UNIDAD_GRANDE = 39             # UNIDAD * PROPORCION_AUREA: separaciones "de sección"

    # Radios de esquina
    RADIO_TARJETA = 10             # border-radius de los contenedores
    RADIO_BOTON   = 6              # border-radius de los botones


PROPORCION_AUREA = 1.618  # proporción usada en las dimensiones del layout


def color_por_umbral(fraccion: float, invertido: bool = False) -> str:
    """
    Devuelve un color de la paleta según 'fraccion' (0.0 a 1.0).

    invertido=False asocia los valores altos a DORADO (p. ej. batería);
    invertido=True invierte la escala, para magnitudes donde más es peor
    (p. ej. consumo). Por debajo de 0.1 siempre GRIS (apagado/sin datos).
    """

    if invertido:
        if fraccion > 0.7:
            return Paleta.ROJO

        elif fraccion > 0.4:
            return Paleta.NARANJA

        elif fraccion > 0.1:
            return Paleta.DORADO

        else:
            return Paleta.GRIS

    else:
        if fraccion > 0.7:
            return Paleta.DORADO

        elif fraccion > 0.4:
            return Paleta.NARANJA

        elif fraccion > 0.1:
            return Paleta.ROJO

        else:
            return Paleta.GRIS


# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.nucleo.paleta

if __name__ == '__main__':
    print("Prueba paleta.py\n")

    print("Caso normal (invertido=False, ej. batería)")
    print(f"1.00 -> {color_por_umbral(1.00)}")          # esperado: DORADO
    print(f"0.75 -> {color_por_umbral(0.75)}")          # esperado: DORADO
    print(f"0.50 -> {color_por_umbral(0.50)}")          # esperado: NARANJA
    print(f"0.20 -> {color_por_umbral(0.20)}")          # esperado: ROJO
    print(f"0.05 -> {color_por_umbral(0.05)}")          # esperado: GRIS
    print(f"0.00 -> {color_por_umbral(0.00)}")          # esperado: GRIS

    print("\nCaso invertido (invertido=True, ej. consumo)")
    print(f"1.00 -> {color_por_umbral(1.00, invertido=True)}")  # esperado: ROJO
    print(f"0.75 -> {color_por_umbral(0.75, invertido=True)}")  # esperado: ROJO
    print(f"0.50 -> {color_por_umbral(0.50, invertido=True)}")  # esperado: NARANJA
    print(f"0.20 -> {color_por_umbral(0.20, invertido=True)}")  # esperado: DORADO
    print(f"0.00 -> {color_por_umbral(0.00, invertido=True)}")  # esperado: GRIS

    print("\nVerificación cruzada: colores deben ser strings hexadecimales")
    color_prueba = color_por_umbral(1.00, invertido=True)
    assert color_prueba == Paleta.ROJO, f"Se esperaba ROJO, llegó {color_prueba}"
    print(f"OK: consumo al máximo da {color_prueba} ({Paleta.ROJO} = Paleta.ROJO)")

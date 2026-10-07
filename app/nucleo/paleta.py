# wall-e-robot/app/nucleo/paleta.py
# Kevin Gámez - 26/08/2026


class Paleta:
    """
    La paleta de colores para la Interfaz Gráfica
    
    funciona como un espacio de nombres agrupador,
    no como un tipo de dato con instancias distintas entre sí.
    
    Además de colores, guarda el "sistema" visual de la GUI: primero calcado
    del mockup (walle_demo.html) y ahora temático "Axiom + Wall-E":
    fondo azul-espacio, paneles de cristal, brillo cian tipo EVE para lo de
    la NAVE (radar, terminal, íconos) y dorado/naranja Wall-E para lo del
    ROBOT (mando, ojos). También las unidades de espaciado y las fuentes.
    Así ninguna pantalla necesita números mágicos sueltos, y ningún color
    se escribe fuera de aquí (regla del proyecto).
    """
    
    # --- Fondos (noche de la nave: azul profundo) ---
    FONDO_APP    = "#0a111f"   # fondo general de la ventana
    FONDO_WIDGET = "#0c1626"   # cara de los paneles (tarjetas)
    FONDO_CANVAS = "#080f1c"   # lienzo interno (radar, gamepad): aún más oscuro

    # --- Acentos del robot (Wall-E) ---
    DORADO       = "#cba135"   # chassis/ojos del robot
    DORADO_DIM   = "#6e5416"   # variante tenue del dorado
    NARANJA      = "#e8932e"   # advertencias / ojos en manual

    # --- Acentos de la nave (Axiom / EVE) ---
    AXIOM_CYAN   = "#58c7f3"   # hologramas e interfaces de la nave
    CYAN_DIM     = "#2471a6"   # bordes y brillos tenues
    HUD_LINE     = "#1c2f4d"   # líneas estructurales de los paneles
    ESCANEO      = "#0a1220"   # scanlines (superpuestas a los paneles)

    # --- Texto ---
    TEXTO_LOG    = "#e8f4ff"   # general (blanco-hielo)
    TEXTO_TENUE  = "#7e9ab8"   # etiquetas de sección e inactivo
    GRIS         = "#33435e"   # "apagado"/sin datos (grafito azulado)
    VERDE_LIMA   = "#8fd82a"   # carga / OK
    ROJO         = "#e05656"   # error / obstáculo

    # --- Borde de los paneles ---
    BORDE_SUAVE  = "#1b2a44"   # borde de las tarjetas de cristal

    # --- Fuentes ---
    FUENTE_TEXTO = "Segoe UI"
    FUENTE_HUD   = "Consolas"

    # --- Sistema de espaciado (una unidad para todo) ---
    UNIDAD        = 24             # --unit: la base de todos los gaps
    UNIDAD_GRANDE = 39             # UNIDAD * PROPORCION_AUREA: separaciones "de sección"

    # --- Radios de esquina: el "lenguaje visual" de las tarjetas ---
    RADIO_TARJETA = 10             # border-radius de los contenedores
    RADIO_BOTON   = 6              # border-radius de los botones


PROPORCION_AUREA = 1.618 # Usar para dimensiones del Layout de Widgets


def color_por_umbral(fraccion: float, invertido: bool = False) -> str:
    """
    Regla del Color por Umbral, diseñada para la UX/UI

    fraccion: 0.0 a 1.0
    invertido: True para casos donde "más" es peor (ej. consumo),
               False para casos donde "más" es mejor (ej. batería)
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
        

# Cajón de pruebas para este archivo
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
    print(f"0.00 -> {color_por_umbral(0.00, invertido=True)}")  # esperado: GRIS (sin actividad)

    print("\nVerificación cruzada: colores deben ser strings hexadecimales")
    color_prueba = color_por_umbral(1.00, invertido=True)
    assert color_prueba == Paleta.ROJO, f"Se esperaba ROJO, llegó {color_prueba}" # assert funciona como una herramienta de prueba automátizada y rápida
    print(f"OK: consumo al máximo da {color_prueba} ({Paleta.ROJO} = Paleta.ROJO)")
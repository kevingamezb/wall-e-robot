# wall-e-robot/app/nucleo/paleta.py
# Kevin Gámez - 26/08/2026


class Paleta:
    """
    La paleta de colores para la Interfaz Gráfica
    
    funciona como un espacio de nombres agrupador,
    no como un tipo de dato con instancias distintas entre sí.
    
    Además de colores, guarda el "sistema" visual calcado del mockup
    (walle_demo.html): la unidad de espaciado y los radios de esquina.
    Así ninguna pantalla necesita números mágicos sueltos.
    """
    
    FONDO_APP     = "#1a1a1a"
    FONDO_WIDGET  = "#0d0d0d"
    DORADO        = "#aa8800"
    DORADO_DIM    = "#6b5600"
    TEXTO_LOG     = "#ffffff"
    GRIS          = "#3a3a3a"
    NARANJA       = "#d88a2a"
    ROJO          = "#c94a4a"
    VERDE_LIMA    = "#8fd82a"
    BORDE_SUAVE   = "#2c2c2c"      # --border-soft (borde de las tarjetas)
    TEXTO_TENUE   = "#8a8a8a"      # --text-dim (labels de sección)

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
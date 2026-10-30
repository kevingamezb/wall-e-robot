# wall-e-robot/app/nucleo/disenio.py
# Kevin Gámez - 29/10/2026


import os

ANCHO_BASE = 3840
ALTO_BASE = 2160

# Factor de escala permitido (1.0 = tamaño del diseño, 3840 x 2160 px).
ESCALA_MIN = 0.25
ESCALA_MAX = 0.40


class Escala:
    """Convierte unidades de diseño a píxeles de pantalla."""

    def __init__(self, factor: float):
        self.factor = factor

    def __call__(self, valor) -> int:
        """Píxeles (entero) de 'valor' unidades de diseño."""
        return int(round(valor * self.factor))

    def caja(self, caja) -> tuple:
        """(x1, y1, x2, y2) en píxeles de una caja en unidades de diseño."""
        return tuple(self(v) for v in caja)

    def fuente(self, unidades) -> int:
        """Tamaño de letra en píxeles (mínimo legible) de 'unidades' de diseño."""
        return max(8, self(unidades))

    @property
    def ancho(self) -> int:
        return self(ANCHO_BASE)

    @property
    def alto(self) -> int:
        return self(ALTO_BASE)


def escala_para_pantalla(ancho_pantalla: int, alto_pantalla: int) -> Escala:
    """Elige la mayor escala que cabe en la pantalla (con margen para la barra
    de título y la barra de tareas). WALLE_ESCALA fuerza un valor concreto."""
    forzada = os.environ.get("WALLE_ESCALA")
    if forzada:
        try:
            return Escala(float(forzada))
        except ValueError:
            pass
    factor = min(ancho_pantalla * 0.97 / ANCHO_BASE,
                 (alto_pantalla - 110) / ALTO_BASE)
    return Escala(max(ESCALA_MIN, min(ESCALA_MAX, factor)))


class Disenio:
    """Cajas (x1, y1, x2, y2) y puntos del diseño, en unidades de diseño."""

    # Marco de la ventana
    LOGO            = (68, 216, 880, 394)
    BARRA_LATERAL   = (26, 410, 937, 2134)
    SELECTOR        = (26, 410, 937, 475)
    # Editor de teclas incrustado: debajo de las pestañas y dentro de la barra,
    # sin tocar el panel central.
    PANEL_CONTROLES = (26, 520, 937, 2080)
    PANEL_CENTRAL   = (985, 387, 3820, 2139)
    CHAFLAN_PANEL   = 44

    # Cabecera
    RAYAS_TITULO    = (1086, 246, 1372, 371)
    TITULO_PANEL    = (1381, 260, 2031, 360)
    TELEMETRIA      = (2365, 323, 2583, 355)

    # Barra lateral: conexión
    TAB_CONECTAR    = (129, 419, 296, 466)
    TAB_CONTROLES   = (584, 419, 760, 466)
    ETIQUETA_IP     = (133, 733, 247, 828)
    CAMPO_IP        = (107, 825, 857, 900)
    ETIQUETA_PORT   = (133, 973, 390, 1068)
    CAMPO_PORT      = (107, 1065, 857, 1140)
    BOTON_CONECTAR  = (130, 1451, 839, 1679)
    ESTADO_CONEXION = (130, 1740, 839, 2080)

    # Tarjetas (cara exterior y línea interior)
    TARJETA_ESTADO      = (1003, 405, 1813, 1273)
    LINEA_ESTADO        = (1043, 440, 1786, 1251)
    TARJETA_ENERGIA     = (1833, 405, 2857, 1273)
    LINEA_CONSUMO       = (1868, 439, 2354, 1252)
    LINEA_BATERIA       = (2382, 439, 2833, 1252)
    TARJETA_REGISTRO    = (2877, 405, 3803, 1273)
    LINEA_REGISTRO      = (2909, 440, 3777, 1251)
    TARJETA_NAVEGACION  = (1004, 1302, 2352, 2095)
    LINEA_NAVEGACION    = (1031, 1330, 2325, 2067)
    TARJETA_CONTROL     = (2373, 1302, 3803, 2095)
    LINEA_CONTROL       = (2401, 1330, 3775, 2067)

    # Separadores verticales dentro de las tarjetas (x, y1, y2, grosor)
    SEP_NAVEGACION      = (1675, 1486, 1992, 11)
    SEP_CONTROL         = (3055, 1464, 2009, 11)

    # Rótulos de tarjeta: x de la pastilla, y superior de la pastilla
    PASTILLA = {
        "estado":     (1083, 473),
        "consumo":    (1901, 473),
        "bateria":    (2419, 473),
        "registro":   (2945, 472),
        "navegacion": (1087, 1366),
        "control":    (2446, 1368),
    }
    PASTILLA_ANCHO = 23
    PASTILLA_ALTO = 68

    # Estado
    PANTALLA_ESTADO = (1077, 597, 1751, 1203)
    ICONO_MODO      = (1214, 621, 1309, 716)
    TEXTO_MODO      = (1326, 629)
    TEXTO_MODO_SUB  = (1326, 690)
    OJOS_CENTRO     = (1414, 905)
    OJOS_ALTO       = 290
    ICONOS_Y        = 1080
    ICONOS_X        = (1137, 1273, 1449, 1590)   # conexión, carga, advertencia, error
    ICONO_LADO      = 100

    # Consumo
    BARRAS_CAJA     = (1955, 597, 2268, 1122)
    BARRA_ALTO      = 58
    BARRA_PASO      = 75
    BARRA_BASE_ALTO = 146
    CONSUMO_ETIQUETA = (2111, 1188)

    # Batería
    PANTALLA_BATERIA = (2409, 571, 2806, 1027)
    SOL_CENTRO       = (2607, 789)
    SOL_RADIO        = 183
    BATERIA_LINEA1   = (2590, 1101)
    BATERIA_LINEA2   = (2581, 1165)

    # Registro
    PANTALLA_REGISTRO = (2946, 559, 3755, 1219)
    TEXTO_REGISTRO    = (2962, 575, 3678, 1203)
    SCROLL_REGISTRO   = (3699, 604, 3724, 1174)

    # Navegación
    RADAR_CENTRO    = (1377, 1893)
    RADAR_RADIOS    = (124, 219, 317)
    RADAR_GROSOR    = 26
    DISTANCIA_TITULO = (1747, 1604)
    DISTANCIA_VALOR  = (1768, 1682)
    MOVIMIENTO_TITULO = (1747, 1836)
    MOVIMIENTO_SIMBOLO = (1767, 1891, 1848, 1964)
    MOVIMIENTO_TEXTO = (1883, 1888)

    # Control (mando)
    FLECHA_ARRIBA   = (2575, 1491, 2886, 1634)
    FLECHA_DERECHA  = (2832, 1581, 2975, 1892)
    FLECHA_ABAJO    = (2575, 1839, 2886, 1982)
    FLECHA_IZQUIERDA = (2485, 1581, 2628, 1892)
    REPOSO          = (2634, 1640, 2827, 1833)
    CUELLO_PISTA    = (3207, 1528, 365)          # x izquierda, y centro, largo
    BRAZO_L_PISTA   = (3278, 1666, 316)          # x centro, y superior, largo
    BRAZO_R_PISTA   = (3496, 1666, 316)
    PISTA_GROSOR    = 26
    THUMB_RADIO     = 30
    ETIQUETA_CUELLO = (3380, 1575)
    ETIQUETA_BRAZOS = (3375, 1975)
    ETIQUETA_L      = (3277, 2009)
    ETIQUETA_R      = (3497, 2009)

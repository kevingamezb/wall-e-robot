# wall-e-robot/app/nucleo/estado.py
# Kevin Gámez - 26/08/2026


from enum import Enum
from dataclasses import dataclass, field
from collections import deque
from time import time


class Modo(Enum):
    """
    Modo de operación del robot.

    Es un Enum (y no un string) para que un typo ('automtico') falle de
    inmediato en vez de propagarse silenciosamente.
    """

    AUTOMATICO = 'automatico'
    MANUAL = 'manual'


class NivelLog(Enum):
    """Severidad de una línea de log; el widget del logger la usa para colorearla."""

    INFO = 'info'
    ADVERTENCIA = 'advertencia'
    ERROR = 'error'


@dataclass
class EntradaLog:
    """Una línea de log: cuándo, de dónde, qué dice y qué tan grave es."""

    timestamp:  float
    origen   :  str
    mensaje  :  str
    nivel    :  NivelLog = NivelLog.INFO


class Logger:
    """
    Buffer circular de las últimas líneas de log con suscriptores.

    Sigue el patrón observador: quien agrega una línea no conoce a los
    consumidores; solo avisa a los suscriptores registrados.
    """

    def __init__(self, max_lineas: int = 30):
        """
        Se usa una deque porque agrega y descarta por ambos extremos en O(1) y,
        con maxlen, descarta sola la línea más vieja al llenarse.
        """

        self._buffer = deque(maxlen=max_lineas)
        self._subscriptores = []

    def agregar_linea(self, origen: str, mensaje: str,
                            nivel: NivelLog = NivelLog.INFO):
        """Agrega una línea al buffer y notifica a los suscriptores."""

        nueva_entrada = EntradaLog(time(), origen, mensaje, nivel)
        self._buffer.append(nueva_entrada)

        for avisar_suscriptor in self._subscriptores:
            avisar_suscriptor(nueva_entrada)

    def agregar_suscriptor(self, suscriptor):
        """
        Registra un callback que se invocará con cada nueva entrada.
        """

        self._subscriptores.append(suscriptor)

    def obtener_lineas(self) -> list[EntradaLog]:
        """Devuelve una copia del buffer (no el buffer interno)."""

        return list(self._buffer)


@dataclass
class PosicionServos:
    """
    Ángulo actual de cada servo.

    Se agrupa aparte de EstadoRobot porque es un concepto cohesivo: por
    ejemplo, el botón de "reposo" del gamepad resetea un PosicionServos entero
    a ceros de una vez, en lugar de tocar campos sueltos por separado.
    """

    cuello          : float = 0.0
    hombro_izquierdo: float = 0.0
    hombro_derecho  : float = 0.0
    # TODO(equipo): definir si se van a usar más servos:
    pulgar_izquierdo: float = 0.0
    pulgar_derecho  : float = 0.0
    radar_us        : float = 0.0


@dataclass
class EstadoRobot:
    """
    Caja de datos compartida: cada campo responde a "¿qué necesita algún
    widget para dibujarse?".

    Los widgets solo leen; la única escritura viene del flujo de comandos del
    gamepad (GUI -> robot).

    Para objetos mutables (PosicionServos, Logger) se usa field(default_factory)
    en vez de un valor por defecto directo: un default compartido haría que
    todos los EstadoRobot apunten a la misma instancia y mezclen sus datos.
    """

    modo:                   Modo  = Modo.AUTOMATICO                                # Ojos y IconoGamepad
    bateria:                float = 1.0                                            # SolCarga
    cargando:               bool  = False                                          # SolCarga
    tiempo_restante_min:    int   = 0                                              # SolCarga
    consumo_watts:          float = 0.0                                            # BarraConsumo
    max_consumo_watts:      float = 15.0                                           # BarraConsumo
    distancia_obstaculo_cm: float | None = None                                    # Radar y Ojos (None = sin lectura)
    conexion_activa:        bool  = False                                          # IconoEstadoConexión
    hay_advertencia:        bool  = False                                          # IconoAdvertencia
    hay_error:              bool  = False                                          # IconoError
    posiciones_servos:      PosicionServos = field(default_factory=PosicionServos) # Gamepad
    logger:                 Logger         = field(default_factory=Logger)         # Logger
    # Para colorear una línea, el render debe usar entrada.nivel.value (texto
    # legible); el Enum crudo no le sirve al widget.


# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.nucleo.estado
if __name__ == '__main__':
    print("Prueba estado.py\n")

    estado = EstadoRobot()

    print(estado.modo)
    print(estado.bateria)

    estado.bateria = 0.42
    estado.modo = Modo.MANUAL
    estado.logger.agregar_linea("SISTEMA", "Prueba manual")

    estado.bateria = 0.10
    estado.logger.agregar_linea("BATERIA", "Batería Baja", NivelLog.ADVERTENCIA)

    print(estado.logger.obtener_lineas())

    ultima_linea = estado.logger.obtener_lineas()[-1]
    print(ultima_linea.nivel)         # NivelLog.ADVERTENCIA
    print(ultima_linea.nivel.value)   # advertencia

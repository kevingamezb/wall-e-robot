# wall-e-robot/app/nucleo/estado.py
# Kevin Gámez - 26/08/2026


from enum import Enum
from dataclasses import dataclass, field
from collections import deque
from time import time


class Modo(Enum): # (Enum)eracion - Clase especial que sirve para crear un conjunto de nombres con valores fijos y constantes
    """
    En qué modo está el robot
    
    Podría ser un string ("automatico"),
    pero un enum evita errores de tipeo silenciosos.
    ['automático' puede ser un error del que se habla (typo)]
    """
    
    AUTOMATICO = 'automatico'
    MANUAL = 'manual'
    
    
class NivelLog(Enum): # (Enum) - Gracias al conjunto de nombres con valores fijos, se puede tener más claridad y orden el el código
    """
    Qué tan grave es una línea de log
    
    Esto es lo que le permite al widget del logger,
    más adelante, colorear cada línea
    """
    
    INFO = 'info'
    ADVERTENCIA = 'advertencia'
    ERROR = 'error'
    
    
@dataclass # Clase diseñada principalmente para almacenar datos y atributos
class EntradaLog:
    """
    Una línea individual del Log
    
    es un paquete con 4 datos: cuándo pasó, 
    de qué parte del sistema vino, 
    qué dice, y qué tan grave es.
    """
    
    timestamp:  float
    origen   :  str
    mensaje  :  str
    nivel    :  NivelLog = NivelLog.INFO
    

class Logger:
    """
    El buffer de 30 líneas + su lógica;
    'El Grupo de WhastApp'
    
    Cuando alguien manda un mensaje,
    no tiene que llamar una por uno a cada
    persona (suscriptor) del grupo para
    avisarles, simplemente lo publica en 
    el grupo, y automáticamente todos los que
    están suscritos al grupo reciben una notificación
    """
    
    def __init__(self, max_lineas: int = 30):
        """
        Constructor del buffer
        
        Se usa una deque (cola de doble extremo) porque
        es una estructura de datos optimizada para agregar
        y eliminar elementos por ambos extremos(al inicio y 
        al final) con una velocidad constante O(1)
        
        dentro de la deque guardamos el buffer (memoria sobre las
        líneas del Logger [temporal]) porque automáticamente elimina
        el primer elemento si está llena y se agrega otro. Precisamente
        como funciona un buffer.
        """
        
        self._buffer = deque(maxlen = max_lineas)                  # Deque de 30 líneas para el buffer
        self._subscriptores = []                                   # Métodos en 'el grupo de WhatsApp'
        
    def agregar_linea(self, origen: str, mensaje: str, 
                            nivel: NivelLog = NivelLog.INFO):
        """
        Método para añadir una nueva línea al buffer
        
        Adicionalmente, avisa a los 'integrantes del grupo
        de WhatsApp' (subscriptores) de cualquier cambio de línea  
        """
        
        nueva_entrada = EntradaLog(time(), origen, mensaje, nivel) # Estructuramos la nueva entrada
        self._buffer.append(nueva_entrada)                         # Guardamos la nueva entrada en el buffer
        
        for avisar_suscriptor in self._subscriptores:             # Avisamos a todos los suscritos de la
            avisar_suscriptor(nueva_entrada)                      # nueva entrada en el buffer
    
    def agregar_suscriptor(self, suscriptor):
        """
        Método para agregar un suscriptor
        
        está pensado para que el suscriptor cree
        un método donde se le pueda llamar (hacer
        callback)
        
        así sería más ordenado y legible el código
        """
        
        self._subscriptores.append(suscriptor)                    # Agregamos el 'callback' a self._suscriptores
        
    def obtener_lineas(self) -> list[EntradaLog]:
        """
        Método para obtener UNA COPIA del buffer
        
        Así cualquiera que lo requiera puede ver
        'El Historial' del 'Grupo de WhatsApp'
        """
        
        return list(self._buffer)                                  # list(self._buffer) retorna una copia del buffer


@dataclass # Diseñanda sin la necesidad de definir un constructor
class PosicionServos:
    """
    Ángulo actual de cada servo
    
    Se separó de RobotState en su propia clase
    porque agrupa un concepto cohesivo (todas
    las posiciones de servos) que se puede razonar
    como una unidad. Por ejemplo, el botón de "reposo"
    del gamepad puede resetear un PosicionServos completo
    a ceros de una sola vez, en vez de tener que tocar 7
    campos sueltos dispersos en RobotState.
    """
    
    cuello          : float = 0.0
    hombro_izquierdo: float = 0.0
    hombro_derecho  : float = 0.0
    pulgar_izquierdo: float = 0.0
    pulgar_derecho  : float = 0.0
    radar_us        : float = 0.0
   #ojo_izquierdo   : float = 0.0 # - Aún no se ha decidido
   #ojo_derecho     : float = 0.0 # - Aún no se ha decidido
    

@dataclass # En este caso se puede usar como la 'caja de datos maestra'
class EstadoRobot:
    """
    La caja de datos principal, agrupa todo lo anterior
    
    Cada campo de RobotState responde a la pregunta
    '¿qué necesita saber algún widget para dibujarse?'
    
    Ninguno de los lectores modifica RobotState directamente
    solo lo leen para decidir qué mostrar. La única excepción
    real es el flujo GUI → Robot (comandos del gamepad)
    
    Para objetos complejos y mutables (como PosicionServos y Logger), 
    no podemos asignar un valor por defecto directo (ej. logger = Logger()). 
    Si lo hiciéramos, se crearía un solo objeto que se compartiría 
    entre TODOS los robots que instanciemos (todos clonarían el mismo 'Grupo 
    de WhatsApp' y se mezclarían sus mensajes).
    
    Usar field(default_factory=Clase) le da 'la receta'. Así, cada 
    vez que creamos un nuevo EstadoRobot(), se 'cocina' una instancia 
    completamente limpia, nueva e independiente de sus servos y de su logger.
    """
    
    modo:                   Modo  = Modo.AUTOMATICO                                # Ojos y IconoGamepad
    bateria:                float = 1.0                                            # SolCarga
    cargando:               bool  = False                                          # SolCarga
    tiempo_restante_min:    int   = 0                                              # SolCarga
    consumo_watts:          float = 0.0                                            # BarraConsumo
    max_consumo_watts:      float = 15.0                                           # BarraConsumo
    distancia_obstaculo_cm: float | None = None # Puede ser float o None           # Radar y Ojos
    conexion_activa:        bool  = False                                          # IconoEstadoConexión
    hay_advertencia:        bool  = False                                          # IconoAdvertencia
    hay_error:              bool  = False                                          # IconoError
    posiciones_servos:      PosicionServos = field(default_factory=PosicionServos) # Gamepad
    logger:                 Logger         = field(default_factory=Logger)         # Logger
    # Actualmente si le pasaramos el Log 'crudo' (estado.logger.obtener_lineas()) a cualquier Widget
    # Este no sabría cómo interpretarlo porque le mandaríamos datos sin parsear, un ejemplo con nivel:
    # print(estado.logger.obtener_lineas()) -> ...nivel=<NivelLog.ADVERTENCIA: 'advertencia'>
    # Esto es perfecto para depurar, pero no para un Widget
    # Cuando se construya el render con Tkinter, para acceder al valor legible del nivel
    # de una entrada se debe usar: entrada.nivel.value (donde "entrada" es un EntradaLog
    # obtenido de estado.logger.obtener_lineas())


# Cajón de pruebas para este archivo
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
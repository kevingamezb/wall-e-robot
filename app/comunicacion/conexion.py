# wall-e-robot/app/comunicacion/conexion.py
# Kevin Gámez - 26/08/2026


from abc import ABC, abstractmethod 
from ..nucleo.estado import EstadoRobot, NivelLog, Modo

import socket # Socket es una librería para Networking de bajo nivel, perfecto para nuestro caso y elección de medio de Comunicación
import json   # Json es un modulo built-in para la conversión de diccionarios a JSON (serialización) y visce-versa (deserialización)

import time   # Librería estandar de Python para trabajar con tiempo y fechas
import random # Estándar de Python para generar números aleatorios, útil para simular datos de sensores en la clase ComunicacionSimulada


class Conexion(ABC):
    """
    Definimos una clase abstracta para la comunicación con el robot.
    Esta clase define los métodos que cualquier clase de comunicación
    debe implementar para interactuar con el robot.
    """
    
    @abstractmethod
    def actualizar_estado(self, estado: EstadoRobot):
        """
        Método abstracto para actualizar el estado del robot.
        Debe ser implementado por cualquier subclase concreta.
        """
        pass
    
    @abstractmethod
    def enviar_mensaje(self, comando: dict):
        """
        Método abstracto para enviar un mensaje al robot.
        Debe ser implementado por cualquier subclase concreta.
        """
        pass


class Comunicacion(Conexion):
    """
    Definimos 'Nuestro Protocolo' de comunicación con el Robot (ESP32).
    Nuestra 'Llamada Telefónica' con sus reglas y métodos.
    
    En términos simples buscamos conectarnos por medio de WiFi al robot
    y comunicarnos con un lenguaje común: JSON, serializando y deserializando
    los datos enviados y recibidos respectivamente.
    
    Nuestros mensajes comunes van a tener una estructura común fácil de entender:
    {"tipo": "log", "origen": "RADAR", "mensaje": "Obstáculo a 8cm", "nivel": "advertencia"} (ESP -> PC)
    {"tipo": "servo", "servo": "cuello", "angulo": 30}                                       (PC -> ESP)
    
    Sobre el buffer entrante [self._mensaje_entrante]: los mensaje entrantes pueden
    llegar "partidos" por la red (medio JSON en una lectura, el resto en la siguiente).
    Por eso se acumula todo en un buffer entrante para despues procesarlo correctamente
    cuando hay un salto de línea \n. Así no se intenta deserializar un JSON incompleto.
    """
    
    def __init__(self, ip: str, puerto: int = 8080):    # Aún no se ha decidido cómo conocer la ip del ESP32 de manera automática.
        """
        Se va a definir un socket (Conexión) AF_INET
        y SOCK_STREAM.
        
        Si tomaramos esta clase como 'una llamada telefónica'
        AF_INET     sería nuestro número a llamar, y
        SOCK_STREAM sería nuestro tipo de llamada
        """
        
        self.conexion = socket.socket(socket.AF_INET,     # Definimos 'con quién nos comunicamos' (Dirección ip + puerto)
                                    socket.SOCK_STREAM)   # Definimos 'cómo nos comunicamos'          (Protocolo TCP)
        self.conexion.connect((ip, puerto))               # Pasamos una tupla (ip, puerto) al socket para conectarnos con el ESP32.
        self.conexion.setblocking(False)                  # No Bloqueante ...
        # Si el programa fuese bloqueante [self.socket.setblocking(True)], recv() congelaría el programa en espera de datos.
        # Con [self.socket.setblocking(False)], recv() no detiene el programa esperando datos
        # Lanza BlockingIOError de inmediato si no hay datos recibidos, que se captura e ignora
        self._mensaje_entrante = ''
        
        
    def actualizar_estado(self, estado: EstadoRobot):
        """
        Definimos el proceso de captura de datos y
        de notificicación a la 'caja maestra' (EstadoRobot)
        """
        
        try:
            datos_crudos = self.conexion.recv(4096).decode() # Escuchamos (max) 4096 bytes de datos de el servidor (ESP32)
            self._mensaje_entrante += datos_crudos         # Añadimos los datos capturados a nuestra caja [self._mensaje_entrante]
        
        except BlockingIOError:
            pass # Simplemente no hay datos nuevos que capturar, normal en modo no bloqueante.
        
        while '\n' in self._mensaje_entrante:              # Cuando haya un salto de línea (fin mensaje) en el mensaje entrante...
            linea, self._mensaje_entrante = self._mensaje_entrante.split('\n', 1)
            # Lo que hacemos aquí es simplemente dividir los mensaje entrantes si están incompletos.
            # linea                  -> Captura el mensaje completo y legible [.split('\n')]
            # self._mensaje_entrante -> Devuelve el 'pedazo' incompleto al buffer entrante en espera de más datos para completar el mensaje [.split(1)]
            if not linea.strip():                          # Se eliminan los espacios ' ' luego se evalúa si existe la línea.
                # Esto es una capa de protección para no deserializar
                # Un JSON vacío, que lanzaría JSONDecoderError
                continue
            
            mensaje = json.loads(linea)                    # Deserializamos el mensaje entrante
            
            if mensaje["tipo"] == "estado":
                # Actualizamos el EstadoRobot con los datos JSON deserializados que el servidor (ESP32) nos manda
                estado.bateria                = mensaje["bateria"]
                estado.modo                   = Modo(mensaje["modo"])                 # El JSON trae un string ('automatico'/'manual');
                                                                                       # lo convertimos al enum Modo para respetar el contrato
                                                                                       # de EstadoRobot (igual que ComunicacionSimulada).
                estado.distancia_obstaculo_cm = mensaje["distancia_cm"]
                estado.consumo_watts          = mensaje["consumo_watts"]
                estado.conexion_activa        = mensaje["conexion_activa"]
                
            elif mensaje["tipo"] == "log":
                # Agregamos una línea nueva al Logger de EstadoRobot
                estado.logger.agregar_linea(
                    mensaje["origen"], mensaje["mensaje"], NivelLog(mensaje["nivel"])
                )
                
    
    def enviar_mensaje(self, comando: dict):
        """
        Enviamos un JSON codificado a bytes para que
        el servidor (ESP32) por medio de Wifi
        """
        
        mensaje = json.dumps(comando) + '\n'
        self.conexion.send(mensaje.encode())
        
        
class ComunicacionSimulada(Conexion):
    """
    Definimos una clase de comunicación simulada para pruebas locales,
    sin necesidad de que exista un ESP32 real conectado.

    A diferencia de Comunicacion (la real), esta clase NO simula el
    "cable de red" completo (serializar a JSON, meterlo a un buffer,
    volver a deserializarlo). Eso sería reinventar un paso innecesario:
    como esta clase ya vive del lado de Python, puede escribir
    directamente en EstadoRobot, que es justo el propósito de que
    EstadoRobot sea una "caja compartida" en vez de algo atado a la red.
    """

    def __init__(self):
        """
        Variables internas que guardan el estado simulado entre
        llamadas, para que los valores cambien de forma progresiva
        y creíble en vez de saltar aleatoriamente cada vez.
        """

        self._bateria_simulada = 1.0     # fracción 0.0-1.0, igual que en EstadoRobot
        self._distancia_simulada = 45.0  # cm
        self._modo_simulado = "automatico"
        self._ultimo_log_tiempo = time.time()

    def actualizar_estado(self, estado: EstadoRobot):
        """
        Calcula valores simulados que cambian con el tiempo,
        y los escribe directamente en la caja maestra (EstadoRobot).

        No hay serialización ni deserialización aquí: eso solo
        tiene sentido cuando el dato realmente viajó por una red,
        que no es el caso de esta clase.
        """

        # Descarga lenta de batería, con piso en 0
        self._bateria_simulada = max(0.0, self._bateria_simulada - 0.001)

        # Variación aleatoria de distancia, dentro de un rango razonable
        variacion_distancia = random.uniform(-2.5, 2.5)
        self._distancia_simulada = max(5.0, min(200.0, self._distancia_simulada + variacion_distancia))

        estado.bateria = round(self._bateria_simulada, 3)
        estado.modo = Modo(self._modo_simulado)
        estado.distancia_obstaculo_cm = round(self._distancia_simulada, 1)
        estado.consumo_watts = round(random.uniform(1.2, 4.8), 2)
        estado.conexion_activa = True

        # Log de prueba cada 10 segundos, para probar el widget del Logger
        if time.time() - self._ultimo_log_tiempo > 10.0:
            estado.logger.agregar_linea(
                "SIMULADOR",
                f"Lectura de prueba. Radar detecta objeto a {round(self._distancia_simulada)}cm",
                NivelLog.INFO
            )
            self._ultimo_log_tiempo = time.time()

    def enviar_mensaje(self, comando: dict):
        """
        Simula el envío de un comando al robot.

        No hay robot real que lo reciba, así que por ahora solo
        se imprime en consola para poder verificar, durante pruebas,
        que la GUI está mandando exactamente el comando esperado.
        """

        print(f"[COMUNICACIÓN SIMULADA] Comando enviado -> {comando}")

        if comando.get("tipo") == "modo":
            self._modo_simulado = comando.get("modo", self._modo_simulado)


# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.comunicacion.conexion
if __name__ == "__main__":
    print("Prueba conexion.py\n")

    # ComunicacionSimulada
    print("ComunicacionSimulada")
    estado = EstadoRobot()
    simulada = ComunicacionSimulada()

    # Después de un solo ciclo, la batería baja un poco y la
    # distancia/consumo toman valores aleatorios razonables.
    simulada.actualizar_estado(estado)

    print(f"bateria            = {estado.bateria}")
    print(f"modo               = {estado.modo}")
    print(f"distancia_obstaculo= {estado.distancia_obstaculo_cm} cm")
    print(f"consumo_watts      = {estado.consumo_watts} W")
    print(f"conexion_activa    = {estado.conexion_activa}")

    # Enviar un comando "modo" debe cambiar el modo simulado interno
    print("\nEnviando comando modo -> 'manual'")
    simulada.enviar_mensaje({"tipo": "modo", "modo": "manual"})
    simulada.actualizar_estado(estado)
    print(f"modo actualizado    = {estado.modo}")

    # ComunicacionSimulada con logger
    # El radar debe loguear cada 10s. Para no esperar 10s reales,
    # solo verificamos que el búfer del logger arranca vacío.
    print("\nLogger (buffer simulado)")
    print(f"lineas de log       = {len(estado.logger.obtener_lineas())}")

    print("\nPruebas OK")
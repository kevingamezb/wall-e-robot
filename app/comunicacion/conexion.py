# wall-e-robot/app/comunicacion/conexion.py - Kevin Gámez
# 24/08/2026 - Fecha de Creación


from app.nucleo.estado import EstadoRobot, NivelLog

import socket # Socket es una librería para Networking de bajo nivel, perfecto para nuestro caso y elección de medio de Comunicación
import json   # Json es un modulo built-in para la conversión de diccionarios a JSON (serialización) y visce-versa (deserialización)


class Comunicacion:
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
                                    socket.SOCK_STREAM) # Definimos 'cómo nos comunicamos'          (Protocolo TCP)
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
                estado.modo                   = mensaje["modo"]
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
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
    {"tipo": "motor", "direccion": "arriba"}                                                 (PC -> ESP)
    {"tipo": "multi", "comandos": [{"tipo":"servo",...}, {"tipo":"motor",...}]}              (PC -> ESP)
    
    El estado ampliado que manda el ESP32 trae más campos que los de la versión
    v1:
    {"tipo":"estado","bateria":0.85,"modo":"manual",
     "hay_advertencia":false,"hay_error":false,
     "distancia_cm":30.5,"consumo_watts":3.2,"conexion_activa":true,
     "cargando":false,"tiempo_restante_min":42,
     "posiciones_servos":{"cuello":0,"hombro_izquierdo":10,...}}
    
    "distancia_cm" y "tiempo_restante_min" pueden valer null (sin lectura de
    radar / sin estimación de batería). El parseo (_procesar_mensaje) es
    TOLERANTE: si un campo no viene (o viene como null), no se toca lo que
    EstadoRobot ya sabía. Así el firmware viejo y el nuevo conviven con la
    misma app.
    
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
            self._procesar_mensaje(mensaje, estado)        # Interpretarlo + escribirlo en la caja maestra
    
    def _procesar_mensaje(self, mensaje: dict, estado: EstadoRobot):
        """
        Interpreta UN mensaje JSON ya deserializado y lo escribe en EstadoRobot.
        
        Separado de actualizar_estado() para poder probarlo (cajón de pruebas)
        sin levantar un socket: el protocolo se prueba con diccionarios puros,
        igual que haría el ESP32 en la red real.
        """
        
        if not isinstance(mensaje, dict) or "tipo" not in mensaje:
            return   # basura (o versión vieja): ignorar sin romper nada
        
        tipo = mensaje["tipo"]
        
        if tipo == "estado":
            self._aplicar_estado(mensaje, estado)
        
        elif tipo == "log":
            # Agregamos una línea nueva al Logger de EstadoRobot
            estado.logger.agregar_linea(
                mensaje.get("origen", "DESCONOCIDO"),
                mensaje.get("mensaje", ""),
                NivelLog(mensaje.get("nivel", "info")),
            )
    
    def _aplicar_estado(self, mensaje: dict, estado: EstadoRobot):
        """
        Actualiza EstadoRobot a partir de un estado del ESP32, campo por campo
        y TOLERANTE:
        
        - Si el campo no viene en el JSON -> no se toca lo que ya sabía.
        - Si el campo es null (distancia_cm, tiempo_restante_min) -> tampoco.
        - Los strings de modo/nivel inválidos -> se ignoran (ValueError).
        - "posiciones_servos" es un objeto con los nombres de los servos.
        
        Así un ESP32 con firmware viejo (menos campos) y uno nuevo conviven
        con la misma app sin saltos.
        """
        
        if isinstance(mensaje.get("bateria"), (int, float)):
            estado.bateria = float(mensaje.get("bateria"))
        
        if isinstance(mensaje.get("modo"), str):
            try:
                estado.modo = Modo(mensaje["modo"])
            except ValueError:
                pass   # modo desconocido: quedarse con el anterior
        
        if (mensaje.get("distancia_cm") is not None
                and isinstance(mensaje.get("distancia_cm"), (int, float))):
            estado.distancia_obstaculo_cm = float(mensaje["distancia_cm"])
        
        if isinstance(mensaje.get("consumo_watts"), (int, float)):
            estado.consumo_watts = float(mensaje["consumo_watts"])
        
        if isinstance(mensaje.get("conexion_activa"), bool):
            estado.conexion_activa = bool(mensaje["conexion_activa"])
        
        if isinstance(mensaje.get("hay_advertencia"), bool):
            estado.hay_advertencia = bool(mensaje["hay_advertencia"])
        
        if isinstance(mensaje.get("hay_error"), bool):
            estado.hay_error = bool(mensaje["hay_error"])
        
        if isinstance(mensaje.get("cargando"), bool):
            estado.cargando = bool(mensaje["cargando"])
        
        if (mensaje.get("tiempo_restante_min") is not None
                and isinstance(mensaje.get("tiempo_restante_min"), (int, float))):
            estado.tiempo_restante_min = int(mensaje["tiempo_restante_min"])
        
        posiciones = mensaje.get("posiciones_servos")
        if isinstance(posiciones, dict):
            for nombre, valor in posiciones.items():
                if (hasattr(estado.posiciones_servos, nombre)
                        and isinstance(valor, (int, float))):
                    setattr(estado.posiciones_servos, nombre, float(valor))
                
    
    def enviar_mensaje(self, comando: dict):
        """
        Enviamos un JSON codificado a bytes para que
        el servidor (ESP32) por medio de Wifi
        """
        
        mensaje = json.dumps(comando) + '\n'
        self.conexion.send(mensaje.encode())
        
        
    def cerrar(self):
        """
        Cuelga el teléfono: cierra el socket con el ESP32.
        
        Idempotente y a prueba de golpes: si el socket ya estaba cerrado
        (o nunca llegó a abrirse del todo), no debe lanzar nada.
        """
        
        try:
            self.conexion.close()
        except OSError:
            pass
        
        
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
        # Cooldowns del logger: solo se avisa al TRANSICIONAR (encendido de
        # una alerta), no en cada ciclo de 60ms mientras la alerta persiste.
        self._aviso_advertencia_log = False
        self._aviso_error_log = False

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

        # Alertas simuladas, para poder probar los íconos de sistema y los ojos:
        #   - Advertencia: obstáculo cerca (< 15cm) o batería baja (< 0.25).
        #   - Error: batería al borde del agotamiento (raro, como en la vida real).
        estado.hay_advertencia = (self._distancia_simulada < 15.0
                                  or self._bateria_simulada < 0.25)
        estado.hay_error = self._bateria_simulada < 0.10

        # Logs que hacen funcionar el sistema de colores del Logger
        # (advertencia = naranja, error = rojo). Con cooldown para no
        # repetir la misma línea mientras la alerta siga activa.
        if estado.hay_advertencia and not self._aviso_advertencia_log:
            estado.logger.agregar_linea(
                "RADAR",
                f"Obstáculo muy cerca: {round(self._distancia_simulada)}cm",
                NivelLog.ADVERTENCIA,
            )
            self._aviso_advertencia_log = True
        elif not estado.hay_advertencia:
            self._aviso_advertencia_log = False

        if estado.hay_error and not self._aviso_error_log:
            estado.logger.agregar_linea(
                "BATERIA",
                "Nivel crítico de batería",
                NivelLog.ERROR,
            )
            self._aviso_error_log = True
        elif not estado.hay_error:
            self._aviso_error_log = False

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


class ConexionOffline(Conexion):
    """
    Representamos el estado "sin robot": sin conexión ni simulador.

    Es un apagado elegante del panel de control: cuando el usuario presiona
    Desconectar (o nunca conectó), se usa esta clase. No produce datos
    (no hay quién los genere) y descarta cualquier comando.
    """

    def actualizar_estado(self, estado: EstadoRobot):
        """No hay robot que leer: solo dejamos claro que no hay conexión."""
        estado.conexion_activa = False

    def enviar_mensaje(self, comando: dict):
        """Sin robot, no hay a quién mandarle el comando: se descarta."""


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

    # Los colores del Logger (naranja/rojo) se prueban así: forzando las
    # condiciones de alerta y comprobando que se loguea UNA vez (cooldown).
    print("\nLogger con colores (advertencia/error)")
    simulada._distancia_simulada = 8.0   # obstáculo muy cerca -> advertencia
    simulada.actualizar_estado(estado)
    lineas_warn = [l for l in estado.logger.obtener_lineas()
                   if l.nivel == NivelLog.ADVERTENCIA]
    assert len(lineas_warn) == 1, f"Debe haber 1 advertencia, hay {len(lineas_warn)}"
    print(f"OK: advertencia -> {lineas_warn[0].origen}: {lineas_warn[0].mensaje}")

    simulada.actualizar_estado(estado)   # la alerta sigue: NO debe repetirse
    lineas_warn = [l for l in estado.logger.obtener_lineas()
                   if l.nivel == NivelLog.ADVERTENCIA]
    assert len(lineas_warn) == 1, "Una alerta activa no debe repetirse en cada ciclo"
    print("OK: cooldown de la advertencia (no se repite)")

    simulada._distancia_simulada = 50.0  # sale de la alerta: se resetea
    simulada.actualizar_estado(estado)
    simulada._bateria_simulada = 0.05    # batería crítica -> error
    simulada.actualizar_estado(estado)
    lineas_err = [l for l in estado.logger.obtener_lineas()
                  if l.nivel == NivelLog.ERROR]
    assert len(lineas_err) == 1, f"Debe haber 1 error, hay {len(lineas_err)}"
    print(f"OK: error -> {lineas_err[0].origen}: {lineas_err[0].mensaje}")

    # ConexionOffline: no produce datos y descarta comandos
    print("\nConexionOffline")
    offline = ConexionOffline()
    offline.actualizar_estado(estado)
    assert estado.conexion_activa is False, "Offline debe apagar conexion_activa"
    offline.enviar_mensaje({"tipo": "motor", "direccion": "arriba"})  # no lanza
    print("OK: conexion_activa=False y los comandos se descartan")

    # Parseo del protocolo real (sin abrir sockets: se instancia la clase
    # con __new__ y se alimenta _procesar_mensaje con diccionarios puros).
    print("\nParseo tolerante del estado ampliado (protocolo real)")
    estado_proto = EstadoRobot()
    proto = Comunicacion.__new__(Comunicacion)

    # Como el ESP32 lo mandaría (firmware ampliado)
    proto._procesar_mensaje({
        "tipo": "estado",
        "bateria": 0.83,
        "modo": "manual",
        "hay_advertencia": True,
        "hay_error": False,
        "distancia_cm": 12.3,
        "consumo_watts": 3.4,
        "conexion_activa": True,
        "cargando": False,
        "tiempo_restante_min": 42,
        "posiciones_servos": {
            "cuello": 30,
            "hombro_izquierdo": -18,
            "hombro_derecho": 0,
            "pulgar_izquierdo": 5,
            "pulgar_derecho": -5,
        },
    }, estado_proto)

    assert estado_proto.bateria == 0.83
    assert estado_proto.modo == Modo.MANUAL
    assert estado_proto.hay_advertencia is True
    assert estado_proto.hay_error is False
    assert estado_proto.distancia_obstaculo_cm == 12.3
    assert estado_proto.consumo_watts == 3.4
    assert estado_proto.conexion_activa is True
    assert estado_proto.cargando is False
    assert estado_proto.tiempo_restante_min == 42
    assert estado_proto.posiciones_servos.cuello == 30.0
    assert estado_proto.posiciones_servos.hombro_izquierdo == -18.0
    assert estado_proto.posiciones_servos.pulgar_derecho == -5.0
    print("OK: todos los campos del estado ampliado se aplicaron")

    # Un estado con campos null/ausentes NO debe machacar lo anterior
    proto._procesar_mensaje({
        "tipo": "estado",
        "distancia_cm": None,        # radar sin lectura
        "tiempo_restante_min": None, # sin estimación
        "cargando": True,
    }, estado_proto)

    assert estado_proto.distancia_obstaculo_cm == 12.3   # se mantiene
    assert estado_proto.tiempo_restante_min == 42         # se mantiene
    assert estado_proto.cargando is True                  # este sí cambió
    print("OK: null/ausencia no pisan valores previos")

    # Modo desconocido: se ignora, no se rompe
    proto._procesar_mensaje({"tipo": "estado", "modo": "turbo"}, estado_proto)
    assert estado_proto.modo == Modo.MANUAL
    print("OK: modo desconocido se ignora")

    # Mensaje sin tipo / basura: se ignora sin lanzar
    proto._procesar_mensaje({"hola": "mundo"}, estado_proto)
    proto._procesar_mensaje(["no soy", "dict"], estado_proto)
    print("OK: mensajes sin 'tipo' se descartan")

    # Log llegado por la red
    proto._procesar_mensaje({
        "tipo": "log",
        "origen": "RADAR",
        "mensaje": "Obstáculo a 8cm",
        "nivel": "advertencia",
    }, estado_proto)
    ultimas = estado_proto.logger.obtener_lineas()
    assert ultimas[-1].nivel == NivelLog.ADVERTENCIA
    assert ultimas[-1].origen == "RADAR"
    print("OK: log de red se integra al logger")

    # Comunicacion.cerrar() existe (socket real se cierra idempotente)
    assert callable(getattr(Comunicacion, "cerrar", None)), "Comunicacion debe tener cerrar()"
    print("OK: Comunicacion.cerrar() existe")

    print("\nPruebas OK")
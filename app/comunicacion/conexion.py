# wall-e-robot/app/comunicacion/conexion.py
# Kevin Gámez - 26/08/2026


from abc import ABC, abstractmethod
from ..nucleo.estado import EstadoRobot, NivelLog, Modo
import socket
import json
import time
import random
from typing import cast


class Conexion(ABC):
    """Interfaz de conexión con el robot (real, simulada u offline)."""

    @abstractmethod
    def actualizar_estado(self, estado: EstadoRobot):
        """Lee al robot y escribe en la caja compartida."""
        pass

    @abstractmethod
    def enviar_mensaje(self, comando: dict):
        """Envía un comando al robot."""
        pass


class Comunicacion(Conexion):
    """
    Conexión real con el ESP32 por WiFi (TCP + JSON).

    El ESP32 es el servidor; aquí se abre el socket cliente. Cada mensaje es
    un JSON terminado en '\\n'.

    App -> ESP32:  {"tipo":"servo","servo":"cuello","angulo":30},
                   {"tipo":"modo","modo":"manual"},
                   {"tipo":"motor","direccion":"arriba"},
                   {"tipo":"multi","comandos":[{...},{...}]}
    ESP32 -> App:  {"tipo":"estado",...} y
                   {"tipo":"log","origen":"RADAR","mensaje":"...","nivel":"..."}

    El parseo del estado es TOLERANTE: un campo ausente o null no pisa lo que
    EstadoRobot ya sabía. Así un firmware viejo (menos campos) y uno nuevo
    conviven con la misma app.

    Sobre self._mensaje_entrante: TCP puede entregar un mensaje "partido" en
    varias lecturas, así que se acumula en un buffer hasta encontrar el '\\n'
    final y recién ahí se deserializa. Evita intentar parsear un JSON incompleto.
    """

    def __init__(self, ip: str, puerto: int = 8080):  # TODO: descubrir la IP del ESP32 automáticamente.
        """
        Abre un socket AF_INET + SOCK_STREAM y se conecta a (ip, puerto).
        """

        self.conexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conexion.connect((ip, puerto))
        # No bloqueante: recv() lanza BlockingIOError de inmediato si no hay
        # datos, en vez de congelar la GUI esperándolos.
        self.conexion.setblocking(False)
        self._mensaje_entrante = ''
        self._perdida = False    # True si la conexión se rompió en el aire

    @property
    def perdida(self) -> bool:
        """
        True si la conexión se interrumpió (el ESP32 se reinició o se apagó).
        main.py lo consulta cada ciclo para degradar a "sin conexión" en vez de
        seguir mandando a un socket muerto.
        """
        # getattr: algunos tests construyen la clase con __new__ (sin __init__).
        return getattr(self, "_perdida", False)

    def actualizar_estado(self, estado: EstadoRobot):
        """Recibe lo pendiente del socket y lo aplica a EstadoRobot."""

        try:
            datos_crudos = self.conexion.recv(4096).decode()
            self._mensaje_entrante += datos_crudos

        except BlockingIOError:
            pass  # no hay datos nuevos: normal en modo no bloqueante

        except OSError:
            # El ESP32 se reinició/apagó o se cortó la conexión: se marca la
            # pérdida para que main.py degrade la GUI y no se siga leyendo de
            # un socket muerto.
            self._perdida = True
            return

        # Procesa cada mensaje completo (delimitado por '\n') que haya en el buffer.
        while '\n' in self._mensaje_entrante:
            linea, self._mensaje_entrante = self._mensaje_entrante.split('\n', 1)

            if not linea.strip():
                continue  # línea vacía: no hay JSON que deserializar

            try:
                mensaje = json.loads(linea)
            except json.JSONDecodeError:
                continue   # línea corrupta (JSON roto): se descarta y sigue

            self._procesar_mensaje(mensaje, estado)

    def _procesar_mensaje(self, mensaje, estado: EstadoRobot):
        """
        Interpreta UN mensaje JSON ya deserializado y lo escribe en EstadoRobot.

        Separado de actualizar_estado() para poder probarlo con diccionarios
        puros (cajón de pruebas) sin abrir un socket.
        """

        if not isinstance(mensaje, dict) or "tipo" not in mensaje:
            return   # basura o versión vieja: ignorar sin romper nada

        tipo = mensaje["tipo"]

        if tipo == "estado":
            self._aplicar_estado(mensaje, estado)

        elif tipo == "log":
            # Un nivel desconocido o ausente no debe tumbar la app: se degrada
            # a INFO y la línea igual entra al logger.
            try:
                nivel = NivelLog(mensaje.get("nivel", "info"))
            except ValueError:
                nivel = NivelLog.INFO

            estado.logger.agregar_linea(
                mensaje.get("origen", "DESCONOCIDO"),
                mensaje.get("mensaje", ""),
                nivel,
            )

    def _aplicar_estado(self, mensaje: dict, estado: EstadoRobot):
        """
        Aplica un estado del ESP32 campo por campo, de forma TOLERANTE:
        - campo ausente -> no se toca lo que ya sabía
        - campo null (distancia_cm, tiempo_restante_min) -> tampoco
        - modo/nivel inválido -> se ignora (ValueError)
        - posiciones_servos -> objeto con los nombres de los servos

        Así un firmware viejo y uno nuevo conviven con la misma app.
        """

        bateria = mensaje.get("bateria")
        if isinstance(bateria, (int, float)):
            estado.bateria = float(bateria)

        if isinstance(mensaje.get("modo"), str):
            try:
                estado.modo = Modo(mensaje["modo"])
            except ValueError:
                pass   # modo desconocido: se conserva el anterior

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
        """Serializa el comando a JSON + '\\n' y lo envía por el socket."""

        mensaje = json.dumps(comando) + '\n'
        try:
            self.conexion.send(mensaje.encode())
        except OSError:
            # Socket muerto (robot apagado/reiniciado): se marca la pérdida
            # para que main.py degrade la GUI, sin colgar la app.
            self._perdida = True

    def cerrar(self):
        """
        Cierra el socket con el ESP32.

        Idempotente: si ya estaba cerrado (o nunca se abrió del todo), no
        lanza nada.
        """

        try:
            self.conexion.close()
        except OSError:
            pass


class ComunicacionSimulada(Conexion): # Para pruebas sin un ESP32 real. 
    """
    Comunicación simulada para probar la app sin un ESP32 real.

    No simula el "cable" completo (serializar/deserializar JSON): como ya vive
    en Python, escribe directo en EstadoRobot, que es justo el motivo de que
    EstadoRobot sea una caja compartida en vez de algo atado a la red.
    """

    def __init__(self):
        """
        Guarda el estado simulado entre llamadas para que los valores cambien
        de forma progresiva y creíble, no saltando al azar en cada ciclo.
        """

        self._bateria_simulada = 1.0     # fracción 0.0-1.0, igual que en EstadoRobot
        self._distancia_simulada = 45.0  # cm
        self._modo_simulado = "automatico"
        self._ultimo_log_tiempo = time.time()
        # Cooldowns del logger: solo se avisa al ENTRAR en la alerta, no en
        # cada ciclo de 60 ms mientras la alerta persiste.
        self._aviso_advertencia_log = False
        self._aviso_error_log = False

    def actualizar_estado(self, estado: EstadoRobot):
        """
        Calcula valores simulados que evolucionan con el tiempo y los escribe
        directo en EstadoRobot (sin serialización, que no aplica aquí).
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

        # Alertas simuladas para probar los íconos de sistema y los ojos:
        #   advertencia: obstáculo cerca (< 15 cm) o batería baja (< 0.25)
        #   error:       batería al borde del agotamiento (raro, como en la vida real)
        estado.hay_advertencia = (self._distancia_simulada < 15.0
                                  or self._bateria_simulada < 0.25)
        estado.hay_error = self._bateria_simulada < 0.10

        # Logs que alimentan los colores del logger (advertencia = naranja,
        # error = rojo), con cooldown para no repetir la misma línea mientras
        # la alerta sigue activa.
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

        # Log de prueba cada 10 s, para ejercitar el widget del logger.
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

        Sin robot real, solo se aplica el efecto local (por ahora, cambiar el
        modo). Soporta "multi" recorriendo sus sub-comandos, igual que el
        firmware.
        """
        print(f"[COMUNICACIÓN SIMULADA] Comando enviado -> {comando}")

        if comando.get("tipo") == "multi":
            for sub in comando.get("comandos", []):
                if isinstance(sub, dict):
                    self._aplicar_comando_simulado(sub)
            return

        self._aplicar_comando_simulado(comando)

    def _aplicar_comando_simulado(self, comando: dict):
        """Aplica UN comando simple al estado simulado (por ahora, solo 'modo')."""
        if comando.get("tipo") == "modo":
            self._modo_simulado = comando.get("modo", self._modo_simulado)


class ConexionOffline(Conexion):
    """
    Estado "sin robot": ni conexión real ni simulador.

    Apagado elegante del panel (tras Desconectar, o si nunca se conectó): no
    produce datos y descarta cualquier comando.
    """

    def actualizar_estado(self, estado: EstadoRobot):
        """No hay robot que leer: solo se marca que no hay conexión."""
        estado.conexion_activa = False

    def enviar_mensaje(self, comando: dict):
        """Sin robot no hay destino: el comando se descarta."""


# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.comunicacion.conexion
if __name__ == "__main__":
    print("Prueba conexion.py\n")

    # ComunicacionSimulada
    print("ComunicacionSimulada")
    estado = EstadoRobot()
    simulada = ComunicacionSimulada()

    # Tras un ciclo, la batería baja un poco y distancia/consumo toman valores
    # aleatorios razonables.
    simulada.actualizar_estado(estado)

    print(f"bateria            = {estado.bateria}")
    print(f"modo               = {estado.modo}")
    print(f"distancia_obstaculo= {estado.distancia_obstaculo_cm} cm")
    print(f"consumo_watts      = {estado.consumo_watts} W")
    print(f"conexion_activa    = {estado.conexion_activa}")

    # Un comando "modo" debe cambiar el modo simulado interno
    print("\nEnviando comando modo -> 'manual'")
    simulada.enviar_mensaje({"tipo": "modo", "modo": "manual"})
    simulada.actualizar_estado(estado)
    print(f"modo actualizado    = {estado.modo}")

    # "multi" debe recorrer sus sub-comandos (igual que el firmware)
    print("\nEnviando comando multi -> [modo automatico, modo manual]")
    simulada.enviar_mensaje({
        "tipo": "multi",
        "comandos": [
            {"tipo": "modo", "modo": "automatico"},
            {"tipo": "modo", "modo": "manual"},
        ],
    })
    simulada.actualizar_estado(estado)
    assert estado.modo == Modo.MANUAL, \
        "El último sub-comando del multi debe quedar aplicado (manual)"
    print(f"OK: modo tras el multi = {estado.modo}")

    # El logger arranca vacío (el log de 10 s no se espera en la prueba)
    print("\nLogger (buffer simulado)")
    print(f"lineas de log       = {len(estado.logger.obtener_lineas())}")

    # Colores del logger: se fuerzan las alertas y se comprueba que se loguea
    # UNA sola vez (cooldown).
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

    # Parseo del protocolo real sin abrir sockets: se instancia con __new__ y
    # se alimenta _procesar_mensaje con diccionarios puros.
    print("\nParseo tolerante del estado ampliado (protocolo real)")
    estado_proto = EstadoRobot()
    proto = Comunicacion.__new__(Comunicacion)

    # Tal como lo mandaría el ESP32 (firmware ampliado)
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
    # assert estado_proto.posiciones_servos.pulgar_derecho == -5.0
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

    # Robustez de red sin sockets reales: se inyecta un socket falso
    print("\nRobustez de red (socket falso)")

    # 1) Un JSON roto en el medio NO debe tumbar ni machacar lo bueno.
    class _SocketBasura:
        """Entrega una línea válida y luego una línea con JSON corrupto."""
        def recv(self, _n):
            return b'{"tipo":"estado","bateria":0.5}\n{"tipo": roto\n'

    roto = Comunicacion.__new__(Comunicacion)
    roto.conexion = cast(socket.socket, _SocketBasura())
    roto._mensaje_entrante = ""
    estado_red = EstadoRobot(bateria=0.1)
    roto.actualizar_estado(estado_red)   # no debe lanzar
    assert estado_red.bateria == 0.5, "La línea buena sí debe procesarse"
    assert not roto.perdida, "Un JSON roto NO es pérdida de conexión"
    print("OK: JSON corrupto se descarta y la línea buena se aplica")

    # 2) Nivel de log desconocido -> degrada a INFO, no rompe.
    class _SocketBien:
        def recv(self, _n):
            return b'{"tipo":"log","origen":"X","mensaje":"hola","nivel":"turbo"}\n'

    log_ok = Comunicacion.__new__(Comunicacion)
    log_ok.conexion = cast(socket.socket, _SocketBien())
    log_ok._mensaje_entrante = ""
    estado_log = EstadoRobot()
    log_ok.actualizar_estado(estado_log)
    assert estado_log.logger.obtener_lineas()[-1].mensaje == "hola"
    print("OK: nivel desconocido degrada a INFO")

    # 3) Conexión caída (recv lanza) -> perdida=True, sin excepción.
    class _SocketCaido:
        def recv(self, _n):
            raise ConnectionResetError("el robot se reinició")

    caido = Comunicacion.__new__(Comunicacion)
    caido.conexion = cast(socket.socket, _SocketCaido())
    caido._mensaje_entrante = ""
    caido.actualizar_estado(EstadoRobot())   # no debe lanzar
    assert caido.perdida, "recv caído debe marcar perdida=True"
    print("OK: recv caído marca perdida=True sin lanzar")

    # 4) Enviar a un socket muerto marca perdida=True, sin excepción.
    class _SocketSendCaido:
        def send(self, _datos):
            raise OSError("socket cerrado")

    send_caido = Comunicacion.__new__(Comunicacion)
    send_caido.conexion = cast(socket.socket, _SocketSendCaido())
    send_caido.enviar_mensaje({"tipo": "motor", "direccion": "arriba"})
    assert send_caido.perdida, "send caído debe marcar perdida=True"
    print("OK: send caído marca perdida=True sin lanzar")

    print("\nPruebas OK")

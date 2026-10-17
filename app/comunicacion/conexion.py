# wall-e-robot/app/comunicacion/conexion.py
# Kevin Gámez - 26/08/2026
"""
Capa de comunicación con el robot.

Protocolo real (Comunicacion): un socket TCP con el ESP32 transporta un
objeto JSON UTF-8 por línea, delimitado por '\\n'. El robot envía mensajes
con "tipo" "estado" o "log":
  - "estado": campos opcionales; null o ausente = sin dato (no pisa el valor
    anterior); tipos y valores desconocidos se ignoran.
  - "log": campos "origen", "mensaje" y "nivel" (nivel desconocido -> INFO).
La GUI solo envía comandos, p. ej. {"tipo": "modo", "modo": "manual"} o un
{"tipo": "multi", "comandos": [...]} que agrupa varios. Las líneas vacías o
con JSON corrupto se descartan sin cortar la conexión; un fallo de recv o
send marca la conexión como perdida para que la GUI degrade a ConexionOffline.
"""


from abc import ABC, abstractmethod
from ..nucleo.estado import EstadoRobot, NivelLog, Modo, Maniobra, NivelConexion
import socket
import json
import time
import random
from typing import cast


# Umbrales de frescura para el nivel de señal.
SEGUNDOS_SENAL_ALTA  = 0.8
SEGUNDOS_SENAL_MEDIA = 2.0


def nivel_por_frescura(segundos: float | None) -> NivelConexion:
    """
    Traduce la antigüedad del último estado a un nivel de conexión.

    None significa que aún no se recibió ningún estado -> NULA.
    """
    if segundos is None:
        return NivelConexion.NULA
    if segundos < SEGUNDOS_SENAL_ALTA:
        return NivelConexion.ALTA
    if segundos < SEGUNDOS_SENAL_MEDIA:
        return NivelConexion.MEDIA
    return NivelConexion.BAJA


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
    """Conexión real con el ESP32 por WiFi (TCP + JSON)."""
    def __init__(self, ip: str, puerto: int = 8080):
        self.conexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conexion.connect((ip, puerto))
        # No bloqueante: recv() lanza BlockingIOError de inmediato si no hay
        # datos, en vez de congelar la GUI esperándolos.
        self.conexion.setblocking(False)
        self._mensaje_entrante = ''
        self._perdida          = False    # True si la conexión se rompió en el aire
        self._ultima_recepcion = None     # time() del último estado recibido

    @property
    def perdida(self) -> bool:
        """True si la conexión se interrumpió (el ESP32 se reinició o se apagó)."""
        # getattr: algunos tests construyen la clase con __new__.
        return getattr(self, "_perdida", False)

    def actualizar_estado(self, estado: EstadoRobot):
        """Recibe lo pendiente del socket y lo aplica a EstadoRobot."""
        try:
            datos_crudos = self.conexion.recv(4096).decode()
            self._mensaje_entrante += datos_crudos

        except BlockingIOError:
            pass

        except OSError:
            # El ESP32 se reinició/apagó o se cortó la conexión
            self._perdida = True
            estado.nivel_conexion = NivelConexion.NULA
            return

        # Procesa cada mensaje completo (delimitado por '\n') que haya en el buffer.
        while '\n' in self._mensaje_entrante:
            linea, self._mensaje_entrante = self._mensaje_entrante.split('\n', 1)

            if not linea.strip():
                continue  # línea vacía

            try:
                mensaje = json.loads(linea)
            except json.JSONDecodeError:
                continue   # línea corrupta

            self._procesar_mensaje(mensaje, estado)

        # El nivel de señal sale de qué tan fresca es la última lectura.
        segundos = None
        if getattr(self, "_ultima_recepcion", None) is not None:
            segundos = time.time() - self._ultima_recepcion # Ignorar error PyLance
        estado.nivel_conexion = nivel_por_frescura(segundos)

    def _procesar_mensaje(self, mensaje, estado: EstadoRobot):
        """Interpreta UN mensaje JSON ya deserializado y lo escribe en EstadoRobot."""

        if not isinstance(mensaje, dict) or "tipo" not in mensaje:
            return   # basura o versión vieja

        tipo = mensaje["tipo"]

        if tipo == "estado":
            self._ultima_recepcion = time.time()
            self._aplicar_estado(mensaje, estado)

        elif tipo == "log":
            try:
                nivel = NivelLog(mensaje.get("nivel", "info"))
            except ValueError:
                nivel = NivelLog.INFO

            estado.logger.agregar_linea(
                mensaje.get("origen" , "DESCONOCIDO"),
                mensaje.get("mensaje", ""),
                nivel,
            )

    def _aplicar_estado(self, mensaje: dict, estado: EstadoRobot):
        """Aplica un estado del ESP32 campo por campo."""

        bateria = mensaje.get("bateria")
        if isinstance(bateria, (int, float)):
            estado.bateria = float(bateria)

        if isinstance(mensaje.get("modo"), str):
            try:
                estado.modo = Modo(mensaje["modo"])
            except ValueError:
                pass   # modo desconocido

        if (mensaje.get("distancia_cm") is not None
                and isinstance(mensaje.get("distancia_cm"), (int, float))):
            estado.distancia_obstaculo_cm = float(mensaje["distancia_cm"])

        if isinstance(mensaje.get("navegacion"), str):
            try:
                estado.navegacion = Maniobra(mensaje["navegacion"])
            except ValueError:
                pass   # maniobra desconocida

        if isinstance(mensaje.get("consumo_watts"), (int, float)):
            estado.consumo_watts = float(mensaje["consumo_watts"])

        if isinstance(mensaje.get("conexion_activa"), bool):
            estado.conexion_activa = bool(mensaje["conexion_activa"])

        if isinstance(mensaje.get("hay_advertencia"), bool):
            estado.hay_advertencia = bool(mensaje["hay_advertencia"])

        if isinstance(mensaje.get("hay_error"), bool):
            estado.hay_error = bool(mensaje["hay_error"])

        if isinstance(mensaje.get("modulo_inactivo"), bool):
            estado.modulo_inactivo = bool(mensaje["modulo_inactivo"])

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
        """Serializa el comando a JSON y lo envía por el socket, + '\\n'."""

        mensaje = json.dumps(comando) + '\n'
        try:
            self.conexion.send(mensaje.encode())
        except OSError:
            # Socket muerto
            self._perdida = True

    def cerrar(self):
        """Cierra el socket con el ESP32."""

        try:
            self.conexion.close()
        except OSError:
            pass


class ComunicacionSimulada(Conexion):
    """Comunicación simulada para probar la app sin un ESP32 real."""

    def __init__(self):
        self._bateria_simulada = 1.0
        self._distancia_simulada = 45.0
        self._modo_simulado = "automatico"
        self._ultimo_log_tiempo = time.time()
        # Cooldowns del logger
        self._aviso_advertencia_log = False
        self._aviso_error_log = False

    def actualizar_estado(self, estado: EstadoRobot):
        """
        Calcula valores simulados que evolucionan con el tiempo y los escribe
        directo en EstadoRobot.
        """

        self._bateria_simulada = max(0.0, self._bateria_simulada - 0.001)

        variacion_distancia = random.uniform(-2.5, 2.5)
        self._distancia_simulada = max(5.0, min(200.0, self._distancia_simulada + variacion_distancia))

        estado.bateria = round(self._bateria_simulada, 3)
        estado.modo = Modo(self._modo_simulado)
        estado.distancia_obstaculo_cm = round(self._distancia_simulada, 1)
        estado.consumo_watts = round(random.uniform(1.2, 4.8), 2)
        estado.conexion_activa = True

        # Nivel de señal simulado
        secuencia_senal = (NivelConexion.ALTA, NivelConexion.ALTA,
                           NivelConexion.MEDIA, NivelConexion.BAJA)
        estado.nivel_conexion = secuencia_senal[int(time.time() / 8) % len(secuencia_senal)]

        # Maniobra decidida (el firmware la manda en automático)
        estado.navegacion = (Maniobra.ALTO if self._distancia_simulada < 15.0
                             else Maniobra.RECTO)

        # Alertas simuladas para probar los íconos de sistema
        estado.hay_advertencia = (self._distancia_simulada < 15.0
                                  or self._bateria_simulada < 0.25)
        estado.hay_error = self._bateria_simulada < 0.10

        # Logs que alimentan los colores del logger
        if estado.hay_advertencia and not self._aviso_advertencia_log:
            estado.logger.agregar_linea(
                "DISTANCIA",
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

        # Log de prueba cada 10 s
        if time.time() - self._ultimo_log_tiempo > 10.0:
            estado.logger.agregar_linea(
                "SIMULADOR",
                f"Lectura de prueba. Sensor de distancia detecta objeto a {round(self._distancia_simulada)}cm",
                NivelLog.INFO
            )
            self._ultimo_log_tiempo = time.time()

    def enviar_mensaje(self, comando: dict):
        """Simula el envío de un comando al robot."""

        print(f"[COMUNICACIÓN SIMULADA] Comando enviado -> {comando}")

        if comando.get("tipo") == "multi":
            for sub in comando.get("comandos", []):
                if isinstance(sub, dict):
                    self._aplicar_comando_simulado(sub)
            return

        self._aplicar_comando_simulado(comando)

    def _aplicar_comando_simulado(self, comando: dict):
        """Aplica un comando simple al estado simulado (por ahora, solo 'modo')."""
        if comando.get("tipo") == "modo":
            self._modo_simulado = comando.get("modo", self._modo_simulado)


class ConexionOffline(Conexion):
    """Estado "sin robot": ni conexión real ni simulador."""

    def actualizar_estado(self, estado: EstadoRobot):
        """No hay robot que leer: solo se marca que no hay conexión."""
        estado.conexion_activa = False
        estado.nivel_conexion = NivelConexion.NULA

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

    assert estado.nivel_conexion in (NivelConexion.ALTA, NivelConexion.MEDIA,
                                     NivelConexion.BAJA), \
        "El simulador siempre reporta un enlace, nunca nulo"
    print(f"nivel_conexion     = {estado.nivel_conexion.value}\n")

    print("Umbrales de nivel de señal (frescura)")
    assert nivel_por_frescura(None) == NivelConexion.NULA, "Sin dato -> nula"
    assert nivel_por_frescura(0.1) == NivelConexion.ALTA, "Fresco < 0.8s -> alta"
    assert nivel_por_frescura(1.0) == NivelConexion.MEDIA, "1s -> media"
    assert nivel_por_frescura(5.0) == NivelConexion.BAJA, "Viejo -> baja"
    print("OK: nula/alta/media/baja\n")

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

    # El logger arranca vacío
    print("\nLogger (buffer simulado)")
    print(f"lineas de log       = {len(estado.logger.obtener_lineas())}")

    # Colores del logger
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

    simulada._distancia_simulada = 50.0  # sale de la alerta
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
    assert estado.nivel_conexion == NivelConexion.NULA, "Offline no tiene señal"
    offline.enviar_mensaje({"tipo": "motor", "direccion": "arriba"})  # no lanza
    print("OK: conexion_activa=False, nivel NULA y los comandos se descartan")

    # Parseo del protocolo real sin abrir sockets: se instancia con __new__ y
    # se alimenta _procesar_mensaje con diccionarios puros.
    print("\nParseo tolerante del estado ampliado (protocolo real)")
    estado_proto = EstadoRobot()
    proto = Comunicacion.__new__(Comunicacion)

    # Tal como lo mandaría el ESP32
    proto._procesar_mensaje({
        "tipo": "estado",
        "bateria": 0.83,
        "modo": "manual",
        "hay_advertencia": True,
        "hay_error": False,
        "distancia_cm": 12.3,
        "navegacion": "alto",
        "consumo_watts": 3.4,
        "conexion_activa": True,
        "cargando": False,
        "modulo_inactivo": True,
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
    assert estado_proto.navegacion == Maniobra.ALTO
    assert estado_proto.consumo_watts == 3.4
    assert estado_proto.conexion_activa is True
    assert estado_proto.cargando is False
    assert estado_proto.modulo_inactivo is True
    assert estado_proto.tiempo_restante_min == 42
    assert estado_proto.posiciones_servos.cuello == 30.0
    assert estado_proto.posiciones_servos.hombro_izquierdo == -18.0
    print("OK: todos los campos del estado ampliado se aplicaron")

    # Un estado con campos null/ausentes NO debe machacar lo anterior
    proto._procesar_mensaje({
        "tipo": "estado",
        "distancia_cm": None,        # sensor de distancia sin lectura
        "tiempo_restante_min": None, # sin estimación
        "cargando": True,
    }, estado_proto)

    assert estado_proto.distancia_obstaculo_cm == 12.3
    assert estado_proto.tiempo_restante_min == 42
    assert estado_proto.cargando is True
    assert estado_proto.modulo_inactivo is True
    print("OK: null/ausencia no pisan valores previos")

    # Maniobra desconocida
    proto._procesar_mensaje({"tipo": "estado", "navegacion": "teletransporte"},
                            estado_proto)
    assert estado_proto.navegacion == Maniobra.ALTO
    print("OK: maniobra desconocida se ignora")

    # Modo desconocido
    proto._procesar_mensaje({"tipo": "estado", "modo": "turbo"}, estado_proto)
    assert estado_proto.modo == Modo.MANUAL
    print("OK: modo desconocido se ignora")

    # Mensaje sin tipo / basura
    proto._procesar_mensaje({"hola": "mundo"}, estado_proto)
    proto._procesar_mensaje(["no soy", "dict"], estado_proto)
    print("OK: mensajes sin 'tipo' se descartan")

    # Log llegado por la red
    proto._procesar_mensaje({
        "tipo": "log",
        "origen": "DISTANCIA",
        "mensaje": "Obstáculo a 8cm",
        "nivel": "advertencia",
    }, estado_proto)
    ultimas = estado_proto.logger.obtener_lineas()
    assert ultimas[-1].nivel == NivelLog.ADVERTENCIA
    assert ultimas[-1].origen == "DISTANCIA"
    print("OK: log de red se integra al logger")

    # Comunicacion.cerrar() existe
    assert callable(getattr(Comunicacion, "cerrar", None)), "Comunicacion debe tener cerrar()"
    print("OK: Comunicacion.cerrar() existe")

    # Robustez de red sin sockets reales: se inyecta un socket falso
    print("\nRobustez de red (socket falso)")

    # 1) Un JSON roto en el medio no debe tumbar ni machacar lo bueno.
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
    assert not roto.perdida, "Un JSON roto no es pérdida de conexión"
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

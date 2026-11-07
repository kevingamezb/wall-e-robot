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
con JSON corrupto se descartan sin cortar la conexión; un cierre limpio, un
fallo de recv/send o un buffer desbordado marcan la conexión como perdida para
que la GUI degrade a ConexionOffline.

El socket es no bloqueante: recv() y send() pueden dejar trabajo pendiente.
Por eso la entrada se acumula como bytes y la salida se guarda en una cola que
se vacía en cada ciclo de la aplicación. Así un envío parcial o un
BlockingIOError no se confunden con una conexión caída.
"""


from abc import ABC, abstractmethod
from collections import deque
from ..nucleo.estado import EstadoRobot, NivelLog, Modo, Maniobra, NivelConexion
import socket
import json
import time
from typing import cast


# Umbrales de frescura para el nivel de señal.
SEGUNDOS_SENAL_ALTA  = 0.8
SEGUNDOS_SENAL_MEDIA = 2.0

# Versión del protocolo que habla esta app. El firmware publica la suya en
# cada mensaje; si es más nueva, la app avisa pero sigue leyendo los campos
# que conoce (compatibilidad hacia atrás).
PROTOCOLO_VERSION = 1

# Límites de memoria para no dejar crecer los buffers sin control si el otro
# extremo envía basura o deja de leer.
MAX_BUFFER_ENTRADA = 64 * 1024
MAX_BUFFER_SALIDA  = 64 * 1024
TAMANO_LECTURA     = 4096

# Tiempo máximo para abrir el socket (el hilo de conexión no se queda colgado
# esperando a un ESP32 apagado).
TIMEOUT_CONEXION_S = 3.0


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
    """Interfaz de conexión con el robot (real u offline)."""
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

        # connect() con timeout para que un robot apagado no deje el hilo de
        # conexión bloqueado durante el timeout largo del sistema operativo.
        try:
            self.conexion.settimeout(TIMEOUT_CONEXION_S)
            self.conexion.connect((ip, puerto))
            # No bloqueante: recv() lanza BlockingIOError de inmediato si no
            # hay datos, en vez de congelar la GUI esperándolos.
            self.conexion.setblocking(False)
        except OSError:
            try:
                self.conexion.close()
            except OSError:
                pass
            raise

        self._buffer_entrada  = bytearray()  # bytes recibidos sin '\n'
        self._buffer_salida   = bytearray()  # bytes pendientes de enviar
        self._perdida         = False        # True si la conexión se rompió
        self._ultima_recepcion = None        # time() del último estado recibido
        self._aviso_version   = False        # ya se avisó de un protocolo nuevo

    @property
    def perdida(self) -> bool:
        """True si la conexión se interrumpió (el ESP32 se reinició o se apagó)."""
        # getattr: algunos tests construyen la clase con __new__.
        return getattr(self, "_perdida", False)

    @property
    def edad_ms(self):
        """Milisegundos desde el último estado recibido."""
        ultima = getattr(self, "_ultima_recepcion", None)
        if ultima is None:
            return None
        return int((time.time() - ultima) * 1000)

    def actualizar_estado(self, estado: EstadoRobot):
        """Vacía la cola de salida y procesa todo lo pendiente del socket."""
        if self.perdida:
            estado.nivel_conexion = NivelConexion.NULA
            return

        # Primero se intenta terminar de enviar lo que quedó pendiente del
        # ciclo anterior (envío parcial o backpressure).
        self._enviar_pendiente()
        if self.perdida:
            estado.nivel_conexion = NivelConexion.NULA
            return

        # Se drena el socket completo, no solo un paquete: el ESP32 puede
        # mandar estado + log juntos y no conviene dejar backlog.
        self._leer_socket()
        if self.perdida:
            estado.nivel_conexion = NivelConexion.NULA
            return

        self._procesar_buffer(estado)

        # El nivel de señal sale de qué tan fresca es la última lectura.
        segundos = None
        ultima_recepcion = getattr(self, "_ultima_recepcion", None)
        if ultima_recepcion is not None:
            segundos = time.time() - ultima_recepcion
        estado.nivel_conexion = nivel_por_frescura(segundos)

    def _marcar_perdida(self):
        """Marca la conexión como caída y libera los buffers pendientes."""
        self._perdida = True
        for nombre in ("_buffer_entrada", "_buffer_salida"):
            buffer = getattr(self, nombre, None)
            if buffer is not None:
                buffer.clear()

    def _leer_socket(self):
        """Acumula todos los bytes disponibles hasta que el socket se vacíe."""
        entrada = getattr(self, "_buffer_entrada", None)
        if entrada is None:
            entrada = bytearray()
            self._buffer_entrada = entrada

        try:
            while True:
                datos = self.conexion.recv(TAMANO_LECTURA)

                # recv() devuelve b'' cuando el otro extremo cerró de forma
                # limpia; eso no lanza excepción y hay que detectarlo.
                if not datos:
                    self._marcar_perdida()
                    return

                entrada.extend(datos)

                # Si no llega un '\n', el buffer no debe crecer sin límite.
                if len(entrada) > MAX_BUFFER_ENTRADA:
                    self._marcar_perdida()
                    return

        except BlockingIOError:
            pass   # no hay más datos por ahora
        except OSError:
            # El ESP32 se reinició/apagó o se cortó la conexión.
            self._marcar_perdida()

    def _procesar_buffer(self, estado: EstadoRobot):
        """Extrae y procesa cada línea completa del buffer de entrada."""
        entrada = getattr(self, "_buffer_entrada", None)
        if not entrada:
            return

        while True:
            corte = entrada.find(b"\n")
            if corte < 0:
                break

            linea = bytes(entrada[:corte])
            del entrada[:corte + 1]

            if not linea.strip():
                continue   # línea vacía

            # Decodificar por línea (no por paquete) resuelve los caracteres
            # UTF-8 que quedan partidos entre dos recv().
            try:
                texto = linea.decode("utf-8", errors="replace")
                mensaje = json.loads(texto)
            except (json.JSONDecodeError, RecursionError, UnicodeError):
                continue   # línea corrupta

            self._procesar_mensaje(mensaje, estado)

    def _enviar_pendiente(self):
        """Intenta vaciar la cola de salida sin bloquear la GUI."""
        salida = getattr(self, "_buffer_salida", None)
        if not salida:
            return

        try:
            while salida:
                enviados = self.conexion.send(salida)

                if not enviados:
                    # send() devolvió 0: el otro extremo ya no acepta datos.
                    self._marcar_perdida()
                    return

                del salida[:enviados]
        except BlockingIOError:
            return   # el socket está lleno; se reintenta en el próximo ciclo
        except OSError:
            self._marcar_perdida()

    def _procesar_mensaje(self, mensaje, estado: EstadoRobot):
        """Interpreta UN mensaje JSON ya deserializado y lo escribe en EstadoRobot."""

        if not isinstance(mensaje, dict) or "tipo" not in mensaje:
            return   # basura o versión vieja

        version = mensaje.get("protocolo")
        if (type(version) is int and version > PROTOCOLO_VERSION
                and not getattr(self, "_aviso_version", False)):
            estado.logger.agregar_linea(
                "PROTOCOLO",
                f"El robot usa el protocolo {version}; esta app soporta "
                f"{PROTOCOLO_VERSION}",
                NivelLog.ADVERTENCIA,
            )
            self._aviso_version = True

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

        if isinstance(mensaje.get("version_firmware"), str):
            estado.version_firmware = mensaje["version_firmware"]

        if isinstance(mensaje.get("ota_pendiente"), bool):
            estado.ota_pendiente = bool(mensaje["ota_pendiente"])

        posiciones = mensaje.get("posiciones_servos")
        if isinstance(posiciones, dict):
            for nombre, valor in posiciones.items():
                if (hasattr(estado.posiciones_servos, nombre)
                        and isinstance(valor, (int, float))):
                    setattr(estado.posiciones_servos, nombre, float(valor))

    def enviar_mensaje(self, comando: dict):
        """Serializa el comando a JSON y lo encola para enviarlo por el socket."""

        if self.perdida:
            return

        # Todo comando sale versionado; el firmware ignora los campos que no
        # conoce, así que añadirlo es compatible con versiones anteriores.
        comando = dict(comando)
        comando.setdefault("protocolo", PROTOCOLO_VERSION)

        try:
            mensaje = json.dumps(comando, ensure_ascii=False) + "\n"
            datos = mensaje.encode("utf-8")
        except (TypeError, ValueError):
            return

        salida = getattr(self, "_buffer_salida", None)
        if salida is None:
            salida = bytearray()
            self._buffer_salida = salida

        if len(salida) + len(datos) > MAX_BUFFER_SALIDA:
            # El robot dejó de leer y la cola creció demasiado: se corta la
            # conexión para que la GUI degrade a offline y no se coma la RAM.
            self._marcar_perdida()
            return

        salida.extend(datos)
        self._enviar_pendiente()

    def cerrar(self):
        """Cierra el socket con el ESP32."""

        try:
            self.conexion.close()
        except OSError:
            pass

        for nombre in ("_buffer_entrada", "_buffer_salida"):
            buffer = getattr(self, nombre, None)
            if buffer is not None:
                buffer.clear()


class ConexionOffline(Conexion):
    """Estado "sin robot": sin conexión activa ni datos."""

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

    print("Umbrales de nivel de señal (frescura)")
    assert nivel_por_frescura(None) == NivelConexion.NULA, "Sin dato -> nula"
    assert nivel_por_frescura(0.1) == NivelConexion.ALTA, "Fresco < 0.8s -> alta"
    assert nivel_por_frescura(1.0) == NivelConexion.MEDIA, "1s -> media"
    assert nivel_por_frescura(5.0) == NivelConexion.BAJA, "Viejo -> baja"
    print("OK: nula/alta/media/baja\n")

    # ConexionOffline: no produce datos y descarta comandos
    print("ConexionOffline")
    estado = EstadoRobot()
    estado.conexion_activa = True    # parte de "conectado" para probar el apagado
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
        "protocolo": 1,
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
        "version_firmware": "1.0.0",
        "ota_pendiente": False,
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
    assert estado_proto.version_firmware == "1.0.0"
    assert estado_proto.ota_pendiente is False
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

    # Robustez de red sin sockets reales: se inyecta un socket falso.
    print("\nRobustez de red (socket falso)")

    class _SocketGuion:
        """Entrega trozos en orden y luego simula un socket no bloqueante."""
        def __init__(self, trozos=None, error_recv=None, error_send=None,
                     limite_send=None):
            self._trozos = deque(trozos or [])
            self._error_recv = error_recv
            self._error_send = error_send
            self._limite_send = limite_send
            self.enviado = bytearray()

        def recv(self, _n):
            if self._error_recv is not None:
                raise self._error_recv
            if self._trozos:
                return self._trozos.popleft()
            raise BlockingIOError()

        def send(self, datos):
            if self._error_send is not None:
                raise self._error_send
            n = len(datos) if self._limite_send is None else min(
                len(datos), self._limite_send)
            self.enviado.extend(datos[:n])
            return n

    def _con(falso):
        con = Comunicacion.__new__(Comunicacion)
        con.conexion = cast(socket.socket, falso)
        con._buffer_entrada = bytearray()
        con._buffer_salida = bytearray()
        con._perdida = False
        con._ultima_recepcion = None
        con._aviso_version = False
        return con

    # 1) Un solo paquete válido no se debe perder (regresión del doble recv).
    unico = _con(_SocketGuion([b'{"tipo":"estado","bateria":0.5}\n']))
    estado_red = EstadoRobot(bateria=0.1)
    unico.actualizar_estado(estado_red)
    assert estado_red.bateria == 0.5, "El primer paquete debe aplicarse"
    assert not unico.perdida
    print("OK: un único paquete se aplica")

    # 2) Cierre limpio (b'') -> perdida=True, sin excepción.
    cerrado = _con(_SocketGuion([b""]))
    cerrado.actualizar_estado(EstadoRobot())
    assert cerrado.perdida, "recv b'' debe marcar perdida=True"
    print("OK: cierre limpio marca perdida=True")

    # 3) JSON roto en el medio no debe tumbar ni machacar lo bueno.
    roto = _con(_SocketGuion([
        b'{"tipo":"estado","bateria":0.5}\n{"tipo": roto\n']))
    estado_red = EstadoRobot(bateria=0.1)
    roto.actualizar_estado(estado_red)
    assert estado_red.bateria == 0.5, "La línea buena sí debe procesarse"
    assert not roto.perdida, "Un JSON roto no es pérdida de conexión"
    print("OK: JSON corrupto se descarta y la línea buena se aplica")

    # 4) UTF-8 partido entre dos paquetes.
    utf8 = _con(_SocketGuion([
        b'{"tipo":"log","origen":"X","mensaje":"ca\xc3',
        b'\xb1a"}\n',
    ]))
    estado_log = EstadoRobot()
    utf8.actualizar_estado(estado_log)
    assert estado_log.logger.obtener_lineas()[-1].mensaje == "caña"
    print("OK: UTF-8 partido entre paquetes se reconstruye")

    # 5) Envío parcial: send() acepta pocos bytes por llamada.
    parcial = _con(_SocketGuion(limite_send=4))
    parcial.enviar_mensaje({"tipo": "motor", "direccion": "arriba"})
    esperado = json.dumps({"tipo": "motor", "direccion": "arriba",
                           "protocolo": PROTOCOLO_VERSION},
                          ensure_ascii=False).encode("utf-8") + b"\n"
    assert bytes(getattr(parcial.conexion, "enviado", bytearray())) == esperado
    assert not parcial.perdida
    print("OK: envío parcial se completa")

    # 6) Backpressure no es pérdida y se reintenta en el próximo ciclo.
    class _SocketLleno(_SocketGuion):
        def __init__(self):
            super().__init__()
            self.llamadas = 0

        def send(self, datos):
            self.llamadas += 1
            if self.llamadas == 1:
                raise BlockingIOError()
            return super().send(datos)

    lleno = _con(_SocketLleno())
    lleno.enviar_mensaje({"tipo": "modo", "modo": "manual"})
    assert not lleno.perdida, "BlockingIOError no es conexión perdida"
    lleno.actualizar_estado(EstadoRobot())
    assert bytes(getattr(lleno.conexion, "enviado", bytearray())).endswith(b"\n")
    print("OK: backpressure se reintenta sin marcar pérdida")

    # 7) Conexión caída (recv lanza) -> perdida=True, sin excepción.
    caido = _con(_SocketGuion(
        error_recv=ConnectionResetError("el robot se reinició")))
    caido.actualizar_estado(EstadoRobot())
    assert caido.perdida, "recv caído debe marcar perdida=True"
    print("OK: recv caído marca perdida=True sin lanzar")

    # 8) Enviar a un socket muerto marca perdida=True, sin excepción.
    send_caido = _con(_SocketGuion(error_send=OSError("socket cerrado")))
    send_caido.enviar_mensaje({"tipo": "motor", "direccion": "arriba"})
    assert send_caido.perdida, "send caído debe marcar perdida=True"
    print("OK: send caído marca perdida=True sin lanzar")

    # 9) Un protocolo más nuevo avisa una sola vez y no rompe.
    version = _con(_SocketGuion([
        b'{"protocolo":99,"tipo":"estado","bateria":0.7}\n']))
    estado_version = EstadoRobot()
    version.actualizar_estado(estado_version)
    avisos = [linea for linea in estado_version.logger.obtener_lineas()
              if linea.origen == "PROTOCOLO"]
    assert len(avisos) == 1
    assert estado_version.bateria == 0.7
    print("OK: protocolo nuevo avisa y sigue parseando")

    print("\nPruebas OK")

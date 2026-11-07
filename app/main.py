# wall-e-robot/app/main.py
# Kevin Gámez - 13/09/2026
#
# Punto de entrada de la aplicación de escritorio del Wall-E.
# Para arrancar (desde la raíz del proyecto, donde está la carpeta 'app'):
#   python -m app.main   (o, equivalentemente,  python -m app)


import queue
import threading
import tkinter as tk
from .nucleo.paleta import Paleta
from .nucleo.disenio import escala_para_pantalla
from .nucleo.estado import EstadoRobot, NivelLog, Modo
from .comunicacion.conexion import Comunicacion, ConexionOffline
from .pantallas.pantalla_principal import PantallaPrincipal
from .widgets.logica.mapeo_teclado import MapeoTeclado
from .widgets.logica.control_teclado import ControlTeclado


# Cada cuántos milisegundos se lee el "robot" y se redibuja la pantalla.
INTERVALO_CICLO_MS = 33

# Puerto en el que escucha el ESP32 (firmware y socket deben coincidir).
PUERTO = 8080

# Reconexión automática: espera creciente entre intentos (1, 2, 4... s).
RECONEXION_ESPERA_INICIAL_MS = 1000
RECONEXION_ESPERA_MAX_MS     = 10000


class Aplicacion:
    """Coordina estado, conexión y pantalla."""
    def __init__(self, root: tk.Tk, escala):
        """Monta la ventana, el estado, la conexión y la pantalla."""
        self.root = root
        self.root.title("Wall-E · Panel de control")
        self.root.configure(bg=Paleta.FONDO_APP)

        # Estado compartido del que leen todos los widgets.
        self.estado = EstadoRobot()

        # Arranca sin conexión: al entrar se pide la IP del robot (ver iniciar()).
        self.conexion = ConexionOffline()

        # La conexión TCP se abre en un hilo para no congelar la GUI mientras
        # el socket espera al ESP32. El hilo deja el resultado en esta cola y
        # el ciclo de la aplicación (hilo de Tk) lo aplica.
        self._conexion_pendiente = False
        self._intento_conexion = 0
        self._resultados_conexion: queue.Queue = queue.Queue()

        # Última conexión válida: se usa para reintentar si el robot se cae.
        self._ultima_ip: str | None = None
        self._ultimo_puerto = PUERTO
        self._reconectando = False
        self._reintentos = 0
        self._reconexion_id = None   # id de root.after() pendiente

        self.contenedor = tk.Frame(root, bg=Paleta.FONDO_APP)
        self.contenedor.pack(fill="both", expand=True)

        # Mapeo de teclado.
        self.mapeo = MapeoTeclado.cargar()

        self.pantalla = PantallaPrincipal(
            self.contenedor,
            self.estado,
            escala,
            on_conectar=self._conectar,
            on_desconectar=self._desconectar,
            on_modo=self._cambiar_modo,
            mapeo=self.mapeo,
            on_cambio_mapeo=self.mapeo.guardar,
            # Mientras se captura una tecla nueva, el teclado no mueve al robot.
            al_captura=self._suspender_teclado,
        )
        # El gamepad dispara siempre hacia la conexión activa (real u offline).
        self.pantalla.conectar_gamepad(lambda cmd: self.conexion.enviar_mensaje(cmd))

        self.control_teclado = ControlTeclado(self.root, self.mapeo,
                                              self.pantalla.gamepad)

    def _suspender_teclado(self, activa: bool):
        """Suspende el control por teclado mientras se captura una tecla nueva."""
        self.control_teclado.suspendido = activa

    # Conexión con el robot
    def _conectar(self, ip: str, puerto: int = PUERTO):
        """Intenta abrir la conexión real con el ESP32 en segundo plano.

        El socket puede tardar varios segundos en responder (o agotar su
        tiempo de espera), así que se abre en un hilo aparte para que la
        ventana siga respondiendo. El resultado se recoge en ciclo().

        Si el robot ya se había conectado antes, esta conexión pasa a ser la
        dirección a la que se reintenta cuando el enlace se cae.
        """
        if self._conexion_pendiente:
            return   # ya hay un intento en curso

        # Un intento manual reemplaza cualquier reintento automático en curso.
        self._cancelar_reconexion()
        self._ultima_ip = ip
        self._ultimo_puerto = puerto
        self._lanzar_intento(ip, puerto, reconectando=False)

    def _lanzar_intento(self, ip: str, puerto: int, reconectando: bool):
        """Lanza el hilo que abre el socket y deja el resultado en la cola."""
        self._conexion_pendiente = True
        self._intento_conexion += 1
        self.pantalla.establecer_conectando(ip, reconectando=reconectando)

        hilo = threading.Thread(
            target=self._abrir_conexion,
            args=(self._intento_conexion, ip, puerto),
            name="conexion-robot",
            daemon=True,
        )
        hilo.start()

    def _programar_reconexion(self):
        """Agenda el siguiente intento automático con espera exponencial.

        La espera arranca en RECONEXION_ESPERA_INICIAL_MS y se duplica en cada
        fallo hasta RECONEXION_ESPERA_MAX_MS. El robot sigue navegando solo
        mientras tanto; en manual sus motores ya se detuvieron por el timeout
        del firmware, así que reintentar es seguro.
        """
        if self._ultima_ip is None:
            return   # nunca hubo una conexión válida que recuperar

        self._cancelar_temporizador_reconexion()
        espera = min(
            RECONEXION_ESPERA_INICIAL_MS * (2 ** min(self._reintentos, 4)),
            RECONEXION_ESPERA_MAX_MS,
        )
        self._reintentos += 1
        self._reconectando = True
        self.pantalla.establecer_conectando(self._ultima_ip, reconectando=True)
        self._reconexion_id = self.root.after(espera, self._reintentar)

    def _reintentar(self):
        """Callback del temporizador: vuelve a abrir el socket."""
        self._reconexion_id = None

        if not self._reconectando or self._conexion_pendiente:
            return   # el usuario desconectó o ya hay un intento en curso

        ip = self._ultima_ip
        if ip is None:
            return   # no hay una dirección válida que recuperar

        self._lanzar_intento(ip, self._ultimo_puerto, reconectando=True)

    def _cancelar_temporizador_reconexion(self):
        """Cancela el root.after() pendiente, si lo hay."""
        if self._reconexion_id is not None:
            try:
                self.root.after_cancel(self._reconexion_id)
            except (AttributeError, tk.TclError):
                pass   # ventana ya cerrada o root falsa en pruebas
            self._reconexion_id = None

    def _cancelar_reconexion(self):
        """Detiene los reintentos y reinicia el backoff."""
        self._cancelar_temporizador_reconexion()
        self._reconectando = False
        self._reintentos = 0

    def _abrir_conexion(self, intento: int, ip: str, puerto: int):
        """Hilo de trabajo: crea la Comunicacion y publica el resultado."""
        try:
            nueva = Comunicacion(ip, puerto)
        except (OSError, ValueError) as error:
            self._resultados_conexion.put((intento, ip, None, error))
        else:
            self._resultados_conexion.put((intento, ip, nueva, None))

    def _procesar_resultados_conexion(self):
        """Aplica en el hilo de Tk los resultados que dejó el hilo de conexión."""
        while True:
            try:
                intento, ip, nueva, error = self._resultados_conexion.get_nowait()
            except queue.Empty:
                return
            self._aplicar_resultado_conexion(intento, ip, nueva, error)

    def _aplicar_resultado_conexion(self, intento, ip, nueva, error):
        """Cierra o adopta el socket según haya ido el intento."""
        # Un intento viejo (el usuario desconectó o reconectó mientras tanto)
        # no debe pisar la conexión actual; si abrió un socket, se descarta.
        if intento != self._intento_conexion:
            if nueva is not None:
                nueva.cerrar()
            return

        self._conexion_pendiente = False

        if error is not None:
            self.pantalla.establecer_conexion(False, "SIN CONEXI\u00d3N")
            self.pantalla.mostrar_error(f"No se pudo conectar: {error}")
            self._programar_reconexion()
            return

        # Conexión lograda: se cancela cualquier reintento pendiente.
        self._cancelar_reconexion()
        self._ultima_ip = ip
        self._cerrar_conexion_actual()
        self.conexion = nueva
        self.pantalla.establecer_conexion(True, ip)

    def _desconectar(self):
        """Cierra la conexión actual y deja el panel sin conexión."""
        # Invalida cualquier intento en curso: si su socket llega después,
        # _aplicar_resultado_conexion lo cerrará sin activarlo.
        self._intento_conexion += 1
        self._conexion_pendiente = False
        # Un cierre explícito del usuario no debe reconectar solo.
        self._ultima_ip = None
        self._cancelar_reconexion()
        self._cerrar_conexion_actual()
        self.conexion = ConexionOffline()
        self.pantalla.establecer_conexion(False, "SIN CONEXI\u00d3N")

    def _cambiar_modo(self):
        """Alterna el modo del robot (manual <-> automático)."""
        if not isinstance(self.conexion, Comunicacion):
            return   # sin robot real no hay a quién pedirle el cambio
        nuevo = (Modo.AUTOMATICO if self.estado.modo == Modo.MANUAL
                 else Modo.MANUAL)
        self.conexion.enviar_mensaje({"tipo": "modo", "modo": nuevo.value})

    def _cerrar_conexion_actual(self):
        """Cierra el socket actual si lo hay."""
        cerrar = getattr(self.conexion, "cerrar", None)
        if callable(cerrar):
            cerrar()

    # Bucle principal de la aplicación
    def ciclo(self):
        """Un paso de la aplicación: leer al robot y redibujar la pantalla."""
        self._procesar_resultados_conexion()
        self.conexion.actualizar_estado(self.estado)

        # Si el robot se apagó/reinició en plena conexión, la red lo marca como
        # "perdida": se degrada a sin-conexión, se avisa en el log y se
        # programa un reintento automático.
        if getattr(self.conexion, "perdida", False):
            self._cerrar_conexion_actual()
            self.conexion = ConexionOffline()
            self.pantalla.establecer_conexion(False, "SIN CONEXI\u00d3N")
            self.estado.logger.agregar_linea(
                "CONEXI\u00d3N",
                "Se perdió la conexión con el robot",
                NivelLog.ADVERTENCIA,
            )
            self._programar_reconexion()

        self.pantalla.actualizar_latencia(getattr(self.conexion, "edad_ms", None))
        self.pantalla.dibujar()
        self.root.after(INTERVALO_CICLO_MS, self.ciclo)

    def iniciar(self):
        """Arranca el bucle y abre la ventana (la IP se escribe en la barra lateral)."""
        self.ciclo()
        self.root.mainloop()


def main():
    """Crea la ventana raíz y arranca la aplicación."""
    ventana = tk.Tk()
    escala = escala_para_pantalla(ventana.winfo_screenwidth(),
                                  ventana.winfo_screenheight())
    ventana.geometry(f"{escala.ancho}x{escala.alto}")
    ventana.resizable(False, False)   # el diseño escala a la pantalla al abrir
    app = Aplicacion(ventana, escala)
    app.iniciar()


if __name__ == "__main__":
    main()

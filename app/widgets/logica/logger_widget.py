# wall-e-robot/app/widgets/logica/logger_widget.py
# Kevin Gámez - 13/09/2026


from ...nucleo.estado import EstadoRobot, EntradaLog


class LoggerWidget:
    """
    El puente entre el modelo de datos del log y la pantalla.

    No dibuja nada, pero es el widget con comportamiento más "activo" de la
    app: al construirse, se SUSCRIBE al Logger de EstadoRobot (el "grupo de
    WhatsApp"). Así, cada vez que alguien agrega una línea, este widget se
    entera al instante y puede avisar a su vez al renderer.

    Por qué nos suscribimos en vez de consultar a mano:
    si el renderer solo consultara cada ciclo, se perdería el instante exacto
    en que llega una línea. Con la suscripción, el renderer se actualiza en
    el momento justo en que algo entra al log.
    """

    def __init__(self, estado: EstadoRobot):
        """
        Constructor del widget del logger.

        estado: la 'caja maestra' (EstadoRobot). De ahí sacamos el Logger
        y nos suscribimos a él para enterarnos de cada línea nueva.
        """
        self.estado = estado
        self._suscriptores = []  # El renderer (u otros) se anotan aquí

        # Nos unimos al "grupo de WhatsApp" del log: desde este momento,
        # el logger nos llamará con cada línea nueva que se agregue.
        self.estado.logger.agregar_suscriptor(self._al_recibir_linea)

    def _al_recibir_linea(self, entrada: EntradaLog):
        """
        El "ping" que nos manda el Logger cuando llega una línea nueva.

        Este método es el callback que registramos en el Logger. Cuando lo
        invocan, reenvía el aviso a nuestros propios suscriptores (los
        renderers), sin guardar nada: leer las líneas lo hace el renderer
        cuando lo necesite, vía obtener_lineas().
        """
        for callback in self._suscriptores:
            callback(entrada)

    def suscribir(self, callback):
        """Anota un callback que será llamado con cada línea nueva del log."""
        self._suscriptores.append(callback)

    def obtener_lineas(self) -> list[EntradaLog]:
        """Devuelve las líneas actuales del log (una copia del buffer)."""
        return self.estado.logger.obtener_lineas()


# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.widgets.logica.logger_widget

if __name__ == "__main__":
    print("Prueba logger_widget.py\n")

    from ...nucleo.estado import NivelLog

    estado = EstadoRobot()

    # 1. Suscribirse: el widget recibe cada línea nueva
    print("=== Suscripción al logger ===")
    widget = LoggerWidget(estado)
    recibidas = []

    widget.suscribir(lambda entrada: recibidas.append(entrada.mensaje))

    estado.logger.agregar_linea("SISTEMA", "Iniciando subsistemas")
    estado.logger.agregar_linea("SENSOR", "Obstáculo a 8cm", NivelLog.ADVERTENCIA)

    assert recibidas == ["Iniciando subsistemas", "Obstáculo a 8cm"], \
        "El widget debería recibir en orden cada línea nueva"
    print(f"OK: recibidas -> {recibidas}\n")

    # 2. obtener_lineas() refleja el buffer del logger
    print("=== Lectura del buffer ===")
    lineas = widget.obtener_lineas()
    assert len(lineas) == 2, "El buffer debería tener 2 líneas"
    assert lineas[-1].nivel == NivelLog.ADVERTENCIA, "La última es advertencia"
    print(f"OK: {len(lineas)} líneas, la última nivel={lineas[-1].nivel.value}\n")

    print("Pruebas OK")
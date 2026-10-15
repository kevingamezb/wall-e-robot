# wall-e-robot/app/widgets/logica/logger_widget.py
# Kevin Gámez - 13/09/2026


from ...nucleo.estado import EstadoRobot, EntradaLog


class LoggerWidget:
    """Encapsula la suscripción al logger del estado para propagar nuevas entradas al renderizado."""
    def __init__(self, estado: EstadoRobot):
        self.estado = estado
        self._suscriptores = []
        self.estado.logger.agregar_suscriptor(self._al_recibir_linea)

    def _al_recibir_linea(self, entrada: EntradaLog):
        for callback in self._suscriptores:
            callback(entrada)

    def suscribir(self, callback):
        self._suscriptores.append(callback)

    def obtener_lineas(self) -> list[EntradaLog]:
        return self.estado.logger.obtener_lineas()

# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.logica.logger_widget

if __name__ == "__main__":
    print("Prueba logger_widget.py\n")

    from ...nucleo.estado import NivelLog

    estado = EstadoRobot()

    print("Suscripción al logger")
    widget = LoggerWidget(estado)
    recibidas = []

    widget.suscribir(lambda entrada: recibidas.append(entrada.mensaje))

    estado.logger.agregar_linea("SISTEMA", "Iniciando subsistemas")
    estado.logger.agregar_linea("SENSOR", "Obstáculo a 8cm", NivelLog.ADVERTENCIA)

    assert recibidas == ["Iniciando subsistemas", "Obstáculo a 8cm"]
    print(f"OK: recibidas -> {recibidas}\n")

    print("Lectura del buffer")
    lineas = widget.obtener_lineas()
    assert len(lineas) == 2
    assert lineas[-1].nivel == NivelLog.ADVERTENCIA
    print(f"OK: {len(lineas)} líneas, la última nivel={lineas[-1].nivel.value}\n")

    print("Pruebas OK")
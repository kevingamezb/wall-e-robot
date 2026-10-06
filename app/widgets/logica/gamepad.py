# wall-e-robot/app/widgets/logica/gamepad.py
# Kevin Gámez - 13/09/2026


from ...nucleo.estado import EstadoRobot
from ...nucleo.paleta import Paleta
from .boton import Boton
from .deslizador import Deslizador, MovimientoDeslizador


# Los rangos de movimiento coinciden con los límites físicos de los servos
# (ver firmware/lib/comunicacion/comunicacion.cpp -> LIMITES[]) y con el
# mockup walle_demo.html (sliders de cuello y brazos).
RANGO_CUELLO = (-70, 70)
RANGO_HOMBRO = (-50, 50)
# Ángulo de las "manos" (pulgares) al abrir/cerrar.
ANGULO_MANO_ABIERTA = 22
ANGULO_MANO_CERRADA = -22


class Gamepad:
    """
    El control manual: un widget COMPUESTO de otros widgets más simples.

    Como dice la arquitectura (plan de API gráfica, nota del Gamepad):
    no es un widget atómico, es una composición de piezas ya existentes.
    Arma:
        - 4 botones de dirección (d-pad)  -> movimiento del robot
        - 1 deslizador horizontal          -> cuello
        - 2 deslizadores verticales        -> hombros (izq y der)
        - 1 botón de reposo                -> vuelve todo a la posición neutra
        - 2 botones de manos               -> abrir/cerrar pinza

    Cada vez que el usuario toca un control, el gamepad arma el comando JSON
    correspondiente y lo "emite" a quien se haya suscrito (normalmente la
    conexión, para enviarlo al robot). Así el gamepad no conoce ni al
    simulador ni al ESP32: solo sabe construir comandos.
    """

    def __init__(self, estado: EstadoRobot):
        """
        Constructor del gamepad.

        estado: la 'caja maestra' (EstadoRobot): se conserva por consistencia
        con el resto de los widgets.
        """
        self.estado = estado
        self.habilitado = True          # solo emite comandos si hay conexión
        self._suscriptores_comando = []  # A quién avisar que hay un comando listo

        # --- Los controles (piezas que ya existen por separado) ---
        self.direccion_arriba   = Boton("ARRIBA")
        self.direccion_abajo    = Boton("ABAJO")
        self.direccion_izquierda = Boton("IZQUIERDA")
        self.direccion_derecha  = Boton("DERECHA")

        self.cuello            = Deslizador(RANGO_CUELLO)
        self.hombro_izquierdo  = Deslizador(RANGO_HOMBRO)
        self.hombro_derecho    = Deslizador(RANGO_HOMBRO)

        self.reposo            = Boton("REPOSO")
        self.mano_abrir        = Boton("ABRIR MANO")
        self.mano_cerrar       = Boton("CERRAR MANO")

        # --- Cableado interno: cada control publica su comando en el gamepad ---
        self.direccion_arriba.suscribir(lambda: self._emitir({"tipo": "motor", "direccion": "arriba"}))
        self.direccion_abajo.suscribir(lambda: self._emitir({"tipo": "motor", "direccion": "abajo"}))
        self.direccion_izquierda.suscribir(lambda: self._emitir({"tipo": "motor", "direccion": "izquierda"}))
        self.direccion_derecha.suscribir(lambda: self._emitir({"tipo": "motor", "direccion": "derecha"}))

        self.cuello.suscribir(lambda e: self._servir_movimiento("cuello", e))
        self.hombro_izquierdo.suscribir(lambda e: self._servir_movimiento("hombro_izquierdo", e))
        self.hombro_derecho.suscribir(lambda e: self._servir_movimiento("hombro_derecho", e))

        self.reposo.suscribir(self._reposo)
        self.mano_abrir.suscribir(lambda: self._mano(ANGULO_MANO_ABIERTA))
        self.mano_cerrar.suscribir(lambda: self._mano(ANGULO_MANO_CERRADA))

    # --- API hacia afuera ---

    def suscribir_comando(self, callback):
        """
        Anota un callback que recibirá cada comando que el gamepad genere.

        Uso típico (en main.py):
            gamepad.suscribir_comando(conexion.enviar_mensaje)
        """
        self._suscriptores_comando.append(callback)

    def habilitar(self, activo: bool):
        """
        Enciende/apaga el gamepad según haya conexión o no.

        Sin conexión no se debe construir ningún comando (así los botones
        y deslizadores se vuelven inofensivos por diseño, no solo visual).
        """
        self.habilitado = activo

    # --- Internos ---

    def _emitir(self, comando: dict):
        """Avisa a todos los suscriptores que hay un comando nuevo."""
        if not self.habilitado:
            return  # sin robot conectado, los comandos no salen
        for callback in self._suscriptores_comando:
            callback(comando)

    def _servir_movimiento(self, servo: str, evento: MovimientoDeslizador):
        """
        Traduce un movimiento de deslizador a un comando servo.

        Se emite solo si el movimiento fue válido (evento.valido), porque
        los ángulos fuera de rango no deben ir al robot (el firmware los
        rechazaría de todos modos).
        """
        if evento.valido:
            self._emitir({"tipo": "servo", "servo": servo, "angulo": int(evento.posicion)})

    def _mano(self, angulo: int):
        """Abre o cierra la pinza: ambos pulgares al mismo ángulo."""
        self._emitir({"tipo": "servo", "servo": "pulgar_izquierdo", "angulo": angulo})
        self._emitir({"tipo": "servo", "servo": "pulgar_derecho", "angulo": angulo})

    def _reposo(self):
        """
        Vuelve a posición neutra: cuello y hombros a 0° (las manos no, que
        no sostienen carga y dependen de la decisión del operador).
        """
        reposiciones = {
            "cuello": 0,
            "hombro_izquierdo": 0,
            "hombro_derecho": 0,
        }
        for servo, angulo in reposiciones.items():
            self._emitir({"tipo": "servo", "servo": servo, "angulo": angulo})


# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.widgets.logica.gamepad

if __name__ == "__main__":
    print("Prueba gamepad.py\n")

    estado = EstadoRobot()
    gamepad = Gamepad(estado)

    comandos = []
    gamepad.suscribir_comando(lambda comando: comandos.append(comando))

    # 1. Dirección -> comando motor
    print("=== Dirección ===")
    gamepad.direccion_arriba.presionar()
    assert comandos[-1] == {"tipo": "motor", "direccion": "arriba"}, \
        "Presionar ARRIBA debería emitir comando motor arriba"
    print(f"OK: {comandos[-1]}\n")

    # 2. Slider del cuello -> comando servo (solo en rango)
    print("=== Cuello ===")
    gamepad.cuello.mover(30)
    assert comandos[-1] == {"tipo": "servo", "servo": "cuello", "angulo": 30}, \
        "Mover cuello a 30 debería emitir comando servo"
    gamepad.cuello.mover(500)  # fuera de rango: NO debe emitirse
    assert len(comandos) == 2, "Un movimiento fuera de rango no debe emitirse"
    print(f"OK: emitido {comandos[-1]}; el 500 fuera de rango no entró\n")

    # 3. Manos -> comando servo para ambos pulgares
    print("=== Mano abrir ===")
    gamepad.mano_abrir.presionar()
    assert comandos[-2] == {"tipo": "servo", "servo": "pulgar_izquierdo", "angulo": 22}
    assert comandos[-1] == {"tipo": "servo", "servo": "pulgar_derecho", "angulo": 22}
    print(f"OK: {comandos[-2]} y {comandos[-1]}\n")

    # 4. Reposo -> cuello y hombros a 0°
    print("=== Reposo ===")
    gamepad.reposo.presionar()
    reposo = comandos[-3:]
    assert all(c["angulo"] == 0 for c in reposo), "Reposo debe mandar 0°"
    assert all(c["tipo"] == "servo" for c in reposo), "Reposo solo envía servos"
    print(f"OK: reposo -> {[c['servo'] for c in reposo]}\n")

    # 5. Sin conexión: el gamepad ignora todo
    print("=== Deshabilitado (sin conexión) ===")
    n = len(comandos)
    gamepad.habilitar(False)
    gamepad.direccion_arriba.presionar()
    gamepad.cuello.mover(10)
    gamepad.mano_abrir.presionar()
    assert len(comandos) == n, "Sin conexión no debe emitirse ningún comando"
    print("OK: los comandos se descartan sin conexión\n")

    # 6. Al habilitar, vuelve a emitir normal
    print("=== Rehabilitado ===")
    gamepad.habilitar(True)
    gamepad.direccion_abajo.presionar()
    assert comandos[-1] == {"tipo": "motor", "direccion": "abajo"}, \
        "Al re-habilitar, los comandos deben volver a salir"
    print(f"OK: {comandos[-1]}\n")

    print("Pruebas OK")
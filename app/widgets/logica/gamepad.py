# wall-e-robot/app/widgets/logica/gamepad.py
# Kevin Gámez - 13/09/2026


from ...nucleo.estado import EstadoRobot
from ...nucleo.paleta import Paleta
from .boton import Boton
from .deslizador import Deslizador, MovimientoDeslizador


RANGO_CUELLO = (-70, 70)
RANGO_HOMBRO = (-50, 50)
ANGULO_MANO_ABIERTA = 22
ANGULO_MANO_CERRADA = -22


class Gamepad:
    """Composición de controles manuales que genera comandos para el movimiento y articulaciones del robot."""
    def __init__(self, estado: EstadoRobot):
        self.estado = estado
        self.habilitado = True
        self._suscriptores_comando = []

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

    def suscribir_comando(self, callback):
        self._suscriptores_comando.append(callback)

    def habilitar(self, activo: bool):
        self.habilitado = activo

    def _emitir(self, comando: dict):
        if not self.habilitado:
            return
        for callback in self._suscriptores_comando:
            callback(comando)

    def _servir_movimiento(self, servo: str, evento: MovimientoDeslizador):
        if evento.valido:
            self._emitir({"tipo": "servo", "servo": servo, "angulo": int(evento.posicion)})

    def _mano(self, angulo: int):
        self._emitir({
            "tipo": "multi",
            "comandos": [
                {"tipo": "servo", "servo": "pulgar_izquierdo", "angulo": angulo},
                {"tipo": "servo", "servo": "pulgar_derecho", "angulo": angulo},
            ],
        })

    def _reposo(self):
        self.cuello.posicion = 0
        self.hombro_izquierdo.posicion = 0
        self.hombro_derecho.posicion = 0

        self._emitir({
            "tipo": "multi",
            "comandos": [
                {"tipo": "servo", "servo": "cuello", "angulo": 0},
                {"tipo": "servo", "servo": "hombro_izquierdo", "angulo": 0},
                {"tipo": "servo", "servo": "hombro_derecho", "angulo": 0},
            ],
        })

# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.logica.gamepad

if __name__ == "__main__":
    print("Prueba gamepad.py\n")

    estado = EstadoRobot()
    gamepad = Gamepad(estado)

    comandos = []
    gamepad.suscribir_comando(lambda comando: comandos.append(comando))

    print("Dirección")
    gamepad.direccion_arriba.presionar()
    assert comandos[-1] == {"tipo": "motor", "direccion": "arriba"}
    print(f"OK: {comandos[-1]}\n")

    print("=== Cuello ===")
    gamepad.cuello.mover(30)
    assert comandos[-1] == {"tipo": "servo", "servo": "cuello", "angulo": 30}
    gamepad.cuello.mover(500)
    assert len(comandos) == 2
    print(f"OK: emitido {comandos[-1]}; el 500 fuera de rango no entró\n")

    print("Mano abrir (multi)")
    gamepad.mano_abrir.presionar()
    assert comandos[-1] == {
        "tipo": "multi",
        "comandos": [
            {"tipo": "servo", "servo": "pulgar_izquierdo", "angulo": 22},
            {"tipo": "servo", "servo": "pulgar_derecho", "angulo": 22},
        ],
    }
    print(f"OK: {comandos[-1]['tipo']} con {len(comandos[-1]['comandos'])} servos\n")

    print("Reposo (multi)")
    gamepad.cuello.mover(30)
    gamepad.hombro_izquierdo.mover(-20)
    gamepad.hombro_derecho.mover(20)
    gamepad.reposo.presionar()
    reposo = comandos[-1]
    assert reposo["tipo"] == "multi"
    assert all(c["angulo"] == 0 for c in reposo["comandos"])
    assert all(c["tipo"] == "servo" for c in reposo["comandos"])
    servos_reposo = [c["servo"] for c in reposo["comandos"]]
    assert servos_reposo == ["cuello", "hombro_izquierdo", "hombro_derecho"]
    assert gamepad.cuello.posicion == 0 and gamepad.hombro_izquierdo.posicion == 0 \
        and gamepad.hombro_derecho.posicion == 0
    print(f"OK: reposo -> {servos_reposo} y sliders al centro\n")

    print("Deshabilitado (sin conexión)")
    n = len(comandos)
    gamepad.habilitar(False)
    gamepad.direccion_arriba.presionar()
    gamepad.cuello.mover(10)
    gamepad.mano_abrir.presionar()
    assert len(comandos) == n
    print("OK: los comandos se descartan sin conexión\n")

    print("Rehabilitado")
    gamepad.habilitar(True)
    gamepad.direccion_abajo.presionar()
    assert comandos[-1] == {"tipo": "motor", "direccion": "abajo"}
    print(f"OK: {comandos[-1]}\n")

    print("Pruebas OK")
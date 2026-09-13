# wall-e-robot/app/widgets/logica/ojos.py
# Kevin Gámez - 13/09/2026


from enum import Enum
from ...nucleo.estado import EstadoRobot, Modo
from ...nucleo.paleta import Paleta


class ExpresionOjos(Enum):
    """
    Las expresiones que puede tener Wall-E en los ojos.

    La silueta de los ojos cambia además del color (a diferencia de los
    demás íconos). Estas 4 expresiones son las que define el plan de diseño:
      NORMAL    - todo bien, modo automático
      MANUAL    - alguien lo está controlando
      OBSTACULO - un objeto está demasiado cerca
      SIN_DATOS - sin conexión / sin información del sensor
    """

    NORMAL = "normal"
    MANUAL = "manual"
    OBSTACULO = "obstaculo"
    SIN_DATOS = "sin_datos"


# Distancia (en cm) por debajo de la cual los ojos se ponen en alerta.
# Valor de arranque, pendiente de calibrar con el sensor real (igual que el
# umbral de obstáculo del modo automático en el firmware).
UMBRAL_OBSTACULO_CM = 15.0


class Ojos:
    """
    Los ojos de Wall-E: el widget "emocional" del robot.

    Es LÓGICA PURA: decide QUÉ expresión debe mostrarse según el estado del
    robot (modo, distancia, conexión), pero no sabe cómo se dibuja un ojo.
    El renderer (widgets/renderizado/ojos_render.py) se encarga del resto.

    Nota de diseño: por ahora la silueta es la base del mockup. La idea de
    hacer los ojos "realistas" (como los de la película) queda pendiente y
    se implementa solo cambiando el renderer, sin tocar esta lógica.
    """

    def __init__(self, estado: EstadoRobot):
        """
        Constructor de los ojos.

        estado: la 'caja maestra' (EstadoRobot). Solo se lee de ahí.
        """
        self.estado = estado

    @property
    def expresion(self) -> ExpresionOjos:
        """La expresión actual, calculada de lo que dice el estado."""
        # 1. Sin información de conexión -> ojos "muertos"/sin datos.
        if not self.estado.conexion_activa:
            return ExpresionOjos.SIN_DATOS

        # 2. Modo manual tiene prioridad sobre un obstáculo lejano:
        #    el operador tiene el control.
        if self.estado.modo == Modo.MANUAL:
            return ExpresionOjos.MANUAL

        # 3. Obstáculo cerca (solo si ya hay un dato de distancia).
        if (self.estado.distancia_obstaculo_cm is not None
                and self.estado.distancia_obstaculo_cm < UMBRAL_OBSTACULO_CM):
            return ExpresionOjos.OBSTACULO

        # 4. Ninguna condición especial -> todo normal.
        return ExpresionOjos.NORMAL

    @property
    def color(self) -> str:
        """El color de los ojos según la expresión actual."""
        colores = {
            ExpresionOjos.NORMAL:    Paleta.DORADO,
            ExpresionOjos.MANUAL:    Paleta.NARANJA,
            ExpresionOjos.OBSTACULO: Paleta.ROJO,
            ExpresionOjos.SIN_DATOS: Paleta.GRIS,
        }
        return colores[self.expresion]

    @property
    def descripcion(self) -> str:
        """Texto legible de la expresión (útil para tooltips/logs)."""
        return self.expresion.value


# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.widgets.logica.ojos

if __name__ == "__main__":
    print("Prueba ojos.py\n")

    estado = EstadoRobot()
    ojos = Ojos(estado)

    # 1. Estado inicial (conectado, automático, sin obstáculo) -> NORMAL
    print("=== Conexión activa, automático, sin obstáculo ===")
    estado.conexion_activa = True
    estado.modo = Modo.AUTOMATICO
    estado.distancia_obstaculo_cm = 80.0
    assert ojos.expresion == ExpresionOjos.NORMAL, "Debería ser NORMAL"
    assert ojos.color == Paleta.DORADO, "NORMAL debería ser DORADO"
    print(f"OK: {ojos.descripcion} / {ojos.color}\n")

    # 2. Modo manual -> MANUAL (aunque haya un obstáculo, prioridad del operador)
    print("=== Modo manual, obstáculo cerca ===")
    estado.modo = Modo.MANUAL
    estado.distancia_obstaculo_cm = 5.0
    assert ojos.expresion == ExpresionOjos.MANUAL, "Manual tiene prioridad"
    assert ojos.color == Paleta.NARANJA, "MANUAL debería ser NARANJA"
    print(f"OK: {ojos.descripcion} / {ojos.color}\n")

    # 3. Automático + obstáculo cerca -> OBSTACULO
    print("=== Automático, obstáculo a 8cm ===")
    estado.modo = Modo.AUTOMATICO
    estado.distancia_obstaculo_cm = 8.0
    assert ojos.expresion == ExpresionOjos.OBSTACULO, "8cm < 15 -> OBSTACULO"
    assert ojos.color == Paleta.ROJO, "OBSTACULO debería ser ROJO"
    print(f"OK: {ojos.descripcion} / {ojos.color}\n")

    # 4. Sin conexión -> SIN_DATOS (aunque el resto diga otra cosa)
    print("=== Sin conexión ===")
    estado.conexion_activa = False
    assert ojos.expresion == ExpresionOjos.SIN_DATOS, "Sin conexión -> SIN_DATOS"
    assert ojos.color == Paleta.GRIS, "SIN_DATOS debería ser GRIS"
    print(f"OK: {ojos.descripcion} / {ojos.color}\n")

    # 5. Sin dato de distancia pero conectado -> NORMAL (no es obstáculo)
    print("=== Conectado pero sin dato de distancia ===")
    estado.conexion_activa = True
    estado.modo = Modo.AUTOMATICO
    estado.distancia_obstaculo_cm = None
    assert ojos.expresion == ExpresionOjos.NORMAL, "None no es obstáculo"
    print(f"OK: {ojos.descripcion}\n")

    print("Pruebas OK")
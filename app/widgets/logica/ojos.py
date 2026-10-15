# wall-e-robot/app/widgets/logica/ojos.py
# Kevin Gámez - 13/09/2026


from enum import Enum
from ...nucleo.estado import EstadoRobot, Modo
from ...nucleo.paleta import Paleta


class ExpresionOjos(Enum):
    """Expresiones visuales de los ojos según el estado del robot."""
    NORMAL = "normal"
    MANUAL = "manual"
    OBSTACULO = "obstaculo"
    SIN_DATOS = "sin_datos"
    ERROR = "error"


UMBRAL_OBSTACULO_CM = 15.0


class Ojos:
    """Determina la expresión de los ojos en función del estado del robot (conexión, modo y distancia)."""
    def __init__(self, estado: EstadoRobot):
        self.estado = estado

    @property
    def expresion(self) -> ExpresionOjos:
        if not self.estado.conexion_activa:
            return ExpresionOjos.SIN_DATOS

        if self.estado.hay_error:
            return ExpresionOjos.ERROR

        if self.estado.modo == Modo.MANUAL:
            return ExpresionOjos.MANUAL

        if (self.estado.distancia_obstaculo_cm is not None
                and self.estado.distancia_obstaculo_cm < UMBRAL_OBSTACULO_CM):
            return ExpresionOjos.OBSTACULO

        return ExpresionOjos.NORMAL

    @property
    def color(self) -> str:
        colores = {
            ExpresionOjos.NORMAL:    Paleta.DORADO,
            ExpresionOjos.MANUAL:    Paleta.NARANJA,
            ExpresionOjos.OBSTACULO: Paleta.ROJO,
            ExpresionOjos.SIN_DATOS: Paleta.GRIS,
            ExpresionOjos.ERROR:     Paleta.ROJO,
        }
        return colores[self.expresion]

    @property
    def descripcion(self) -> str:
        return self.expresion.value

# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.logica.ojos

if __name__ == "__main__":
    print("Prueba ojos.py\n")

    estado = EstadoRobot()
    ojos = Ojos(estado)

    print("Conexión activa, automático, sin obstáculo")
    estado.conexion_activa = True
    estado.modo = Modo.AUTOMATICO
    estado.distancia_obstaculo_cm = 80.0
    assert ojos.expresion == ExpresionOjos.NORMAL
    assert ojos.color == Paleta.DORADO
    print(f"OK: {ojos.descripcion} / {ojos.color}\n")

    print("Modo manual, obstáculo cerca")
    estado.modo = Modo.MANUAL
    estado.distancia_obstaculo_cm = 5.0
    assert ojos.expresion == ExpresionOjos.MANUAL
    assert ojos.color == Paleta.NARANJA
    print(f"OK: {ojos.descripcion} / {ojos.color}\n")

    print("Automático, obstáculo a 8cm")
    estado.modo = Modo.AUTOMATICO
    estado.distancia_obstaculo_cm = 8.0
    assert ojos.expresion == ExpresionOjos.OBSTACULO
    assert ojos.color == Paleta.ROJO
    print(f"OK: {ojos.descripcion} / {ojos.color}\n")

    print("Sin conexión")
    estado.conexion_activa = False
    assert ojos.expresion == ExpresionOjos.SIN_DATOS
    assert ojos.color == Paleta.GRIS
    print(f"OK: {ojos.descripcion} / {ojos.color}\n")

    print("Error crítico (batería)")
    estado.conexion_activa = True
    estado.modo = Modo.AUTOMATICO
    estado.hay_error = True
    assert ojos.expresion == ExpresionOjos.ERROR
    assert ojos.color == Paleta.ROJO
    print(f"OK: {ojos.descripcion} / {ojos.color}\n")

    print("Error pesa más que manual y obstáculo")
    estado.modo = Modo.MANUAL
    estado.distancia_obstaculo_cm = 3.0
    assert ojos.expresion == ExpresionOjos.ERROR
    print(f"OK: {ojos.descripcion}\n")

    print("Sin conexión pesa más que error")
    estado.conexion_activa = False
    assert ojos.expresion == ExpresionOjos.SIN_DATOS
    print(f"OK: {ojos.descripcion}\n")

    estado.conexion_activa = True
    estado.hay_error = False
    estado.modo = Modo.AUTOMATICO

    print("Conectado pero sin dato de distancia")
    estado.conexion_activa = True
    estado.modo = Modo.AUTOMATICO
    estado.distancia_obstaculo_cm = None
    assert ojos.expresion == ExpresionOjos.NORMAL
    print(f"OK: {ojos.descripcion}\n")

    print("Pruebas OK")
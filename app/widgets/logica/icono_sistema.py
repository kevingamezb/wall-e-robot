# wall-e-robot/app/widgets/logica/icono_sistema.py
# Kevin Gámez - 13/09/2026


from enum import Enum
from ...nucleo.estado import EstadoRobot, Modo
from ...nucleo.paleta import Paleta


class TipoIcono(Enum):
    """Identificadores de los iconos de sistema definidos en el mockup."""
    ADVERTENCIA = "advertencia"
    CARGANDO    = "cargando"
    MODO_MANUAL = "modo_manual"
    ERROR       = "error"
    CONEXION    = "conexion"


class IconoSistema:
    """Determina el estado de activación y color de un icono de sistema según el estado del robot."""
    def __init__(self, estado: EstadoRobot, tipo: TipoIcono):
        self.estado = estado
        self.tipo = tipo

    @property
    def activo(self) -> bool:
        activadores = {
            TipoIcono.ADVERTENCIA: self.estado.hay_advertencia,
            TipoIcono.CARGANDO:    self.estado.cargando,
            TipoIcono.MODO_MANUAL: self.estado.modo == Modo.MANUAL,
            TipoIcono.ERROR:       self.estado.hay_error,
            TipoIcono.CONEXION:    self.estado.conexion_activa,
        }
        return activadores[self.tipo]

    @property
    def color(self) -> str:
        if not self.activo:
            return Paleta.GRIS

        colores = {
            TipoIcono.ADVERTENCIA: Paleta.NARANJA,
            TipoIcono.CARGANDO:    Paleta.VERDE_LIMA,
            TipoIcono.MODO_MANUAL: Paleta.AXIOM_CYAN,
            TipoIcono.ERROR:       Paleta.ROJO,
            TipoIcono.CONEXION:    Paleta.AXIOM_CYAN,
        }
        return colores[self.tipo]

    @property
    def titulo(self) -> str:
        return self.tipo.value

# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.logica.icono_sistema

if __name__ == "__main__":
    print("Prueba icono_sistema.py\n")

    estado = EstadoRobot()
    iconos = {tipo: IconoSistema(estado, tipo) for tipo in TipoIcono}

    print("Estado inicial")
    estado.conexion_activa = True
    assert iconos[TipoIcono.CONEXION].activo
    assert iconos[TipoIcono.CONEXION].color == Paleta.AXIOM_CYAN
    assert not iconos[TipoIcono.ADVERTENCIA].activo
    assert iconos[TipoIcono.ADVERTENCIA].color == Paleta.GRIS
    assert not iconos[TipoIcono.MODO_MANUAL].activo
    print("OK: solo CONEXION activa\n")

    print("Advertencia + error")
    estado.hay_advertencia = True
    estado.hay_error = True
    assert iconos[TipoIcono.ADVERTENCIA].activo
    assert iconos[TipoIcono.ADVERTENCIA].color == Paleta.NARANJA
    assert iconos[TipoIcono.ERROR].activo
    assert iconos[TipoIcono.ERROR].color == Paleta.ROJO
    print("OK: ADVERTENCIA naranja, ERROR rojo\n")

    print("Manual + cargando")
    estado.modo = Modo.MANUAL
    estado.cargando = True
    assert iconos[TipoIcono.MODO_MANUAL].activo
    assert iconos[TipoIcono.MODO_MANUAL].color == Paleta.AXIOM_CYAN
    assert iconos[TipoIcono.CARGANDO].activo
    assert iconos[TipoIcono.CARGANDO].color == Paleta.VERDE_LIMA
    print("OK: MODO_MANUAL cian, CARGANDO verde lima\n")

    print("Pruebas OK")
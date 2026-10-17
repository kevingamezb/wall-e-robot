# wall-e-robot/app/widgets/logica/icono_sistema.py
# Kevin Gámez - 13/09/2026


from enum import Enum
from ...nucleo.estado import EstadoRobot, Modo, NivelConexion
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
            # Un módulo inactivo (config incompleta) también enciende el error.
            TipoIcono.ERROR:       self.estado.hay_error or self.estado.modulo_inactivo,
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

    @property
    def archivo(self) -> str:
        """Nombre (sin extensión) del PNG del recurso para este ícono."""
        if self.tipo == TipoIcono.CONEXION:
            # No hay recurso para NULA: se reutiliza el de conectividad alta.
            return {
                NivelConexion.ALTA:  "conectividad_alta",
                NivelConexion.MEDIA: "conectividad_media",
                NivelConexion.BAJA:  "conectividad_baja",
                NivelConexion.NULA:  "conectividad_alta",
            }[self.estado.nivel_conexion]

        return {
            TipoIcono.ADVERTENCIA: "advertencia",
            TipoIcono.CARGANDO:    "cargando",
            TipoIcono.MODO_MANUAL: "controlador",
            TipoIcono.ERROR:       "error",
        }[self.tipo]

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

    print("Módulo inactivo enciende ERROR")
    estado.hay_error = False
    estado.modulo_inactivo = True
    assert iconos[TipoIcono.ERROR].activo, "Un módulo inactivo debe encender ERROR"
    assert iconos[TipoIcono.ERROR].color == Paleta.ROJO
    estado.modulo_inactivo = False
    assert not iconos[TipoIcono.ERROR].activo
    print("OK: config incompleta -> ícono ERROR\n")

    print("Recursos por tipo")
    estado.nivel_conexion = NivelConexion.ALTA
    assert iconos[TipoIcono.ADVERTENCIA].archivo == "advertencia"
    assert iconos[TipoIcono.CARGANDO].archivo == "cargando"
    assert iconos[TipoIcono.MODO_MANUAL].archivo == "controlador"
    assert iconos[TipoIcono.ERROR].archivo == "error"
    assert iconos[TipoIcono.CONEXION].archivo == "conectividad_alta"
    estado.nivel_conexion = NivelConexion.MEDIA
    assert iconos[TipoIcono.CONEXION].archivo == "conectividad_media"
    estado.nivel_conexion = NivelConexion.BAJA
    assert iconos[TipoIcono.CONEXION].archivo == "conectividad_baja"
    print("OK: cada ícono apunta a su PNG\n")

    print("Pruebas OK")
# wall-e-robot/app/widgets/logica/icono_sistema.py
# Kevin Gámez - 13/09/2026


from enum import Enum
from ...nucleo.estado import EstadoRobot, Modo
from ...nucleo.paleta import Paleta


class TipoIcono(Enum):
    """Los 5 íconos de sistema del mockup: una instancia por cada uno."""

    ADVERTENCIA = "advertencia"
    CARGANDO    = "cargando"
    MODO_MANUAL = "modo_manual"
    ERROR       = "error"
    CONEXION    = "conexion"


class IconoSistema:
    """
    Un ícono de sistema individual.

    A diferencia de los ojos, estos íconos cambian SOLO de color (la forma
    es siempre la misma). El plan de diseño lo llama "recoloreo": la forma
    no cambia, lo que cambia es qué color tiene según el estado del robot.

    Es LÓGICA PURA: responde si el ícono está ACTIVO (on/off) y de qué color,
    pero no sabe cómo dibujarlo. El renderer dibuja el glifo correspondiente.

    Colores por ícono activo (definidos aquí, de acuerdo al tema Axiom):
      ADVERTENCIA -> NARANJA     ERROR       -> ROJO
      CARGANDO    -> VERDE_LIMA  CONEXION    -> AXIOM_CYAN (holograma de la nave)
      MODO_MANUAL -> AXIOM_CYAN
    Inactivo -> GRIS (apagado).
    """

    def __init__(self, estado: EstadoRobot, tipo: TipoIcono):
        """
        Constructor de un ícono.

        estado: la 'caja maestra' (EstadoRobot). Solo se lee de ahí.
        tipo:   cuál de los 5 íconos es este (TipoIcono).
        """
        self.estado = estado
        self.tipo = tipo

    @property
    def activo(self) -> bool:
        """Si este ícono debe verse encendido, según el estado del robot."""
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
        """Color del ícono activo (GRIS si está inactivo)."""
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
        """Texto legible del ícono (útil como tooltip)."""
        return self.tipo.value


# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.widgets.logica.icono_sistema

if __name__ == "__main__":
    print("Prueba icono_sistema.py\n")

    estado = EstadoRobot()
    iconos = {tipo: IconoSistema(estado, tipo) for tipo in TipoIcono}

    # 1. Estado inicial (conectado, automático, sin alertas)
    #    Solo CONEXION activa; el resto apagado.
    print("=== Estado inicial ===")
    estado.conexion_activa = True
    assert iconos[TipoIcono.CONEXION].activo, "Conectado -> CONEXION activo"
    assert iconos[TipoIcono.CONEXION].color == Paleta.AXIOM_CYAN
    assert not iconos[TipoIcono.ADVERTENCIA].activo, "Sin advertencia -> apagado"
    assert iconos[TipoIcono.ADVERTENCIA].color == Paleta.GRIS
    assert not iconos[TipoIcono.MODO_MANUAL].activo, "Automático -> manual apagado"
    print("OK: solo CONEXION activa\n")

    # 2. Advertencia y error
    print("=== Advertencia + error ===")
    estado.hay_advertencia = True
    estado.hay_error = True
    assert iconos[TipoIcono.ADVERTENCIA].activo
    assert iconos[TipoIcono.ADVERTENCIA].color == Paleta.NARANJA
    assert iconos[TipoIcono.ERROR].activo
    assert iconos[TipoIcono.ERROR].color == Paleta.ROJO
    print("OK: ADVERTENCIA naranja, ERROR rojo\n")

    # 3. Modo manual + cargando a la vez
    print("=== Manual + cargando ===")
    estado.modo = Modo.MANUAL
    estado.cargando = True
    assert iconos[TipoIcono.MODO_MANUAL].activo
    assert iconos[TipoIcono.MODO_MANUAL].color == Paleta.AXIOM_CYAN
    assert iconos[TipoIcono.CARGANDO].activo
    assert iconos[TipoIcono.CARGANDO].color == Paleta.VERDE_LIMA
    print("OK: MODO_MANUAL cian, CARGANDO verde lima\n")

    print("Pruebas OK")
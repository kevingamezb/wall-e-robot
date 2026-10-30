# wall-e-robot/app/widgets/logica/sol_bateria.py
# Kevin Gámez - 13/09/2026


from ...nucleo.estado import EstadoRobot
from ...nucleo.paleta import Paleta


class SolBateria:
    """Representa el nivel de batería mediante los rayos del sol y proporciona color y etiqueta para su renderizado."""
    TOTAL_RAYOS = 8
    # Sin cargar: 0 rayos gris, 1-2 rojo, 3-5 naranja y de 6 en adelante dorado.
    UMBRAL_ROJO = 2
    UMBRAL_NARANJA = 5

    def __init__(self, estado: EstadoRobot):
        self.estado = estado

    @property
    def sin_datos(self) -> bool:
        """Sin conexión no hay lectura de batería: el sol queda gris e inerte."""
        return not self.estado.conexion_activa

    @property
    def rayos_encendidos(self) -> int:
        # Sin datos (o cargando) el sol se dibuja lleno; el color dice el resto.
        if self.sin_datos or self.estado.cargando:
            return self.TOTAL_RAYOS
        return round(self.estado.bateria * self.TOTAL_RAYOS)

    @property
    def color(self) -> str:
        if self.sin_datos:
            return Paleta.GRIS
        if self.estado.cargando:
            return Paleta.VERDE_LIMA

        if self.rayos_encendidos <= 0:
            return Paleta.GRIS
        elif self.rayos_encendidos <= self.UMBRAL_ROJO:
            return Paleta.ROJO
        elif self.rayos_encendidos <= self.UMBRAL_NARANJA:
            return Paleta.NARANJA
        else:
            return Paleta.DORADO

    @property
    def etiqueta(self) -> str:
        if self.sin_datos:
            return "sin datos"
        if self.estado.cargando:
            return "cargando"
        return f"{self.rayos_encendidos} / {self.TOTAL_RAYOS}"

    @property
    def tiempo_restante_min(self) -> int:
        return self.estado.tiempo_restante_min

# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.logica.sol_bateria

if __name__ == "__main__":
    print("Prueba sol_bateria.py\n")

    estado = EstadoRobot()
    estado.conexion_activa = True   # con robot hay lectura de batería

    print("Batería llena (1.0)")
    sol = SolBateria(estado)
    assert sol.rayos_encendidos == 8
    assert sol.color == Paleta.DORADO
    assert sol.etiqueta == "8 / 8"
    print(f"OK: {sol.etiqueta} / {sol.color}\n")

    print("Batería media (0.5)")
    estado.bateria = 0.5
    assert sol.rayos_encendidos == 4
    assert sol.color == Paleta.NARANJA
    print(f"OK: {sol.etiqueta} / {sol.color}\n")

    print("Batería baja (0.2)")
    estado.bateria = 0.2
    assert sol.rayos_encendidos == 2
    assert sol.color == Paleta.ROJO
    print(f"OK: {sol.etiqueta} / {sol.color}\n")

    print("Cargando")
    estado.bateria = 0.2
    estado.cargando = True
    assert sol.rayos_encendidos == 8
    assert sol.color == Paleta.VERDE_LIMA
    assert sol.etiqueta == "cargando"
    print(f"OK: {sol.etiqueta} / {sol.color}\n")

    print("Sin datos (sin conexión)")
    estado.cargando = False
    estado.bateria = 0.2
    estado.conexion_activa = False
    assert sol.rayos_encendidos == 8
    assert sol.color == Paleta.GRIS
    assert sol.etiqueta == "sin datos"
    print(f"OK: {sol.etiqueta} / {sol.color}, sol lleno pero gris\n")

    print("Pruebas OK")
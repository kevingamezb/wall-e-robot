# wall-e-robot/app/widgets/logica/barras_consumo.py
# Kevin Gámez - 13/09/2026


from ...nucleo.estado import EstadoRobot
from ...nucleo.paleta import Paleta, color_por_umbral


class BarrasConsumo:
    """Determina el número y color de las barras de consumo según la fracción de consumo instantáneo."""

    TOTAL_BARRISTAS = 10

    def __init__(self, estado: EstadoRobot):
        self.estado = estado

    @property
    def fraccion(self) -> float:
        if self.estado.max_consumo_watts <= 0:
            return 0.0
        return self.estado.consumo_watts / self.estado.max_consumo_watts

    @property
    def barritas_encendidas(self) -> int:
        return round(self.fraccion * self.TOTAL_BARRISTAS)

    @property
    def color(self) -> str:
        return color_por_umbral(self.fraccion, invertido=True)

    @property
    def etiqueta_watts(self) -> str:
        return f"{self.estado.consumo_watts:.1f} W"

# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.logica.barras_consumo
if __name__ == "__main__":
    print("Prueba barras_consumo.py\n")

    estado = EstadoRobot()
    barras = BarrasConsumo(estado)

    print("=== Sin consumo (0 W de 15 W) ===")
    estado.consumo_watts = 0.0
    estado.max_consumo_watts = 15.0
    assert barras.fraccion == 0.0
    assert barras.barritas_encendidas == 0
    assert barras.color == Paleta.GRIS
    print(f"OK: {barras.barritas_encendidas}/10, {barras.etiqueta_watts}\n")

    print("=== Consumo medio (4.2 W de 15 W) ===")
    estado.consumo_watts = 4.2
    assert abs(barras.fraccion - 0.28) < 0.001
    assert barras.barritas_encendidas == 3
    assert barras.color == Paleta.DORADO
    print(f"OK: {barras.barritas_encendidas}/10, {barras.etiqueta_watts}\n")

    print("=== Consumo alto (8 W de 15 W) ===")
    estado.consumo_watts = 8.0
    assert barras.barritas_encendidas == 5
    assert barras.color == Paleta.NARANJA
    print(f"OK: {barras.barritas_encendidas}/10, {barras.etiqueta_watts}\n")

    print("=== Consumo máximo (15 W de 15 W) ===")
    estado.consumo_watts = 15.0
    assert barras.barritas_encendidas == 10
    assert barras.color == Paleta.ROJO
    print(f"OK: {barras.barritas_encendidas}/10, {barras.etiqueta_watts}\n")

    print("Pruebas OK")
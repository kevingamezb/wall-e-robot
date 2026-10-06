# wall-e-robot/app/widgets/logica/barras_consumo.py
# Kevin Gámez - 13/09/2026


from ...nucleo.estado import EstadoRobot
from ...nucleo.paleta import Paleta, color_por_umbral


class BarrasConsumo:
    """
    Las barritas de consumo apiladas (estilo lector MoE de la película).

    Mientras más energía consume el robot, más barritas se "encienden".
    Aquí "más es peor": el color lo decide color_por_umbral(fraccion,
    invertido=True), la regla central de paleta.py:

      0.0 - 0.1  -> GRIS (sin actividad: no hay barritas encendidas)
      0.1 - 0.4  -> DORADO (consumo tranquilo)
      0.4 - 0.7  -> NARANJA
      0.7 - 1.0  -> ROJO (consumo alto)

    Es LÓGICA PURA: solo responde cuántas barritas y de qué color.
    El renderer (widgets/renderizado/) es quien las dibuja en Tkinter.
    """

    TOTAL_BARRISTAS = 10  # El mockup dibuja 10 barritas apiladas

    def __init__(self, estado: EstadoRobot):
        """
        Constructor de las barras de consumo.

        estado: la 'caja maestra' (EstadoRobot). Solo se lee de ahí.
        """
        self.estado = estado

    @property
    def fraccion(self) -> float:
        """
        Qué fracción del consumo máximo se está usando (0.0 a 1.0).

        Protección extra: si max_consumo_watts fuera 0 (no debería), se
        devuelve 0.0 para no dividir entre cero.
        """
        if self.estado.max_consumo_watts <= 0:
            return 0.0
        return self.estado.consumo_watts / self.estado.max_consumo_watts

    @property
    def barritas_encendidas(self) -> int:
        """Cuántas de las 10 barritas deben verse encendidas."""
        return round(self.fraccion * self.TOTAL_BARRISTAS)

    @property
    def color(self) -> str:
        """Color de las barritas según la fracción (invertido: más = peor)."""
        return color_por_umbral(self.fraccion, invertido=True)

    @property
    def etiqueta_watts(self) -> str:
        """Texto con el consumo instantáneo en watts, un decimal."""
        return f"{self.estado.consumo_watts:.1f} W"


# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.widgets.logica.barras_consumo

if __name__ == "__main__":
    print("Prueba barras_consumo.py\n")

    estado = EstadoRobot()
    barras = BarrasConsumo(estado)

    # 1. Sin consumo -> fracción 0, sin barritas, sin color
    print("=== Sin consumo (0 W de 15 W) ===")
    estado.consumo_watts = 0.0
    estado.max_consumo_watts = 15.0
    assert barras.fraccion == 0.0, "Fracción debería ser 0.0"
    assert barras.barritas_encendidas == 0, "No debería haber barritas"
    assert barras.color == Paleta.GRIS, "Consumo nulo debería ser GRIS (sin actividad)"
    print(f"OK: {barras.barritas_encendidas}/10, {barras.etiqueta_watts}\n")

    # 2. Consumo medio (4.2 W de 15 W) -> fracción 0.28 -> 3 barritas DORADO
    print("=== Consumo medio (4.2 W de 15 W) ===")
    estado.consumo_watts = 4.2
    assert abs(barras.fraccion - 0.28) < 0.001, "4.2/15 = 0.28"
    assert barras.barritas_encendidas == 3, "round(0.28*10) = 3 barritas"
    assert barras.color == Paleta.DORADO, "0.28 <= 0.4, DORADO"
    print(f"OK: {barras.barritas_encendidas}/10, {barras.etiqueta_watts}\n")

    # 3. Consumo alto (8 W de 15 W) -> fracción 0.53 -> 5 barritas NARANJA
    print("=== Consumo alto (8 W de 15 W) ===")
    estado.consumo_watts = 8.0
    assert barras.barritas_encendidas == 5, "round(0.53*10) = 5 barritas"
    assert barras.color == Paleta.NARANJA, "0.53 > 0.4, NARANJA"
    print(f"OK: {barras.barritas_encendidas}/10, {barras.etiqueta_watts}\n")

    # 4. Consumo máximo (15 W) -> 10 barritas ROJO
    print("=== Consumo máximo (15 W de 15 W) ===")
    estado.consumo_watts = 15.0
    assert barras.barritas_encendidas == 10, "Fracción 1.0 -> 10 barritas"
    assert barras.color == Paleta.ROJO, "Fracción 1.0 > 0.7, ROJO"
    print(f"OK: {barras.barritas_encendidas}/10, {barras.etiqueta_watts}\n")

    print("Pruebas OK")
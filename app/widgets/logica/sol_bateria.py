# wall-e-robot/app/widgets/logica/sol_bateria.py
# Kevin Gámez - 13/09/2026


from ...nucleo.estado import EstadoRobot
from ...nucleo.paleta import Paleta


class SolBateria:
    """
    El "Sol" de batería: la fracción de carga se dibuja como rayos de un sol.

    La metáfora es la del sol de Wall-E: cuando el robot está cargando, el sol
    se "enciende" completo (12 rayos, verde lima); cuando está en batería,
    cada rayo apagado representa la energía gastada.

    Este widget es LÓGICA PURA: no sabe cómo se dibuja. Solo responde las
    preguntas que el renderer necesita:
      - ¿cuántos rayos van encendidos?
      - ¿qué color correspondería?
      - ¿qué etiqueta mostrar?

    Los umbrales de color siguen la referencia visual del mockup (walle_demo.html):
      0 rayos  -> GRIS (sin energía)
      1-4      -> ROJO
      5-7      -> NARANJA
      8-12     -> DORADO
      cargando -> VERDE_LIMA
    """

    TOTAL_RAYOS = 12          # El sol de la película tiene 12 rayos
    UMBRAL_ROJO = 4           # 4/12 y 7/12 son los cortes de color del mockup
    UMBRAL_NARANJA = 7

    def __init__(self, estado: EstadoRobot):
        """
        Constructor del sol.

        estado: la 'caja maestra' (EstadoRobot). El sol SOLO lee de ahí;
        nunca escribe ni se entera de dónde vienen los datos.
        """
        self.estado = estado

    @property
    def rayos_encendidos(self) -> int:
        """
        Cuántos rayos del sol deben verse encendidos.

        Si está cargando, los 12 (el sol está "completo").
        Si no, la fracción de batería redondeada a rayos:
          bateria = 0.66  ->  round(0.66 * 12) = 8 rayos
        """
        if self.estado.cargando:
            return self.TOTAL_RAYOS
        return round(self.estado.bateria * self.TOTAL_RAYOS)

    @property
    def color(self) -> str:
        """El color del sol según el estado (ver umbrales en el docstring).

        Nota de diseño: NO se usa color_por_umbral() de paleta.py. El sol
        dibuja por RAYOS (12, discretos), no por fracción continua: 0 rayos
        = sin energía, 1-4 ROJO, 5-7 NARANJA, 8-12 DORADO. Sus cortes por
        diseño difieren de los de magnitud continua (barras de consumo).
        """
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
        """Texto corto junto al sol: 'cargando' o '8/12'."""
        if self.estado.cargando:
            return "cargando"
        return f"{self.rayos_encendidos}/{self.TOTAL_RAYOS}"

    @property
    def tiempo_restante_min(self) -> int:
        """Minutos estimados de autonomía restantes (leidos de EstadoRobot)."""
        return self.estado.tiempo_restante_min


# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.widgets.logica.sol_bateria

if __name__ == "__main__":
    print("Prueba sol_bateria.py\n")

    estado = EstadoRobot()

    # 1. Estado inicial: batería llena, sin cargar -> 12 rayos, DORADO
    print("=== Batería llena (1.0) ===")
    sol = SolBateria(estado)
    assert sol.rayos_encendidos == 12, "Batería llena debería dar 12 rayos"
    assert sol.color == Paleta.DORADO, "Batería llena debería ser DORADO"
    assert sol.etiqueta == "12/12", "Etiqueta debería decir 12/12"
    print(f"OK: {sol.etiqueta} / {sol.color}\n")

    # 2. Mitad de batería -> 6 rayos, NARANJA
    print("=== Batería media (0.5) ===")
    estado.bateria = 0.5
    assert sol.rayos_encendidos == 6, "0.5*12 = 6 rayos"
    assert sol.color == Paleta.NARANJA, "6 rayos debería ser NARANJA"
    print(f"OK: {sol.etiqueta} / {sol.color}\n")

    # 3. Batería baja -> pocos rayos, ROJO
    print("=== Batería baja (0.2) ===")
    estado.bateria = 0.2
    assert sol.rayos_encendidos == 2, "round(0.2*12) = 2 rayos"
    assert sol.color == Paleta.ROJO, "2 rayos debería ser ROJO"
    print(f"OK: {sol.etiqueta} / {sol.color}\n")

    # 4. Cargando -> 12 rayos VERDE_LIMA
    print("=== Cargando ===")
    estado.bateria = 0.2
    estado.cargando = True
    assert sol.rayos_encendidos == 12, "Cargando enciende los 12 rayos"
    assert sol.color == Paleta.VERDE_LIMA, "Cargando debería ser VERDE_LIMA"
    assert sol.etiqueta == "cargando", "Etiqueta debería decir 'cargando'"
    print(f"OK: {sol.etiqueta} / {sol.color}\n")

    print("Pruebas OK")
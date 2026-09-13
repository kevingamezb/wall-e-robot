# wall-e-robot/app/widgets/logica/radar.py
# Kevin Gámez - 13/09/2026


from ...nucleo.estado import EstadoRobot


# Ángulo de barrido total (en grados): el radar cubre medio círculo (180°).
ANGULO_MAXIMO_BARRIDO = 180
# Cuántos grados avanza el barrido en cada paso (el renderer lo "anima"
# llamando a avanzar() una vez por ciclo de refresco).
PASO_BARRIDO_GRADOS = 2.0


class Radar:
    """
    El radar de barrido (estilo pantalla de la película).

    Lleva la LÓGICA del barrido: en qué ángulo está la "línea radiante"
    ahora mismo y hacia dónde va. Es como un reloj de arena que se llena
    y se vacía: barre de 0° a 180° y vuelve, en un vaivén infinito.

    También responde qué hay que mostrar sobre el obstáculo: la distancia
    leída del EstadoRobot y si está "cerca" (alerta).

    Es LÓGICA PURA: no dibuja. El renderer (`radar_render.py`) avanza el
    barrido llamando a `avanzar()` y pinta la línea en la posición actual.
    """

    def __init__(self, estado: EstadoRobot):
        """
        Constructor del radar.

        estado: la 'caja maestra' (EstadoRobot). Solo se lee de ahí.
        """
        self.estado = estado
        self.angulo = 0.0        # Ángulo actual de la línea de barrido
        self._subiendo = True    # True mientras barre de 0° hacia 180°

    @property
    def distancia_cm(self):
        """La distancia al obstáculo leída del estado (puede ser None)."""
        return self.estado.distancia_obstaculo_cm

    @property
    def hay_obstaculo(self) -> bool:
        """True si ya hay una lectura de distancia (hay algo que mostrar)."""
        return self.estado.distancia_obstaculo_cm is not None

    def avanzar(self):
        """
        Avanza un paso el barrido (y da la vuelta cuando llega al final).

        Cada llamada avanza PASO_BARRIDO_GRADOS. Al llegar a 180° invierte
        la dirección; al llegar a 0° vuelve a subir. Así el radar barre
        todo el frente del robot sin parar.
        """
        if self._subiendo:
            self.angulo += PASO_BARRIDO_GRADOS
            if self.angulo >= ANGULO_MAXIMO_BARRIDO:
                self.angulo = ANGULO_MAXIMO_BARRIDO
                self._subiendo = False
        else:
            self.angulo -= PASO_BARRIDO_GRADOS
            if self.angulo <= 0.0:
                self.angulo = 0.0
                self._subiendo = True


# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.widgets.logica.radar

if __name__ == "__main__":
    print("Prueba radar.py\n")

    estado = EstadoRobot()
    radar = Radar(estado)

    # 1. Arranca barriendo hacia arriba desde 0°
    print("=== Arranque ===")
    assert radar.angulo == 0.0, "El radar arranca en 0°"
    assert radar._subiendo, "Debe barrer en sentido ascendente al inicio"
    assert not radar.hay_obstaculo, "Sin dato de distancia aún"
    print(f"OK: ángulo inicial {radar.angulo}°, sin obstáculo\n")

    # 2. Avanza hasta el tope (180°) y da la vuelta
    print("=== Vaivén completo (0 -> 180 -> 0) ===")
    radar.avanzar()
    assert radar.angulo == PASO_BARRIDO_GRADOS, "Avance de un paso"
    print(f"OK: avanzó a {radar.angulo}°")

    # Forzamos 240 pasos: suficiente para viajar 0->180 y casi volver.
    for _ in range(240):
        radar.avanzar()
    assert 0.0 <= radar.angulo <= 180.0, "El ángulo nunca sale del rango"
    print(f"OK: tras 240 pasos quedó en {radar.angulo}° y está "
          f"{'subiendo' if radar._subiendo else 'bajando'}\n")

    # 3. Distancia: hay obstáculo cuando el estado trae un dato
    print("=== Detección de obstáculo ===")
    estado.distancia_obstaculo_cm = 37.0
    assert radar.hay_obstaculo, "Con distancia hay obstáculo"
    assert radar.distancia_cm == 37.0, "Debe exponer la distancia leída"
    print(f"OK: objeto a {radar.distancia_cm}cm\n")

    # 4. Sin dato de distancia -> no hay obstáculo que mostrar
    print("=== Sin dato de distancia ===")
    estado.distancia_obstaculo_cm = None
    assert not radar.hay_obstaculo, "Sin dato no hay obstáculo"
    print("OK: radar sin detecciones\n")

    print("Pruebas OK")
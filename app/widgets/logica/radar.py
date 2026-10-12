# wall-e-robot/app/widgets/logica/radar.py
# Kevin Gámez - 13/09/2026


from ...nucleo.estado import EstadoRobot


ANGULO_MAXIMO_BARRIDO = 180
PASO_BARRIDO_GRADOS = 2.0


class Radar:
    """Gestiona el barrido angular del radar y la exposición de la distancia detectada."""

    def __init__(self, estado: EstadoRobot):
        self.estado = estado
        self.angulo = 0.0
        self._subiendo = True

    @property
    def distancia_cm(self):
        return self.estado.distancia_obstaculo_cm

    @property
    def hay_obstaculo(self) -> bool:
        return self.estado.distancia_obstaculo_cm is not None

    def avanzar(self):
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
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.logica.radar
if __name__ == "__main__":
    print("Prueba radar.py\n")

    estado = EstadoRobot()
    radar = Radar(estado)

    print("=== Arranque ===")
    assert radar.angulo == 0.0
    assert radar._subiendo
    assert not radar.hay_obstaculo
    print(f"OK: ángulo inicial {radar.angulo}°, sin obstáculo\n")

    print("=== Vaivén completo (0 -> 180 -> 0) ===")
    radar.avanzar()
    assert radar.angulo == PASO_BARRIDO_GRADOS
    print(f"OK: avanzó a {radar.angulo}°")

    for _ in range(240):
        radar.avanzar()
    assert 0.0 <= radar.angulo <= 180.0
    print(f"OK: tras 240 pasos quedó en {radar.angulo}° y está "
          f"{'subiendo' if radar._subiendo else 'bajando'}\n")

    print("=== Detección de obstáculo ===")
    estado.distancia_obstaculo_cm = 37.0
    assert radar.hay_obstaculo
    assert radar.distancia_cm == 37.0
    print(f"OK: objeto a {radar.distancia_cm}cm\n")

    print("=== Sin dato de distancia ===")
    estado.distancia_obstaculo_cm = None
    assert not radar.hay_obstaculo
    print("OK: radar sin detecciones\n")

    print("Pruebas OK")
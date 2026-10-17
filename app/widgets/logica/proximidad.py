# wall-e-robot/app/widgets/logica/proximidad.py
# Kevin Gámez - 13/10/2026


from ...nucleo.estado import EstadoRobot


# Distancia (cm) que se mapea al borde exterior del medidor.
RANGO_MAX_CM = 200


class Proximidad:
    """Traduce la distancia al obstáculo en una fracción de cercanía (0-1)."""
    def __init__(self, estado: EstadoRobot):
        self.estado = estado

    @property
    def distancia_cm(self):
        return self.estado.distancia_obstaculo_cm

    @property
    def hay_obstaculo(self) -> bool:
        """True si hay lectura, aunque el objeto esté lejos del sensor."""
        return self.estado.distancia_obstaculo_cm is not None

    @property
    def cercania(self) -> float:
        """0.0 = sin lectura o muy lejos; 1.0 = pegado al sensor."""
        if self.estado.distancia_obstaculo_cm is None:
            return 0.0
        distancia = max(0.0, float(self.estado.distancia_obstaculo_cm))
        return 1.0 - min(distancia, RANGO_MAX_CM) / RANGO_MAX_CM

    @property
    def etiqueta(self) -> str:
        if self.estado.distancia_obstaculo_cm is None:
            return "SIN LECTURA"
        return f"{self.estado.distancia_obstaculo_cm:.0f} cm"

# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.logica.proximidad

if __name__ == "__main__":
    print("Prueba proximidad.py\n")

    estado = EstadoRobot()
    prox = Proximidad(estado)

    print("Sin lectura")
    assert not prox.hay_obstaculo
    assert prox.cercania == 0.0
    assert prox.etiqueta == "SIN LECTURA"
    print(f"OK: {prox.etiqueta}, cercania={prox.cercania}\n")

    print("Objeto lejos (150 cm)")
    estado.distancia_obstaculo_cm = 150.0
    assert prox.hay_obstaculo
    assert abs(prox.cercania - 0.25) < 0.001
    assert prox.etiqueta == "150 cm"
    print(f"OK: {prox.etiqueta}, cercania={prox.cercania:.2f}\n")

    print("Objeto medio (100 cm)")
    estado.distancia_obstaculo_cm = 100.0
    assert abs(prox.cercania - 0.5) < 0.001
    print(f"OK: {prox.etiqueta}, cercania={prox.cercania:.2f}\n")

    print("Objeto pegado (0 cm)")
    estado.distancia_obstaculo_cm = 0.0
    assert prox.cercania == 1.0
    print(f"OK: {prox.etiqueta}, cercania={prox.cercania}\n")

    print("Objeto fuera de rango (250 cm) se recorta a 0")
    estado.distancia_obstaculo_cm = 250.0
    assert prox.cercania == 0.0
    print(f"OK: {prox.etiqueta}, cercania={prox.cercania}\n")

    print("Pruebas OK")

# wall-e-robot/app/widgets/logica/deslizador.py
# Kevin Gámez - 28/08/2026


class MovimientoDeslizador:
    """Contiene la posición solicitada y la validez de un intento de desplazamiento del deslizador."""
    def __init__(self, posicion: float, valido: bool):
        self.posicion = posicion
        self.valido   = valido


class Deslizador:
    """Controla la posición de un deslizador dentro de un rango definido y notifica los intentos de desplazamiento."""
    def __init__(self, rango: tuple):
        self.rango       = rango
        self.posicion    = 0

        self.suscriptores = []


    def suscribir(self, suscriptor):
        self.suscriptores.append(suscriptor)


    def _actualizar(self, posicion: float, valido: bool):
        evento = MovimientoDeslizador(posicion, valido)

        for suscriptor in self.suscriptores:
            suscriptor(evento)


    def mover(self, posicion: float):
        if posicion < min(self.rango) or posicion > max(self.rango):
            self._actualizar(posicion, valido=False)
            return

        self.posicion = posicion
        self._actualizar(posicion, valido=True)

# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.logica.deslizador

if __name__ == "__main__":
    print("Prueba deslizador.py\n")

    def _crear_contador():
        contador = {"avisos": 0}

        def contar(_evento):
            contador["avisos"] += 1

        return contador, contar

    print("Estado inicial")
    d = Deslizador((-70, 70))
    assert d.rango == (-70, 70)
    assert d.posicion == 0
    print("OK: rango y posicion correctos\n")

    print("Un suscriptor")
    contador, contar = _crear_contador()
    d.suscribir(contar)

    d.mover(25)
    assert contador["avisos"] == 1
    assert d.posicion == 25
    print("OK: se avisó 1 vez y la posición quedó en 25\n")

    print("Múltiples suscriptores")
    c1, contar1 = _crear_contador()
    c2, contar2 = _crear_contador()
    d.suscribir(contar1)
    d.suscribir(contar2)

    d.mover(-50)
    assert c1["avisos"] == 1
    assert c2["avisos"] == 1
    print("OK: ambos suscriptores fueron avisados\n")

    print("Fuera de rango avisa con valido=False")
    eventos = []

    def guardar_evento(evento):
        eventos.append(evento)

    d.suscribir(guardar_evento)

    posicion_antes = d.posicion
    d.mover(5000)

    assert d.posicion == posicion_antes
    ultimo = eventos[-1]
    assert ultimo.posicion == 5000
    assert ultimo.valido is False
    print("OK: fuera de rango no mueve, pero avisa con valido=False\n")

    print("Movimientos repetidos")
    for i in range(2):
        d.mover(i)
    assert c1["avisos"] == 4
    assert c2["avisos"] == 4
    print("OK: los movimientos sumaron avisos a ambos suscriptores\n")

    print("El sobre con posición válida")
    d.mover(10)
    ultimo = eventos[-1]
    assert ultimo.posicion == 10
    assert ultimo.valido is True
    print(f"OK: el sobre llevó posición {ultimo.posicion} y valido={ultimo.valido}\n")

    print("Conexión desacoplada (simula al Logger)")
    def avisar_log_de_deslizador(evento):
        if not evento.valido:
            print(f"[LOGGER] ADVERTENCIA: ángulo {evento.posicion} fuera de rango")

    logueador = Deslizador((-90, 90))
    logueador.suscribir(avisar_log_de_deslizador)
    logueador.mover(-1000)

    print("\nPruebas OK")

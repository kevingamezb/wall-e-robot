# wall-e-robot/app/widgets/logica/deslizador.py
# Kevin Gámez - 28/08/2026


class MovimientoDeslizador:
    """
    El "sobre" que representa cada intento de mover el deslizador.

    Cuando el deslizador avisa a sus suscriptores, les entrega un
    sobre con la posición solicitada y si esa posición era válida.
    Así el que escucha decide qué hacer (moverse, loguear un error,
    ignorarlo...), sin que el deslizador dependa de nadie concreto.
    """

    def __init__(self, posicion: float, valido: bool):
        self.posicion = posicion  # La posición que se intentó
        self.valido   = valido    # True si estaba dentro del rango


class Deslizador:
    """
    Un deslizador es como la perilla de volumen de una radio:
    tiene un valor que va de un mínimo a un máximo, y el usuario
    lo sube o lo baja moviendo la perilla.

    Cuando la perilla cambia de valor (o se intenta cambiarla), el
    deslizador "avisa" a todos los suscriptores entregándoles un
    MovimientoDeslizador. Al igual que el botón, no le importa qué
    hace cada uno; solo se encarga de avisar.
    """

    def __init__(self, rango: tuple):
        """
        Constructor del deslizador.

        rango: una tupla (minimo, maximo) que limita hasta dónde
               puede moverse la "perilla" (ej. (-70, 70) grados).

        Empieza en la posición 0 y aún no tiene a quién avisar.
        """

        self.rango       = rango  # (mínimo, máximo) permitidos
        self.posicion    = 0      # El valor actual de la perilla

        self.suscriptores = []    # La "libreta de contactos", como el botón


    def suscribir(self, suscriptor):
        """
        Agrega un contacto a la libreta.

        Igual que unirse a un grupo de WhatsApp, cada suscriptor queda
        guardado para ser avisado cada vez que el deslizador se mueva
        (o se intente mover).
        """

        self.suscriptores.append(suscriptor)


    def _actualizar(self, posicion: float, valido: bool):
        """
        El "cableado" interno: avisa a todos con un "sobre".

        Recorre la libreta y llama a cada contacto entregándole un
        MovimientoDeslizador con la posición intentada y si era válida.
        Es privado (guion bajo al inicio), así que solo lo usa el
        deslizador; nadie debería llamarlo desde fuera.
        """

        evento = MovimientoDeslizador(posicion, valido)

        for suscriptor in self.suscriptores:
            suscriptor(evento)


    def mover(self, posicion: float):
        """
        Mueve la "perilla" a la posición indicada, si es válida.

        Si la posición está fuera del rango permitido, la "perilla" no
        se mueve, pero igual se avisa a los suscriptores con valido=False.
        Así el logger (u otro) puede enterarse de que se pidió un ángulo
        fuera de rango, sin que el deslizador se acople directamente.
        """

        # Si está fuera de rango: no nos movemos, pero avisamos del intento.
        if posicion < min(self.rango) or posicion > max(self.rango):
            self._actualizar(posicion, valido=False)
            return

        # Guardamos la nueva posición y avisamos con valido=True.
        self.posicion = posicion
        self._actualizar(posicion, valido=True)


# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.widgets.logica.deslizador

if __name__ == "__main__":
    print("Prueba deslizador.py\n")


    # Función auxiliar de conteo
    # Devuelve una función que cuenta las veces que es llamada.
    # Usamos un dict (no un int) porque Python no modifica los ints
    # por referencia; el dict sí cambia y podemos leerlo después.
    # Recibe el "sobre" (MovimientoDeslizador) pero solo cuenta.
    def _crear_contador():
        contador = {"avisos": 0}

        def contar(_evento):
            contador["avisos"] += 1

        return contador, contar


    # 1. Estado inicial
    print("=== Estado inicial ===")
    d = Deslizador((-70, 70))
    assert d.rango == (-70, 70), "El rango inicial no coincide"
    assert d.posicion == 0,       "Un deslizador nuevo debería estar en posición 0"
    print("OK: rango y posicion correctos\n")


    # 2. Un suscriptor se avisa al mover
    print("=== Un suscriptor ===")
    contador, contar = _crear_contador()
    d.suscribir(contar)

    d.mover(25)
    assert contador["avisos"] == 1, "Se debería haber avisado 1 vez"
    assert d.posicion == 25,        "Tras mover, la posición debería ser 25"
    print("OK: se avisó 1 vez y la posición quedó en 25\n")


    # 3. Múltiples suscriptores
    print("=== Múltiples suscriptores ===")
    c1, contar1 = _crear_contador()
    c2, contar2 = _crear_contador()
    d.suscribir(contar1)
    d.suscribir(contar2)

    d.mover(-50)
    assert c1["avisos"] == 1, "El suscriptor 1 debería haber sido avisado"
    assert c2["avisos"] == 1, "El suscriptor 2 debería haber sido avisado"
    print("OK: ambos suscriptores fueron avisados\n")


    # 4. Fuera de rango: no mueve pero ahora SÍ avisa (valido=False)
    print("=== Fuera de rango avisa con valido=False ===")
    eventos = []  # Aquí van los "sobres" recibidos

    def guardar_evento(evento):
        eventos.append(evento)

    d.suscribir(guardar_evento)

    posicion_antes = d.posicion
    d.mover(5000)  # 5000 está fuera de (-70, 70)

    assert d.posicion == posicion_antes,  "Fuera de rango no debería cambiar la posición"
    ultimo = eventos[-1]
    assert ultimo.posicion == 5000, "El sobre debería llevar la posición intentada"
    assert ultimo.valido is False,  "El sobre debería marcar valido=False"
    print("OK: fuera de rango no mueve, pero avisa con valido=False\n")


    # 5. Movimientos repetidos acumulan avisos
    print("=== Movimientos repetidos ===")
    # Cuenta: mover(-50) prueba 3, mover(5000) prueba 4, +2 aquí = 4 por suscriptor.
    for i in range(2):
        d.mover(i)
    assert c1["avisos"] == 4, f"El suscriptor 1 debería tener 4 avisos, tiene {c1['avisos']}"
    assert c2["avisos"] == 4, f"El suscriptor 2 debería tener 4 avisos, tiene {c2['avisos']}"
    print("OK: los movimientos sumaron avisos a ambos suscriptores\n")


    # 6. El suscriptor recibe la posición válida en el sobre
    print("=== El sobre con posición válida ===")
    d.mover(10)
    ultimo = eventos[-1]
    assert ultimo.posicion == 10, "El sobre debería llevar la posición 10"
    assert ultimo.valido is True, "Una posición en rango debería marcarse valido=True"
    print(f"OK: el sobre llevó posición {ultimo.posicion} y valido={ultimo.valido}\n")


    # 7. Conexión desacoplada con un "logger" de ejemplo
    print("=== Conexión desacoplada (simula al Logger) ===")
    # Aquí vemos cómo un suscriptor externo decide loguear el error.
    # En la app real esto llamaría a estado.logger.agregar_linea(...).
    def avisar_log_de_deslizador(evento):
        if not evento.valido:
            print(f"[LOGGER] ADVERTENCIA: ángulo {evento.posicion} fuera de rango")

    logueador = Deslizador((-90, 90))
    logueador.suscribir(avisar_log_de_deslizador)
    logueador.mover(-1000)  # imprime: [LOGGER] ADVERTENCIA: ángulo -1000 fuera de rango


    print("\nPruebas OK")

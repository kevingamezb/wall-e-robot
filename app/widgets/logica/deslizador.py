# wall-e-robot/app/widgets/logica/deslizador.py
# Kevin Gámez - 28/08/2026


class Deslizador:
    """
    Un deslizador es como la perilla de volumen de una radio:
    tiene un valor que va de un mínimo a un máximo, y el usuario
    lo sube o lo baja moviendo la perilla.

    Cuando la perilla cambia de valor, el deslizador "avisa" a todos
    los suscriptores cuánto vale ahora (igual que el botón avisa
    cuando lo presionan, pero aquí además pasando el nuevo valor).
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
        guardado para ser avisado cada vez que el deslizador se mueva.
        """

        self.suscriptores.append(suscriptor)


    def _actualizar(self):
        """
        El "cableado" interno: avisa a todos con el valor actual.

        Recorre la libreta y llama a cada contacto pasándole la
        posición. Es privado (guion bajo al inicio), así que solo lo
        usa el deslizador; nadie debería llamarlo desde fuera.
        """

        for suscriptor in self.suscriptores:
            suscriptor(self.posicion)


    def mover(self, posicion: float):
        """
        Mueve la "perilla" a la posición indicada, si es válida.

        Si la posición está fuera del rango permitido, se ignora
        (es como intentar subir el volumen más allá del máximo:
        simplemente no pasa nada).
        """

        # Si está fuera de rango, no hacemos nada y salimos.
        if posicion < min(self.rango) or posicion > max(self.rango):
            return

        # Guardamos la nueva posición y avisamos a todos.
        self.posicion = posicion
        self._actualizar()


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
    # Acepta un argumento (el valor nuevo) aunque no lo usa.
    def _crear_contador():
        contador = {"avisos": 0}

        def contar(_valor):
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


    # 4. Fuera de rango no avisa ni cambia
    print("=== Fuera de rango ===")
    avisos_antes = c1["avisos"]
    d.mover(5000)  # 5000 está fuera de (-70, 70)
    assert d.posicion == -50,             "Fuera de rango no debería cambiar la posición"
    assert c1["avisos"] == avisos_antes,  "Fuera de rango no debería avisar a nadie"
    print("OK: mover fuera de rango se ignora\n")


    # 5. Movimientos repetidos acumulan avisos
    print("=== Movimientos repetidos ===")
    for i in range(2):
        d.mover(i)
    assert c1["avisos"] == 3, f"El suscriptor 1 debería tener 3 avisos, tiene {c1['avisos']}"
    assert c2["avisos"] == 3, f"El suscriptor 2 debería tener 3 avisos, tiene {c2['avisos']}"
    print("OK: los movimientos sumaron avisos a ambos suscriptores\n")


    # 6. El suscriptor recibe el nuevo valor
    print("=== El suscriptor recibe el valor ===")
    valores_recibidos = []

    def guardar_valor(valor):
        valores_recibidos.append(valor)

    d.suscribir(guardar_valor)
    d.mover(10)
    assert d.posicion == 10, "La posición debería ser 10"
    assert valores_recibidos[-1] == 10, "El último valor recibido debería ser 10"
    print(f"OK: el suscriptor recibió el valor {valores_recibidos[-1]}\n")


    # 7. Demostración simple con valor
    print("=== Demostración simple ===")
    def cuando_se_mueve(valor):
        print(f"¡El deslizador se movió!, ahora está en {valor}°")

    demo = Deslizador((-50, 50))
    demo.suscribir(cuando_se_mueve)
    demo.mover(25)  # imprime: ¡El deslizador se movió!, ahora está en 25°


    print("\nPruebas OK")

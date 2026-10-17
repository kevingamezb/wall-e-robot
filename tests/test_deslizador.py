# wall-e-robot/tests/test_deslizador.py
# Kevin Gámez - 16/10/2026

"""Pruebas de app.widgets.logica.deslizador: rango, posición y validez."""


from app.widgets.logica.deslizador import Deslizador, MovimientoDeslizador


def test_estado_inicial():
    """El rango se guarda tal cual y la posición arranca en 0."""
    d = Deslizador((-70, 70))
    assert d.rango == (-70, 70)
    assert d.posicion == 0


def test_mover_dentro_del_rango_actualiza_posicion(contador):
    """Un movimiento válido cambia la posición y avisa una vez."""
    d = Deslizador((-70, 70))
    d.suscribir(contador)

    d.mover(25)

    assert contador.avisos == 1
    assert d.posicion == 25
    evento = contador.ultimo[0][0]
    assert isinstance(evento, MovimientoDeslizador)
    assert evento.posicion == 25
    assert evento.valido is True


def test_mover_fuera_de_rango_no_cambia_posicion(contador):
    """Un movimiento inválido no altera la posición pero sí notifica valido=False."""
    d = Deslizador((-70, 70))
    d.suscribir(contador)

    posicion_antes = d.posicion
    d.mover(5000)

    assert d.posicion == posicion_antes
    assert contador.avisos == 1
    evento = contador.ultimo[0][0]
    assert evento.posicion == 5000
    assert evento.valido is False


def test_limites_del_rango_son_inclusivos():
    """Los extremos del rango cuentan como posiciones válidas."""
    d = Deslizador((-70, 70))

    d.mover(-70)
    assert d.posicion == -70

    d.mover(70)
    assert d.posicion == 70


def test_multiples_suscriptores():
    """Todos los suscriptores reciben cada evento de movimiento."""
    d = Deslizador((-70, 70))
    c1, c2 = _ContadorLocal(), _ContadorLocal()
    d.suscribir(c1)
    d.suscribir(c2)

    d.mover(-50)

    assert c1.avisos == 1
    assert c2.avisos == 1


def test_movimientos_repetidos_suman_avisos(contador):
    """Cada llamada a mover() genera un evento, incluso repetido."""
    d = Deslizador((-70, 70))
    d.suscribir(contador)

    for i in range(4):
        d.mover(i)

    assert contador.avisos == 4


def test_conexion_desacoplada_al_logger():
    """El deslizador no conoce al suscriptor: solo entrega el evento."""
    avisos = []
    logueador = Deslizador((-90, 90))
    logueador.suscribir(
        lambda evento: avisos.append(evento) if not evento.valido else None)

    logueador.mover(-1000)

    assert len(avisos) == 1
    assert avisos[0].posicion == -1000
    assert avisos[0].valido is False


class _ContadorLocal:
    """Suscriptor que cuenta eventos (recibe el argumento 'evento')."""

    def __init__(self):
        self.avisos = 0

    def __call__(self, _evento):
        self.avisos += 1

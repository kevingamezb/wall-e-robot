# wall-e-robot/app/widgets/logica/navegacion.py
# Kevin Gámez - 13/10/2026


from ...nucleo.estado import EstadoRobot, Maniobra, Modo
from ...nucleo.paleta import Paleta


# Glifo que representa cada maniobra.
SIMBOLOS = {
    Maniobra.RECTO:     "\u25b2",   # ▲
    Maniobra.IZQUIERDA: "\u25c0",   # ◀
    Maniobra.DERECHA:   "\u25b6",   # ▶
    Maniobra.ALTO:      "\u25a0",   # ■
}

ETIQUETAS = {
    Maniobra.RECTO:     "RECTO",
    Maniobra.IZQUIERDA: "IZQUIERDA",
    Maniobra.DERECHA:   "DERECHA",
    Maniobra.ALTO:      "ALTO",
}


class Navegacion:
    """Expone la maniobra que decidió el ESP32 y el modo actual."""
    def __init__(self, estado: EstadoRobot):
        self.estado = estado

    @property
    def maniobra(self) -> Maniobra:
        return self.estado.navegacion

    @property
    def en_manual(self) -> bool:
        return self.estado.modo == Modo.MANUAL

    @property
    def simbolo(self) -> str:
        if self.en_manual:
            return "\u2014"          # - (control del operador)
        return SIMBOLOS[self.maniobra]

    @property
    def etiqueta(self) -> str:
        if self.en_manual:
            return "MANUAL"
        return ETIQUETAS[self.maniobra]

    @property
    def color(self) -> str:
        if self.en_manual:
            return Paleta.NARANJA
        if self.maniobra == Maniobra.ALTO:
            return Paleta.ROJO
        return Paleta.AXIOM_CYAN

# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.logica.navegacion

if __name__ == "__main__":
    print("Prueba navegacion.py\n")

    estado = EstadoRobot()
    nav = Navegacion(estado)

    print("Automático, recto")
    assert not nav.en_manual
    assert nav.maniobra == Maniobra.RECTO
    assert nav.etiqueta == "RECTO"
    assert nav.color == Paleta.AXIOM_CYAN
    print(f"OK: {nav.simbolo} {nav.etiqueta} / {nav.color}\n")

    print("Automático, obstáculo: alto")
    estado.navegacion = Maniobra.ALTO
    assert nav.etiqueta == "ALTO"
    assert nav.color == Paleta.ROJO
    print(f"OK: {nav.simbolo} {nav.etiqueta} / {nav.color}\n")

    print("Automático, giro a la izquierda")
    estado.navegacion = Maniobra.IZQUIERDA
    assert nav.etiqueta == "IZQUIERDA"
    print(f"OK: {nav.simbolo} {nav.etiqueta} / {nav.color}\n")

    print("Manual: manda el operador")
    estado.modo = Modo.MANUAL
    assert nav.en_manual
    assert nav.etiqueta == "MANUAL"
    assert nav.color == Paleta.NARANJA
    print(f"OK: {nav.simbolo} {nav.etiqueta} / {nav.color}\n")

    print("Pruebas OK")

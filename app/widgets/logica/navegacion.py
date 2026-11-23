from ...nucleo.estado import EstadoRobot, Maniobra, Modo
from ...nucleo.paleta import Paleta


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
    """Expone la maniobra que decidió el ESP32 y el modo actual; en manual manda el operador."""
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
    def descripcion(self) -> str:
        """Frase larga de la maniobra para la tarjeta de navegación."""
        if self.estado.detenido:
            return "Demo en curso" if self.estado.demo_activa else "Detenido"
        if self.en_manual:
            return "Control manual"
        if self.maniobra == Maniobra.ALTO:
            if self.estado.distancia_obstaculo_cm is None:
                return "Sin lectura\nfrontal"
            if self.estado.hay_advertencia:
                return "Obstáculo\nal frente"
        return {
            Maniobra.RECTO:     "Avanzando recto",
            Maniobra.IZQUIERDA: "Girando a la\nIzquierda",
            Maniobra.DERECHA:   "Girando a la\nDerecha",
            Maniobra.ALTO:      "Detenido",
        }[self.maniobra]

    @property
    def color(self) -> str:
        if self.en_manual:
            return Paleta.NARANJA
        if self.maniobra == Maniobra.ALTO:
            return Paleta.ROJO
        return Paleta.AZUL

# Cajón de Pruebas
if __name__ == "__main__":
    print("Prueba navegacion.py\n")

    estado = EstadoRobot()
    estado.modo = Modo.AUTOMATICO   # el firmware arranca en manual
    nav = Navegacion(estado)

    print("Arranque sin datos: alto")
    assert not nav.en_manual
    assert nav.maniobra == Maniobra.ALTO
    assert nav.etiqueta == "ALTO"
    assert nav.color == Paleta.ROJO
    print(f"OK: {nav.simbolo} {nav.etiqueta} / {nav.color}\n")

    print("Automático, recto")
    estado.navegacion = Maniobra.RECTO
    assert not nav.en_manual
    assert nav.maniobra == Maniobra.RECTO
    assert nav.etiqueta == "RECTO"
    assert nav.color == Paleta.AZUL
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

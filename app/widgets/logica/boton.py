# wall-e-robot/app/widgets/logica/boton.py
# Kevin Gámez - 27/08/2026


from ...nucleo.paleta import Paleta


class Boton:
    """Gestiona el estado y la notificación a suscriptores de un botón de la interfaz."""
    def __init__(self, texto: str):
        self.texto = texto
        self.presionado = False
        self.en_hover = False

        self._suscriptores = []

    def suscribir(self, suscriptor):
        self._suscriptores.append(suscriptor)

    def _actualizar(self):
        for suscriptor in self._suscriptores:
            suscriptor()

    def presionar(self):
        self.presionado = True
        self._actualizar()

    def soltar(self):
        self.presionado = False

    def entrar_hover(self):
        self.en_hover = True

    def salir_hover(self):
        self.en_hover = False
        
        
    @property
    def color_fondo(self):
        if self.presionado:
            return Paleta.DORADO
        if self.en_hover:
            return Paleta.DORADO_DIM
        return Paleta.FONDO_APP
    
# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.logica.boton

if __name__ == "__main__":
    print("Prueba boton.py\n")

    def _crear_contador():
        contador = {"avisos": 0}

        def contar():
            contador["avisos"] += 1

        return contador, contar

    print("Estado inicial")
    b = Boton("Abrir mano")
    assert b.texto == "Abrir mano"
    assert b.presionado is False
    assert b.color_fondo == Paleta.FONDO_APP
    print("OK: texto, sin presionar y color FONDO_APP correctos\n")

    print("Un suscriptor:")
    contador, contar = _crear_contador()
    b.suscribir(contar)

    b.presionar()
    assert contador["avisos"] == 1
    assert b.presionado is True
    assert b.color_fondo == Paleta.DORADO
    print("OK: se avisó 1 vez, quedó presionado y color DORADO\n")

    print("Múltiples suscriptores:")
    c1, contar1 = _crear_contador()
    c2, contar2 = _crear_contador()
    b.suscribir(contar1)
    b.suscribir(contar2)

    b.presionar()
    assert c1["avisos"] == 1
    assert c2["avisos"] == 1
    print("OK: ambos suscriptores fueron avisados\n")

    print("Soltar no lanza avisos:")
    b.soltar()
    assert b.presionado is False
    assert b.color_fondo == Paleta.FONDO_APP
    assert c1["avisos"] == 1 and c2["avisos"] == 1
    print("OK: al soltar no se avisa y vuelve a FONDO_APP\n")

    print("Presiones repetidas:")
    for _ in range(2):
        b.presionar()
    assert c1["avisos"] == 3
    assert c2["avisos"] == 3
    print("OK: dos presiones extra sumaron avisos a ambos suscriptores\n")

    print("Hover (mouse encima):")
    b.soltar()
    b.entrar_hover()
    assert b.en_hover is True
    assert b.color_fondo == Paleta.DORADO_DIM
    assert c1["avisos"] == 3 and c2["avisos"] == 3
    print("OK: en_hover=True, color DORADO_DIM y sin avisos\n")

    print("Hover + presionado:")
    b.presionar()
    assert b.color_fondo == Paleta.DORADO
    print("OK: presionado sigue viéndose DORADO en hover\n")

    print("Salir del hover:")
    b.soltar()
    b.salir_hover()
    assert b.en_hover is False
    assert b.color_fondo == Paleta.FONDO_APP
    print("OK: en_hover=False y color FONDO_APP\n")

    print("Demostración simple:")
    def cuando_se_presiona():
        print("¡Alguien presionó el botón!")

    demo = Boton("Abrir mano")
    demo.suscribir(cuando_se_presiona)
    demo.presionar()

    print("\nPruebas OK")
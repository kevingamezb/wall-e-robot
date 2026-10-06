# wall-e-robot/app/widgets/logica/boton.py
# Kevin Gámez - 27/08/2026


from ...nucleo.paleta import Paleta # Paleta (definida en paleta.py) nos da los colores del botón


class Boton:
    """
    Un botón es como el timbre de una casa: cuando alguien lo presiona,
    "suena" y todos los que están atentos al timbre se enteran.

    El botón solo sabe su texto, si está presionado, y a quién avisar
    cuando lo presionan. No le importa qué hace cada uno de los
    avisados; solo se encarga de avisarles.
    """
    
    def __init__(self, texto: str):
        """
        Constructor del botón.
        
        texto: la etiqueta que se ve en el botón (ej. "Abrir mano").
        
        Se guarda la lista de "suscriptores" vacía: el botón aún no
        sabe a quién avisar cuando lo presionen.
        """
        
        self.texto = texto                    # La etiqueta visible del botón
        self.presionado = False               # El estado actual (como un interruptor apagado)
        self.en_hover = False                 # El mouse está encima sin presionar
        
        self._suscriptores = []               # La "libreta de contactos" del botón
        
        
    def suscribir(self, suscriptor):
        """
        Agrega un "contacto" a la libreta.
        
        Al igual que unirse a un grupo de WhatsApp, cuando alguien se
        suscribe, el botón lo guarda en self._suscriptores para después
        poder llamarlo al presionarse.
        """
        
        self._suscriptores.append(suscriptor)
        
        
    def _actualizar(self):
        """
        El "cableado" interno: avisa a todos los suscriptores.
        
        Recorre la libreta y llama a cada contacto. Es privado (por eso
        el guion bajo al inicio), así que solo el botón lo usa; nadie
        debería llamarlo desde fuera.
        """
        
        for suscriptor in self._suscriptores:
            suscriptor()
        
        
    def presionar(self):
        """
        Simula que alguien presiona el botón.
        
        Enciende el "interruptor" (presionado = True) y avisa a todos
        los suscriptores.
        """
        
        self.presionado = True
        self._actualizar()
        
        
    def soltar(self):
        """
        Simula que se deja de presionar el botón.
        
        Solo apaga el "interruptor"; no avisa a nadie.
        """
        
        self.presionado = False
        
        
    def entrar_hover(self):
        """
        El mouse entró sobre el botón (sin presionar todavía).
        
        Es un estado PURAMENTE visual: no avisa a ningún suscriptor.
        El botón solo lo recuerda para que su color lo comunique.
        """
        
        self.en_hover = True
        
        
    def salir_hover(self):
        """
        El mouse salió del área del botón.
        
        Igual que entrar_hover, es solo visual y no avisa a nadie.
        """
        
        self.en_hover = False
        
        
    @property
    def color_fondo(self):
        """
        El color de fondo del botón, calculado según su estado.
        
        Este decorador @property permite leer el color como si fuera un
        atributo normal (boton.color_fondo), pero por dentro calcula el
        valor. El botón cambia de color para comunicar sus tres estados
        de forma visual, en orden de "intensidad"):
            - Sin interacción    -> FONDO_APP   (negro: en reposo)
            - Hover (mouse encima) -> DORADO_DIM (ámbar apagado: "soy clickeable")
            - Presionado          -> DORADO      (ámbar brillante: "me están usando")
        """
        
        if self.presionado:
            return Paleta.DORADO
        if self.en_hover:
            return Paleta.DORADO_DIM
        return Paleta.FONDO_APP
    

# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.widgets.logica.boton


if __name__ == "__main__":
    print("Prueba boton.py\n")


    # Función auxiliar de conteo
    # Devuelve una función que, al ser llamada, incrementa el contador.
    # Usamos un dict en vez de un int porque Python no modifica los ints
    # por referencia; el dict sí cambia y podemos leerlo después.
    def _crear_contador():
        contador = {"avisos": 0}

        def contar():
            contador["avisos"] += 1

        return contador, contar


    # 1. Estado inicial
    print("Estado inicial")
    b = Boton("Abrir mano")
    assert b.texto == "Abrir mano", "El texto inicial no coincide"
    assert b.presionado is False, "Un botón nuevo debería estar sin presionar"
    assert b.color_fondo == Paleta.FONDO_APP, "El color inicial debería ser FONDO_APP"
    print("OK: texto, sin presionar y color FONDO_APP correctos\n")


    # 2. Un suscriptor se avisa al presionar 
    print("Un suscriptor:")
    contador, contar = _crear_contador()
    b.suscribir(contar)

    b.presionar()
    assert contador["avisos"] == 1, "Se debería haber avisado 1 vez"
    assert b.presionado is True, "Tras presionar debería estar presionado"
    assert b.color_fondo == Paleta.DORADO, "Presionado debería verse DORADO"
    print("OK: se avisó 1 vez, quedó presionado y color DORADO\n")


    # 3. Múltiples suscriptores 
    print("Múltiples suscriptores:")
    c1, contar1 = _crear_contador()
    c2, contar2 = _crear_contador()
    b.suscribir(contar1)
    b.suscribir(contar2)

    b.presionar()
    assert c1["avisos"] == 1, "El suscriptor 1 debería haber sido avisado"
    assert c2["avisos"] == 1, "El suscriptor 2 debería haber sido avisado"
    print("OK: ambos suscriptores fueron avisados\n")


    # 4. Soltar apaga pero no avisa 
    print("Soltar no lanza avisos:")
    b.soltar()
    assert b.presionado is False, "Tras soltar no debería estar presionado"
    assert b.color_fondo == Paleta.FONDO_APP, "Suelto debería verse FONDO_APP"
    assert c1["avisos"] == 1 and c2["avisos"] == 1, "Soltar no debería avisar a nadie"
    print("OK: al soltar no se avisa y vuelve a FONDO_APP\n")


    # 5. Múltiples presiones acumulan avisos 
    print("Presiones repetidas:")
    for _ in range(2):
        b.presionar()
    assert c1["avisos"] == 3, f"El suscriptor 1 debería tener 3 avisos, tiene {c1['avisos']}"
    assert c2["avisos"] == 3, f"El suscriptor 2 debería tener 3 avisos, tiene {c2['avisos']}"
    print("OK: dos presiones extra sumaron avisos a ambos suscriptores\n")


    # 6. Hover: es visual y NO avisa a los suscriptores 
    print("Hover (mouse encima):")
    b.soltar()
    b.entrar_hover()
    assert b.en_hover is True, "entrar_hover debería encender en_hover"
    assert b.color_fondo == Paleta.DORADO_DIM, "En hover el botón debe verse DORADO_DIM"
    assert c1["avisos"] == 3 and c2["avisos"] == 3, "El hover no debería avisar a nadie"
    print("OK: en_hover=True, color DORADO_DIM y sin avisos\n")


    # 7. Hover tiene menor prioridad que presionado 
    print("Hover + presionado:")
    b.presionar()
    assert b.color_fondo == Paleta.DORADO, "Presionado debe ganar siempre al hover"
    print("OK: presionado sigue viéndose DORADO en hover\n")


    # 8. Salir del hover vuelve a reposo 
    print("Salir del hover:")
    b.soltar()
    b.salir_hover()
    assert b.en_hover is False, "salir_hover debería apagar en_hover"
    assert b.color_fondo == Paleta.FONDO_APP, "Sin hover ni presión debe volver a FONDO_APP"
    print("OK: en_hover=False y color FONDO_APP\n")


    # Bonus: demostración simple con print 
    # Un suscriptor que solo imprime, para ver el aviso "en vivo".
    print("Demostración simple:")
    def cuando_se_presiona():
        print("¡Alguien presionó el botón!")

    demo = Boton("Abrir mano")
    demo.suscribir(cuando_se_presiona)
    demo.presionar()  # imprime: ¡Alguien presionó el botón!


    print("\nPruebas OK")
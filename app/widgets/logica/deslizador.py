# wall-e-robot/app/widgets/logica/delizador.py
# Kevin Gámez - 28/08/2026


class Deslizador:
    def __init__(self, rango: tuple):
        self.rango    = rango
        self.posicion = 0
        
        self.suscriptores = []
        
        
    def suscribir(self, suscriptor):
        self.suscriptores.append(suscriptor)
    
    
    def _actualizar(self):
        for suscriptor in self.suscriptores:
            suscriptor(self.posicion)
            
            
    def mover(self, posicion: float):
        if posicion < min(self.rango) or posicion > max(self.rango):
            return # Ángulo incorrecto
        
        self.posicion = posicion
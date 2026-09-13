# wall-e-robot/app/main.py
# Kevin Gámez - 13/09/2026
#
# Punto de entrada de la aplicación de escritorio del Wall-E.
#
# Para arrancar (desde la raíz del proyecto, donde está la carpeta 'app'):
#   python -m app.main


import tkinter as tk
from .nucleo.paleta import Paleta
from .nucleo.estado import EstadoRobot
from .comunicacion.conexion import ComunicacionSimulada
from .pantallas.monitoreo import PantallaMonitoreo
from .pantallas.control_manual import PantallaControlManual


# Cada cuántos milisegundos se lee el "robot" y se redibuja la pantalla.
# 60 ms ~ 16 cuadros por segundo: más que suficiente para una GUI y deja
# tranquilo al procesador (un ESP32 real tampoco actualiza más rápido).
INTERVALO_CICLO_MS = 60


class Aplicacion:
    """
    El 'cerebro' de la GUI: une estado + conexión + pantallas.

    Tiene dos pantallas (monitoreo y control manual) que se intercambian
    según pulse el usuario. Nada inventa aquí: pregunta al estado, le pasa
    los comandos del gamepad a la conexión y cada ciclo pide a la pantalla
    activa que se redibuje.
    """

    def __init__(self, root: tk.Tk):
        """Monta la ventana, el estado, la conexión y la pantalla inicial."""
        self.root = root
        self.root.title("Wall-E · Panel de control")
        self.root.configure(bg=Paleta.FONDO_APP)

        # La 'caja maestra': todo el programa lee de aquí.
        self.estado = EstadoRobot()

        # Conexión con el robot. Ahora mismo es el simulador; cuando el
        # firmware del ESP32 esté listo, se cambia solo esta línea.
        self.conexion = ComunicacionSimulada()

        # Contenedor donde viven las pantallas (se vacía al cambiar).
        self.contenedor = tk.Frame(root, bg=Paleta.FONDO_APP)
        self.contenedor.pack(fill="both", expand=True)

        self.pantalla = None
        self.mostrar(PantallaMonitoreo)

    # --- Navegación entre pantallas ---

    def mostrar(self, clase_pantalla):
        """
        Sustituye la pantalla activa por otra clase de pantalla.

        Se destruye la anterior (con todos sus canvas) y se construye la
        nueva sobre el mismo contenedor. El estado sobrevive: como las
        pantallas leen del MISMO EstadoRobot, siempre van sincronizadas.
        """
        if self.pantalla is not None:
            self.pantalla.frame.destroy()

        if clase_pantalla is PantallaMonitoreo:
            self.pantalla = PantallaMonitoreo(
                self.contenedor,
                self.estado,
                on_cambiar=lambda: self.mostrar(PantallaControlManual),
            )
        else:
            pantalla = PantallaControlManual(
                self.contenedor,
                self.estado,
                on_cambiar=lambda: self.mostrar(PantallaMonitoreo),
            )
            # Los comandos del gamepad salen hacia la conexión.
            pantalla.conectar_gamepad(self.conexion.enviar_mensaje)
            self.pantalla = pantalla

    # --- Bucle principal de la aplicación ---

    def ciclo(self):
        """Un 'paso' de la aplicación: leer al robot + redibujar pantalla."""
        self.conexion.actualizar_estado(self.estado)
        if self.pantalla is not None:
            self.pantalla.dibujar()
        self.root.after(INTERVALO_CICLO_MS, self.ciclo)

    def iniciar(self):
        """Arranca el bucle y abre la ventana."""
        self.ciclo()
        self.root.mainloop()


if __name__ == "__main__":
    ventana = tk.Tk()
    ventana.geometry("1080x700")
    app = Aplicacion(ventana)
    app.iniciar()
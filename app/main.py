# wall-e-robot/app/main.py
# Kevin Gámez - 13/09/2026
#
# Punto de entrada de la aplicación de escritorio del Wall-E.
#
# Para arrancar (desde la raíz del proyecto, donde está la carpeta 'app'):
#   python -m app.main


import tkinter as tk
from .nucleo.paleta import Paleta
from .nucleo.estado import EstadoRobot, NivelLog
from .comunicacion.conexion import Comunicacion, ComunicacionSimulada, ConexionOffline
from .pantallas.pantalla_principal import PantallaPrincipal


# Cada cuántos milisegundos se lee el "robot" y se redibuja la pantalla.
# 60 ms ~ 16 cuadros por segundo: más que suficiente para una GUI y deja
# tranquilo al procesador (un ESP32 real tampoco actualiza más rápido).
INTERVALO_CICLO_MS = 60

# Puerto en el que escucha el ESP32 (el fw del robot y el socket de aquí
# se escriben por parejas; por defecto 8080 como hemos acordado).
PUERTO = 8080


class Aplicacion:
    """
    El 'cerebro' de la GUI: une estado + conexión + pantalla.

    Ahora es una sola pantalla (PantallaPrincipal): todo está siempre a la
    vista y la conexión se administra desde ahí con CONECTAR / DESCONECTAR.
    Cada ciclo pregunta al estado, pasa los comandos del gamepad a la
    conexión activa y pide a la pantalla que se redibuje.

    Estados de conexión que se manejan aquí:
        - simulador    (arranque)          : ComunicacionSimulada
        - robot por IP (tras CONECTAR)     : Comunicacion
        - sin conexión (tras DESCONECTAR)  : ConexionOffline
    """

    def __init__(self, root: tk.Tk):
        """Monta la ventana, el estado, la conexión y la pantalla."""
        self.root = root
        self.root.title("Wall-E · Panel de control")
        self.root.configure(bg=Paleta.FONDO_APP)

        # La 'caja maestra': todo el programa lee de aquí.
        self.estado = EstadoRobot()

        # Conexión con el robot. Prima el simulador; el usuario puede
        # conectar con un ESP32 real dándonos su IP.
        self.conexion = ComunicacionSimulada()

        self.contenedor = tk.Frame(root, bg=Paleta.FONDO_APP)
        self.contenedor.pack(fill="both", expand=True)

        self.pantalla = PantallaPrincipal(
            self.contenedor,
            self.estado,
            on_conectar=self._pedir_ip,
            on_desconectar=self._desconectar,
        )
        # El gamepad siempre dispara hacia la conexión ACTIVA: la función
        # cierra sobre self.conexion, así al cambiar de conexión el mando
        # empieza a hablar con el robot nuevo sin volver a cablear nada.
        self.pantalla.conectar_gamepad(lambda cmd: self.conexion.enviar_mensaje(cmd))
        self.pantalla.establecer_conexion(True, "SIMULADOR")

    # --- Conexión con el robot (modal de IP) ---

    def _pedir_ip(self):
        """Abre el modal que pide la IP del ESP32 (con grab, como un diálogo)."""
        modal = tk.Toplevel(self.root)
        modal.title("Conectar al Wall-E")
        modal.configure(bg=Paleta.FONDO_APP)
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()

        tk.Label(modal, text="Dirección IP del Wall-E:",
                 bg=Paleta.FONDO_APP, fg=Paleta.TEXTO_LOG,
                 font=("Segoe UI", 10)).grid(
            row=0, column=0, columnspan=2, sticky="w",
            padx=Paleta.UNIDAD, pady=(Paleta.UNIDAD, 0))

        entrada = tk.Entry(modal, width=20, font=("Segoe UI", 10),
                           bg=Paleta.FONDO_WIDGET, fg=Paleta.TEXTO_LOG,
                           insertbackground=Paleta.DORADO)
        entrada.grid(row=1, column=0, columnspan=2, sticky="we",
                     padx=Paleta.UNIDAD, pady=(Paleta.UNIDAD // 2, 0))
        entrada.insert(0, "192.168.4.1")  # IP típica del modo AP del ESP32
        entrada.focus_set()

        lbl_error = tk.Label(modal, text="", bg=Paleta.FONDO_APP,
                             fg=Paleta.ROJO, font=("Segoe UI", 9))
        lbl_error.grid(row=2, column=0, columnspan=2, sticky="w",
                       padx=Paleta.UNIDAD, pady=(Paleta.UNIDAD // 2, 0))

        def _confirmar():
            """Intenta abrir el socket; si falla, muestra el error en el modal."""
            try:
                self._conectar(entrada.get().strip())
            except (OSError, ValueError) as error:
                lbl_error.config(text=f"No se pudo conectar: {error}")
                return
            modal.destroy()

        def _cancelar():
            """Cierra el modal sin conectar."""
            modal.destroy()

        btn_conectar = tk.Button(modal, text="CONECTAR", width=10,
                                 bg=Paleta.FONDO_WIDGET, fg=Paleta.DORADO,
                                 activebackground=Paleta.DORADO_DIM,
                                 activeforeground=Paleta.TEXTO_LOG,
                                 font=("Segoe UI", 9, "bold"), relief="flat",
                                 command=_confirmar)
        btn_conectar.grid(row=3, column=0, sticky="we",
                          padx=(Paleta.UNIDAD, Paleta.UNIDAD // 2),
                          pady=Paleta.UNIDAD)

        btn_cancelar = tk.Button(modal, text="CANCELAR", width=10,
                                 bg=Paleta.FONDO_WIDGET, fg=Paleta.TEXTO_TENUE,
                                 activebackground=Paleta.GRIS,
                                 activeforeground=Paleta.TEXTO_LOG,
                                 font=("Segoe UI", 9, "bold"), relief="flat",
                                 command=_cancelar)
        btn_cancelar.grid(row=3, column=1, sticky="we",
                          padx=(Paleta.UNIDAD // 2, Paleta.UNIDAD),
                          pady=Paleta.UNIDAD)

        modal.bind("<Return>", lambda _e: _confirmar())
        modal.bind("<Escape>", lambda _e: _cancelar())

    def _conectar(self, ip: str):
        """
        Cambia a la conexión real con el ESP32 de la IP dada.

        Lanza OSError/ValueError si no se puede abrir el socket; el modal
        las captura y las muestra como error en pantalla.
        """
        nueva = Comunicacion(ip, PUERTO)
        self._cerrar_conexion_actual()
        self.conexion = nueva
        self.pantalla.establecer_conexion(True, ip)

    def _desconectar(self):
        """Cuelga el teléfono y deja el panel sin conexión."""
        self._cerrar_conexion_actual()
        self.conexion = ConexionOffline()
        self.pantalla.establecer_conexion(False, "SIN CONEXI\u00d3N")

    def _cerrar_conexion_actual(self):
        """Cierra el socket actual si lo hay (los simuladores no tienen)."""
        cerrar = getattr(self.conexion, "cerrar", None)
        if callable(cerrar):
            cerrar()

    # --- Bucle principal de la aplicación ---

    def ciclo(self):
        """Un 'paso' de la aplicación: leer al robot + redibujar pantalla."""
        self.conexion.actualizar_estado(self.estado)

        # Si el robot se apagó/reinició en plena conexión, la red lo marca
        # como "perdida": se degrada a sin-conexión y se avisa en el log.
        if getattr(self.conexion, "perdida", False):
            self._cerrar_conexion_actual()
            self.conexion = ConexionOffline()
            self.pantalla.establecer_conexion(False, "SIN CONEXI\u00d3N")
            self.estado.logger.agregar_linea(
                "CONEXI\u00d3N",
                "Se perdió la conexión con el robot",
                NivelLog.ADVERTENCIA,
            )

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
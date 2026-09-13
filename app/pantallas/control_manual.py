# wall-e-robot/app/pantallas/control_manual.py
# Kevin Gámez - 13/09/2026


import tkinter as tk
from ..nucleo.paleta import Paleta
from ..nucleo.estado import EstadoRobot
from ..widgets.logica.boton import Boton
from ..widgets.logica.ojos import Ojos
from ..widgets.logica.icono_sistema import IconoSistema, TipoIcono
from ..widgets.logica.sol_bateria import SolBateria
from ..widgets.logica.barras_consumo import BarrasConsumo
from ..widgets.logica.radar import Radar
from ..widgets.logica.logger_widget import LoggerWidget
from ..widgets.logica.gamepad import Gamepad
from ..widgets.renderizado.ojos_render import OjosRenderer
from ..widgets.renderizado.icono_sistema_render import IconoSistemaRenderer
from ..widgets.renderizado.barras_consumo_render import BarrasConsumoRenderer
from ..widgets.renderizado.sol_bateria_render import SolBateriaRenderer
from ..widgets.renderizado.radar_render import RadarRenderer
from ..widgets.renderizado.logger_widget_render import LoggerWidgetRenderer
from ..widgets.renderizado.boton_render import BotonRenderer
from ..widgets.renderizado.gamepad_render import GamepadRenderer


class PantallaControlManual:
    """
    Pantalla de control manual: el robot "a mano".

    Layout (igual que la de monitoreo, pero cambiando la fila 2):
      Fila 1: [Estados: ojos · íconos+consumo · sol]  [Logger]
      Fila 2: [Radar compacto]                         [Gamepad]

    El gamepad se construye aquí pero los comandos se envían a la conexión
    a través de 'conectar_gamepad', que main.py cabi le pasa el simulador
    (o el ESP32 real, sin tocar esta pantalla).
    """

    def __init__(self, parent, estado: EstadoRobot, on_cambiar=None):
        """
        Constructor de la pantalla.

        parent     : el frame contenedor (en main.py).
        estado     : la 'caja maestra' compartida con todo el programa.
        on_cambiar : callback que se invoca al pulsar "Monitoreo".
        """
        self.estado = estado
        self.frame = tk.Frame(parent, bg=Paleta.FONDO_APP)
        self.frame.pack(fill="both", expand=True)

        # --- Widgets lógicos (vistas del mismo estado) ---
        self.ojos = Ojos(estado)
        self.iconos = [IconoSistema(estado, t) for t in TipoIcono]
        self.sol = SolBateria(estado)
        self.barras = BarrasConsumo(estado)
        self.radar = Radar(estado)
        self.logger = LoggerWidget(estado)
        self.gamepad = Gamepad(estado)
        self.boton_monitoreo = Boton("MONITOREO")
        if on_cambiar is not None:
            self.boton_monitoreo.suscribir(on_cambiar)

        # --- Distribución de la gilla ---
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        self._construir_columna_estado()
        self._construir_logger()
        self._construir_radar()
        self._construir_gamepad()

    # --- Construcción de cada bloque ---

    def _construir_columna_estado(self):
        """Columna izquierda superior: ojos, íconos+consumo y sol."""
        col = tk.Frame(self.frame, bg=Paleta.FONDO_APP)
        col.grid(row=0, column=0, sticky="nw", padx=14, pady=10)

        canvas_ojos = tk.Canvas(col, width=130, height=56,
                                bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_ojos.pack(anchor="w")
        self.render_ojos = OjosRenderer(self.ojos, canvas_ojos, 12, 14)

        fila = tk.Frame(col, bg=Paleta.FONDO_APP)
        fila.pack(anchor="w", pady=(8, 0))

        canvas_iconos = tk.Canvas(fila, width=150, height=30,
                                  bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_iconos.pack(side="left")
        self.render_iconos = []
        for i, icono in enumerate(self.iconos):
            render = IconoSistemaRenderer(icono, canvas_iconos, 3 + i * 27, 3, 24)
            self.render_iconos.append(render)

        canvas_barras = tk.Canvas(fila, width=44, height=130,
                                  bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_barras.pack(side="left", padx=(8, 0))
        self.render_barras = BarrasConsumoRenderer(self.barras, canvas_barras, 9, 124)

        self.lbl_consumo = tk.Label(fila, text="", bg=Paleta.FONDO_WIDGET,
                                    fg=Paleta.TEXTO_LOG, font=("Segoe UI", 8))
        self.lbl_consumo.pack(side="left", padx=(8, 0))

        canvas_sol = tk.Canvas(col, width=100, height=100,
                               bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_sol.pack(anchor="w", pady=(8, 0))
        self.render_sol = SolBateriaRenderer(self.sol, canvas_sol, 50, 50)

        self.lbl_sol = tk.Label(col, text="", bg=Paleta.FONDO_APP,
                                font=("Segoe UI", 10, "bold"))
        self.lbl_sol.pack(anchor="w")
        self.lbl_tiempo = tk.Label(col, text="", bg=Paleta.FONDO_APP,
                                   fg=Paleta.TEXTO_LOG, font=("Segoe UI", 9))
        self.lbl_tiempo.pack(anchor="w")

    def _construir_logger(self):
        """Marco superior derecho: la terminal de log."""
        marco = tk.Frame(self.frame, bg=Paleta.FONDO_WIDGET)
        marco.grid(row=0, column=1, sticky="nsew", padx=(0, 14), pady=10)
        self.render_logger = LoggerWidgetRenderer(self.logger, marco)

    def _construir_radar(self):
        """Marco inferior izquierdo: radar compacto + botón de retorno."""
        marco = tk.Frame(self.frame, bg=Paleta.FONDO_APP)
        marco.grid(row=1, column=0, sticky="nw", padx=14, pady=(0, 10))

        canvas_radar = tk.Canvas(marco, width=280, height=280,
                                 bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_radar.pack()
        self.render_radar = RadarRenderer(self.radar, canvas_radar, 140, 140, 130)

        self.lbl_dist = tk.Label(marco, text="", bg=Paleta.FONDO_APP,
                                 fg=Paleta.DORADO, font=("Segoe UI", 10))
        self.lbl_dist.pack(pady=(6, 0))

        canvas_boton = tk.Canvas(marco, width=200, height=50,
                                 bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_boton.pack(pady=(10, 0))
        self.render_boton = BotonRenderer(self.boton_monitoreo, canvas_boton, 16, 7, 168, 36)

    def _construir_gamepad(self):
        """Marco inferior derecho: el gamepad completo."""
        marco = tk.Frame(self.frame, bg=Paleta.FONDO_APP)
        marco.grid(row=1, column=1, sticky="se", padx=(0, 14), pady=(0, 10))

        canvas_gamepad = tk.Canvas(marco, width=640, height=380,
                                   bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_gamepad.pack()
        self.render_gamepad = GamepadRenderer(self.gamepad, canvas_gamepad, 640, 380)

    # --- API hacia afuera ---

    def conectar_gamepad(self, callback):
        """
        Conecta los comandos del gamepad a la conexión.

        Uso típico (en main.py):
            pantalla.conectar_gamepad(conexion.enviar_mensaje)
        """
        self.gamepad.suscribir_comando(callback)

    # --- Ciclo de actualización ---

    def dibujar(self):
        """Redibuja todos los bloques de la pantalla (se llama cada ciclo)."""
        self.render_ojos.dibujar()
        for render in self.render_iconos:
            render.dibujar()
        self.render_barras.dibujar()
        self.render_sol.dibujar()
        self.render_radar.dibujar()
        self.render_boton.dibujar()
        self.render_gamepad.dibujar()

        # Etiquetas que dependen del estado (el logger se actualiza solo).
        self.lbl_consumo.config(text=self.barras.etiqueta_watts)

        self.lbl_sol.config(text=self.sol.etiqueta, fg=self.sol.color)
        minutos = self.estado.tiempo_restante_min
        self.lbl_tiempo.config(text=f"~{minutos} min" if minutos else "--")

        distancia = self.estado.distancia_obstaculo_cm
        texto = (f"Objeto detectado a {distancia:.0f} cm"
                 if distancia is not None else "Sin detección")
        self.lbl_dist.config(text=texto)
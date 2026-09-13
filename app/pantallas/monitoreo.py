# wall-e-robot/app/pantallas/monitoreo.py
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
from ..widgets.renderizado.ojos_render import OjosRenderer
from ..widgets.renderizado.icono_sistema_render import IconoSistemaRenderer
from ..widgets.renderizado.barras_consumo_render import BarrasConsumoRenderer
from ..widgets.renderizado.sol_bateria_render import SolBateriaRenderer
from ..widgets.renderizado.radar_render import RadarRenderer
from ..widgets.renderizado.logger_widget_render import LoggerWidgetRenderer
from ..widgets.renderizado.boton_render import BotonRenderer


class PantallaMonitoreo:
    """
    Pantalla principal: la vista de "estado" del robot.

    Layout (16:9, proporción áurea, como define el plan):
      Fila 1: [Estados: ojos · íconos+consumo · sol]  [Logger]
      Fila 2: [Radar]                                  [Botón Control manual]

    Los widgets de esta pantalla se construyen sobre el MISMO EstadoRobot
    que usa la pantalla de control: aunque son instancias propias, todas
    leen del mismo sitio, así que se ven sincronizadas al instante.
    """

    def __init__(self, parent, estado: EstadoRobot, on_cambiar=None):
        """
        Constructor de la pantalla.

        parent     : el frame contenedor (en main.py).
        estado     : la 'caja maestra' compartida con todo el programa.
        on_cambiar : callback que se invoca al pulsar "Control manual".
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
        self.boton_manual = Boton("CONTROL MANUAL")
        if on_cambiar is not None:
            self.boton_manual.suscribir(on_cambiar)

        # --- Distribución de la gilla ---
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        self._construir_columna_estado()
        self._construir_logger()
        self._construir_radar()
        self._construir_navegacion()

    # --- Construcción de cada bloque ---

    def _construir_columna_estado(self):
        """Columna izquierda superior: ojos, íconos+consumo y sol."""
        col = tk.Frame(self.frame, bg=Paleta.FONDO_APP)
        col.grid(row=0, column=0, sticky="nw", padx=14, pady=10)

        # Ojos.
        canvas_ojos = tk.Canvas(col, width=130, height=56,
                                bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_ojos.pack(anchor="w")
        self.render_ojos = OjosRenderer(self.ojos, canvas_ojos, 12, 14)

        # Fila con íconos de sistema + barras de consumo.
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

        # Etiqueta de watts junto a las barras.
        self.lbl_consumo = tk.Label(fila, text="", bg=Paleta.FONDO_WIDGET,
                                    fg=Paleta.TEXTO_LOG, font=("Segoe UI", 8))
        self.lbl_consumo.pack(side="left", padx=(8, 0))

        # Sol de batería + etiquetas debajo.
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
        """Marco inferior izquierdo: radar + etiqueta de distancia."""
        marco = tk.Frame(self.frame, bg=Paleta.FONDO_APP)
        marco.grid(row=1, column=0, sticky="nw", padx=14, pady=(0, 10))

        canvas_radar = tk.Canvas(marco, width=380, height=380,
                                 bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_radar.pack()
        self.render_radar = RadarRenderer(self.radar, canvas_radar, 190, 190, 180)

        self.lbl_dist = tk.Label(marco, text="", bg=Paleta.FONDO_APP,
                                 fg=Paleta.DORADO, font=("Segoe UI", 10))
        self.lbl_dist.pack(pady=(6, 0))

    def _construir_navegacion(self):
        """Marco inferior derecho: botón para ir al control manual."""
        marco = tk.Frame(self.frame, bg=Paleta.FONDO_APP)
        marco.grid(row=1, column=1, sticky="ne", padx=14, pady=10)

        canvas_boton = tk.Canvas(marco, width=200, height=56,
                                 bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_boton.pack()
        self.render_boton = BotonRenderer(self.boton_manual, canvas_boton, 16, 8, 168, 40)

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

        # Etiquetas que dependen del estado (el logger se actualiza solo).
        self.lbl_consumo.config(text=self.barras.etiqueta_watts)

        self.lbl_sol.config(text=self.sol.etiqueta, fg=self.sol.color)
        minutos = self.estado.tiempo_restante_min
        self.lbl_tiempo.config(text=f"~{minutos} min" if minutos else "--")

        distancia = self.estado.distancia_obstaculo_cm
        texto = (f"Objeto detectado a {distancia:.0f} cm"
                 if distancia is not None else "Sin detección")
        self.lbl_dist.config(text=texto)
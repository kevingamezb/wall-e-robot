# wall-e-robot/app/pantallas/pantalla_principal.py
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
from ..widgets.renderizado.tarjeta import crear_tarjeta


class PantallaPrincipal:
    """
    La pantalla única de la aplicación: un panel de control, sin navegación.

    Layout (mockup walle_demo.html), todo dentro de tarjetas:
      Fila 1: [ESTADO]                      [TERMINAL]
      Fila 2: [RADAR]                       [CONTROL MANUAL]

    En la tarjeta CONTROL MANUAL viven: el estado de conexión (etiqueta),
    los botones CONECTAR/DESCONECTAR y el gamepad (cruceta + deslizadores).

    Espaciado: Paleta.UNIDAD y sus fracciones. La fila 2 estira ambas
    tarjetas con sticky="nsew" para que el gamepad y el radar queden a la
    misma altura; la tarjeta ESTADO se encoge a su contenido (sticky "nw").
    """

    def __init__(self, parent, estado: EstadoRobot,
                 on_conectar=None, on_desconectar=None):
        """
        Constructor de la pantalla.

        parent         : el frame contenedor (en main.py).
        estado         : la 'caja maestra' compartida con todo el programa.
        on_conectar    : callback al pulsar CONECTAR (abre el modal con la IP).
        on_desconectar : callback al pulsar DESCONECTAR (cuelga el teléfono).
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
        self.boton_conectar = Boton("CONECTAR")
        self.boton_desconectar = Boton("DESCONECTAR")
        if on_conectar is not None:
            self.boton_conectar.suscribir(on_conectar)
        if on_desconectar is not None:
            self.boton_desconectar.suscribir(on_desconectar)

        # --- Distribución de la gilla ---
        # Columnas con peso áureo (10:16): el radar y el gamepad comparten
        # espacio. La tarjeta ESTADO se estira a su celda (sticky "nsew")
        # y reparte su contenido internamente en 3 columnas.
        self.frame.grid_columnconfigure(0, weight=10)
        self.frame.grid_columnconfigure(1, weight=16)
        self.frame.grid_rowconfigure(0, weight=0)
        self.frame.grid_rowconfigure(1, weight=1)

        self._construir_columna_estado()
        self._construir_logger()
        self._construir_radar()
        self._construir_control_manual()

        # Arrancamos "sin conexión": main.py la marcará según corresponda.
        self.establecer_conexion(False, "SIN CONEXI\u00d3N")

    # --- Construcción de cada bloque (dentro de su tarjeta) ---

    def _construir_columna_estado(self):
        """Tarjeta 'ESTADO': ojos | íconos+consumo | sol, en 3 columnas.

        La tarjeta se estira a toda su celda (sticky nsew) y el contenido se
        reparte en 3 columnas que expanden parejo (pack side=left expand).
        Así no queda una franja apretada a la izquierda: cada grupo (ojos,
        consumo, sol) ocupa su tercio del ancho disponible, como el mockup.
        """
        col = crear_tarjeta(self.frame, "ESTADO")
        col.grid(row=0, column=0, sticky="nsew",
                 padx=Paleta.UNIDAD // 2, pady=Paleta.UNIDAD // 2)

        pad = Paleta.UNIDAD // 3
        arriba = Paleta.UNIDAD // 4

        # 3 columnas de igual peso (cada una expande a su tercio de ancho).
        col0 = tk.Frame(col, bg=Paleta.FONDO_WIDGET)
        col0.pack(side="left", expand=True, fill="both")
        col1 = tk.Frame(col, bg=Paleta.FONDO_WIDGET)
        col1.pack(side="left", expand=True, fill="both")
        col2 = tk.Frame(col, bg=Paleta.FONDO_WIDGET)
        col2.pack(side="left", expand=True, fill="both")

        # Columna 0: ojos.
        canvas_ojos = tk.Canvas(col0, width=130, height=56,
                                bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_ojos.pack(anchor="n", pady=(arriba, 0))
        self.render_ojos = OjosRenderer(self.ojos, canvas_ojos, 12, 14)

        # Columna 1: íconos de sistema arriba, barras de consumo + watts debajo.
        canvas_iconos = tk.Canvas(col1, width=150, height=30,
                                  bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_iconos.pack(anchor="n", pady=(arriba, 0))
        self.render_iconos = []
        for i, icono in enumerate(self.iconos):
            render = IconoSistemaRenderer(icono, canvas_iconos, 3 + i * 27, 3, 24)
            self.render_iconos.append(render)

        fila_barras = tk.Frame(col1, bg=Paleta.FONDO_WIDGET)
        fila_barras.pack(anchor="n", pady=(pad, 0))

        # Barras x5 (v4). 10 barritas de (alto+sep) = 10*26 = 260px de columna;
        # canvas de 264 para que la base respire dentro del alto disponible.
        canvas_barras = tk.Canvas(fila_barras, width=64, height=264,
                                  bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_barras.pack(side="left")
        self.render_barras = BarrasConsumoRenderer(
            self.barras, canvas_barras, 6, 260,
            ancho_barra=50, alto_barra=20, separacion=6)

        self.lbl_consumo = tk.Label(fila_barras, text="", bg=Paleta.FONDO_WIDGET,
                                    fg=Paleta.TEXTO_LOG, font=("Segoe UI", 8))
        self.lbl_consumo.pack(side="left", padx=(pad, 0))

        # Columna 2: sol de batería + etiquetas debajo.
        canvas_sol = tk.Canvas(col2, width=100, height=100,
                               bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_sol.pack(anchor="n", pady=(arriba, 0))
        self.render_sol = SolBateriaRenderer(self.sol, canvas_sol, 50, 50)

        self.lbl_sol = tk.Label(col2, text="", bg=Paleta.FONDO_WIDGET,
                                font=("Segoe UI", 10, "bold"))
        self.lbl_sol.pack(anchor="n", pady=(Paleta.UNIDAD // 4, 0))
        self.lbl_tiempo = tk.Label(col2, text="", bg=Paleta.FONDO_WIDGET,
                                   fg=Paleta.TEXTO_LOG, font=("Segoe UI", 9))
        self.lbl_tiempo.pack(anchor="n")

    def _construir_logger(self):
        """Tarjeta 'TERMINAL': la terminal de log."""
        marco = crear_tarjeta(self.frame, "TERMINAL")
        marco.grid(row=0, column=1, sticky="nsew",
                   padx=Paleta.UNIDAD // 2, pady=Paleta.UNIDAD // 2)
        self.render_logger = LoggerWidgetRenderer(self.logger, marco)

    def _construir_radar(self):
        """Tarjeta 'RADAR': radar + etiqueta de distancia, centrados."""
        marco = crear_tarjeta(self.frame, "RADAR")
        marco.grid(row=1, column=0, sticky="nsew",
                   padx=Paleta.UNIDAD // 2, pady=(0, Paleta.UNIDAD // 2))

        canvas_radar = tk.Canvas(marco, width=300, height=300,
                                 bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_radar.pack(expand=True, pady=(Paleta.UNIDAD // 4, 0))
        self.render_radar = RadarRenderer(self.radar, canvas_radar, 150, 150, 140)

        self.lbl_dist = tk.Label(marco, text="", bg=Paleta.FONDO_WIDGET,
                                 fg=Paleta.DORADO, font=("Segoe UI", 10))
        self.lbl_dist.pack(padx=Paleta.UNIDAD // 3,
                           pady=(Paleta.UNIDAD // 4, Paleta.UNIDAD // 3))

    def _construir_control_manual(self):
        """Tarjeta 'CONTROL MANUAL': conexión + gamepad."""
        marco = crear_tarjeta(self.frame, "CONTROL MANUAL")
        marco.grid(row=1, column=1, sticky="nsew",
                   padx=Paleta.UNIDAD // 2, pady=(0, Paleta.UNIDAD // 2))

        # Cabecera: estado de conexión (izquierda) y botones (derecha).
        cabecera = tk.Frame(marco, bg=Paleta.FONDO_WIDGET)
        cabecera.pack(fill="x", padx=Paleta.UNIDAD // 3,
                      pady=(Paleta.UNIDAD // 4, 0))

        lbl_captura = tk.Label(cabecera, text="CONEXI\u00d3N", bg=Paleta.FONDO_WIDGET,
                               fg=Paleta.TEXTO_TENUE, font=("Segoe UI", 7))
        lbl_captura.pack(anchor="w")
        self.lbl_estado_conexion = tk.Label(cabecera, text="", bg=Paleta.FONDO_WIDGET,
                                            font=("Segoe UI", 10, "bold"))
        self.lbl_estado_conexion.pack(anchor="w")

        botones = tk.Frame(cabecera, bg=Paleta.FONDO_WIDGET)
        botones.pack(side="right", pady=(0, Paleta.UNIDAD // 4))

        canvas_conectar = tk.Canvas(botones, width=106, height=30,
                                    bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_conectar.pack(side="left", padx=(0, Paleta.UNIDAD // 3))
        self.render_conectar = BotonRenderer(
            self.boton_conectar, canvas_conectar, 6, 5, 94, 20, tamano_fuente=9)

        canvas_desconectar = tk.Canvas(botones, width=130, height=30,
                                       bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_desconectar.pack(side="left")
        self.render_desconectar = BotonRenderer(
            self.boton_desconectar, canvas_desconectar, 6, 5, 118, 20, tamano_fuente=9)

        # Gamepad.
        canvas_gamepad = tk.Canvas(marco, width=600, height=300,
                                   bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_gamepad.pack(padx=Paleta.UNIDAD // 3,
                            pady=(Paleta.UNIDAD // 4, Paleta.UNIDAD // 3))
        self.render_gamepad = GamepadRenderer(self.gamepad, canvas_gamepad, 600, 300)

    # --- Conexión ---

    def conectar_gamepad(self, callback):
        """Conecta los comandos del gamepad hacia la conexión del robot."""
        self.gamepad.suscribir_comando(callback)

    def establecer_conexion(self, activa: bool, etiqueta: str):
        """
        Refleja el estado de la conexión en la interfaz.

        activa   : si hay (o no) un robot del que leer.
        etiqueta : qué dice el indicador (p. ej. "SIMULADOR", una IP...).
        """
        self.gamepad.habilitar(activa)
        self.lbl_estado_conexion.config(
            text=etiqueta,
            fg=Paleta.DORADO if activa else Paleta.GRIS,
        )

    # --- Ciclo de actualización ---

    def dibujar(self):
        """Redibuja todos los bloques de la pantalla (se llama cada ciclo)."""
        self.render_ojos.dibujar()
        for render in self.render_iconos:
            render.dibujar()
        self.render_barras.dibujar()
        self.render_sol.dibujar()
        self.render_radar.dibujar()
        self.render_conectar.dibujar()
        self.render_desconectar.dibujar()
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


if __name__ == "__main__":
    # Cajón de Pruebas: monta la pantalla única en una ventana real.
    print("=== PantallaPrincipal (cajón de pruebas) ===")

    raiz = tk.Tk()
    raiz.geometry("1080x700")
    raiz.configure(bg=Paleta.FONDO_APP)

    estado = EstadoRobot()
    pantalla = PantallaPrincipal(raiz, estado,
                                 on_conectar=lambda: None,
                                 on_desconectar=lambda: None)

    # Conexión simulada y gamepad "enchufado" a ella.
    from ..comunicacion.conexion import ComunicacionSimulada
    simulada = ComunicacionSimulada()
    pantalla.conectar_gamepad(simulada.enviar_mensaje)
    pantalla.establecer_conexion(True, "SIMULADOR")

    # Un par de ciclos con ambas conexiones (online y offline) para
    # comprobar que el renderer del gamepad conmuta bien la capa "apagado".
    for _ in range(3):
        simulada.actualizar_estado(estado)
        pantalla.dibujar()
        raiz.update()
    estado.conexion_activa = False
    pantalla.establecer_conexion(False, "SIN CONEXI\u00d3N")
    pantalla.dibujar()
    raiz.update()
    print("OK: pantalla única construida, ciclos y capa offline dibujados")
    raiz.destroy()
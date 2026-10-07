# wall-e-robot/app/pantallas/pantalla_principal.py
# Kevin Gámez - 13/09/2026


import tkinter as tk
from ..nucleo.paleta import Paleta, color_por_umbral
from ..nucleo.estado import EstadoRobot, Modo
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
from ..widgets.renderizado.tarjeta import crear_tarjeta, subir_decoracion


class PantallaPrincipal:
    """
    La pantalla única de la aplicación: un panel de control, sin navegación.

    Layout (tema Axiom + Wall-E), todo dentro de tarjetas:
      Fila 0: [BARRA DE SISTEMA (título + indicadores en vivo)]
      Fila 1: [ESTADO]                      [TERMINAL]
      Fila 2: [RADAR]                       [CONTROL MANUAL]

    En la tarjeta CONTROL MANUAL viven: el estado de conexión (etiqueta),
    los botones CONECTAR/DESCONECTAR/CONTROLES y el gamepad.

    Espaciado: Paleta.UNIDAD y sus fracciones. La fila 2 estira ambas
    tarjetas con sticky="nsew" para que el gamepad y el radar queden a la
    misma altura; la tarjeta ESTADO se encoge a su contenido (sticky "nw").
    """

    def __init__(self, parent, estado: EstadoRobot,
                 on_conectar=None, on_desconectar=None, on_controles=None):
        """
        Constructor de la pantalla.

        parent         : el frame contenedor (en main.py).
        estado         : la 'caja maestra' compartida con todo el programa.
        on_conectar    : callback al pulsar CONECTAR (abre el modal con la IP).
        on_desconectar : callback al pulsar DESCONECTAR (cuelga el teléfono).
        on_controles   : callback al pulsar CONTROLES (abre el mapeo de teclado).
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
        self.boton_controles = Boton("CONTROLES")
        if on_conectar is not None:
            self.boton_conectar.suscribir(on_conectar)
        if on_desconectar is not None:
            self.boton_desconectar.suscribir(on_desconectar)
        if on_controles is not None:
            self.boton_controles.suscribir(on_controles)

        # --- Distribución de la gilla ---
        # Columnas con peso áureo (10:16): el radar y el gamepad comparten
        # espacio. Fila 0 = barra de sistema (alto fijo), fila 1 = estado y
        # terminal (alto fijo), fila 2 = radar y control (la que crece).
        self.frame.grid_columnconfigure(0, weight=10)
        self.frame.grid_columnconfigure(1, weight=16)
        self.frame.grid_rowconfigure(0, weight=0)
        self.frame.grid_rowconfigure(1, weight=0)
        self.frame.grid_rowconfigure(2, weight=1)

        self._construir_barra_sistema()
        self._construir_columna_estado()
        self._construir_logger()
        self._construir_radar()
        self._construir_control_manual()

        # Arrancamos "sin conexión": main.py la marcará según corresponda.
        self.establecer_conexion(False, "SIN CONEXI\u00d3N")

    # --- Construcción de cada bloque (dentro de su tarjeta) ---

    def _construir_barra_sistema(self):
        """Barra HUD superior: identidad de la nave + indicadores en vivo.

        Es la "cabecera del terminal": a la izquierda el título del módulo,
        a la derecha tres lecturas que se actualizan solas en dibujar()
        (enlace, modo y batería), con la misma guarda anti-repintado que el
        resto de la pantalla.
        """
        barra = tk.Frame(self.frame, bg=Paleta.FONDO_APP)
        barra.grid(row=0, column=0, columnspan=2, sticky="ew",
                   padx=Paleta.UNIDAD // 2, pady=(Paleta.UNIDAD // 3, 0))

        # Izquierda: AXIOM ▸ subtítulo del módulo.
        izq = tk.Frame(barra, bg=Paleta.FONDO_APP)
        izq.pack(side="left")
        tk.Label(
            izq, text="AXIOM",
            bg=Paleta.FONDO_APP, fg=Paleta.AXIOM_CYAN,
            font=(Paleta.FUENTE_HUD, 15, "bold"),
        ).pack(side="left")
        tk.Label(
            izq, text="\u25b8 M\u00d3DULO DE CONTROL \u25b8 UNIDAD WALL-E",
            bg=Paleta.FONDO_APP, fg=Paleta.TEXTO_TENUE,
            font=(Paleta.FUENTE_HUD, 9),
        ).pack(side="left", padx=(8, 0))

        # Derecha: los tres indicadores en vivo.
        der = tk.Frame(barra, bg=Paleta.FONDO_APP)
        der.pack(side="right")

        self.lbl_ind_enlace = tk.Label(
            der, text="", bg=Paleta.FONDO_APP, font=(Paleta.FUENTE_HUD, 9, "bold"),
        )
        self.lbl_ind_enlace.pack(side="left", padx=(0, 22))
        self.lbl_ind_modo = tk.Label(
            der, text="", bg=Paleta.FONDO_APP, font=(Paleta.FUENTE_HUD, 9, "bold"),
        )
        self.lbl_ind_modo.pack(side="left", padx=(0, 22))
        self.lbl_ind_bateria = tk.Label(
            der, text="", bg=Paleta.FONDO_APP, font=(Paleta.FUENTE_HUD, 9, "bold"),
        )
        self.lbl_ind_bateria.pack(side="left")

        # Línea divisoria cian bajo la barra (el "borde luminoso").
        tk.Canvas(barra, height=2, bg=Paleta.CYAN_DIM,
                  highlightthickness=0).pack(fill="x", pady=(6, 0))

    def _actualizar_indicadores(self):
        """Refresca los 3 indicadores de la barra solo si algo cambió."""
        # Enlace: el estado que fijó establecer_conexion().
        activa = self._conexion_activa
        texto_enlace = "\u25cf ENLACE ACTIVO" if activa else "\u25cf SIN ENLACE"
        color_enlace = Paleta.AXIOM_CYAN if activa else Paleta.GRIS
        if (self.lbl_ind_enlace.cget("text") != texto_enlace
                or self.lbl_ind_enlace.cget("fg") != color_enlace):
            self.lbl_ind_enlace.config(text=texto_enlace, fg=color_enlace)

        # Modo: dorado en manual (es el del robot), tenue en automático.
        manual = self.estado.modo == Modo.MANUAL
        texto_modo = "MODO MANUAL" if manual else "MODO AUTOM\u00c1TICO"
        color_modo = Paleta.DORADO if manual else Paleta.TEXTO_TENUE
        if (self.lbl_ind_modo.cget("text") != texto_modo
                or self.lbl_ind_modo.cget("fg") != color_modo):
            self.lbl_ind_modo.config(text=texto_modo, fg=color_modo)

        # Batería: porcentaje coloreado con la misma regla por umbral.
        pct = int(round(max(0.0, min(1.0, self.estado.bateria)) * 100))
        texto_bat = f"BATER\u00cdA {pct}%"
        color_bat = color_por_umbral(self.estado.bateria)
        if (self.lbl_ind_bateria.cget("text") != texto_bat
                or self.lbl_ind_bateria.cget("fg") != color_bat):
            self.lbl_ind_bateria.config(text=texto_bat, fg=color_bat)

    def _construir_columna_estado(self):
        """Tarjeta 'ESTADO': ojos | íconos+consumo | sol, en 3 columnas.

        La tarjeta se estira a toda su celda (sticky nsew) y el contenido se
        reparte en 3 columnas que expanden parejo (pack side=left expand).
        Así no queda una franja apretada a la izquierda: cada grupo (ojos,
        consumo, sol) ocupa su tercio del ancho disponible, como el mockup.
        """
        col = crear_tarjeta(self.frame, "ESTADO")
        col.grid(row=1, column=0, sticky="nsew",
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

        subir_decoracion(col)

    def _construir_logger(self):
        """Tarjeta 'TERMINAL': la terminal de log."""
        marco = crear_tarjeta(self.frame, "TERMINAL")
        marco.grid(row=1, column=1, sticky="nsew",
                   padx=Paleta.UNIDAD // 2, pady=Paleta.UNIDAD // 2)
        self.render_logger = LoggerWidgetRenderer(self.logger, marco)
        subir_decoracion(marco)

    def _construir_radar(self):
        """Tarjeta 'RADAR': radar + etiqueta de distancia, centrados."""
        marco = crear_tarjeta(self.frame, "RADAR")
        marco.grid(row=2, column=0, sticky="nsew",
                   padx=Paleta.UNIDAD // 2, pady=(0, Paleta.UNIDAD // 2))

        canvas_radar = tk.Canvas(marco, width=300, height=300,
                                 bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_radar.pack(expand=True, pady=(Paleta.UNIDAD // 4, 0))
        self.render_radar = RadarRenderer(self.radar, canvas_radar, 150, 150, 140)

        self.lbl_dist = tk.Label(marco, text="", bg=Paleta.FONDO_WIDGET,
                                 fg=Paleta.AXIOM_CYAN, font=(Paleta.FUENTE_HUD, 10, "bold"))
        self.lbl_dist.pack(padx=Paleta.UNIDAD // 3,
                           pady=(Paleta.UNIDAD // 4, Paleta.UNIDAD // 3))
        subir_decoracion(marco)

    def _construir_control_manual(self):
        """Tarjeta 'CONTROL MANUAL': conexión + gamepad."""
        marco = crear_tarjeta(self.frame, "CONTROL MANUAL")
        marco.grid(row=2, column=1, sticky="nsew",
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

        canvas_controles = tk.Canvas(botones, width=86, height=30,
                                     bg=Paleta.FONDO_WIDGET, highlightthickness=0)
        canvas_controles.pack(side="left", padx=(0, Paleta.UNIDAD // 3))
        self.render_controles = BotonRenderer(
            self.boton_controles, canvas_controles, 6, 5, 74, 20, tamano_fuente=8)

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
        subir_decoracion(marco)

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
        self._conexion_activa = activa
        self.gamepad.habilitar(activa)
        self.lbl_estado_conexion.config(
            text=etiqueta,
            fg=Paleta.DORADO if activa else Paleta.GRIS,
        )

    # --- Ciclo de actualización ---

    def dibujar(self):
        """Redibuja todos los bloques de la pantalla (se llama cada ciclo)."""
        self._actualizar_indicadores()
        self.render_ojos.dibujar()
        for render in self.render_iconos:
            render.dibujar()
        self.render_barras.dibujar()
        self.render_sol.dibujar()
        self.render_radar.dibujar()
        self.render_conectar.dibujar()
        self.render_desconectar.dibujar()
        self.render_controles.dibujar()
        self.render_gamepad.dibujar()

        # Etiquetas que dependen del estado (el logger se actualiza solo).
        # Cada una solo se reconfigura si su texto cambió (evita trabajo
        # muerto de Tk en cada ciclo de 60 ms).
        texto_consumo = self.barras.etiqueta_watts
        color_consumo = self.barras.color
        if (self.lbl_consumo.cget("text") != texto_consumo
                or self.lbl_consumo.cget("fg") != color_consumo):
            self.lbl_consumo.config(text=texto_consumo, fg=color_consumo)

        texto_sol = self.sol.etiqueta
        if self.lbl_sol.cget("text") != texto_sol or self.lbl_sol.cget("fg") != self.sol.color:
            self.lbl_sol.config(text=texto_sol, fg=self.sol.color)

        minutos = self.estado.tiempo_restante_min
        texto_tiempo = f"~{minutos} min" if minutos else "--"
        if self.lbl_tiempo.cget("text") != texto_tiempo:
            self.lbl_tiempo.config(text=texto_tiempo)

        distancia = self.estado.distancia_obstaculo_cm
        texto_dist = (f"Objeto detectado a {distancia:.0f} cm"
                      if distancia is not None else "Sin detección")
        if self.lbl_dist.cget("text") != texto_dist:
            self.lbl_dist.config(text=texto_dist)


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
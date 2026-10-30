# wall-e-robot/app/pantallas/pantalla_principal.py
# Kevin Gámez - 13/09/2026
# Rediseño de la GUI.


import time
import textwrap
import tkinter as tk
import tkinter.font as tkfont

from ..nucleo.paleta import Paleta
from ..nucleo.disenio import Disenio
from ..nucleo.estado import EstadoRobot, Modo
from ..widgets.logica.boton import Boton
from ..widgets.logica.ojos import Ojos
from ..widgets.logica.icono_sistema import IconoSistema, TipoIcono
from ..widgets.logica.sol_bateria import SolBateria
from ..widgets.logica.barras_consumo import BarrasConsumo
from ..widgets.logica.proximidad import Proximidad
from ..widgets.logica.navegacion import Navegacion
from ..widgets.logica.logger_widget import LoggerWidget
from ..widgets.logica.gamepad import Gamepad
from ..widgets.renderizado.ojos_render import OjosRenderer
from ..widgets.renderizado.icono_sistema_render import IconoSistemaRenderer
from ..widgets.renderizado.barras_consumo_render import BarrasConsumoRenderer
from ..widgets.renderizado.sol_bateria_render import SolBateriaRenderer
from ..widgets.renderizado.navegacion_render import NavegacionRenderer
from ..widgets.renderizado.logger_widget_render import LoggerWidgetRenderer
from ..widgets.renderizado.boton_imagen_render import BotonImagenRenderer
from ..widgets.renderizado.gamepad_render import GamepadRenderer
from ..widgets.renderizado.base_render import rectangulo_redondeado
from ..widgets.renderizado.recoloreo import Recoloreo
from ..widgets.renderizado.tarjeta import Tarjeta, pantalla_oscura, linea_vertical
from ..widgets.renderizado.texto_render import Texto
from ..widgets.renderizado import carga_recursos


# Tipografía de los textos del diseño (px por unidad de diseño).
COLOR_TAB_FONDO = "#24272b"
SIN_CONEXION = "SIN CONEXIÓN"


def _achaflanado(caja, chaflan):
    """Puntos de un rectángulo con las 4 esquinas cortadas en diagonal."""
    x1, y1, x2, y2 = caja
    c = chaflan
    return [x1 + c, y1, x2 - c, y1, x2, y1 + c, x2, y2 - c,
            x2 - c, y2, x1 + c, y2, x1, y2 - c, x1, y1 + c]


class PantallaPrincipal:
    """Pantalla única de la aplicación: barra lateral de conexión + panel de control."""
    def __init__(self, parent, estado: EstadoRobot, escala,
                 on_conectar=None, on_desconectar=None, on_controles=None,
                 on_modo=None):
        """
        parent         : el frame contenedor (en main.py).
        estado         : el estado compartido con todo el programa.
        escala         : Escala (unidades de diseño -> píxeles).
        on_conectar    : callback(ip, puerto); en main abre la conexión en un hilo.
        on_desconectar : callback al pulsar DESCONECTAR o cancelar la conexión.
        on_controles   : callback al pulsar CONTROLES (abre el mapeo de teclado).
        on_modo        : callback al pulsar el rótulo de modo (manual/automático).
        """
        self.estado = estado
        self.e = e = escala
        self.campo_ip: tk.Entry
        self.campo_port: tk.Entry
        self._on_conectar = on_conectar
        self._on_desconectar = on_desconectar
        self._conexion_activa = False
        self._conexion_pendiente = False
        self._tiempos = []          # instantes de los últimos dibujos (FPS)
        self._latencia_ms = None

        self.canvas = tk.Canvas(parent, width=e.ancho, height=e.alto,
                                bg=Paleta.FONDO_APP, highlightthickness=0)
        self.canvas.pack()
        self.frame = self.canvas   # compatibilidad con el diseño anterior

        # Widgets lógicos
        self.ojos = Ojos(estado)
        self.iconos = {t: IconoSistema(estado, t) for t in TipoIcono}
        self.sol = SolBateria(estado)
        self.barras = BarrasConsumo(estado)
        self.proximidad = Proximidad(estado)
        self.navegacion = Navegacion(estado)
        self.logger = LoggerWidget(estado)
        self.gamepad = Gamepad(estado)
        self.boton_conectar = Boton("Conectar")
        self.boton_controles = Boton("Controles")
        # El botón de modo solo se habilita con conexión (necesita al robot).
        self.boton_modo = Boton("MODO: --", habilitado=False)
        self.boton_conectar.suscribir(self._al_pulsar_conectar)
        if on_controles is not None:
            self.boton_controles.suscribir(on_controles)
        if on_modo is not None:
            self.boton_modo.suscribir(on_modo)

        self._construir_marco()
        self._construir_barra_lateral()
        self._construir_estado()
        self._construir_energia()
        self._construir_registro()
        self._construir_navegacion()
        self._construir_control()

        self.establecer_conexion(False, SIN_CONEXION)

    # Marco de la ventana
    def _construir_marco(self):
        """Fondo plateado, logo, cabecera y los dos paneles negros."""
        e, c = self.e, self.canvas
        c.create_image(0, 0, image=carga_recursos.cargar_fondo(
            "fondo_app", e.ancho, e.alto), anchor="nw")
        c.create_image(e(66), e(238), image=carga_recursos.cargar_ancho(
            "titulo", e(828)), anchor="nw")

        for caja, chaflan in ((Disenio.BARRA_LATERAL, 40),
                              (Disenio.PANEL_CENTRAL, Disenio.CHAFLAN_PANEL)):
            puntos = [e(v) for v in _achaflanado(caja, chaflan)]
            c.create_polygon(puntos, fill=Paleta.FONDO_NEGRO, outline="#24272b",
                             width=max(1, e(8)))

        # Cabecera: rayas + título + telemetría.
        x1, y1, x2, _ = Disenio.RAYAS_TITULO
        c.create_image(e(x1), e(y1), image=carga_recursos.cargar_ancho(
            "bombillitos", e(x2 - x1)), anchor="nw")
        tx, ty, _, tb = Disenio.TITULO_PANEL
        Texto(c, e(tx), e((ty + tb) / 2), "Panel de Control", e.fuente(92),
              Paleta.TEXTO_LOG, ancla="w", contorno=Paleta.TINTA,
              grosor=max(2, e(7)))
        mx, my, _, mb = Disenio.TELEMETRIA
        self._telemetria = Texto(c, e(mx), e((my + mb) / 2), "| -- FPS | -- ms |",
                                 e.fuente(30), Paleta.TEXTO_LOG, ancla="w")

    # Barra lateral (conexión)
    def _construir_barra_lateral(self):
        e, c = self.e, self.canvas
        x1, y1, x2, y2 = e.caja(Disenio.SELECTOR)
        c.create_polygon(
            x1 + e(40), y1, x2 - e(40), y1, x2, y1 + e(40), x2, y2, x1, y2,
            x1, y1 + e(40), fill=COLOR_TAB_FONDO, outline="")

        # Pestañas: "Conectar" (activa) y "Controles" (abre el mapeo de teclas).
        cx, cy, cx2, cy2 = Disenio.TAB_CONECTAR
        Texto(c, e((cx + cx2) / 2), e((cy + cy2) / 2), "Conectar", e.fuente(44),
              Paleta.DORADO, ancla="center")
        kx, ky, kx2, ky2 = Disenio.TAB_CONTROLES
        self._tab_controles = Texto(c, e((kx + kx2) / 2), e((ky + ky2) / 2),
                                    "Controles", e.fuente(44), Paleta.TEXTO_LOG,
                                    ancla="center")
        self._enlazar_clic(self._tab_controles.id, self.boton_controles,
                           lambda hover: self._tab_controles.poner(
                               color=Paleta.DORADO if hover else Paleta.TEXTO_LOG))

        # Campos IP y puerto.
        familia = tkfont.nametofont("TkDefaultFont").actual("family")
        for caja_etiqueta, caja_campo, etiqueta, valor, nombre in (
            (Disenio.ETIQUETA_IP, Disenio.CAMPO_IP, "IP:", "192.168.4.1", "campo_ip"),
            (Disenio.ETIQUETA_PORT, Disenio.CAMPO_PORT, "PORT:", "8080", "campo_port"),
        ):
            ex, ey, _, eb = caja_etiqueta
            Texto(c, e(ex), e(eb), etiqueta, e.fuente(88), Paleta.DORADO,
                  ancla="sw")
            fx1, fy1, fx2, fy2 = e.caja(caja_campo)
            campo = tk.Entry(
                c, font=(familia, -max(10, e(48))), bg=Paleta.TARJETA,
                fg=Paleta.TINTA, insertbackground=Paleta.TINTA, relief="flat",
                bd=0, highlightthickness=0, disabledbackground="#b9bfc5",
                disabledforeground=Paleta.FONDO_WIDGET)
            campo.insert(0, valor)
            campo.bind("<Return>", lambda _ev: self.boton_conectar.presionar())
            c.create_window(fx1, fy1, window=campo, anchor="nw",
                            width=fx2 - fx1, height=fy2 - fy1)
            setattr(self, nombre, campo)

        # Botón Conectar / Desconectar.
        bx1, by1, bx2, by2 = e.caja(Disenio.BOTON_CONECTAR)
        self.render_conectar = BotonImagenRenderer(
            self.boton_conectar, c, bx1, by1, bx2 - bx1, "boton_conectar",
            variantes={
                "hover":      [(Paleta.DORADO, "#f3cd5a", 45)],
                "presionado": [(Paleta.DORADO, "#c79a1f", 45)],
            },
            texto="Conectar", texto_px=e.fuente(116), texto_color=Paleta.TINTA)

        # Estado de la conexión / errores.
        sx, sy, _, _ = Disenio.ESTADO_CONEXION
        self._estado_conexion = Texto(c, e(sx), e(sy), "", e.fuente(46),
                                      Paleta.GRIS, ancla="nw")

    def _enlazar_clic(self, item, boton, al_hover=None):
        """Hace que un ítem del canvas se comporte como botón lógico."""
        c = self.canvas

        def entrar(_ev):
            if boton.habilitado:
                c.configure(cursor="hand2")
                if al_hover:
                    al_hover(True)

        def salir(_ev):
            c.configure(cursor="")
            if al_hover:
                al_hover(False)

        c.tag_bind(item, "<ButtonPress-1>", lambda _ev: boton.presionar())
        c.tag_bind(item, "<ButtonRelease-1>", lambda _ev: boton.soltar())
        c.tag_bind(item, "<Enter>", entrar)
        c.tag_bind(item, "<Leave>", salir)

    # Tarjetas
    def _construir_estado(self):
        e, c = self.e, self.canvas
        self.t_estado = Tarjeta(c, e, Disenio.TARJETA_ESTADO, Disenio.LINEA_ESTADO,
                                "estado", "Estado")
        pantalla_oscura(c, e, Disenio.PANTALLA_ESTADO)

        # Rótulo de modo: ícono del mando + texto (clic = cambiar de modo).
        ix, iy, ix2, _ = Disenio.ICONO_MODO
        self.render_modo_icono = IconoSistemaRenderer(
            self.iconos[TipoIcono.MODO_MANUAL], c, e(ix), e(iy), e(ix2 - ix))
        self.render_modo_icono.dibujar()
        tx, ty = Disenio.TEXTO_MODO
        self._modo_titulo = Texto(c, e(tx), e(ty), "Modo Manual", e.fuente(44),
                                  Paleta.GRIS, ancla="nw")
        sx, sy = Disenio.TEXTO_MODO_SUB
        self._modo_sub = Texto(c, e(sx), e(sy), "Desactivado", e.fuente(30),
                               Paleta.GRIS, ancla="nw")
        for item in (self.render_modo_icono._ids["imagen"], self._modo_titulo.id,
                     self._modo_sub.id):
            self._enlazar_clic(item, self.boton_modo)

        ox, oy = Disenio.OJOS_CENTRO
        alto = e(Disenio.OJOS_ALTO)
        self.render_ojos = OjosRenderer(
            self.ojos, c, e(ox) - alto, e(oy) - alto / 2, alto_imagen=alto)

        self.render_iconos = []
        orden = (TipoIcono.CONEXION, TipoIcono.CARGANDO, TipoIcono.ADVERTENCIA,
                 TipoIcono.ERROR)
        for tipo, x in zip(orden, Disenio.ICONOS_X):
            self.render_iconos.append(IconoSistemaRenderer(
                self.iconos[tipo], c, e(x), e(Disenio.ICONOS_Y),
                e(Disenio.ICONO_LADO)))

    def _construir_energia(self):
        e, c = self.e, self.canvas
        self.t_consumo = Tarjeta(c, e, Disenio.TARJETA_ENERGIA, Disenio.LINEA_CONSUMO,
                                 "consumo", "Consumo")
        self.t_bateria = Tarjeta(c, e, None, Disenio.LINEA_BATERIA,
                                 "bateria", "Batería")
        self.render_barras = BarrasConsumoRenderer(self.barras, c, e)
        wx, wy = Disenio.CONSUMO_ETIQUETA
        self._lbl_consumo = Texto(c, e(wx), e(wy), "", e.fuente(62), Paleta.GRIS,
                                  ancla="center", contorno=Paleta.TINTA,
                                  grosor=max(2, e(6)))

        pantalla_oscura(c, e, Disenio.PANTALLA_BATERIA)
        sx, sy = Disenio.SOL_CENTRO
        self.render_sol = SolBateriaRenderer(self.sol, c, e, sx, sy,
                                             Disenio.SOL_RADIO)
        l1x, l1y = Disenio.BATERIA_LINEA1
        l2x, l2y = Disenio.BATERIA_LINEA2
        self._lbl_sol = Texto(c, e(l1x), e(l1y), "", e.fuente(62), Paleta.DORADO_DIM,
                              ancla="center", contorno=Paleta.DORADO_BORDE,
                              grosor=max(2, e(6)))
        self._lbl_pct = Texto(c, e(l2x), e(l2y), "", e.fuente(62), Paleta.DORADO,
                              ancla="center", contorno=Paleta.DORADO_BORDE,
                              grosor=max(2, e(6)))

    def _construir_registro(self):
        e, c = self.e, self.canvas
        self.t_registro = Tarjeta(c, e, Disenio.TARJETA_REGISTRO,
                                  Disenio.LINEA_REGISTRO, "registro", "Registro")
        x1, y1, x2, y2 = e.caja(Disenio.PANTALLA_REGISTRO)
        rectangulo_redondeado(c, x1, y1, x2, y2, e(46), fill=Paleta.TARJETA,
                              outline=Paleta.TINTA, width=max(2, e(9)))
        self.render_logger = LoggerWidgetRenderer(self.logger, c, e)

    def _construir_navegacion(self):
        e, c = self.e, self.canvas
        self.t_navegacion = Tarjeta(c, e, Disenio.TARJETA_NAVEGACION,
                                    Disenio.LINEA_NAVEGACION, "navegacion",
                                    "Navegación")
        sx, y1, y2, g = Disenio.SEP_NAVEGACION
        linea_vertical(c, e, sx, y1, y2, g)
        self.render_navegacion = NavegacionRenderer(
            self.proximidad, self.navegacion, c, e)

    def _construir_control(self):
        e, c = self.e, self.canvas
        self.t_control = Tarjeta(c, e, Disenio.TARJETA_CONTROL,
                                 Disenio.LINEA_CONTROL, "control", "Control")
        sx, y1, y2, g = Disenio.SEP_CONTROL
        linea_vertical(c, e, sx, y1, y2, g)
        self.render_gamepad = GamepadRenderer(self.gamepad, c, e)

    # Conexión
    def conectar_gamepad(self, callback):
        """Conecta los comandos del gamepad hacia la conexión del robot."""
        self.gamepad.suscribir_comando(callback)

    def _al_pulsar_conectar(self):
        """Botón de la barra lateral: conecta, cancela el intento o desconecta."""
        if self._conexion_pendiente:
            if self._on_desconectar:
                self._on_desconectar()
            return
        if self._conexion_activa:
            if self._on_desconectar:
                self._on_desconectar()
            return
        ip = self.campo_ip.get().strip()
        try:
            puerto = int(self.campo_port.get().strip())
            if not 0 < puerto < 65536:
                raise ValueError("el puerto debe estar entre 1 y 65535")
            if self._on_conectar:
                self._on_conectar(ip, puerto)
        except (OSError, ValueError) as error:
            self.mostrar_error(f"No se pudo conectar: {error}")

    def mostrar_error(self, mensaje: str):
        """Muestra un error de conexión bajo el botón (en rojo)."""
        self._estado_conexion.poner(
            texto=textwrap.fill(mensaje, 24), color=Paleta.ROJO)

    def establecer_conectando(self, etiqueta: str):
        """Indica que se está abriendo la conexión; el botón permite cancelar."""
        self._conexion_pendiente = True
        self._conexion_activa = False
        self.boton_modo.habilitado = False
        self.boton_conectar.texto = "Cancelar"
        for campo in (self.campo_ip, self.campo_port):
            campo.config(state="disabled")
        self._estado_conexion.poner(
            texto=textwrap.fill(f"Conectando a {etiqueta}...", 24),
            color=Paleta.DORADO)

    def establecer_conexion(self, activa: bool, etiqueta: str):
        """
        Refleja el estado de la conexión en la interfaz.

        activa   : si hay (o no) un robot del que leer.
        etiqueta : qué dice el indicador (p. ej. "SIN CONEXIÓN", una IP...).
        """
        self._conexion_pendiente = False
        self._conexion_activa = activa
        # El botón de modo necesita al robot para enviarle el comando.
        self.boton_modo.habilitado = activa
        self.boton_conectar.texto = "Desconectar" if activa else "Conectar"
        for campo in (self.campo_ip, self.campo_port):
            campo.config(state="disabled" if activa else "normal")
        self._estado_conexion.poner(
            texto=textwrap.fill(etiqueta, 24),
            color=Paleta.DORADO if activa else Paleta.GRIS)

    def actualizar_latencia(self, milisegundos):
        """Dato de latencia (ms) para la cabecera; None si no hay."""
        self._latencia_ms = milisegundos

    # Ciclo de actualización
    def _fps(self) -> int:
        ahora = time.perf_counter()
        self._tiempos.append(ahora)
        self._tiempos = [t for t in self._tiempos if ahora - t <= 1.0]
        return len(self._tiempos)

    @staticmethod
    def _oscuro(color, t=0.62):
        return Recoloreo.interpolar(color, "#000000", t)

    def dibujar(self):
        """Redibuja todos los bloques de la pantalla (se llama cada ciclo)."""
        estado = self.estado
        # El gamepad solo manda en manual: en automático decide el robot.
        self.gamepad.habilitar(
            self._conexion_activa and estado.modo == Modo.MANUAL)

        manual = estado.modo == Modo.MANUAL
        if not self._conexion_activa:
            self.boton_modo.texto = "MODO: --"
        else:
            self.boton_modo.texto = "MODO: MANUAL" if manual else "MODO: AUTOMÁTICO"

        # Cabecera
        ms = "--" if self._latencia_ms is None else self._latencia_ms
        self._telemetria.poner(texto=f"| {self._fps()} FPS | {ms} ms |")

        # Estado
        self.render_modo_icono.dibujar()
        self._modo_titulo.poner(
            color=Paleta.DORADO if manual else Paleta.GRIS)
        self._modo_sub.poner(texto="Activado" if manual else "Desactivado",
                             color=Paleta.DORADO if manual else Paleta.GRIS)
        self.render_ojos.dibujar()
        for render in self.render_iconos:
            render.dibujar()

        # Energía
        self.render_barras.dibujar()
        self.render_sol.dibujar()
        color_consumo = self.barras.color
        self._lbl_consumo.poner(texto=self.barras.etiqueta_watts,
                                color=color_consumo,
                                contorno=self._oscuro(color_consumo, 0.7))
        color_sol = self.sol.color
        pct = (f"{int(round(max(0.0, min(1.0, estado.bateria)) * 100))} %"
               if estado.conexion_activa else "-- %")
        self._lbl_sol.poner(texto=self.sol.etiqueta,
                            color=self._oscuro(color_sol, 0.33),
                            contorno=self._oscuro(color_sol, 0.7))
        self._lbl_pct.poner(texto=pct, color=color_sol,
                            contorno=self._oscuro(color_sol, 0.62))

        # Navegación y control
        self.render_navegacion.dibujar()
        self.render_gamepad.dibujar()

        # Pastillas de alerta de cada tarjeta.
        if estado.hay_error or estado.modulo_inactivo:
            alerta = Paleta.ROJO
        elif estado.hay_advertencia:
            alerta = Paleta.NARANJA
        else:
            alerta = Paleta.DORADO
        self.t_estado.alertar(alerta)
        self.t_consumo.alertar(color_consumo if color_consumo != Paleta.GRIS
                               else Paleta.DORADO)
        self.t_bateria.alertar(color_sol if color_sol != Paleta.GRIS
                               else Paleta.DORADO)
        cerca = self.proximidad.cercania
        self.t_navegacion.alertar(Paleta.ROJO if cerca > 0.7 else
                                  Paleta.NARANJA if cerca > 0.4 else Paleta.DORADO)
        self.t_control.alertar(Paleta.DORADO if self.gamepad.habilitado
                               else Paleta.GRIS)
        self.render_conectar.dibujar()


# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.pantallas.pantalla_principal

if __name__ == "__main__":
    from ..nucleo.disenio import Escala
    print("PantallaPrincipal")

    raiz = tk.Tk()
    escala = Escala(0.3)
    raiz.geometry(f"{escala.ancho}x{escala.alto}")
    raiz.configure(bg=Paleta.FONDO_APP)

    estado = EstadoRobot()
    pantalla = PantallaPrincipal(raiz, estado, escala,
                                 on_conectar=lambda ip, puerto: None,
                                 on_desconectar=lambda: None)
    comandos = []
    pantalla.conectar_gamepad(comandos.append)

    # Conectado y en manual -> el mando queda activo; luego sin conexión.
    estado.conexion_activa = True
    estado.modo = Modo.MANUAL
    pantalla.establecer_conexion(True, "192.168.4.1")
    for _ in range(3):
        pantalla.dibujar()
        raiz.update()
    assert pantalla.gamepad.habilitado, "Conectado + manual habilita el mando"

    estado.conexion_activa = False
    pantalla.establecer_conexion(False, SIN_CONEXION)
    pantalla.dibujar()
    raiz.update()
    assert not pantalla.gamepad.habilitado, "Sin conexión apaga el mando"

    # Un puerto inválido se muestra como error, sin lanzar excepción.
    pantalla.campo_port.delete(0, "end")
    pantalla.campo_port.insert(0, "abc")
    pantalla.boton_conectar.presionar()
    assert "No se pudo conectar" in pantalla._estado_conexion.texto
    print("OK: pantalla construida, ciclos, capa apagada y error de puerto")
    raiz.destroy()

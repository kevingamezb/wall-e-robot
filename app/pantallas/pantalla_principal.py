import json
import time
import textwrap
import tkinter as tk
import tkinter.font as tkfont

from ..nucleo.paleta import Paleta
from ..nucleo.disenio import Disenio, RECORTE_SUPERIOR
from ..nucleo.estado import EstadoRobot, Modo
from ..rutas import directorio_configuracion
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
from ..widgets.renderizado.texto_render import Texto, foto_texto
from ..widgets.renderizado import carga_recursos
from .modal_controles import ModalControles


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
                 on_conectar=None, on_desconectar=None, on_modo=None,
                 mapeo=None, on_cambio_mapeo=None, al_captura=None, on_ota=None,
                 on_detener=None, on_demo=None, on_configuracion=None):
        """
        parent         : el frame contenedor (en main.py).
        estado         : el estado compartido con todo el programa.
        escala         : Escala (unidades de diseño -> píxeles).
        on_conectar    : callback(ip, puerto); en main abre la conexión en un hilo.
        on_desconectar : callback al pulsar DESCONECTAR o cancelar la conexión.
        on_modo        : callback al pulsar el rótulo de modo (manual/automático).
        mapeo          : MapeoTeclado que edita la pestaña "Controles" de la barra
                         lateral (None = sin esa pestaña).
        on_cambio_mapeo: callback tras cada cambio del mapeo (para guardarlo).
        al_captura     : callback(bool): True mientras se captura una tecla nueva.
        """
        self.estado = estado
        self.e = e = escala
        self.campo_ip: tk.Entry
        self.campo_port: tk.Entry
        self._on_conectar = on_conectar
        self._on_ota = on_ota
        self._on_desconectar = on_desconectar
        self._mapeo = mapeo
        self._on_cambio_mapeo = on_cambio_mapeo
        self._al_captura = al_captura
        self._pagina = "conectar"
        # Conserva los objetos Texto para que sus PhotoImage sobrevivan al vaciar la caché.
        self._items_conexion = []
        self._items_avanzados = []
        self._avanzado = False
        self._conexion_activa = False
        self._conexion_pendiente = False
        self._destino_intentado = None
        self._tiempos = []          # instantes de los últimos dibujos (FPS)
        self._latencia_ms = None
        self._rotulos_acciones = {}

        self.canvas = tk.Canvas(parent, width=e.ancho, height=e.alto_panel,
                                bg=Paleta.FONDO_APP, highlightthickness=0,
                                scrollregion=(0, e(RECORTE_SUPERIOR), e.ancho, e.alto))
        self.canvas.pack()
        self.canvas.yview_moveto(0)
        self.frame = self.canvas   # compatibilidad con el diseño anterior

        self.ojos = Ojos(estado)
        self.iconos = {t: IconoSistema(estado, t) for t in TipoIcono}
        self.sol = SolBateria(estado)
        self.barras = BarrasConsumo(estado)
        self.proximidad = Proximidad(estado)
        self.navegacion = Navegacion(estado)
        self.logger = LoggerWidget(estado)
        self.gamepad = Gamepad(estado)
        self.boton_conectar = Boton("Conectar")
        self.boton_modo = Boton("MODO: --", habilitado=False)
        self.boton_conectar.suscribir(self._al_pulsar_conectar)
        if on_modo is not None:
            self.boton_modo.suscribir(on_modo)

        self._construir_marco()
        if on_configuracion is not None:
            self._crear_accion("Configuración", on_configuracion, (2660, 267, 3120, 364),
                               Paleta.FONDO_WIDGET, color_texto=Paleta.DORADO, habilitada=True)
        self._acciones_robot = [
            self._crear_accion(texto, callback, caja, color)
            for texto, callback, caja, color in (
                ("Demo", on_demo, (3160, 267, 3430, 364), Paleta.DORADO),
                ("Detener", on_detener, (3470, 267, 3803, 364), Paleta.ROJO),
            ) if callback is not None
        ]
        self._construir_barra_lateral()
        self._construir_estado()
        self._construir_energia()
        self._construir_registro()
        self._construir_navegacion()
        self._construir_control()

        self.establecer_conexion(False, SIN_CONEXION)

    def _crear_accion(self, texto, callback, caja, color,
                      color_texto=Paleta.TINTA, habilitada=False):
        e, c = self.e, self.canvas
        estado = "normal" if habilitada else "disabled"
        boton = tk.Button(c, text=texto, command=callback, bg=color,
                          relief="flat", state=estado)
        rotulos = {
            "normal": foto_texto(texto, e.fuente(46), color_texto, master=c),
            "disabled": foto_texto(texto, e.fuente(46), Paleta.GRIS, master=c),
        }
        self._rotulos_acciones[boton] = rotulos
        boton.configure(image=rotulos[estado])
        x1, y1, x2, y2 = e.caja(caja)
        c.create_window(x1, y1, window=boton, anchor="nw",
                        width=x2-x1, height=y2-y1)
        return boton

    def _construir_marco(self):
        """Fondo plateado, logo, cabecera y los dos paneles negros."""
        e, c = self.e, self.canvas
        c.create_image(0, 0, image=carga_recursos.cargar_fondo(
            "fondo_app", e.ancho, e.alto, master=c), anchor="nw")
        c.create_image(e(66), e(238), image=carga_recursos.cargar_ancho(
            "titulo", e(828), master=c), anchor="nw")

        for caja, chaflan in ((Disenio.BARRA_LATERAL, 40),
                              (Disenio.PANEL_CENTRAL, Disenio.CHAFLAN_PANEL)):
            puntos = [e(v) for v in _achaflanado(caja, chaflan)]
            c.create_polygon(puntos, fill=Paleta.FONDO_NEGRO, outline="#24272b",
                             width=max(1, e(8)))

        x1, y1, x2, _ = Disenio.RAYAS_TITULO
        c.create_image(e(x1), e(y1), image=carga_recursos.cargar_ancho(
            "bombillitos", e(x2 - x1), master=c), anchor="nw")
        tx, ty, _, tb = Disenio.TITULO_PANEL
        self._titulo_panel = Texto(
            c, e(tx), e((ty + tb) / 2), "Panel de Control", e.fuente(92),
            Paleta.TEXTO_LOG, ancla="w", contorno=Paleta.TINTA,
            grosor=max(2, e(7)))
        mx, my, _, mb = Disenio.TELEMETRIA
        self._telemetria = Texto(c, e(mx), e((my + mb) / 2), "| -- FPS | -- ms |",
                                 e.fuente(30), Paleta.TEXTO_LOG, ancla="w")

    def _construir_barra_lateral(self):
        e, c = self.e, self.canvas
        x1, y1, x2, y2 = e.caja(Disenio.SELECTOR)
        c.create_polygon(
            x1 + e(40), y1, x2 - e(40), y1, x2, y1 + e(40), x2, y2, x1, y2,
            x1, y1 + e(40), fill=COLOR_TAB_FONDO, outline="")

        cx, cy, cx2, cy2 = Disenio.TAB_CONECTAR
        self._tab_conectar = Texto(c, e((cx + cx2) / 2), e((cy + cy2) / 2),
                                   "Conectar", e.fuente(44), Paleta.DORADO,
                                   ancla="center")
        kx, ky, kx2, ky2 = Disenio.TAB_CONTROLES
        self._tab_controles = Texto(c, e((kx + kx2) / 2), e((ky + ky2) / 2),
                                    "Controles", e.fuente(44), Paleta.TEXTO_LOG,
                                    ancla="center")
        # El clic se enlaza a toda la pestaña, no solo a los píxeles del texto:
        # así funciona también al pulsar el borde o el hueco entre letras.
        self._areas_pestanas = []
        for caja, nombre in ((Disenio.TAB_CONECTAR, "conectar"),
                             (Disenio.TAB_CONTROLES, "controles")):
            x1, y1, x2, y2 = e.caja(caja)
            area = c.create_rectangle(x1, y1, x2, y2, fill="", outline="")
            c.tag_bind(area, "<ButtonPress-1>",
                       lambda _ev, n=nombre: self.mostrar_pagina(n))
            c.tag_bind(area, "<Enter>",
                       lambda _ev: c.configure(cursor="hand2"))
            c.tag_bind(area, "<Leave>", lambda _ev: c.configure(cursor=""))
            self._areas_pestanas.append(area)

        familia = tkfont.nametofont("TkDefaultFont").actual("family")
        x, y = Disenio.ETIQUETA_WIFI
        self._items_conexion.append(Texto(
            c, e(x), e(y), "Wi-Fi", e.fuente(62), Paleta.DORADO))
        x1, y1, x2, y2 = e.caja(Disenio.CAMPO_WIFI)
        self._red_wifi = tk.StringVar(master=c, value="Red no disponible")
        red = tk.Entry(c, textvariable=self._red_wifi, state="readonly",
                       readonlybackground=Paleta.FONDO_WIDGET, fg=Paleta.TEXTO_LOG,
                       relief="flat", bd=0, takefocus=False,
                       font=(Paleta.FUENTE_TEXTO, -e.fuente(43)))
        self._items_conexion.append(c.create_window(
            x1, y1, window=red, anchor="nw", width=x2 - x1, height=y2 - y1))

        self._ruta_conexion = directorio_configuracion() / "conexion.json"
        self._destino_guardado = self._cargar_destino()
        ip, puerto = self._destino_guardado or ("192.168.4.1", 8080)
        for caja_etiqueta, caja_campo, etiqueta, valor, nombre in (
            (Disenio.ETIQUETA_IP, Disenio.CAMPO_IP, "IP:", ip, "campo_ip"),
            (Disenio.ETIQUETA_PORT, Disenio.CAMPO_PORT, "PORT:", str(puerto), "campo_port"),
        ):
            ex, ey, _, eb = caja_etiqueta
            texto = Texto(c, e(ex), e(eb), etiqueta, e.fuente(88),
                          Paleta.DORADO, ancla="sw")
            self._items_avanzados.append(texto)
            fx1, fy1, fx2, fy2 = e.caja(caja_campo)
            campo = tk.Entry(
                c, font=(familia, -max(10, e(48))), bg=Paleta.TARJETA,
                fg=Paleta.TINTA, insertbackground=Paleta.TINTA, relief="flat",
                bd=0, highlightthickness=0, disabledbackground="#b9bfc5",
                disabledforeground=Paleta.FONDO_WIDGET)
            campo.insert(0, valor)
            campo.bind("<Return>", lambda _ev: self.boton_conectar.presionar())
            self._items_avanzados.append(c.create_window(
                fx1, fy1, window=campo, anchor="nw",
                width=fx2 - fx1, height=fy2 - fy1))
            setattr(self, nombre, campo)

        rotulo_avanzado = "Configuración Avanzada"
        avanzado = tk.Button(c, text=rotulo_avanzado,
                             command=self._alternar_avanzado,
                             relief="flat", bg=Paleta.FONDO_WIDGET)
        rotulo_imagen = foto_texto(rotulo_avanzado, e.fuente(42),
                       Paleta.DORADO, master=c)
        setattr(avanzado, "_rotulo", rotulo_imagen)
        avanzado.configure(image=rotulo_imagen)
        self._items_conexion.append(c.create_window(
            e(107), e(1200), window=avanzado, anchor="nw",
            width=e(750), height=e(90)))
        self._mostrar_avanzado()

        bx1, by1, bx2, by2 = e.caja(Disenio.BOTON_CONECTAR)
        self.render_conectar = BotonImagenRenderer(
            self.boton_conectar, c, bx1, by1, bx2 - bx1, "boton_conectar",
            variantes={
                "hover":      [(Paleta.DORADO, "#f3cd5a", 45)],
                "presionado": [(Paleta.DORADO, "#c79a1f", 45)],
            },
            texto="Conectar", texto_px=e.fuente(116), texto_color=Paleta.TINTA)

        sx, sy, _, _ = Disenio.ESTADO_CONEXION
        self._estado_conexion = Texto(c, e(sx), e(sy), "", e.fuente(46),
                                      Paleta.GRIS, ancla="nw")
        self._items_conexion.append(self._estado_conexion)

        if self._on_ota is not None:
            ota = tk.Button(c, text="OTA", command=self._on_ota,
                            bg=Paleta.FONDO_WIDGET, fg=Paleta.DORADO,
                            activebackground=Paleta.DORADO, activeforeground=Paleta.TINTA,
                            relief="flat", cursor="hand2")
            imagen_ota = foto_texto("OTA", e.fuente(62), Paleta.DORADO, master=c)
            setattr(ota, "_imagen_ota", imagen_ota)
            ota.configure(image=imagen_ota, activebackground=Paleta.FONDO_CANVAS)
            self._items_conexion.append(c.create_window(
                bx1, e(1940), window=ota, anchor="nw",
                width=bx2 - bx1, height=e(116)))

        self.panel_controles = None
        if self._mapeo is not None:
            self.panel_controles = ModalControles(
                c, self._mapeo, on_cambio=self._on_cambio_mapeo or (lambda: None),
                incrustado=True, al_captura=self._al_captura, escala=e)
            px, py, px2, py2 = e.caja(Disenio.PANEL_CONTROLES)
            ventana = self.panel_controles.ventana
            if not isinstance(ventana, tk.Frame):
                raise TypeError("El argumento 'window' de create_window debe ser un Frame, no un Toplevel.")
            self._ventana_controles = c.create_window(
                px, py, window=ventana, anchor="nw",
                width=px2 - px, height=py2 - py, state="hidden")

    def _cargar_destino(self):
        try:
            datos = json.loads(self._ruta_conexion.read_text(encoding="utf-8"))
            ip, puerto = datos["ip"], datos["puerto"]
            if isinstance(ip, str) and ip.strip() and type(puerto) is int and 1 <= puerto <= 65535:
                return ip, puerto
        except (OSError, ValueError, KeyError, TypeError):
            pass
        return None

    def _alternar_avanzado(self):
        self._avanzado = not self._avanzado
        self._mostrar_avanzado()
        if not self._avanzado:
            self.canvas.focus_set()

    def _mostrar_avanzado(self):
        visible = self._avanzado and self._pagina == "conectar"
        for item in self._items_avanzados:
            if isinstance(item, Texto):
                item.mostrar(visible)
            else:
                self.canvas.itemconfigure(item, state="normal" if visible else "hidden")

    def mostrar_pagina(self, pagina: str):
        """Cambia el contenido de la barra lateral: 'conectar' o 'controles'."""
        c = self.canvas
        if pagina == "controles" and self.panel_controles is None:
            return
        if pagina == "conectar" and self.panel_controles is not None:
            # Cancela la captura para que escribir en el formulario no cambie un atajo.
            self.panel_controles.cancelar_captura()
        self._pagina = pagina
        en_conexion = pagina == "conectar"
        for item in self._items_conexion:
            if isinstance(item, Texto):
                item.mostrar(en_conexion)
            else:
                c.itemconfig(item, state="normal" if en_conexion else "hidden")
        self.render_conectar.mostrar(en_conexion)
        self._mostrar_avanzado()
        if self.panel_controles is not None:
            c.itemconfig(self._ventana_controles,
                         state="hidden" if en_conexion else "normal")
        self._tab_conectar.poner(
            color=Paleta.DORADO if en_conexion else Paleta.TEXTO_LOG)
        self._tab_controles.poner(
            color=Paleta.TEXTO_LOG if en_conexion else Paleta.DORADO)

        # Devuelve el foco al lienzo para que la tecla M funcione como atajo.
        self.canvas.focus_set()

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

    def _construir_estado(self):
        e, c = self.e, self.canvas
        self.t_estado = Tarjeta(c, e, Disenio.TARJETA_ESTADO, Disenio.LINEA_ESTADO,
                                "estado", "Estado")
        pantalla_oscura(c, e, Disenio.PANTALLA_ESTADO)

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
        self._lbl_medicion_bateria = Texto(c, e(l2x), e(1220), "", e.fuente(30),
                                         Paleta.TINTA, ancla="center")

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
            if not ip:
                raise ValueError("escribe la IP del robot en Configuración avanzada")
            puerto = int(self.campo_port.get().strip())
            if not 0 < puerto < 65536:
                raise ValueError("el puerto debe estar entre 1 y 65535")
            if self._on_conectar:
                self._destino_intentado = (ip, puerto)
                self._on_conectar(ip, puerto)
        except (OSError, ValueError) as error:
            self.mostrar_error(f"No se pudo conectar: {error}")

    def mostrar_error(self, mensaje: str):
        """Muestra un error de conexión bajo el botón (en rojo)."""
        self._estado_conexion.poner(
            texto=textwrap.fill(mensaje, 24), color=Paleta.ROJO)

    def establecer_conectando(self, etiqueta: str, reconectando: bool = False):
        """
        Indica que se está abriendo la conexión; el botón permite cancelar.

        reconectando: es un reintento automático tras perder el enlace, no un
        primer intento manual. Cambia solo el texto para que el usuario sepa
        que la app lo está intentando sola.
        """
        self._conexion_pendiente = True
        self._conexion_activa = False
        self.boton_modo.habilitado = False
        self.boton_conectar.texto = "Cancelar"
        for campo in (self.campo_ip, self.campo_port):
            campo.config(state="disabled")
        accion = "Reconectando con" if reconectando else "Conectando a"
        self._estado_conexion.poner(
            texto=textwrap.fill(f"{accion} {etiqueta}...", 24),
            color=Paleta.DORADO)

    def establecer_conexion(self, activa: bool, etiqueta: str):
        """
        Refleja el estado de la conexión en la interfaz.

        activa   : si hay (o no) un robot del que leer.
        etiqueta : qué dice el indicador (p. ej. "SIN CONEXIÓN", una IP...).
        """
        self._conexion_pendiente = False
        self._conexion_activa = activa
        self.boton_modo.habilitado = activa
        self.boton_conectar.texto = "Desconectar" if activa else "Conectar"
        destino = self._destino_intentado
        if activa and destino and destino[0] == etiqueta:
            if destino != self._destino_guardado:
                try:
                    self._ruta_conexion.parent.mkdir(parents=True, exist_ok=True)
                    self._ruta_conexion.write_text(
                        json.dumps({"ip": destino[0], "puerto": destino[1]}), encoding="utf-8")
                except OSError:
                    pass
                else:
                    self._destino_guardado = destino
        for campo in (self.campo_ip, self.campo_port):
            campo.config(state="disabled" if activa else "normal")
        self._estado_conexion.poner(
            texto=textwrap.fill(f"Conectado · {etiqueta}" if activa else etiqueta, 24),
            color=Paleta.DORADO if activa else Paleta.GRIS)

    def actualizar_red_wifi(self, nombre):
        self._red_wifi.set(nombre or "Red no disponible")

    def actualizar_latencia(self, milisegundos):
        """Dato de latencia (ms) para la cabecera; None si no hay."""
        self._latencia_ms = milisegundos

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
        self.gamepad.habilitar(
            self._conexion_activa and estado.modo == Modo.MANUAL and not estado.detenido)
        compatible = self._conexion_activa and estado.detenido is not None
        for boton in self._acciones_robot:
            habilitado = compatible and (boton.cget("text") != "Demo" or not estado.demo_activa)
            estado_boton = "normal" if habilitado else "disabled"
            boton.configure(state=estado_boton,
                            image=self._rotulos_acciones[boton][estado_boton])

        manual = estado.modo == Modo.MANUAL
        if not self._conexion_activa:
            self.boton_modo.texto = "MODO: --"
        else:
            self.boton_modo.texto = "MODO: MANUAL" if manual else "MODO: AUTOMÁTICO"

        ms = "--" if self._latencia_ms is None else self._latencia_ms
        self._telemetria.poner(texto=f"| {self._fps()} FPS | {ms} ms |")

        self.render_modo_icono.dibujar()
        detenido = self._conexion_activa and estado.detenido
        self._modo_titulo.poner(
            texto="Detenido" if detenido else "Modo Manual",
            color=Paleta.DORADO if manual else Paleta.GRIS)
        subtitulo = "Activado" if manual else "Desactivado"
        if detenido:
            subtitulo = "Demo en curso" if estado.demo_activa else "Clic para reanudar"
        self._modo_sub.poner(texto=subtitulo,
                             color=Paleta.DORADO if manual else Paleta.GRIS)
        self.render_ojos.dibujar()
        for render in self.render_iconos:
            render.dibujar()

        self.render_barras.dibujar()
        self.render_sol.dibujar()
        color_consumo = self.barras.color
        self._lbl_consumo.poner(texto=self.barras.etiqueta_watts,
                                color=color_consumo,
                                contorno=self._oscuro(color_consumo, 0.7))
        color_sol = self.sol.color
        pct = (f"≈ {int(round(max(0.0, min(1.0, estado.bateria)) * 100))} %"
               if not self.sol.sin_datos else "-- %")
        self._lbl_sol.poner(texto=self.sol.etiqueta,
                            color=self._oscuro(color_sol, 0.33),
                            contorno=self._oscuro(color_sol, 0.7))
        self._lbl_pct.poner(texto=pct, color=color_sol,
                            contorno=self._oscuro(color_sol, 0.62))
        voltaje, corriente = estado.voltaje_bateria_v, estado.corriente_bateria_a
        medicion = (f"{voltaje:.2f} V / {corriente * 1000:.0f} mA"
                    if self._conexion_activa and voltaje is not None and corriente is not None else "")
        self._lbl_medicion_bateria.poner(texto=medicion)

        self.render_navegacion.dibujar()
        self.render_gamepad.dibujar()

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
        self.t_navegacion.alertar(self.proximidad.color)
        self.t_control.alertar(Paleta.DORADO if self.gamepad.habilitado
                               else Paleta.GRIS)
        self.render_conectar.dibujar()
        self.render_conectar.mostrar(self._pagina == "conectar")


# Cajón de Pruebas
if __name__ == "__main__":
    from ..nucleo.disenio import Escala
    print("PantallaPrincipal")

    raiz = tk.Tk()
    escala = Escala(0.3)
    raiz.geometry(f"{escala.ancho}x{escala.alto_panel}")
    raiz.configure(bg=Paleta.FONDO_APP)

    estado = EstadoRobot()
    pantalla = PantallaPrincipal(raiz, estado, escala,
                                 on_conectar=lambda ip, puerto: None,
                                 on_desconectar=lambda: None)
    comandos = []
    pantalla.conectar_gamepad(comandos.append)

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

    pantalla.campo_port.delete(0, "end")
    pantalla.campo_port.insert(0, "abc")
    pantalla.boton_conectar.presionar()
    assert "No se pudo conectar" in pantalla._estado_conexion.texto
    print("OK: pantalla construida, ciclos, capa apagada y error de puerto")
    raiz.destroy()

# wall-e-robot/app/pantallas/modal_controles.py
# Kevin Gámez - 06/10/2026
#
# Editor de los controles de teclado (ventana aparte o pestaña incrustada).


import tkinter as tk

from ..nucleo.disenio import Disenio, Escala
from ..nucleo.paleta import Paleta
from ..widgets.logica.mapeo_teclado import (
    ACCIONES, MODIFICADORAS, MapeoTeclado, nombre_tecla,
)
from ..widgets.renderizado.base_render import rectangulo_redondeado
from ..widgets.renderizado.logger_widget_render import rectangulo_puntos
from ..widgets.renderizado.texto_render import fuente as fuente_quadrillion
from ..widgets.renderizado.texto_render import foto_texto


# Geometría en unidades de diseño. A la escala máxima (0.40) cada fila mide
# ~57 px, la tecla 180 x 42 px y la × 56 x 42 px; por debajo se reducen en la
# misma proporción para que sigan cabiendo en la barra lateral.
FILA_ALTO    = 104    # alto de cada fila (sin separadores entre ellas)
BOTON_ANCHO  = 96     # botón × (cuadrado, mismo alto que la tecla)
CONTROL_ALTO = 76     # alto de la caja de la tecla y de la ×
SEPARACION   = 8
MARGEN_FILA  = 14     # aire a los lados de cada fila
BARRA_ANCHO  = 26
COLOR_BORDE  = "#6b6d8a"   # contorno de las cajas de tecla y ×
ANCHO_PANEL  = Disenio.PANEL_CONTROLES[2] - Disenio.PANEL_CONTROLES[0]
# Columna del nombre: lo justo para "Hombro izq. arriba" en una línea. La caja
# de la tecla ocupa todo el resto, así los botones quedan pegados al nombre.
ANCHO_NOMBRE = 450


class _BarraLista:
    """Barra vertical propia: carril oscuro, perilla dorada, rueda y arrastre.

    Reproduce el lenguaje visual de la barra del Registro sin depender del
    Scrollbar nativo de Tk (que no permite pintar la perilla).
    """

    def __init__(self, padre, e, al_mover):
        """Crea el carril; 'al_mover' recibe la fracción (0..1) a mostrar."""
        self.e = e
        self.al_mover = al_mover
        self.canvas = tk.Canvas(
            padre, width=max(6, e(BARRA_ANCHO)), bg=Paleta.FONDO_NEGRO,
            highlightthickness=0, bd=0, cursor="arrow",
        )
        self._primero = 0.0
        self._ultimo = 1.0
        self._perilla = None
        self._pista = None
        self._alto_perilla = 0
        self._y_perilla = 0
        self._agarre = None
        self.canvas.bind("<Configure>", lambda _e: self.redibujar())
        self.canvas.bind("<ButtonPress-1>", self._al_presionar)
        self.canvas.bind("<B1-Motion>", self._al_arrastrar)
        self.canvas.bind("<ButtonRelease-1>", self._soltar)

    # Sincronización con el lienzo de filas
    def set(self, primero, ultimo):
        """Recibe la porción visible (yscrollcommand) y redibuja la perilla."""
        self._primero, self._ultimo = float(primero), float(ultimo)
        self.redibujar()

    def _medidas(self):
        """(ancho, alto, margen) actuales del carril."""
        ancho = self.canvas.winfo_width()
        if ancho <= 1:
            ancho = self.canvas.winfo_reqwidth()
        alto = self.canvas.winfo_height()
        if alto <= 1:
            alto = self.canvas.winfo_reqheight()
        margen = max(2, self.e(4))
        return ancho, alto, margen

    def redibujar(self):
        """Pinta el carril y coloca la perilla según la porción visible."""
        ancho, alto, margen = self._medidas()
        if ancho <= 2 or alto <= 2:
            return
        radio = max(2, self.e(8))
        if self._pista is None:
            self._pista = rectangulo_redondeado(
                self.canvas, margen, margen, ancho - margen, alto - margen,
                radio, fill=Paleta.FONDO_NEGRO, outline=Paleta.HUD_LINE,
                width=max(1, self.e(2)))
            self._perilla = rectangulo_redondeado(
                self.canvas, margen, margen, ancho - margen, alto - margen,
                radio, fill=Paleta.DORADO, outline=Paleta.DORADO_BORDE,
                width=max(1, self.e(2)))
        else:
            self.canvas.coords(self._pista, *rectangulo_puntos(
                margen, margen, ancho - margen, alto - margen, radio))

        visible = self._ultimo - self._primero
        util = max(1, (alto - 2 * margen))
        if visible >= 0.999:
            self.canvas.itemconfigure(self._perilla, state="hidden")
            self._alto_perilla = 0
            self._y_perilla = 0
            return

        alto_perilla = max(self.e(45), util * max(0.0, visible))
        y = margen + (util - alto_perilla) * (
            self._primero / max(1e-9, 1.0 - visible))
        self._alto_perilla = alto_perilla
        self._y_perilla = y
        self.canvas.itemconfigure(self._perilla, state="normal")
        self.canvas.coords(self._perilla, *rectangulo_puntos(
            margen, y, ancho - margen, y + alto_perilla, radio))

    # Arrastre
    def _al_presionar(self, evento):
        """Empieza el arrastre; un clic en el carril salta a esa posición."""
        if self._alto_perilla <= 0:
            return
        dentro = self._y_perilla <= evento.y <= self._y_perilla + self._alto_perilla
        self._agarre = (evento.y - self._y_perilla if dentro
                        else self._alto_perilla / 2)
        self._mover(evento.y)

    def _al_arrastrar(self, evento):
        """Mueve la perilla mientras se arrastra."""
        if self._agarre is not None:
            self._mover(evento.y)

    def _soltar(self, _evento=None):
        """Termina el arrastre."""
        self._agarre = None

    def _mover(self, y):
        """Convierte la posición del puntero en una fracción de la lista."""
        _ancho, alto, margen = self._medidas()
        recorrido = max(1, (alto - 2 * margen) - self._alto_perilla)
        fraccion = (y - self._agarre - margen) / recorrido
        self.al_mover(max(0.0, min(1.0, fraccion)))


class ModalControles:
    """
    Modal para reasignar las teclas del mapeo.

    Cada cambio se notifica vía on_cambio para que el dueño lo persista.
    """

    def __init__(self, raiz: tk.Misc, mapeo: MapeoTeclado, on_cambio=None,
                 incrustado: bool = False, al_captura=None, escala=None):
        """Construye el modal y engancha la captura de teclas a la ventana.

        incrustado : True para dibujarlo como un Frame dentro de 'raiz' (la
                     barra lateral) en vez de una ventana aparte; el dueño lo
                     coloca con place/pack y lo muestra u oculta.
        al_captura : callback(bool) al entrar/salir del modo captura.
        escala     : Escala del diseño; sin ella se usa la máxima (0.40).
        """
        self.incrustado = incrustado
        self._al_captura = al_captura or (lambda _activa: None)
        self.mapeo = mapeo
        self.on_cambio = on_cambio or (lambda: None)
        self._capturando = None  # accion_id en modo captura (o None)
        self.e = escala or Escala(0.40)

        if incrustado:
            self.ventana = tk.Frame(raiz, bg=Paleta.FONDO_NEGRO)
        else:
            self.ventana = tk.Toplevel(raiz)
            self.ventana.title("Configurar controles")
            self.ventana.configure(bg=Paleta.FONDO_APP)
            self.ventana.resizable(False, False)
            self.ventana.transient(raiz) # Ignorar error de Pylance.
            self.ventana.grab_set() # TODO: Investigar error [tkinter.TclError: grab failed: window not viewable]
        fondo = Paleta.FONDO_NEGRO if incrustado else Paleta.FONDO_APP

        # Sugerencia y estado de captura.
        self.lbl_ayuda = tk.Label(
            self.ventana, text="Selecciona una tecla para reasignarla. Esc cancela la captura.",
            bg=fondo, fg=Paleta.TEXTO_TENUE,
            font=(Paleta.FUENTE_TEXTO, 8), justify="left", anchor="w",
        )
        self.lbl_ayuda.pack(fill="x", padx=self._px(Paleta.UNIDAD),
                            pady=(self._px(Paleta.UNIDAD), 0))
        self._poner_texto(self.lbl_ayuda, self.lbl_ayuda.cget("text"),
                          self._fuente(34), Paleta.TEXTO_TENUE,
                          ancho_px=self._ancho_texto())

        self.lbl_estado = tk.Label(
            self.ventana, text="", bg=fondo,
            fg=Paleta.DORADO, font=(Paleta.FUENTE_TEXTO, 8), anchor="w",
        )
        self.lbl_estado.pack(fill="x", padx=self._px(Paleta.UNIDAD),
                             pady=(self._px(4), 0))
        self._poner_estado("", Paleta.DORADO)

        # Lista desplazable: las filas mantienen su tamaño táctil sin ocultar
        # acciones. La barra usa los mismos colores que el registro.
        lista = tk.Frame(self.ventana, bg=Paleta.FONDO_WIDGET)
        lista.pack(fill="both", expand=True, padx=self._px(SEPARACION),
                   pady=(self._px(SEPARACION // 2), 0))
        self.barra_filas = _BarraLista(lista, self.e, self._mover_lista)
        self.barra_filas.canvas.pack(side="right", fill="y",
                                     padx=(self._px(6), 0))
        self.lienzo_filas = tk.Canvas(
            lista, bg=Paleta.FONDO_WIDGET, highlightthickness=0, bd=0,
            yscrollincrement=max(1, self._px(FILA_ALTO // 2)),
        )
        self.lienzo_filas.pack(side="left", fill="both", expand=True)
        self.lienzo_filas.configure(yscrollcommand=self.barra_filas.set)
        self.marco_filas = tk.Frame(self.lienzo_filas, bg=Paleta.FONDO_WIDGET)
        self._ventana_filas = self.lienzo_filas.create_window(
            0, 0, window=self.marco_filas, anchor="nw")
        self.marco_filas.bind("<Configure>", self._actualizar_region_filas)
        self.lienzo_filas.bind("<Configure>", self._ajustar_ancho_filas)
        self._enlazar_rueda(self.lienzo_filas, self.marco_filas,
                            self.barra_filas.canvas)

        # Lista de filas (acción | tecla | limpiar).
        self._filas = {}  # accion_id -> (btn_tecla, btn_limpiar)
        self._construir_filas()

        # Pie: restaurar por defecto + cerrar.
        pie = tk.Frame(self.ventana, bg=fondo)
        pie.pack(fill="x", padx=self._px(Paleta.UNIDAD),
                 pady=self._px(Paleta.UNIDAD))

        btn_restaurar = tk.Button(
            pie, text="Restaurar por defecto", bg=fondo,
            fg=Paleta.DORADO, activebackground=Paleta.DORADO_BORDE,
            activeforeground=Paleta.TEXTO_LOG, relief="flat", bd=0,
            highlightthickness=max(1, self._px(3)),
            highlightbackground=Paleta.DORADO_DIM,
            padx=self._px(18), pady=self._px(10),
            font=(Paleta.FUENTE_TEXTO, 8, "bold"), command=self._restaurar,
        )
        btn_restaurar.pack(side="left")
        self._poner_texto(btn_restaurar, "Restaurar por defecto",
                          self._fuente(32), Paleta.DORADO)

        if not incrustado:
            btn_cerrar = tk.Button(
                pie, text="CERRAR", bg=Paleta.FONDO_WIDGET, fg=Paleta.DORADO,
                activebackground=Paleta.DORADO_DIM, activeforeground=Paleta.TEXTO_LOG,
                relief="flat", font=(Paleta.FUENTE_TEXTO, 8, "bold"),
                command=self.ventana.destroy,
            )
            btn_cerrar.pack(side="right")
            self._poner_texto(btn_cerrar, "CERRAR", self._fuente(32),
                              Paleta.DORADO)

        if incrustado:
            # Un Frame no recibe teclas por sí mismo: se escucha en la ventana
            # (solo actúa mientras hay una captura en curso).
            self.ventana.winfo_toplevel().bind("<KeyPress>", self._al_tecla, add="+")
        else:
            self.ventana.bind("<KeyPress>", self._al_tecla)
        self._refrescar_filas()

    # Medidas y textos
    def _px(self, unidades):
        """Unidades de diseño -> píxeles enteros (mínimo 1)."""
        return max(1, int(round(self.e(unidades))))

    def _fuente(self, unidades):
        """Tamaño de letra en píxeles (mínimo legible) para la escala actual."""
        return self.e.fuente(unidades)

    def _ancho_texto(self):
        """Ancho útil (px) de las etiquetas de ayuda y estado."""
        return self._px(ANCHO_PANEL - 2 * Paleta.UNIDAD)

    @staticmethod
    def _envolver(texto, px, ancho_px, max_lineas=None):
        """Parte 'texto' en líneas que quepan en 'ancho_px' (Quadrillion)."""
        if not texto:
            return ""
        tipo = fuente_quadrillion(px)
        lineas, actual = [], ""
        for palabra in texto.split():
            prueba = f"{actual} {palabra}".strip()
            if actual and tipo.getlength(prueba) > ancho_px:
                lineas.append(actual)
                actual = palabra
            else:
                actual = prueba
        if actual:
            lineas.append(actual)
        if max_lineas and len(lineas) > max_lineas:
            lineas = lineas[:max_lineas]
            ultima = lineas[-1]
            while ultima and tipo.getlength(ultima + "…") > ancho_px:
                ultima = ultima[:-1]
            lineas[-1] = ultima.rstrip() + "…"
        return "\n".join(lineas)

    def _poner_texto(self, widget, texto, px, color, ancho_px=None,
                     max_lineas=None, respaldo=False):
        """Dibuja Quadrillion en un control Tk sin perder su texto accesible.

        El texto nativo queda del color del fondo (invisible) para lectores de
        pantalla; la imagen es la que se ve. 'respaldo' usa otra fuente cuando
        Quadrillion no tiene los glifos (flechas, por ejemplo).
        """
        widget._texto_plano = texto   # lo que dice el control (el texto nativo va vacío)
        if not texto:
            widget._texto_quadrillion = None
            widget.config(image="", text="")
            return
        visible = (self._envolver(texto, px, ancho_px, max_lineas)
                   if ancho_px else texto)
        imagen = foto_texto(visible, px, color, alinear="left",
                            respaldo=respaldo, master=widget)
        widget._texto_quadrillion = imagen
        opciones = {
            "text": "", "image": imagen, "compound": "center",
            "fg": widget.cget("bg"),
        }
        if isinstance(widget, tk.Label):
            opciones["anchor"] = "w"
        if isinstance(widget, tk.Button):
            # El texto nativo también debe quedar oculto en hover/deshabilitado:
            # se pinta del color del fondo activo, no del normal.
            opciones["activeforeground"] = widget.cget("activebackground")
            opciones["disabledforeground"] = widget.cget("bg")
        widget.config(**opciones)

    def _poner_estado(self, texto, color=Paleta.DORADO):
        """Muestra el aviso de estado (máximo dos líneas) en Quadrillion."""
        self._poner_texto(self.lbl_estado, texto, self._fuente(34), color,
                          ancho_px=self._ancho_texto(), max_lineas=2,
                          respaldo=True)

    # Construcción
    def _construir_filas(self):
        """Crea una fila por acción: nombre | tecla (flexible) | ×.

        Las filas van pegadas, separadas por una línea fina, y la caja de la
        tecla ocupa el espacio sobrante para que no quede un hueco entre el
        nombre y los botones.
        """
        for n, accion in enumerate(ACCIONES):
            fila = tk.Frame(self.marco_filas, bg=Paleta.FONDO_WIDGET,
                            height=self._px(FILA_ALTO))
            fila.pack(fill="x")
            fila.pack_propagate(False)

            celda_nombre = tk.Frame(fila, bg=Paleta.FONDO_WIDGET,
                                    width=self._px(ANCHO_NOMBRE))
            celda_nombre.pack(side="left", fill="y")
            celda_nombre.pack_propagate(False)
            lbl_nombre = tk.Label(
                celda_nombre, anchor="w", justify="left",
                bg=Paleta.FONDO_WIDGET, fg=Paleta.TEXTO_LOG,
                font=(Paleta.FUENTE_TEXTO, 8),
            )
            lbl_nombre.pack(fill="both", expand=True,
                            padx=(self._px(MARGEN_FILA), 0))
            self._poner_texto(lbl_nombre, accion.nombre, self._fuente(32),
                              Paleta.TEXTO_LOG,
                              ancho_px=self._px(ANCHO_NOMBRE - MARGEN_FILA - 10),
                              max_lineas=2)

            caja_limpiar = tk.Frame(fila, bg=Paleta.FONDO_WIDGET,
                                    width=self._px(BOTON_ANCHO),
                                    height=self._px(CONTROL_ALTO))
            caja_limpiar.pack(side="right",
                              padx=(self._px(SEPARACION),
                                    self._px(MARGEN_FILA)))
            caja_limpiar.pack_propagate(False)
            caja_tecla = tk.Frame(fila, bg=Paleta.FONDO_WIDGET,
                                  height=self._px(CONTROL_ALTO))
            caja_tecla.pack(side="left", fill="x", expand=True)
            caja_tecla.pack_propagate(False)

            btn_tecla = tk.Button(
                caja_tecla, width=1, height=1, relief="flat",
                bg=Paleta.FONDO_NEGRO, activebackground=Paleta.FONDO_CANVAS,
                bd=0, highlightthickness=max(1, self._px(3)),
                highlightbackground=COLOR_BORDE,
                highlightcolor=Paleta.DORADO, takefocus=True,
                font=(Paleta.FUENTE_TEXTO, 1),
                command=lambda a=accion.id: self._empezar_captura(a),
            )
            btn_tecla.pack(fill="both", expand=True)

            btn_limpiar = tk.Button(
                caja_limpiar, width=1, height=1, relief="flat",
                bg=Paleta.FONDO_NEGRO, fg=Paleta.TEXTO_TENUE,
                activebackground=Paleta.ROJO, activeforeground=Paleta.TEXTO_LOG,
                bd=0, highlightthickness=max(1, self._px(3)),
                highlightbackground=COLOR_BORDE,
                highlightcolor=Paleta.DORADO, takefocus=True,
                font=(Paleta.FUENTE_TEXTO, 1),
                command=lambda a=accion.id: self._limpiar(a),
            )
            btn_limpiar.pack(fill="both", expand=True)
            btn_limpiar.bind("<Enter>", lambda _ev, b=btn_limpiar:
                             self._resaltar_limpiar(b, True))
            btn_limpiar.bind("<Leave>", lambda _ev, b=btn_limpiar:
                             self._resaltar_limpiar(b, False))

            self._filas[accion.id] = (btn_tecla, btn_limpiar)
            self._enlazar_rueda(fila, celda_nombre, lbl_nombre, caja_tecla,
                                btn_tecla, caja_limpiar, btn_limpiar)
            for boton in (btn_tecla, btn_limpiar):
                boton.bind("<FocusIn>",
                           lambda _ev, b=boton: self._asegurar_visible(b),
                           add="+")
            if n < len(ACCIONES) - 1:
                tk.Frame(self.marco_filas, bg=Paleta.HUD_LINE,
                         height=1).pack(fill="x")

    def _resaltar_limpiar(self, boton, activo):
        """Resalta la × al pasar el mouse (solo si hay tecla que limpiar)."""
        if str(boton.cget("state")) == "disabled":
            return
        boton.config(bg=Paleta.ROJO if activo else Paleta.FONDO_NEGRO,
                     activebackground=Paleta.ROJO)
        self._poner_texto(boton, "\u2715", self._fuente(50),
                          Paleta.TEXTO_LOG if activo else Paleta.TEXTO_TENUE,
                          respaldo=True)

    # Desplazamiento
    def _actualizar_region_filas(self, _evento=None):
        """Sincroniza el área desplazable cuando cambian las filas."""
        self.lienzo_filas.configure(scrollregion=self.lienzo_filas.bbox("all"))

    def _ajustar_ancho_filas(self, evento):
        """Hace que las filas ocupen todo el ancho disponible del panel."""
        self.lienzo_filas.itemconfigure(self._ventana_filas, width=evento.width)

    def _mover_lista(self, fraccion):
        """Mueve la lista cuando se arrastra la perilla."""
        self.lienzo_filas.yview_moveto(fraccion)

    def _asegurar_visible(self, widget):
        """Desplaza la lista para que la fila del control enfocado se vea."""
        fila = widget.master.master
        y = fila.winfo_y()
        alto_fila = fila.winfo_height()
        region = self.lienzo_filas.cget("scrollregion")
        if not region:
            return
        if isinstance(region, str):
            contenido = float(region.split()[-1])
        else:
            contenido = float(region[-1])
        visible = self.lienzo_filas.winfo_height()
        if contenido <= 0 or visible <= 1:
            return
        inicio = self.lienzo_filas.canvasy(0)
        if y < inicio:
            self.lienzo_filas.yview_moveto(y / contenido)
        elif y + alto_fila > inicio + visible:
            self.lienzo_filas.yview_moveto(
                (y + alto_fila - visible) / contenido)

    def _enlazar_rueda(self, *widgets):
        """Engancha la rueda del mouse a la lista y a todos sus hijos."""
        for widget in widgets:
            widget.bind("<MouseWheel>", self._rueda_filas)
            widget.bind("<Button-4>", lambda _e: self._desplazar(-2))
            widget.bind("<Button-5>", lambda _e: self._desplazar(2))

    def _desplazar(self, pasos):
        """Desplaza la lista 'pasos' unidades y corta la propagación."""
        self.lienzo_filas.yview_scroll(pasos, "units")
        return "break"

    def _rueda_filas(self, evento):
        """Desplaza la lista con rueda."""
        if not evento.delta:
            return "break"
        return self._desplazar(-2 if evento.delta > 0 else 2)

    # Lógica (sin cambios)
    def _empezar_captura(self, accion_id: str):
        """Entra en modo captura para la acción dada (hace toggle si es la misma)."""
        self._capturando = None if self._capturando == accion_id else accion_id
        self._al_captura(self._capturando is not None)
        self._poner_estado(
            (f"Presiona una tecla para «{self._accion(accion_id).nombre}»..."
             if self._capturando else ""))
        self._refrescar_filas()

    def cancelar_captura(self):
        """Sale del modo captura sin cambiar el mapeo (al ocultar el panel)."""
        if self._capturando is None:
            return
        self._capturando = None
        self._al_captura(False)
        self._poner_estado("Captura cancelada")
        self._refrescar_filas()

    def _al_tecla(self, evento):
        """Captura la tecla presionada y la asigna a la acción en espera."""
        if self._capturando is None:
            return
        keysym = evento.keysym

        if keysym in ("Escape", "Cancel"):
            self._capturando = None
            self._al_captura(False)
            self._poner_estado("Captura cancelada")
            self._refrescar_filas()
            return
        if keysym in MODIFICADORAS:
            return  # un modificador solo no es un control

        accion_anterior = self.mapeo.buscar_accion(keysym)
        self.mapeo.asignar(self._capturando, keysym)
        self.on_cambio()

        mensaje = (f"{nombre_tecla(keysym)} asignada a "
                   f"«{self._accion(self._capturando).nombre}»")
        if accion_anterior is not None and accion_anterior != self._capturando:
            mensaje += f"; «{self._accion(accion_anterior).nombre}» la perdió"
        self._poner_estado(mensaje, Paleta.DORADO)
        self._capturando = None
        self._al_captura(False)
        self._refrescar_filas()


    def _limpiar(self, accion_id: str):
        """Quita la tecla asignada a la acción y avisa del cambio."""
        self.mapeo.limpiar(accion_id)
        self.on_cambio()
        self._poner_estado(f"«{self._accion(accion_id).nombre}» sin tecla",
                           Paleta.TEXTO_TENUE)
        self._refrescar_filas()

    def _restaurar(self):
        """Restaura el mapeo de fábrica y avisa del cambio."""
        self.mapeo.restaurar_por_defecto()
        self.on_cambio()
        self._poner_estado("Controles restaurados de fábrica", Paleta.DORADO)
        self._refrescar_filas()


    def _accion(self, accion_id: str):
        """Devuelve la definición de la acción; lanza KeyError si no existe."""
        for accion in ACCIONES:
            if accion.id == accion_id:
                return accion
        raise KeyError(accion_id)

    def _refrescar_filas(self):
        """Pinta el estado de cada fila (tecla asignada / captura en curso)."""
        for accion_id, (btn_tecla, btn_limpiar) in self._filas.items():
            capturando = self._capturando == accion_id
            tecla = self.mapeo.tecla_de(accion_id)

            texto = ("Pulsa…" if capturando else
                     (nombre_tecla(tecla) if tecla else "(sin tecla)"))
            color = (Paleta.TINTA if capturando else
                     (Paleta.TEXTO_LOG if tecla else Paleta.GRIS))
            fondo = Paleta.DORADO if capturando else Paleta.FONDO_NEGRO
            btn_tecla.config(
                bg=fondo,
                highlightbackground=(Paleta.DORADO if capturando
                                     else COLOR_BORDE),
                activebackground=(Paleta.DORADO_DIM if capturando
                                  else Paleta.FONDO_CANVAS),
            )
            self._poner_texto(btn_tecla, texto, self._fuente(44), color,
                              respaldo=True)

            habilitado = bool(tecla)
            btn_limpiar.config(
                state="normal" if habilitado else "disabled",
                bg=Paleta.FONDO_NEGRO, activebackground=Paleta.ROJO,
                highlightbackground=COLOR_BORDE if habilitado else Paleta.HUD_LINE,
                cursor="hand2" if habilitado else "arrow",
            )
            self._poner_texto(btn_limpiar, "\u2715", self._fuente(50),
                              Paleta.TEXTO_TENUE if habilitado else Paleta.GRIS,
                              respaldo=True)


# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.pantallas.modal_controles

if __name__ == "__main__":
    import types
    from ..widgets.logica.mapeo_teclado import MapeoTeclado

    print("Prueba modal_controles.py\n")

    raiz = tk.Tk()
    raiz.withdraw()
    mapeo = MapeoTeclado()

    cambios = []
    modal = ModalControles(raiz, mapeo, on_cambio=lambda: cambios.append(True))
    raiz.update()

    # La fila muestra la tecla por defecto de cada acción
    modal._refrescar_filas()
    btn_arriba, _ = modal._filas["arriba"]
    assert getattr(btn_arriba, "_texto_plano", btn_arriba.cget("text")) == "\u2191", f"Debería verse ↑, llegó {btn_arriba.cget('text')}"
    print("OK: la cruceta muestra la flecha de fábrica\n")

    # Captura: asignar una tecla nueva notifica el cambio y guarda
    modal._empezar_captura("arriba")
    assert modal._capturando == "arriba", "Debe entrar en modo captura"
    modal._al_tecla(types.SimpleNamespace(keysym="U"))
    assert mapeo.tecla_de("arriba") == "U", "La tecla capturada debe asignarse"
    assert len(cambios) == 1, "El cambio debe notificarse (para guardar el JSON)"
    assert modal._capturando is None, "Tras capturar se sale del modo"
    print("OK: captura en vivo asigna y avisa del cambio\n")

    # Esc cancela la captura sin tocar el mapeo
    n_original = mapeo.tecla_de("abajo")
    modal._empezar_captura("abajo")
    modal._al_tecla(types.SimpleNamespace(keysym="Escape"))
    assert mapeo.tecla_de("abajo") == n_original, "Esc no debe cambiar nada"
    print("OK: Esc cancela sin modificar\n")

    # Los modificadores solos no se asignan
    modal._empezar_captura("abajo")
    modal._al_tecla(types.SimpleNamespace(keysym="Shift_L"))
    assert mapeo.tecla_de("abajo") == n_original, "Shift solo no se asigna"
    modal._al_tecla(types.SimpleNamespace(keysym="v"))
    assert mapeo.tecla_de("abajo") == "v"
    print("OK: los modificadores se ignoran al capturar\n")

    # Una tecla robada de otra acción se avisa en el estado
    modal._empezar_captura("abajo")
    modal._al_tecla(types.SimpleNamespace(keysym="q"))  # 'q' era de cuello_mas
    assert mapeo.tecla_de("abajo") == "q", "abajo toma la q"
    assert mapeo.tecla_de("cuello_mas") is None, "cuello_mas la pierde"
    mensaje = getattr(modal.lbl_estado, "_texto_plano", modal.lbl_estado.cget("text"))
    assert "la perdi\u00f3" in mensaje, "Debe avisar que otra acción perdió la tecla"
    print(f"OK: {mensaje}\n")

    # Limpiar y restaurar
    modal._limpiar("abajo")
    assert mapeo.tecla_de("abajo") is None
    modal._restaurar()
    assert mapeo.tecla_de("abajo") == "Down"
    print("OK: limpiar y restaurar por defecto\n")

    modal.ventana.destroy()
    raiz.destroy()
    print("Pruebas OK")
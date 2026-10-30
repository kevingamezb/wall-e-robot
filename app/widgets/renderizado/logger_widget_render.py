# wall-e-robot/app/widgets/renderizado/logger_widget_render.py
# Kevin Gámez - 13/09/2026
# Rediseño: terminal clara dentro de la tarjeta "Registro" y barra de
# desplazamiento propia (pista oscura + perilla dorada), como en el diseño.


import math
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
from ...nucleo.paleta import Paleta
from ...nucleo.disenio import Disenio
from ...nucleo.estado import NivelLog
from .base_render import rectangulo_redondeado


# Tipografías monoespaciadas, por orden de preferencia.
MONOESPACIADAS = ("Consolas", "DejaVu Sans Mono", "Menlo", "Courier New")

# Colores de las etiquetas sobre fondo claro.
COLOR_TS = "#6b6d8a"
COLOR_AVISO = "#a85f00"
COLOR_ERROR = "#c0332f"


def _familia_mono(raiz) -> str:
    """Primera familia monoespaciada disponible en el sistema."""
    disponibles = {f.lower() for f in tkfont.families(raiz)}
    for familia in MONOESPACIADAS:
        if familia.lower() in disponibles:
            return familia
    return "TkFixedFont"


class BarraRegistro:
    """Barra de desplazamiento del registro, dibujada en el canvas."""

    def __init__(self, canvas, e, texto):
        self.canvas, self.e, self.texto = canvas, e, texto
        x1, y1, x2, y2 = e.caja(Disenio.SCROLL_REGISTRO)
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.pista = rectangulo_redondeado(
            canvas, x1, y1, x2, y2, (x2 - x1) / 2,
            fill=Paleta.FONDO_WIDGET, outline=Paleta.TINTA, width=max(1, e(6)))
        self.perilla = rectangulo_redondeado(
            canvas, x1 + e(5), y1 + e(5), x2 - e(5), y1 + e(60), e(9),
            fill=Paleta.DORADO, outline=Paleta.DORADO_BORDE, width=max(1, e(5)))
        self._arrastre = None
        for item in (self.pista, self.perilla):
            canvas.tag_bind(item, "<ButtonPress-1>", self._al_presionar)
            canvas.tag_bind(item, "<B1-Motion>", self._al_arrastrar)
        texto.configure(yscrollcommand=self.actualizar)

    def actualizar(self, primero, ultimo):
        """Coloca la perilla según la porción visible del texto."""
        primero, ultimo = float(primero), float(ultimo)
        margen = self.e(5)
        util = (self.y2 - self.y1) - 2 * margen
        visible = ultimo - primero
        if visible >= 1.0:
            # Todo cabe: la perilla queda en reposo, arriba, con su tamaño base.
            alto, y = self.e(55), self.y1 + margen
        else:
            alto = max(self.e(45), util * visible)
            y = self.y1 + margen + (util - alto) * (primero / (1.0 - visible))
        self.canvas.coords(self.perilla, *rectangulo_puntos(
            self.x1 + margen, y, self.x2 - margen, y + alto, self.e(9)))

    def _mover_a(self, y):
        util = (self.y2 - self.y1) - 2 * self.e(5)
        self.texto.yview_moveto(max(0.0, min(1.0, (y - self.y1) / max(1, util))))

    def _al_presionar(self, evento):
        self._mover_a(evento.y - self.e(25))

    def _al_arrastrar(self, evento):
        self._mover_a(evento.y - self.e(25))


def rectangulo_puntos(x1, y1, x2, y2, radio):
    """Puntos de un rectángulo redondeado (para actualizar un polígono)."""
    radio = max(0, min(radio, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = []
    for cx, cy, ini in ((x2 - radio, y1 + radio, -90), (x2 - radio, y2 - radio, 0),
                        (x1 + radio, y2 - radio, 90), (x1 + radio, y1 + radio, 180)):
        for k in range(9):
            a = math.radians(ini + 90 * k / 8)
            pts += [cx + radio * math.cos(a), cy + radio * math.sin(a)]
    return pts


class LoggerWidgetRenderer:
    """Renderer del widget del logger: la terminal de la app."""
    MAX_LINEAS = 30

    def __init__(self, widget_logico, canvas: tk.Canvas, e):
        """Monta el terminal de solo lectura sobre el canvas."""
        self.widget  = widget_logico
        self._lineas = 0  # cantidad de líneas presentes en el terminal

        x1, y1, x2, y2 = e.caja(Disenio.TEXTO_REGISTRO)
        familia = _familia_mono(canvas)
        self.texto = tk.Text(
            canvas,
            bg=Paleta.TARJETA,
            fg=Paleta.TINTA,
            insertbackground=Paleta.TINTA,
            font=(familia, -max(9, e(42))),
            relief="flat", bd=0, highlightthickness=0,
            state="disabled", wrap="word",
            padx=e(8), pady=e(6), cursor="arrow",
        )
        canvas.create_window(x1, y1, window=self.texto, anchor="nw",
                             width=x2 - x1, height=y2 - y1)

        self.texto.tag_config("ts",    foreground=COLOR_TS)
        self.texto.tag_config("prmt",  foreground=Paleta.DORADO_DIM)
        self.texto.tag_config("info",  foreground=Paleta.TINTA)
        self.texto.tag_config("warn",  foreground=COLOR_AVISO)
        self.texto.tag_config("error", foreground=COLOR_ERROR)

        self.barra = BarraRegistro(canvas, e, self.texto)

        # Rueda del mouse (Windows/macOS: <MouseWheel>; Linux: Button-4/5).
        self.texto.bind("<MouseWheel>", self._al_rueda)
        self.texto.bind("<Button-4>", lambda _e: self.texto.yview_scroll(-1, "units"))
        self.texto.bind("<Button-5>", lambda _e: self.texto.yview_scroll(1, "units"))

        self.widget.suscribir(self._agregar_linea)
        for entrada in self.widget.obtener_lineas():
            self._agregar_linea(entrada)

    def _al_rueda(self, evento):
        """Desplaza el terminal con la rueda del mouse."""
        pasos = -1 * (evento.delta // 120) if evento.delta else 0
        self.texto.yview_scroll(pasos, "units")

    def _etiqueta_para(self, nivel) -> str:
        """Devuelve la etiqueta de color ('info'/'warn'/'error') del nivel."""
        return {
            NivelLog.INFO:        "info",
            NivelLog.ADVERTENCIA: "warn",
            NivelLog.ERROR:       "error",
        }[nivel]

    def _agregar_linea(self, entrada):
        """Inserta una línea con formato y recorta a las últimas 30."""
        try:
            self.texto.configure(state="normal")
            marca = datetime.fromtimestamp(entrada.timestamp).strftime("%d-%m-%Y %H:%M")
            self.texto.insert("end", f"[{marca}] ", ("ts",))
            self.texto.insert("end", "> ", ("prmt",))
            self.texto.insert("end", f"[{entrada.origen}] ",
                              (self._etiqueta_para(entrada.nivel),))
            self.texto.insert("end", f"{entrada.mensaje}\n",
                              (self._etiqueta_para(entrada.nivel),))
            self._lineas += 1
            if self._lineas > self.MAX_LINEAS:
                self.texto.delete("1.0", "2.0")   # borra la línea más vieja
            self.texto.configure(state="disabled")
            self.texto.see("end")
        except tk.TclError:
            pass   # el terminal ya fue destruido

    def dibujar(self):
        """API común con el resto de renderers."""

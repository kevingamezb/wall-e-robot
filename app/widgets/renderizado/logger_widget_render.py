# wall-e-robot/app/widgets/renderizado/logger_widget_render.py
# Kevin Gámez - 13/09/2026


import tkinter as tk
from datetime import datetime
from ...nucleo.paleta import Paleta
from ...nucleo.estado import NivelLog


class LoggerWidgetRenderer:
    """Renderer del widget del logger: la terminal de la app."""
    MAX_LINEAS = 30

    def __init__(self, widget_logico, parent: tk.Widget):
        """Monta el terminal de solo lectura y se suscribe al widget lógico."""
        self.widget  = widget_logico
        self._lineas = 0  # cantidad de líneas presentes en el terminal

        # Terminal: Text de solo lectura, oscuro, estilo consola.
        self.texto = tk.Text(
            parent,
            bg=Paleta.FONDO_WIDGET,
            fg=Paleta.TEXTO_LOG,
            insertbackground=Paleta.TEXTO_LOG,
            font=(Paleta.FUENTE_HUD, 10),
            relief="flat",
            state="disabled",
            height=14,
            wrap="word",
            padx=8, pady=6,
        )
        self.texto.pack(fill="both", expand=True)

        # Etiquetas de color por nivel, aplicadas a rangos del Text.
        self.texto.tag_config("ts",   foreground=Paleta.CYAN_DIM)
        self.texto.tag_config("prmt", foreground=Paleta.AXIOM_CYAN)
        self.texto.tag_config("info", foreground=Paleta.TEXTO_LOG)
        self.texto.tag_config("warn", foreground=Paleta.NARANJA)
        self.texto.tag_config("error", foreground=Paleta.ROJO)

        # Rueda del mouse para desplazar el historial.
        self.texto.bind("<MouseWheel>", self._al_rueda)

        # Suscripción al widget lógico: cada línea nueva llega aquí.
        self.widget.suscribir(self._agregar_linea)

        # Si ya había líneas antes de suscribirse, se cargan.
        for entrada in self.widget.obtener_lineas():
            self._agregar_linea(entrada)

    def _al_rueda(self, evento):
        """Desplaza el terminal con la rueda del mouse (en cualquier OS)."""
        pasos = -1 * (evento.delta // 120)  # un "click" de rueda = 1 línea
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
            self.texto.configure(state="normal")  # el Text solo se edita aquí

            # Timestamp local con formato DD-MM-AAAA HH:MM (ej: [06-10-2026 20:02]).
            marca = datetime.fromtimestamp(entrada.timestamp).strftime(
                "%d-%m-%Y %H:%M",
            )
            self.texto.insert(
                "end",
                f"[{marca}] ",
                ("ts",),
            )
            self.texto.insert(
                "end",
                "\u25b8 ",
                ("prmt",),
            )
            self.texto.insert(
                "end",
                f"[{entrada.origen}] ",
                (self._etiqueta_para(entrada.nivel),),
            )
            self.texto.insert(
                "end",
                f"{entrada.mensaje}\n",
                (self._etiqueta_para(entrada.nivel),),
            )

            self._lineas += 1
            if self._lineas > self.MAX_LINEAS:
                self.texto.delete("1.0", "2.0")  # borra la línea más vieja

            self.texto.configure(state="disabled")
            self.texto.see("end")  # siempre mostrar la línea más reciente
        except tk.TclError:
            # El terminal ya fue destruido (cambio de pantalla)
            pass

    def dibujar(self):
        """API común con el resto de renderers."""
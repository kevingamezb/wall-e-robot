# wall-e-robot/app/widgets/renderizado/logger_widget_render.py
# Kevin Gámez - 13/09/2026


import tkinter as tk
from datetime import datetime
from ...nucleo.paleta import Paleta
from ...nucleo.estado import NivelLog


class LoggerWidgetRenderer:
    """
    Renderer (Tkinter) del widget del logger: la "terminal" de la app.

    A diferencia del resto de los renderers (que pintan en un Canvas), este
    usa un widget de Tkinter real: un `tk.Text`. Es lo adecuado para una
    lista de líneas desplazable con colores por nivel de gravedad.

    Se SUSCRIBE al widget lógico (LoggerWidget): cada vez que llega una
    línea nueva al log, el renderer la agrega al terminal al instante, con
    su color (info blanco, advertencia naranja, error rojo) y su hora.
    Mantiene las últimas 30 líneas, como define el modelo de datos.
    """

    MAX_LINEAS = 30

    def __init__(self, widget_logico, parent: tk.Widget):
        """
        Constructor del renderer del logger.

        widget_logico : el LoggerWidget lógico (recibe las líneas del Logger).
        parent        : el frame/canvas que contendrá el terminal.
        """
        self.widget = widget_logico
        self._lineas = 0  # cuántas líneas hay hoy en el terminal

        # Terminal: Text apagado (solo lectura) oscuro, como una consola.
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

        # Etiquetas de color por nivel (las usamos con los rangos del Text).
        self.texto.tag_config("ts",   foreground=Paleta.CYAN_DIM)
        self.texto.tag_config("prmt", foreground=Paleta.AXIOM_CYAN)
        self.texto.tag_config("info", foreground=Paleta.TEXTO_LOG)
        self.texto.tag_config("warn", foreground=Paleta.NARANJA)
        self.texto.tag_config("error", foreground=Paleta.ROJO)

        # Rueda del mouse para desplazar el historial.
        self.texto.bind("<MouseWheel>", self._al_rueda)

        # Nos unimos al widget lógico: cada línea nueva llega aquí.
        self.widget.suscribir(self._agregar_linea)

        # Si ya había líneas antes de suscribirnos, las cargamos.
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
        """Inserta una línea nueva con formato, y recorta a las últimas 30."""
        try:
            self.texto.configure(state="normal")  # Text solo se edita aquí adentro

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
            # El terminal ya fue destruido (se cambió de pantalla): el
            # callback viejo sigue vivo, pero ya no hay nada que pintar.
            pass

    def dibujar(self):
        """
        API común con el resto de renderers.

        El terminal se actualiza solo vía suscripción (cuando llega una
        línea nueva), así que dibujar() no tiene nada que repintar.
        """
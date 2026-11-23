import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageDraw, ImageTk

from ..nucleo.configuracion_control import OPCIONES_MOTORES, OPCIONES_SERVOS
from ..nucleo.paleta import Paleta
from ..widgets.renderizado.texto_render import foto_texto


class ModalConfiguracion(tk.Toplevel):
    def __init__(self, parent, configuracion):
        raiz = parent.winfo_toplevel()
        super().__init__(raiz, bg=Paleta.FONDO_NEGRO)
        self.withdraw()
        self.transient(raiz)
        self.title("Configuración")
        self.resizable(False, False)
        self._configuracion = configuracion
        self._opciones = {}
        self._rotulos = []
        self._interruptores = [self._imagen_interruptor(activo) for activo in (False, True)]

        panel = tk.Frame(self, bg=Paleta.FONDO_NEGRO, padx=22, pady=18)
        panel.pack(fill="both", expand=True)
        tk.Label(panel, image=self._texto("Configuración", 26),
                 bg=Paleta.FONDO_NEGRO).pack(anchor="w", pady=(0, 12))
        self._grupo(panel, "Servos", OPCIONES_SERVOS.values())
        self._grupo(panel, "Motores", OPCIONES_MOTORES)

        acciones = tk.Frame(panel, bg=Paleta.FONDO_NEGRO)
        acciones.pack(anchor="e", pady=(4, 0))
        for texto, comando, fondo, color in (
            ("Cancelar", self.destroy, Paleta.FONDO_WIDGET, Paleta.TEXTO_LOG),
            ("Aplicar", self._aplicar, Paleta.DORADO, Paleta.TINTA),
        ):
            tk.Button(acciones, text=texto, image=self._texto(texto, 15, color),
                      command=comando, bg=fondo, activebackground=fondo,
                      relief="flat", padx=12, pady=7).pack(side="left", padx=(8, 0))

        self.bind("<Escape>", lambda _evento: self.destroy())
        self.update_idletasks()
        ancho, alto = self.winfo_reqwidth(), self.winfo_reqheight()
        x = raiz.winfo_rootx() + (raiz.winfo_width() - ancho) // 2
        y = raiz.winfo_rooty() + (raiz.winfo_height() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{max(0, x)}+{max(0, y)}")
        self.deiconify()
        self.wait_visibility()
        self.grab_set()
        self._primer_interruptor.focus_set()

    def _texto(self, texto, px, color=Paleta.DORADO):
        rotulo = foto_texto(texto, px, color, master=self)
        self._rotulos.append(rotulo)
        return rotulo

    def _imagen_interruptor(self, activo):
        imagen = Image.new("RGBA", (34, 19))
        dibujo = ImageDraw.Draw(imagen)
        borde = Paleta.DORADO if activo else Paleta.TEXTO_TENUE
        fondo = Paleta.DORADO if activo else Paleta.FONDO_CANVAS
        dibujo.rounded_rectangle((0, 0, 33, 18), radius=9, fill=fondo, outline=borde)
        x = 18 if activo else 3
        dibujo.ellipse((x, 3, x + 12, 15), fill=Paleta.TINTA if activo else borde)
        return ImageTk.PhotoImage(imagen, master=self)

    def _grupo(self, panel, titulo, opciones):
        tk.Label(panel, image=self._texto(titulo, 16),
                 bg=Paleta.FONDO_NEGRO).pack(anchor="w", pady=(0, 4))
        grupo = tk.Frame(panel, bg=Paleta.FONDO_WIDGET)
        grupo.pack(fill="x", pady=(0, 10))
        for clave, texto in opciones:
            valor = tk.BooleanVar(master=self, value=self._configuracion.valores[clave])
            fila = tk.Frame(grupo, bg=Paleta.FONDO_WIDGET)
            fila.pack(fill="x", padx=10, pady=2)
            etiqueta = tk.Label(fila, text=texto, anchor="w", width=32,
                                font=(Paleta.FUENTE_TEXTO, 11),
                                bg=Paleta.FONDO_WIDGET, fg=Paleta.TEXTO_LOG)
            etiqueta.pack(side="left", fill="x", expand=True)
            interruptor = tk.Checkbutton(
                fila, text=texto, variable=valor, image=self._interruptores[0],
                selectimage=self._interruptores[1], indicatoron=False,
                bg=Paleta.FONDO_WIDGET, selectcolor=Paleta.FONDO_WIDGET,
                activebackground=Paleta.FONDO_WIDGET, highlightthickness=1,
                highlightbackground=Paleta.FONDO_WIDGET, highlightcolor=Paleta.DORADO,
                relief="flat", offrelief="flat", borderwidth=0)
            interruptor.pack(side="right", padx=(10, 0))
            etiqueta.bind("<Button-1>", lambda _evento, boton=interruptor: boton.invoke())
            if not self._opciones:
                self._primer_interruptor = interruptor
            self._opciones[clave] = valor

    def _aplicar(self):
        try:
            self._configuracion.aplicar({clave: valor.get() for clave, valor in self._opciones.items()})
        except OSError as error:
            messagebox.showerror("Configuración", f"No se pudo guardar la configuración.\n{error}",
                                 parent=self)
            return
        self.destroy()

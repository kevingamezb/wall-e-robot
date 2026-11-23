import queue
import threading
import tkinter as tk

from ..comunicacion.credenciales_red import (
    CLAVE_FABRICA, USUARIO_FABRICA, guardar_por_red, preparar_credenciales,
)
from ..nucleo.paleta import Paleta
from ..widgets.renderizado.texto_render import foto_texto


class ModalCredenciales(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent, bg=Paleta.FONDO_NEGRO)
        self.transient(parent)
        self.title("Wi-Fi y OTA")
        self.resizable(False, False)
        self.guardado = False
        self._ocupado = False
        self._resultado = queue.SimpleQueue()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.bind("<Escape>", lambda _evento: self._cerrar())

        panel = tk.Frame(self, bg=Paleta.FONDO_NEGRO, padx=22, pady=18)
        panel.pack(fill="both", expand=True)
        self._titulo = foto_texto("Wi-Fi y OTA", 23, Paleta.DORADO, master=self)
        tk.Label(panel, image=self._titulo, bg=Paleta.FONDO_NEGRO).pack(anchor="w")
        tk.Label(panel, text="Conecta el computador a la red WALL-E.",
                 fg=Paleta.TEXTO_LOG, bg=Paleta.FONDO_NEGRO).pack(anchor="w", pady=(6, 12))
        self._actuales = self._campos(panel, "Acceso OTA actual", (
            ("Usuario", False, USUARIO_FABRICA), ("Contraseña", True, CLAVE_FABRICA),
        ))
        self._nuevas = self._campos(panel, "Nuevas credenciales", (
            ("Contraseña Wi-Fi", True, ""), ("Usuario OTA", False, ""),
            ("Contraseña OTA", True, ""),
        ))

        self._estado = tk.StringVar(self)
        tk.Label(panel, textvariable=self._estado, fg=Paleta.DORADO, bg=Paleta.FONDO_NEGRO,
                 wraplength=340, justify="left").pack(anchor="w", pady=8)
        acciones = tk.Frame(panel, bg=Paleta.FONDO_NEGRO)
        acciones.pack(anchor="e")
        self._cancelar = tk.Button(acciones, text="Cancelar", command=self._cerrar)
        self._cancelar.pack(side="left", padx=(0, 8))
        self._guardar = tk.Button(acciones, text="Guardar y reiniciar", bg=Paleta.DORADO,
                                  command=self._aplicar)
        self._guardar.pack(side="left")
        self.wait_visibility()
        self.grab_set()
        self._nuevas[0].focus_set()

    def _campos(self, panel, titulo, opciones):
        grupo = tk.LabelFrame(panel, text=titulo, bg=Paleta.FONDO_NEGRO,
                             fg=Paleta.DORADO, padx=8, pady=6)
        grupo.pack(fill="x", pady=(0, 8))
        grupo.columnconfigure(1, weight=1)
        campos = []
        for fila, (texto, secreta, valor) in enumerate(opciones):
            tk.Label(grupo, text=texto, bg=Paleta.FONDO_NEGRO,
                     fg=Paleta.TEXTO_LOG).grid(row=fila, column=0, sticky="w", padx=(0, 8), pady=2)
            campo = tk.Entry(grupo, show="*" if secreta else "")
            campo.insert(0, valor)
            campo.grid(row=fila, column=1, sticky="ew", pady=2)
            campos.append(campo)
        return campos

    def _cerrar(self):
        if not self._ocupado:
            self.destroy()

    def _aplicar(self):
        usuario, clave = (campo.get() for campo in self._actuales)
        if not usuario or not clave:
            self._estado.set("Introduce el usuario y la contraseña OTA actuales.")
            return
        try:
            mensaje = preparar_credenciales(*(campo.get() for campo in self._nuevas))
        except ValueError as error:
            self._estado.set(str(error))
            return
        self._ocupar(True)
        self._estado.set("Guardando en el ESP32…")
        threading.Thread(target=self._enviar, args=(usuario, clave, mensaje), daemon=True).start()
        self.after(60, self._comprobar)

    def _ocupar(self, ocupada):
        self._ocupado = ocupada
        for widget in (self._guardar, self._cancelar, *self._actuales, *self._nuevas):
            widget.configure(state="disabled" if ocupada else "normal")

    def _enviar(self, usuario, clave, mensaje):
        try:
            guardar_por_red(usuario, clave, mensaje)
        except OSError as error:
            self._resultado.put(str(error))
        else:
            self._resultado.put(None)

    def _comprobar(self):
        try:
            error = self._resultado.get_nowait()
        except queue.Empty:
            self.after(60, self._comprobar)
            return
        if error:
            self._estado.set(error)
            self._ocupar(False)
            return
        self.guardado = True
        self.destroy()

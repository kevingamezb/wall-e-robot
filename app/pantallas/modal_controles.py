# wall-e-robot/app/pantallas/modal_controles.py
# Kevin Gámez - 06/10/2026
#
# La ventana de configuración del teclado, estilo emulador de consola
# (PCSX2/Dolphin): una fila por acción y "clic en la acción -> presiona la
# tecla". La captura se hace en esta ventana (tiene el foco con grab_set), así
# las teclas que se asignan no disparan comandos de la pantalla principal.


import tkinter as tk

from ..nucleo.paleta import Paleta
from ..widgets.logica.mapeo_teclado import (
    ACCIONES, MODIFICADORAS, MapeoTeclado, nombre_tecla,
)


class ModalControles:
    """
    Modal de configuración de controles.

    - Cada acción (cruceta, manos, reposo, ejes) es una fila con su tecla.
    - Clic en la fila: entra en modo captura ("Presiona una tecla...").
    - La siguiente tecla se asigna; Esc cancela; los modificadores solos se
      ignoran (no son controles).
    - Cada cambio se notifica por `on_cambio` (en main.py: guardar el JSON).
    """

    def __init__(self, raiz: tk.Misc, mapeo: MapeoTeclado, on_cambio=None):
        self.mapeo = mapeo
        self.on_cambio = on_cambio or (lambda: None)
        self._capturando = None  # accion_id en modo captura (o None)

        self.ventana = tk.Toplevel(raiz)
        self.ventana.title("Configurar controles")
        self.ventana.configure(bg=Paleta.FONDO_APP)
        self.ventana.resizable(False, False)
        self.ventana.transient(raiz)
        self.ventana.grab_set()

        # Sugerencia y estado de captura.
        self.lbl_ayuda = tk.Label(
            self.ventana, text="Clic en la tecla de una acción y pulsa la nueva tecla. "
                               "Esc cancela.",
            bg=Paleta.FONDO_APP, fg=Paleta.TEXTO_TENUE,
            font=(Paleta.FUENTE_TEXTO, 8), justify="left",
        )
        self.lbl_ayuda.pack(fill="x", padx=Paleta.UNIDAD, pady=(Paleta.UNIDAD, 0))

        self.lbl_estado = tk.Label(
            self.ventana, text="", bg=Paleta.FONDO_APP,
            fg=Paleta.DORADO, font=(Paleta.FUENTE_TEXTO, 8), anchor="w",
        )
        self.lbl_estado.pack(fill="x", padx=Paleta.UNIDAD, pady=(4, 0))

        # Lista de filas (acción | tecla | limpiar).
        self.marco_filas = tk.Frame(self.ventana, bg=Paleta.FONDO_WIDGET)
        self.marco_filas.pack(fill="both", padx=Paleta.UNIDAD,
                              pady=(Paleta.UNIDAD // 2, 0))
        self._filas = {}  # accion_id -> (btn_tecla, btn_limpiar)
        self._construir_filas()

        # Pie: restaurar por defecto + cerrar.
        pie = tk.Frame(self.ventana, bg=Paleta.FONDO_APP)
        pie.pack(fill="x", padx=Paleta.UNIDAD, pady=Paleta.UNIDAD)

        btn_restaurar = tk.Button(
            pie, text="RESTAURAR POR DEFECTO", bg=Paleta.FONDO_WIDGET,
            fg=Paleta.TEXTO_TENUE, activebackground=Paleta.GRIS,
            activeforeground=Paleta.TEXTO_LOG, relief="flat",
            font=(Paleta.FUENTE_TEXTO, 8, "bold"), command=self._restaurar,
        )
        btn_restaurar.pack(side="left")

        btn_cerrar = tk.Button(
            pie, text="CERRAR", bg=Paleta.FONDO_WIDGET, fg=Paleta.DORADO,
            activebackground=Paleta.DORADO_DIM, activeforeground=Paleta.TEXTO_LOG,
            relief="flat", font=(Paleta.FUENTE_TEXTO, 8, "bold"), command=self.ventana.destroy,
        )
        btn_cerrar.pack(side="right")

        self.ventana.bind("<KeyPress>", self._al_tecla)
        self._refrescar_filas()

    # --- Construcción ---

    def _construir_filas(self):
        """Crea una fila por acción. El contenido cambia; la estructura no."""
        for fila, accion in enumerate(ACCIONES):
            lbl_nombre = tk.Label(
                self.marco_filas, text=accion.nombre, anchor="w",
                bg=Paleta.FONDO_WIDGET, fg=Paleta.TEXTO_LOG,
                font=(Paleta.FUENTE_TEXTO, 9),
            )
            lbl_nombre.grid(row=fila, column=0, sticky="w",
                            padx=(Paleta.UNIDAD // 3, Paleta.UNIDAD // 2),
                            pady=2)

            btn_tecla = tk.Button(
                self.marco_filas, width=12, relief="flat",
                bg=Paleta.FONDO_APP, font=(Paleta.FUENTE_TEXTO, 9, "bold"),
                command=lambda a=accion.id: self._empezar_captura(a),
            )
            btn_tecla.grid(row=fila, column=1, padx=2, pady=2)

            btn_limpiar = tk.Button(
                self.marco_filas, text="\u2715", width=2, relief="flat",
                bg=Paleta.FONDO_APP, fg=Paleta.TEXTO_TENUE,
                activebackground=Paleta.ROJO, activeforeground=Paleta.TEXTO_LOG,
                font=(Paleta.FUENTE_TEXTO, 9, "bold"),
                command=lambda a=accion.id: self._limpiar(a),
            )
            btn_limpiar.grid(row=fila, column=2, padx=(2, Paleta.UNIDAD // 3), pady=2)

            self._filas[accion.id] = (btn_tecla, btn_limpiar)

    # --- Captura ---

    def _empezar_captura(self, accion_id: str):
        """Entra en modo captura para la acción dada (hace toggle si es la misma)."""
        self._capturando = None if self._capturando == accion_id else accion_id
        self.lbl_estado.config(
            text=("Presiona la tecla para «" + nombre_tecla(self.mapeo.tecla_de(accion_id) or "")
                  + "»..." if self._capturando else ""))
        self._refrescar_filas()

    def _al_tecla(self, evento):
        """Captura la tecla presionada y la asigna a la acción en espera."""
        if self._capturando is None:
            return
        keysym = evento.keysym

        if keysym in ("Escape", "Cancel"):
            self._capturando = None
            self.lbl_estado.config(text="Captura cancelada")
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
        self.lbl_estado.config(text=mensaje, fg=Paleta.DORADO)
        self._capturando = None
        self._refrescar_filas()

    # --- Acciones ---

    def _limpiar(self, accion_id: str):
        self.mapeo.limpiar(accion_id)
        self.on_cambio()
        self.lbl_estado.config(
            text=f"«{self._accion(accion_id).nombre}» sin tecla",
            fg=Paleta.TEXTO_TENUE)
        self._refrescar_filas()

    def _restaurar(self):
        self.mapeo.restaurar_por_defecto()
        self.on_cambio()
        self.lbl_estado.config(text="Controles restaurados de fábrica",
                               fg=Paleta.DORADO)
        self._refrescar_filas()

    # --- Internos ---

    def _accion(self, accion_id: str):
        for accion in ACCIONES:
            if accion.id == accion_id:
                return accion
        raise KeyError(accion_id)

    def _refrescar_filas(self):
        """Pinta el estado de cada fila (tecla asignada / captura en curso)."""
        for accion_id, (btn_tecla, btn_limpiar) in self._filas.items():
            capturando = self._capturando == accion_id
            tecla = self.mapeo.tecla_de(accion_id)

            btn_tecla.config(
                text="... Presiona una tecla ..." if capturando else (
                    nombre_tecla(tecla) if tecla else "(sin tecla)"),
                fg=Paleta.DORADO if capturando else (
                    Paleta.TEXTO_LOG if tecla else Paleta.GRIS),
                activebackground=Paleta.DORADO_DIM if capturando else Paleta.FONDO_APP,
            )
            btn_limpiar.config(state="normal" if tecla else "disabled")


# Cajón de Pruebas (abre y cierra la ventana sola)
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
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

    # 1. La fila muestra la tecla por defecto de cada acción
    modal._refrescar_filas()
    btn_arriba, _ = modal._filas["arriba"]
    assert btn_arriba.cget("text") == "\u2191", f"Debería verse ↑, llegó {btn_arriba.cget('text')}"
    print("OK: la cruceta muestra la flecha de fábrica\n")

    # 2. Captura: asignar una tecla nueva notifica el cambio y guarda
    modal._empezar_captura("arriba")
    assert modal._capturando == "arriba", "Debe entrar en modo captura"
    modal._al_tecla(types.SimpleNamespace(keysym="U"))
    assert mapeo.tecla_de("arriba") == "U", "La tecla capturada debe asignarse"
    assert len(cambios) == 1, "El cambio debe notificarse (para guardar el JSON)"
    assert modal._capturando is None, "Tras capturar se sale del modo"
    print("OK: captura en vivo asigna y avisa del cambio\n")

    # 3. Esc cancela la captura sin tocar el mapeo
    n_original = mapeo.tecla_de("abajo")
    modal._empezar_captura("abajo")
    modal._al_tecla(types.SimpleNamespace(keysym="Escape"))
    assert mapeo.tecla_de("abajo") == n_original, "Esc no debe cambiar nada"
    print("OK: Esc cancela sin modificar\n")

    # 4. Los modificadores solos no se asignan
    modal._empezar_captura("abajo")
    modal._al_tecla(types.SimpleNamespace(keysym="Shift_L"))
    assert mapeo.tecla_de("abajo") == n_original, "Shift solo no se asigna"
    modal._al_tecla(types.SimpleNamespace(keysym="v"))
    assert mapeo.tecla_de("abajo") == "v"
    print("OK: los modificadores se ignoran al capturar\n")

    # 5. Una tecla robada de otra acción se avisa en el estado
    modal._empezar_captura("abajo")
    modal._al_tecla(types.SimpleNamespace(keysym="q"))  # 'q' era de cuello_mas
    assert mapeo.tecla_de("abajo") == "q", "abajo toma la q"
    assert mapeo.tecla_de("cuello_mas") is None, "cuello_mas la pierde"
    mensaje = modal.lbl_estado.cget("text")
    assert "la perdi\u00f3" in mensaje, "Debe avisar que otra acción perdió la tecla"
    print(f"OK: {mensaje}\n")

    # 6. Limpiar y restaurar
    modal._limpiar("abajo")
    assert mapeo.tecla_de("abajo") is None
    modal._restaurar()
    assert mapeo.tecla_de("abajo") == "Down"
    print("OK: limpiar y restaurar por defecto\n")

    modal.ventana.destroy()
    raiz.destroy()
    print("Pruebas OK")
# wall-e-robot/app/widgets/logica/control_teclado.py
# Kevin Gámez - 06/10/2026
#
# El "cable" del teclado al gamepad: traduce <KeyPress>/<KeyRelease> de Tk en
# las mismas acciones que produce el ratón (cruceta, manos, reposo, ejes).
# Reusa el cableado de comandos del Gamepad, así las teclas se ven en el
# renderer y los comandos salen por la misma puerta (gated por habilitado).


import tkinter as tk
import types

from .mapeo_teclado import (
    ACCIONES, DISCRETO, EJE, MODIFICADORAS, Accion, MapeoTeclado, accion_por_id,
)

# Cuánto esperamos entre pasos de un EJE mientras se mantiene la tecla.
# (Más lento que el auto-repetido del teclado: un deslizador de ±70° a 33 ms
#  por tecla se barrería entero en ~2 s; 5° cada 120 ms es un movimiento suave.)
INTERVALO_PASO_MS = 120

# Las direcciones usan el auto-repetido del teclado: mientras se sostiene la
# tecla, Tk re-lanza <KeyPress> y cada repetición vuelve a emitir el comando
# motor. Así el robot no muere por el timeout de seguridad del firmware (~2 s).
MOTOR_ACCIONES = {"arriba", "abajo", "izquierda", "derecha"}

# Botón del gamepad que respalda cada acción discreta (para la visual y emitir).
BOTONES = {
    "arriba": lambda g: g.direccion_arriba,
    "abajo": lambda g: g.direccion_abajo,
    "izquierda": lambda g: g.direccion_izquierda,
    "derecha": lambda g: g.direccion_derecha,
    "reposo": lambda g: g.reposo,
    "mano_abrir": lambda g: g.mano_abrir,
    "mano_cerrar": lambda g: g.mano_cerrar,
}

# (deslizador_del_gamepad, signo) por acción de eje.
DESLIZADORES = {
    "cuello_mas": ("cuello", 1),
    "cuello_menos": ("cuello", -1),
    "hombro_izq_mas": ("hombro_izquierdo", 1),
    "hombro_izq_menos": ("hombro_izquierdo", -1),
    "hombro_der_mas": ("hombro_derecho", 1),
    "hombro_der_menos": ("hombro_derecho", -1),
}


class ControlTeclado:
    """
    Escucha las teclas de la ventana y las despacha al gamepad.

    Reglas de comportamiento:
      - Solo reacciona a teclas del perfil (MapeoTeclado); el resto se ignora.
      - Discretas (manos/reposo): disparan UNA vez aunque el teclado repita
        la pulsación; soltar resetea la visual.
      - Direcciones de motor: cada <KeyPress> (incl. el auto-repetido) vuelve
        a emitir el comando; soltar corta.
      - Ejes (cuello/hombros): un paso cada INTERVALO_PASO_MS mientras se
        sostiene; el Deslizador clampa el rango como con el ratón.
      - Funciona solo con la ventana enfocada (igual que un emulador). Si el
        foco se va (modal, otra app), se limpia el estado para no dejar una
        tecla "clavada".
    """

    def __init__(self, raiz: tk.Misc, mapeo: MapeoTeclado, gamepad):
        self.raiz = raiz
        self.mapeo = mapeo
        self.gamepad = gamepad

        self._pulsadas = set()        # keysyms sostenidos en este momento
        self._temporizadores = {}     # keysym -> id del after() de repetición

        raiz.bind("<KeyPress>", self._al_presionar)
        raiz.bind("<KeyRelease>", self._al_soltar)
        raiz.bind("<FocusOut>", lambda _e: self.limpiar_estado())

    # --- Entrada de teclado ---

    def _al_presionar(self, evento):
        keysym = evento.keysym
        if keysym in MODIFICADORAS:
            return
        accion_id = self.mapeo.buscar_accion(keysym)
        if accion_id is None:
            return
        accion = accion_por_id(accion_id)

        if accion.tipo == EJE:
            self._pulsadas.add(keysym)
            self._aplicar_paso(accion)
            self._programar_repite(keysym, accion)
        elif accion_id in MOTOR_ACCIONES:
            # El auto-repetido del teclado re-dispara esto -> comando repetido.
            self._pulsadas.add(keysym)
            self._pulsar_boton(accion_id)
        elif keysym not in self._pulsadas:
            # Discreta (manos/reposo): dispara UNA vez; lo que sigue del
            # auto-repetido se ignora mientras la tecla siga sostenida.
            self._pulsadas.add(keysym)
            self._pulsar_boton(accion_id)

    def _al_soltar(self, evento):
        keysym = evento.keysym
        self._pulsadas.discard(keysym)

        timer = self._temporizadores.pop(keysym, None)
        if timer is not None:
            self.raiz.after_cancel(timer)

        accion_id = self.mapeo.buscar_accion(keysym)
        if accion_id is not None and accion_id in BOTONES:
            self._soltar_boton(accion_id)

    # --- Despacho ---

    def _pulsar_boton(self, accion_id: str):
        BOTONES[accion_id](self.gamepad).presionar()

    def _soltar_boton(self, accion_id: str):
        BOTONES[accion_id](self.gamepad).soltar()

    def _aplicar_paso(self, accion: Accion):
        """Un paso del eje (+/- paso grados), como lo haría el ratón."""
        clave, signo = DESLIZADORES[accion.id]
        deslizador = getattr(self.gamepad, clave)
        deslizador.mover(deslizador.posicion + signo * accion.paso)

    def _programar_repite(self, keysym: str, accion: Accion):
        """Agenda el siguiente paso del eje mientras se siga sosteniendo."""
        def repetir():
            if keysym in self._pulsadas:
                self._aplicar_paso(accion)
                self._programar_repite(keysym, accion)
        self._temporizadores[keysym] = self.raiz.after(INTERVALO_PASO_MS, repetir)

    def limpiar_estado(self):
        """Cancela repeticiones y suelta los botones (foco perdido, etc.)."""
        for keysym in list(self._pulsadas):
            self._al_soltar(
                types.SimpleNamespace(keysym=keysym))


# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.widgets.logica.control_teclado

if __name__ == "__main__":
    print("Prueba control_teclado.py\n")

    import types
    from ...nucleo.estado import EstadoRobot
    from .gamepad import Gamepad

    def _tecla(keysym):
        """Un 'evento' de teclado mínimo (sin abrir ventana)."""
        return types.SimpleNamespace(keysym=keysym)

    raiz = tk.Tk()
    raiz.withdraw()

    estado = EstadoRobot()
    gamepad = Gamepad(estado)
    comandos = []
    gamepad.suscribir_comando(comandos.append)
    control = ControlTeclado(raiz, MapeoTeclado(), gamepad)

    # 1. Flecha arriba -> comando motor (el renderer queda presionado)
    print("=== Dirección con motor (auto-repetido) ===")
    control._al_presionar(_tecla("Up"))
    assert comandos[-1] == {"tipo": "motor", "direccion": "arriba"}
    assert gamepad.direccion_arriba.presionado, "La tecla debe encender el botón"
    control._al_presionar(_tecla("Up"))  # simula auto-repetido del teclado
    assert len(comandos) >= 2, "Repetir la tecla debe re-emitir para no morir por timeout"
    control._al_soltar(_tecla("Up"))
    assert not gamepad.direccion_arriba.presionado, "Soltar apaga el botón"
    print(f"OK: {len(comandos)} emisiones de motor sueltas\n")

    # 2. Mano abrir -> UN disparo, aunque el teclado repita la pulsación
    print("=== Discreta dispara una sola vez ===")
    n = len(comandos)
    control._al_presionar(_tecla("space"))
    control._al_presionar(_tecla("space"))  # auto-repetido: NO debe multiplicar
    assert len(comandos) == n + 1, "Abrir mano debe emitir una única vez"
    assert comandos[-1]["tipo"] == "multi"
    control._al_soltar(_tecla("space"))
    print("OK: auto-repetido ignorado en discretas\n")

    # 3. Eje: paso a paso mientras se sostiene, se detiene al soltar
    print("=== Eje (cuello) paso a paso ===")
    n = len(comandos)
    control._al_presionar(_tecla("q"))  # cuello_mas
    assert len(comandos) == n + 1, "El primer paso sí se emite"
    assert comandos[-1] == {"tipo": "servo", "servo": "cuello", "angulo": 5}
    assert gamepad.cuello.posicion == 5
    control._aplicar_paso(accion_por_id("cuello_mas"))  # siguiente paso
    assert gamepad.cuello.posicion == 10
    control._al_soltar(_tecla("q"))
    assert "q" not in control._temporizadores, "El temporizador se cancela al soltar"
    control.raiz.update()
    assert gamepad.cuello.posicion == 10, "Al soltar el eje no debe seguir avanzando"
    print(f"OK: pasos de 5°, se detiene en {gamepad.cuello.posicion}\n")

    # 4. Reposo por teclado
    print("=== Reposo ===")
    n = len(comandos)
    control._al_presionar(_tecla("r"))
    control._al_soltar(_tecla("r"))
    assert len(comandos) == n + 1
    assert comandos[-1]["tipo"] == "multi"
    print("OK: reposo dispara UN multi\n")

    # 5. Teclas sin mapear se ignoran; modificadores también
    print("=== Teclas ignoradas ===")
    n = len(comandos)
    control._al_presionar(_tecla("F12"))
    control._al_presionar(_tecla("Shift_L"))
    assert len(comandos) == n, "F12 y Shift no deben generar comandos"
    control._al_soltar(_tecla("Shift_L"))
    print("OK: teclas ajenas al perfil no hacen nada\n")

    # 6. Direcciones opuestas no chocan: soltar la izquierda no apaga derecha
    print("=== Presiones simultáneas ===")
    control._al_presionar(_tecla("Up"))
    control._al_presionar(_tecla("Left"))
    control._al_soltar(_tecla("Left"))
    assert gamepad.direccion_arriba.presionado, "Soltar una tecla no apaga la otra"
    control._al_soltar(_tecla("Up"))
    assert not gamepad.direccion_arriba.presionado
    print("OK: cada tecla con su propio estado\n")

    # 7. limpiar_estado al perder el foco
    print("=== Pérdida de foco ===")
    control._al_presionar(_tecla("r"))
    control.limpiar_estado()
    assert not gamepad.reposo.presionado, "Al perder el foco se sueltan los botones"
    assert not control._pulsadas, "El estado pulsado queda limpio"
    print("OK: estado limpio tras FocusOut\n")

    raiz.destroy()
    print("Pruebas OK")
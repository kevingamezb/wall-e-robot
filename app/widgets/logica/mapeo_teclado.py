# wall-e-robot/app/widgets/logica/mapeo_teclado.py
# Kevin Gámez - 06/10/2026
#
# El "perfil de controles": la traducción tecla (keysym de Tk) -> acción
# del robot, con persistencia en configuracion/controles.json (estilo
# retroarch.cfg). Es LÓGICA PURA: no toca la GUI. El driver (control_teclado.py)
# y el modal (modal_controles.py) la consumen.


import json
from dataclasses import dataclass
from pathlib import Path


# Acciones mapeables. IDs estables (van al JSON; NO renombrarlos) y nombres
# para la GUI. tipo: "discreto" (dispara 1 vez; manos/reposo) o "eje"
# (paso a paso mientras se mantiene; cuello/hombros).
DISCRETO = "discreto"
EJE = "eje"

# Paso de cuello/hombros por "pulsado" del teclado (los servos aceptan ±70°).
PASO_CUELLO = 5
PASO_HOMBRO = 5


@dataclass(frozen=True)
class Accion:
    """Descriptor de una acción mapeable del control manual."""
    id: str       # clave estable para el JSON
    nombre: str   # etiqueta que se ve en la GUI
    tipo: str     # DISCRETO | EJE
    paso: int = 0 # para EJE, cuántos grados avanza por paso


ACCIONES = (
    Accion("arriba", "Avanzar", DISCRETO),
    Accion("abajo", "Retroceder", DISCRETO),
    Accion("izquierda", "Girar izquierda", DISCRETO),
    Accion("derecha", "Girar derecha", DISCRETO),
    Accion("reposo", "Reposo", DISCRETO),
    Accion("mano_abrir", "Abrir mano", DISCRETO),
    Accion("mano_cerrar", "Cerrar mano", DISCRETO),
    Accion("cuello_mas", "Cuello arriba", EJE, PASO_CUELLO),
    Accion("cuello_menos", "Cuello abajo", EJE, PASO_CUELLO),
    Accion("hombro_izq_mas", "Hombro izq. arriba", EJE, PASO_HOMBRO),
    Accion("hombro_izq_menos", "Hombro izq. abajo", EJE, PASO_HOMBRO),
    Accion("hombro_der_mas", "Hombro der. arriba", EJE, PASO_HOMBRO),
    Accion("hombro_der_menos", "Hombro der. abajo", EJE, PASO_HOMBRO),
)

# Teclas que no tienen sentido como control (modificadores solas). Al capturar
# una tecla en el modal se ignoran. Escape aparte, que cancela la captura.
MODIFICADORAS = {
    "Shift_L", "Shift_R", "Control_L", "Control_R",
    "Alt_L", "Alt_R", "Caps_Lock",
}

RUTA_CONTROLES = Path(__file__).resolve().parents[3] / "configuracion" / "controles.json"


def _teclas_por_defecto() -> dict:
    """Perfil de fábrica: flechas mueven, letras para cuello/hombros/manos."""
    return {
        "arriba": "Up",
        "abajo": "Down",
        "izquierda": "Left",
        "derecha": "Right",
        "reposo": "r",
        "mano_abrir": "space",
        "mano_cerrar": "c",
        "cuello_mas": "q",
        "cuello_menos": "a",
        "hombro_izq_mas": "w",
        "hombro_izq_menos": "s",
        "hombro_der_mas": "e",
        "hombro_der_menos": "d",
    }


def accion_por_id(accion_id: str) -> Accion:
    """Devuelve la Accion del ID dado (lanza KeyError si no existe)."""
    for accion in ACCIONES:
        if accion.id == accion_id:
            return accion
    raise KeyError(accion_id)


def nombre_tecla(keysym: str) -> str:
    """'Up' -> '↑', 'space' -> 'ESPACIO', 'q' -> 'Q' (para la GUI)."""
    especiales = {
        "Up": "\u2191", "Down": "\u2193", "Left": "\u2190", "Right": "\u2192",
        "space": "ESPACIO", "Return": "ENTRAR", "Escape": "ESC",
        "Tab": "TAB", "BackSpace": "RETROCESO", "Delete": "SUPR",
        "Home": "INICIO", "End": "FIN", "Prior": "RE P\xc1G",
        "Next": "AV P\xc1G",
    }
    if keysym in especiales:
        return especiales[keysym]
    if len(keysym) == 1:
        return keysym.upper()
    return keysym


class MapeoTeclado:
    """
    El perfil de controles: dict accion_id -> keysym.

    Reglas:
      - Una acción siempre tiene UNA tecla (si se le asigna otra, se reemplaza).
      - Una tecla solo puede estar en UNA acción (la última asignación manda y
        la acción ocupada anterior se libera).
      - El archivo JSON admite 'version' para poder migrar el formato.
    """

    VERSION = 1

    def __init__(self, mapa: dict | None = None):
        self._mapa = dict(mapa) if mapa is not None else _teclas_por_defecto()

    # --- Persistencia ---

    @classmethod
    def cargar(cls, ruta: Path | None = None) -> "MapeoTeclado":
        """
        Carga el perfil desde JSON. Si falta el archivo o hay entradas
        inválidas, se completan con los valores por defecto.
        """
        ruta = ruta or RUTA_CONTROLES
        mapa = {}
        if ruta.is_file():
            try:
                datos = json.loads(ruta.read_text(encoding="utf-8"))
                mapa = datos.get("teclado", {})
            except (json.JSONDecodeError, OSError):
                mapa = {}
            if not isinstance(mapa, dict):
                mapa = {}
            mapa = {k: v for k, v in mapa.items() if isinstance(v, str)}

        mapa = cls(mapa)
        mapa._completar_faltantes()
        return mapa

    def guardar(self, ruta: Path | None = None) -> Path:
        """Escribe el perfil en JSON (crea la carpeta si hace falta)."""
        ruta = ruta or RUTA_CONTROLES
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps({
            "version": self.VERSION,
            "teclado": dict(sorted(self._mapa.items())),
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        return ruta

    # --- Consultas ---

    def tecla_de(self, accion_id: str) -> str | None:
        return self._mapa.get(accion_id)

    def tecla_de_o_por_defecto(self, accion_id: str) -> str:
        return self._mapa.get(accion_id, _teclas_por_defecto().get(accion_id))

    def buscar_accion(self, keysym: str) -> str | None:
        """A qué acción está asignada la tecla (None si no está mapeada)."""
        for accion_id, tecla in self._mapa.items():
            if tecla == keysym:
                return accion_id
        return None

    def tecla_ocupada(self, keysym: str, excepto: str | None = None) -> str | None:
        """Acción que ocupa la tecla, ignorando 'excepto' (para reasignar)."""
        for accion_id, tecla in self._mapa.items():
            if tecla == keysym and accion_id != excepto:
                return accion_id
        return None

    # --- Edición ---

    def asignar(self, accion_id: str, keysym: str):
        """
        Asigna una tecla a una acción. Si la tecla estaba en otra acción,
        esa acción queda sin tecla (una tecla = una acción).
        """
        accion_por_id(accion_id)  # valida que exista la acción
        ocupada = self.tecla_ocupada(keysym, excepto=accion_id)
        if ocupada is not None:
            self._mapa.pop(ocupada, None)
        self._mapa[accion_id] = keysym

    def limpiar(self, accion_id: str):
        """Deja la acción sin tecla asignada."""
        accion_por_id(accion_id)
        self._mapa.pop(accion_id, None)

    def restaurar_por_defecto(self):
        self._mapa = _teclas_por_defecto()

    # --- Internos ---

    def _completar_faltantes(self):
        """Acciones sin tecla declarada reciben la tecla de fábrica."""
        faltan = {a.id for a in ACCIONES} - set(self._mapa)
        for accion_id in faltan:
            self._mapa[accion_id] = _teclas_por_defecto()[accion_id]
        # Cualquier id desconocido (de un JSON viejo/ajeno) se descarta.
        validas = {a.id for a in ACCIONES}
        self._mapa = {k: v for k, v in self._mapa.items() if k in validas}


# Cajón de Pruebas
#
# Ejecutar desde la raíz del proyecto (donde está la carpeta 'app'):
#   python -m app.widgets.logica.mapeo_teclado

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # console cp1252 no imprime ↑/↓
    except Exception:
        pass
    print("Prueba mapeo_teclado.py\n")

    # 1. Perfil por defecto cubre todas las acciones y sin teclas duplicadas
    print("=== Perfil por defecto ===")
    mapeo = MapeoTeclado()
    assert {a.id for a in ACCIONES} <= set(mapeo._mapa), "Faltan acciones"
    teclas = list(mapeo._mapa.values())
    assert len(teclas) == len(set(teclas)), "Una tecla no puede repetirse"
    assert mapeo.tecla_de("arriba") == "Up", "ARRIBA debería ser la flecha ↑"
    print(f"OK: {len(mapeo._mapa)} acciones, teclas únicas\n")

    # 2. Cargar sin archivo -> por defecto; con archivo -> round-trip
    print("=== Persistencia (JSON) ===")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "controles.json"
        mapeo.guardar(ruta)
        mapeo2 = MapeoTeclado.cargar(ruta)
        assert mapeo2._mapa == mapeo._mapa, "Guardar/cargar debe ser idéntico"
        ruta.unlink()
        mapeo3 = MapeoTeclado.cargar(ruta)  # sin archivo -> defaults
        assert mapeo3.tecla_de("reposo") == "r"
    print("OK: round-trip y fallback a defaults sin archivo\n")

    # 3. Asignar: reemplaza la tecla anterior y libera la acción ocupada
    print("=== Asignaciones y conflictos ===")
    mapeo = MapeoTeclado()
    mapeo.asignar("arriba", "x")  # x no estaba ocupada
    assert mapeo.tecla_de("arriba") == "x"
    mapeo.asignar("abajo", "x")   # x estaba en 'arriba': se libera
    assert mapeo.tecla_de("abajo") == "x", "abajo ahora toma x"
    assert mapeo.tecla_de("arriba") is None, "arriba queda sin tecla"
    assert mapeo.buscar_accion("x") == "abajo"
    assert mapeo.tecla_ocupada("x") == "abajo"
    print("OK: una tecla = una acción (la última manda)\n")

    # 4. Limpiar y restaurar
    print("=== Limpiar / restaurar ===")
    mapeo.limpiar("abajo")
    assert mapeo.tecla_de("abajo") is None
    mapeo.restaurar_por_defecto()
    assert mapeo.tecla_de("abajo") == "Down"
    print("OK: limpiar libera; restaurar vuelve a fábrica\n")

    # 5. Nombres legibles de teclas para la GUI
    print("=== nombre_tecla ===")
    assert nombre_tecla("Up") == "\u2191"
    assert nombre_tecla("space") == "ESPACIO"
    assert nombre_tecla("q") == "Q"
    assert nombre_tecla("F5") == "F5"
    print(f"OK: {nombre_tecla('Up')} / {nombre_tecla('space')} / {nombre_tecla('q')}\n")

    # 6. Acciones válidas: 13 en total
    assert len(ACCIONES) == 13
    ejes = [a for a in ACCIONES if a.tipo == EJE]
    assert len(ejes) == 6 and all(a.paso > 0 for a in ejes)
    print("OK: catálogo con 13 acciones, 6 de eje con paso\n")

    print("Pruebas OK")
# wall-e-robot/app/widgets/logica/mapeo_teclado.py
# Kevin Gámez - 06/10/2026


import json
from dataclasses import dataclass
from pathlib import Path


DISCRETO = "discreto"
EJE = "eje"

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
    Accion("arriba"          , "Avanzar"           , DISCRETO),
    Accion("abajo"           , "Retroceder"        , DISCRETO),
    Accion("izquierda"       , "Girar izquierda"   , DISCRETO),
    Accion("derecha"         , "Girar derecha"     , DISCRETO),
    Accion("reposo"          , "Reposo"            , DISCRETO),
    Accion("cuello_mas"      , "Cuello arriba"     , EJE, PASO_CUELLO),
    Accion("cuello_menos"    , "Cuello abajo"      , EJE, PASO_CUELLO),
    Accion("hombro_izq_mas"  , "Hombro izq. arriba", EJE, PASO_HOMBRO),
    Accion("hombro_izq_menos", "Hombro izq. abajo" , EJE, PASO_HOMBRO),
    Accion("hombro_der_mas"  , "Hombro der. arriba", EJE, PASO_HOMBRO),
    Accion("hombro_der_menos", "Hombro der. abajo" , EJE, PASO_HOMBRO),
)

# Teclas modificadoras: se ignoran al leer el teclado; nunca disparan acciones.
MODIFICADORAS = {
    "Shift_L", "Shift_R", "Control_L", "Control_R",
    "Alt_L", "Alt_R", "Caps_Lock",
}

RUTA_CONTROLES = Path(__file__).resolve().parents[3] / "configuracion" / "controles.json"


def _teclas_por_defecto() -> dict:
    return {
        "arriba"          : "Up",
        "abajo"           : "Down",
        "izquierda"       : "Left",
        "derecha"         : "Right",
        "reposo"          : "r",
        "cuello_mas"      : "q",
        "cuello_menos"    : "a",
        "hombro_izq_mas"  : "w",
        "hombro_izq_menos": "s",
        "hombro_der_mas"  : "e",
        "hombro_der_menos": "d",
    }


def accion_por_id(accion_id: str) -> Accion:
    for accion in ACCIONES:
        if accion.id == accion_id:
            return accion
    raise KeyError(accion_id)


def nombre_tecla(keysym: str) -> str:
    """Devuelve el nombre legible de la tecla para mostrar en la GUI."""
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
    """Asociación editable entre acciones y teclas, persistible en el JSON de controles."""
    VERSION = 1

    def __init__(self, mapa: dict[str, str] | None = None):
        self._mapa: dict[str, str] = dict(mapa) if mapa is not None else _teclas_por_defecto()

    @classmethod
    def cargar(cls, ruta: Path | None = None) -> "MapeoTeclado":
        """Carga el mapa desde el JSON; si falta o es inválido usa los valores por defecto y completa las acciones faltantes."""
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
        ruta = ruta or RUTA_CONTROLES
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps({
            "version": self.VERSION,
            "teclado": dict(sorted(self._mapa.items())),
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        return ruta

    # Consultas
    def tecla_de(self, accion_id: str) -> str | None:
        return self._mapa.get(accion_id)

    def tecla_de_o_por_defecto(self, accion_id: str) -> str:
        tecla = self._mapa.get(accion_id)
        if tecla is not None:
            return tecla
        return _teclas_por_defecto()[accion_id]

    def buscar_accion(self, keysym: str) -> str | None:
        for accion_id, tecla in self._mapa.items():
            if tecla == keysym:
                return accion_id
        return None

    def tecla_ocupada(self, keysym: str, excepto: str | None = None) -> str | None:
        for accion_id, tecla in self._mapa.items():
            if tecla == keysym and accion_id != excepto:
                return accion_id
        return None

    def asignar(self, accion_id: str, keysym: str):
        """Asigna la tecla a la acción; si ya estaba en uso, libera la acción que la ocupaba."""
        accion_por_id(accion_id)
        ocupada = self.tecla_ocupada(keysym, excepto=accion_id)
        if ocupada is not None:
            self._mapa.pop(ocupada, None)
        self._mapa[accion_id] = keysym

    def limpiar(self, accion_id: str):
        """Deja sin tecla la acción indicada (error si la acción no existe)."""
        accion_por_id(accion_id)
        self._mapa.pop(accion_id, None)

    def restaurar_por_defecto(self):
        self._mapa = _teclas_por_defecto()

    def _completar_faltantes(self):
        faltan = {a.id for a in ACCIONES} - set(self._mapa)
        for accion_id in faltan:
            self._mapa[accion_id] = _teclas_por_defecto()[accion_id]
        validas = {a.id for a in ACCIONES}
        self._mapa = {k: v for k, v in self._mapa.items() if k in validas}

# Cajón de Pruebas
# Ejecutar desde la raíz del proyecto:
#   python -m app.widgets.logica.mapeo_teclado

if __name__ == "__main__":
    import sys
    try:
        reconfigure = getattr(sys.stdout, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("Prueba mapeo_teclado.py\n")

    # Perfil por defecto cubre todas las acciones y sin teclas duplicadas
    print("Perfil por defecto")
    mapeo = MapeoTeclado()
    assert {a.id for a in ACCIONES} <= set(mapeo._mapa), "Faltan acciones"
    teclas = list(mapeo._mapa.values())
    assert len(teclas) == len(set(teclas)), "Una tecla no puede repetirse"
    assert mapeo.tecla_de("arriba") == "Up", "ARRIBA debería ser la flecha ↑"
    print(f"OK: {len(mapeo._mapa)} acciones, teclas únicas\n")

    # Cargar sin archivo -> por defecto; con archivo -> round-trip
    print("Persistencia (JSON)")
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

    # Asignar: reemplaza la tecla anterior y libera la acción ocupada
    print("Asignaciones y conflictos")
    mapeo = MapeoTeclado()
    mapeo.asignar("arriba", "x")  # x no estaba ocupada
    assert mapeo.tecla_de("arriba") == "x"
    mapeo.asignar("abajo", "x")   # x estaba en 'arriba': se libera
    assert mapeo.tecla_de("abajo") == "x", "abajo ahora toma x"
    assert mapeo.tecla_de("arriba") is None, "arriba queda sin tecla"
    assert mapeo.buscar_accion("x") == "abajo"
    assert mapeo.tecla_ocupada("x") == "abajo"
    print("OK: una tecla = una acción (la última manda)\n")

    # Limpiar y restaurar
    print("Limpiar / restaurar")
    mapeo.limpiar("abajo")
    assert mapeo.tecla_de("abajo") is None
    mapeo.restaurar_por_defecto()
    assert mapeo.tecla_de("abajo") == "Down"
    print("OK: limpiar libera; restaurar vuelve a fábrica\n")

    # Nombres legibles de teclas para la GUI
    print("nombre_tecla")
    assert nombre_tecla("Up") == "\u2191"
    assert nombre_tecla("space") == "ESPACIO"
    assert nombre_tecla("q") == "Q"
    assert nombre_tecla("F5") == "F5"
    print(f"OK: {nombre_tecla('Up')} / {nombre_tecla('space')} / {nombre_tecla('q')}\n")

    # Acciones válidas: 11 en total
    assert len(ACCIONES) == 11
    ejes = [a for a in ACCIONES if a.tipo == EJE]
    assert len(ejes) == 6 and all(a.paso > 0 for a in ejes)
    print("OK: catálogo con 11 acciones, 6 de eje con paso\n")

    print("Pruebas OK")
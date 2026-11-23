import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from ..rutas import directorio_configuracion


OPCIONES_SERVOS = {
    "hombro_izquierdo": ("invertirServoBrazoIzquierdo", "Invertir brazo izquierdo"),
    "hombro_derecho": ("invertirServoBrazoDerecho", "Invertir brazo derecho"),
    "cuello": ("invertirServoCuello", "Invertir cuello"),
}
OPCIONES_MOTORES = (
    ("invertirMotoresAdelanteAtras", "Invertir adelante / atrás"),
    ("invertirMotoresIzquierdaDerecha", "Invertir izquierda / derecha"),
)
DIRECCIONES = {
    "arriba": (0, "abajo"), "abajo": (0, "arriba"),
    "izquierda": (1, "derecha"), "derecha": (1, "izquierda"),
}
CLAVES = tuple(clave for clave, _ in (*OPCIONES_SERVOS.values(), *OPCIONES_MOTORES))


class ConfiguracionControl:
    def __init__(self, ruta: Path | None = None):
        self.ruta = ruta if ruta is not None else directorio_configuracion() / "control_robot.json"
        try:
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            datos = {}
        if not isinstance(datos, dict):
            datos = {}
        self.valores = {clave: datos.get(clave) is True for clave in CLAVES}

    def aplicar(self, valores: dict[str, bool]):
        nuevos = {clave: valores.get(clave) is True for clave in CLAVES}
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = None
        try:
            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.ruta.parent,
                                    delete=False) as archivo:
                temporal = Path(archivo.name)
                json.dump(nuevos, archivo, indent=2)
            temporal.replace(self.ruta)
        finally:
            if temporal is not None:
                temporal.unlink(missing_ok=True)
        self.valores = nuevos

    def ajustar_comando(self, comando: dict) -> dict:
        tipo = comando.get("tipo")
        if tipo == "servo":
            servo = comando.get("servo")
            opcion = OPCIONES_SERVOS.get(servo) if isinstance(servo, str) else None
            if opcion and self.valores[opcion[0]]:
                return {**comando, "angulo": -comando["angulo"]}
        elif tipo == "motor":
            nombre_direccion = comando.get("direccion")
            direccion = DIRECCIONES.get(nombre_direccion) if isinstance(nombre_direccion, str) else None
            if direccion and self.valores[OPCIONES_MOTORES[direccion[0]][0]]:
                return {**comando, "direccion": direccion[1]}
        elif tipo == "multi":
            return {**comando, "comandos": [
                self.ajustar_comando(subcomando) for subcomando in comando["comandos"]
            ]}
        return comando

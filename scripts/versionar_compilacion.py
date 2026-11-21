import os
import re
from pathlib import Path


CONFIG = Path(__file__).resolve().parents[1] / "firmware" / "include" / "config.h"
VERSION = re.compile(
    rb'(PROYECTO_VERSION\s*=\s*")'
    rb'([0-9]+\.[0-9]+\.[0-9]+)(?:\.[0-9]+\.g[0-9a-f]{12})?(")'
)


def versionar(config: Path, ejecucion: str, commit: str) -> str:
    if not re.fullmatch(r"[1-9][0-9]*", ejecucion):
        raise ValueError("El número de ejecución debe ser un entero positivo.")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Se requiere el SHA completo del commit de la compilación.")

    contenido = config.read_bytes()
    coincidencias = list(VERSION.finditer(contenido))
    if len(coincidencias) != 1:
        raise ValueError("config.h debe contener una única versión base Mayor.Menor.Parche.")

    coincidencia = coincidencias[0]
    version = f"{coincidencia[2].decode('ascii')}.{ejecucion}.g{commit[:12]}"
    inicio, fin = coincidencia.span()
    config.write_bytes(
        contenido[:inicio] + coincidencia[1] + version.encode("ascii")
        + coincidencia[3] + contenido[fin:]
    )
    return version


def main() -> None:
    version = versionar(CONFIG, os.environ["GITHUB_RUN_NUMBER"], os.environ["GITHUB_SHA"])
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as salida:
        print(f"version={version}", file=salida)
    print(f"Versión de la compilación: {version}")


if __name__ == "__main__":
    main()

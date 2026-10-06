# wall-e-robot/pruebas/ejecutar_cajones.py
# Kevin Gámez - 13/09/2026
#
# Ejecuta TODOS los cajones de pruebas que NO abren ventanas (todo excepto
# la GUI completa de app/main.py). Cada uno se corre en un proceso aparte,
# igual que si se ejecutara a mano, y se reporta OK/FALLA.
#
# Uso (desde la raíz del proyecto, donde está la carpeta 'app'):
#   python pruebas/ejecutar_cajones.py

import subprocess
import sys
from pathlib import Path


# Cajones sin GUI, en orden de "base -> piezas -> sistema".
CAJONES = [
    "app.nucleo.paleta",
    "app.nucleo.estado",
    "app.widgets.logica.boton",
    "app.widgets.logica.deslizador",
    "app.widgets.logica.gamepad",
    "app.widgets.logica.ojos",
    "app.widgets.logica.icono_sistema",
    "app.widgets.logica.sol_bateria",
    "app.widgets.logica.barras_consumo",
    "app.widgets.logica.radar",
    "app.widgets.logica.logger_widget",
    "app.comunicacion.conexion",
    "app.widgets.logica.mapeo_teclado",
    "app.widgets.logica.control_teclado",
]


def main() -> int:
    """Corre cada cajón en un subproceso y resume los resultados."""
    raiz = Path(__file__).resolve().parent.parent

    fallidos = []
    for modulo in CAJONES:
        resultado = subprocess.run(
            [sys.executable, "-m", modulo],
            cwd=str(raiz),
            capture_output=True,
            text=True,
        )

        if resultado.returncode == 0:
            print(f"[OK   ] {modulo}")
        else:
            print(f"[FALLA] {modulo}")
            fallidos.append(modulo)
            print(resultado.stdout)
            print(resultado.stderr)

    print()
    if fallidos:
        print(f"FALLARON {len(fallidos)} de {len(CAJONES)}:")
        for modulo in fallidos:
            print(f"  - {modulo}")
        return 1

    print(f"Todos los cajones pasaron ({len(CAJONES)} en verde).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
# wall-e-robot/empaquetado/lanzador.py
# Kevin Gámez - 17/10/2026
#
# Punto de entrada que usa PyInstaller para construir el ejecutable. Mantiene
# el arranque real en app.main (una sola fuente de verdad) y solo añade la raíz
# del proyecto a sys.path para poder importar el paquete 'app' al correr como
# script (congelado, 'app' ya viaja dentro del bundle).


import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.main import main


if __name__ == "__main__":
    main()

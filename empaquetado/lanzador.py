# PyInstaller usa este lanzador. Al ejecutarlo como script, sys.path debe incluir la raíz del repo.


import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.main import main


if __name__ == "__main__":
    main()

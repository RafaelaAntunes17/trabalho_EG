import sys
from pathlib import Path

# permite correr pytest a partir da raiz sem instalar o pacote
sys.path.insert(0, str(Path(__file__).parent.parent))

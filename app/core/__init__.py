import sys
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Core configuration package
from app.core.config import settings
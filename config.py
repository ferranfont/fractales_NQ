"""
Configuración global para detección de fractales en Gold (GC)
"""
from pathlib import Path

# Día a procesar/visualizar (cambiar según necesidad)
DIA = "2015-01-02"


# Directorios del proyecto
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FRACTALS_DIR = OUTPUTS_DIR / "fractals"

# Parámetros de detección de fractales ZigZag
MIN_CHANGE_PCT_MINOR = 0.09  # 0.02% umbral para fractales pequeños
MIN_CHANGE_PCT_MAJOR = 0.15  # 0.10% umbral para fractales grandes

# Parámetros de agregación (no usado actualmente, datos ya vienen en OHLC)
AGGREGATION_WINDOW = 60  # 60 segundos (velas de 1 minuto)


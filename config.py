"""
Configuración global para detección de fractales en Gold (GC)
"""
from pathlib import Path

# ============================================================================
# RANGO DE FECHAS
# ============================================================================
START_DATE = "2025-01-02"
END_DATE = "2025-04-25"

# ============================================================================
# DIRECTORIOS DEL PROYECTO
# ============================================================================
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FRACTALS_DIR = OUTPUTS_DIR / "fractals"

# ============================================================================
# PARÁMETROS DE FRACTALES ZIGZAG (PRECIO)
# ============================================================================
MIN_CHANGE_PCT_MINOR = 0.50    # 0.50% umbral para fractales pequeños
MIN_CHANGE_PCT_MAJOR = 2.1     # 2.1% umbral para fractales grandes

# ============================================================================
# PARÁMETROS DE VISUALIZACIÓN
# ============================================================================
PLOT_MINOR_FRACTALS = False    # True = dibujar fractales MINOR en el gráfico
PLOT_MAJOR_FRACTALS = False     # True = dibujar fractales MAJOR en el gráfico

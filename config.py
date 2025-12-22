"""
Configuración global para detección de fractales en Gold (GC)
"""
from pathlib import Path

# ============================================================================
# RANGO DE FECHAS
# ============================================================================
START_DATE = "2024-03-29"
END_DATE = "2024-05-02"

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
# PARÁMETROS DE ANÁLISIS DE CONSOLIDACIÓN
# ============================================================================
CONSOLIDATION_PRICE_RANGE_PERIOD = 7     # Número de fractales para cálculo de rango y ATR
CONSOLIDATION_ATR_THRESHOLD = 1.20       # Multiplicador del ATR para umbral de consolidación

# ============================================================================
# PARÁMETROS DE VISUALIZACIÓN
# ============================================================================
PLOT_MINOR_FRACTALS = True       # True = dibujar fractales MINOR en el gráfico
PLOT_MAJOR_FRACTALS = False      # True = dibujar fractales MAJOR en el gráfico
PLOT_MINOR_DOTS = True          # True = dibujar puntos en fractales MINOR
PLOT_MAJOR_DOTS = False          # True = dibujar puntos (circles) en fractales MAJOR

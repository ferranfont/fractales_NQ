"""
Configuración global para detección de fractales en NQ (Nasdaq Futures)
"""
from pathlib import Path

# ============================================================================
# FECHA ÚNICA (NO HAY RANGO, SOLO UNA FECHA)
# ============================================================================
DATE = "20251103" # Fecha en formato YYYYMMDD

# Compatibilidad con código existente
START_DATE = DATE
END_DATE = DATE

# ============================================================================
# DIRECTORIOS DEL PROYECTO
# ============================================================================
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FRACTALS_DIR = OUTPUTS_DIR / "fractals"

# ============================================================================
# PARÁMETROS DE FRACTALES ZIGZAG (PRECIO) - AJUSTADOS PARA NQ
# ============================================================================
# NQ tiene precio ~26000, por lo que los porcentajes pueden ser diferentes a GC
MIN_CHANGE_PCT_MINOR = 0.10   #0.15% umbral para fractales pequeños (~39 puntos en NQ)
MIN_CHANGE_PCT_MAJOR = 0.20   # 0.50% umbral para fractales grandes (~130 puntos en NQ)

# ============================================================================
# PARÁMETROS DE ANÁLISIS DE CONSOLIDACIÓN
# ============================================================================
CONSOLIDATION_PRICE_RANGE_PERIOD = 7     # Número de fractales para cálculo de rango y ATR
CONSOLIDATION_ATR_THRESHOLD = 1.20       # Multiplicador del ATR para umbral de consolidación
TRIGGER_THRESHOLD = 5000                 # Umbral de frecuencia invertida para trigger de consolidación
TRIGGER_PERIODS = 2                      # Número de fractales consecutivos por encima del umbral

# ============================================================================
# PARÁMETROS DE INDICADORES TÉCNICOS
# ============================================================================
PLOT_VWAP = True                 # True = dibujar indicador VWAP en el gráfico
VWAP_FAST = 50                   # Periodo para VWAP rápido (magenta)
VWAP_SLOW = 200                  # Periodo para VWAP lento (verde)

# ============================================================================
# PARÁMETROS DE VISUALIZACIÓN
# ============================================================================
PLOT_MINOR_FRACTALS = True       # True = dibujar fractales MINOR en el gráfico
PLOT_MAJOR_FRACTALS = True      # True = dibujar fractales MAJOR en el gráfico
PLOT_MINOR_DOTS = True          # True = dibujar puntos en fractales MINOR
PLOT_MAJOR_DOTS = False          # True = dibujar puntos (circles) en fractales MAJOR
HIDE_FREQUENCY_INDICATOR = True  # True = ocultar subplot de frecuencia (mantiene puntos naranjas)
SHOW_REGRESSION_CHANNEL = False  # True = mostrar canal de regresión en el gráfico


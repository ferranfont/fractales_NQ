"""
Configuración global para detección de fractales en NQ (Nasdaq Futures)
"""
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN DE FECHAS
# ============================================================================
# Opción 1: Fecha única (descomentar para usar una sola fecha)
DATE = "20251103"  # Fecha en formato YYYYMMDD
START_DATE = DATE
END_DATE = DATE

# ============================================================================
# TRADING PARAMETERS
# ============================================================================
TP_POINTS = 5.0                  # Take profit in points, usar 4 para scalping and 20 for swing
SL_POINTS = 9.0                  # Stop loss in points, usar 9 para scalping
MAXIMUM_POSITIONS_OPEN = 1       # Maximum number of positions open simultaneously

START_TRADING_HOUR = "09:00:00"  # Hora de inicio de análisis (HH:MM:SS)
END_TRADING_HOUR = "22:00:00"    # Hora de fin de análisis (HH:MM:SS)

# ============================================================================
# DIRECTORIOS DEL PROYECTO
# ============================================================================
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FRACTALS_DIR = OUTPUTS_DIR / "fractals"
CHARTS_DIR = OUTPUTS_DIR / "charts"

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
SHOW_FAST_VWAP = True            # True = mostrar VWAP Fast (magenta)
SHOW_SLOW_VWAP = False           # True = mostrar VWAP Slow (verde)
VWAP_FAST = 50                   # Periodo para VWAP rápido (magenta)
VWAP_SLOW = 100                  # Periodo para VWAP lento (verde)

PRICE_EJECTION_TRIGGER = 0.001   # Porcentaje mínimo de distancia entre precio y VWAP fast para trigger (0.001 = 0.1%)
OVER_PRICE_EJECTION_TRIGGER = 0.003  # Porcentaje para trigger de sobre-alejamiento (puntos rojos) (0.005 = 0.5%)

# ============================================================================
# PARÁMETROS DE VISUALIZACIÓN
# ============================================================================
PLOT_MINOR_FRACTALS = True       # True = dibujar fractales MINOR en el gráfico
PLOT_MAJOR_FRACTALS = True      # True = dibujar fractales MAJOR en el gráfico
PLOT_MINOR_DOTS = True          # True = dibujar puntos en fractales MINOR
PLOT_MAJOR_DOTS = False          # True = dibujar puntos (circles) en fractales MAJOR

HIDE_FREQUENCY_INDICATOR = True   # True = ocultar subplot de frecuencia (mantiene puntos naranjas)
SHOW_REGRESSION_CHANNEL = False   # True = mostrar canal de regresión en el gráfico


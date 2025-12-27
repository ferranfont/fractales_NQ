"""
Configuración global para detección de fractales en NQ (Nasdaq Futures)
"""
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN DE FECHAS (single day analysis)
# ============================================================================
# Opción 1: Fecha única (descomentar para usar una sola fecha)
DATE = "20251009"  # Fecha en formato YYYYMMDD
START_DATE = DATE
END_DATE = DATE

# ============================================================================
# CONFIGURACIÓN DE ITERACIÓN (iterate_all_days.py)
# ============================================================================
USE_ALL_DAYS_AVAILABLE = True               # True = procesar todos los días en data/, False = usar rango específico
ALL_DAYS_SEGMENT_START = "20241001"         # Fecha inicial del segmento (solo si USE_ALL_DAYS_AVAILABLE=False)
ALL_DAYS_SEGMENT_END = "20251031"           # Fecha final del segmento (solo si USE_ALL_DAYS_AVAILABLE=False)

# ============================================================================
# TRADING PARAMETERS GENERAL
# ============================================================================
POINT_VALUE = 20.0                          # Valor de cada punto en USD (NQ = $20)

# ============================================================================
# TRADING PARAMETERS VWAP MOMENTUM STRATEGY (Price Ejection - Green Dots)
# ============================================================================
ENABLE_VWAP_MOMENTUM_STRATEGY = True        # True = ejecutar estrategia, False = NO ejecutar
VWAP_MOMENTUM_TP_POINTS = 125.0             # Take profit in points
VWAP_MOMENTUM_SL_POINTS = 75.0              # Stop loss in points
VWAP_MOMENTUM_MAX_POSITIONS = 1             # Maximum number of positions open simultaneously
VWAP_MOMENTUM_STRAT_START_HOUR = "00:00:00" # Hora de inicio de trading
VWAP_MOMENTUM_STRAT_END_HOUR = "22:59:59"   # Hora de fin de trading
USE_VWAP_SLOPE_INDICATOR_STOP_LOSS = True   # True = cerrar posición cuando VWAP slope cruza por debajo del threshold bajo, False = usar solo SL en puntos

# ============================================================================
# TRADING PARAMETERS VWAP CROSSOVER STRATEGY
# ============================================================================
ENABLE_VWAP_CROSSOVER_STRATEGY = False      # True = ejecutar estrategia, False = NO ejecutar
VWAP_CROSSOVER_TP_POINTS = 5.0              # Take profit in points
VWAP_CROSSOVER_SL_POINTS = 9.0              # Stop loss in points
VWAP_CROSSOVER_MAX_POSITIONS = 1            # Maximum number of positions open simultaneously
VWAP_CROSSOVER_START_HOUR = "16:30:00"      # Hora de inicio de trading
VWAP_CROSSOVER_END_HOUR = "22:00:00"        # Hora de fin de trading

# ============================================================================
# DIRECTORIOS DEL PROYECTO
# ============================================================================
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FRACTALS_DIR = OUTPUTS_DIR / "fractals"
CHARTS_DIR = OUTPUTS_DIR / "charts"
MODELS_DIR = OUTPUTS_DIR / "modelos_json"

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

PRICE_EJECTION_TRIGGER = 0.001          # Porcentaje mínimo de distancia entre precio y VWAP fast para trigger (0.001 = 0.1%)
OVER_PRICE_EJECTION_TRIGGER = 0.003     # Porcentaje para trigger de sobre-alejamiento (puntos rojos) (0.005 = 0.5%)

VWAP_SLOPE_DEGREE_WINDOW = 10                 # Window (in bars) to calculate VWAP slope at entry/exit
SHOW_SUBPLOT_VWAP_SLOPE_INDICATOR = True      # True = mostrar subplot de VWAP Slope, False = ocultar subplot
VWAP_SLOPE_INDICATOR_HIGH_VALUE = 0.6         # Threshold alto para VWAP Slope indicator
VWAP_SLOPE_INDICATOR_LOW_VALUE = 0.01         # Threshold bajo para VWAP Slope indicator

# ============================================================================
# PARÁMETROS DE VISUALIZACIÓN
# ============================================================================
PLOT_MINOR_FRACTALS = False       # True = dibujar fractales MINOR en el gráfico
PLOT_MAJOR_FRACTALS = False      # True = dibujar fractales MAJOR en el gráfico
PLOT_MINOR_DOTS = False          # True = dibujar puntos en fractales MINOR
PLOT_MAJOR_DOTS = False          # True = dibujar puntos (circles) en fractales MAJOR

SHOW_FREQUENCY_INDICATOR = False   # True = mostrar subplot de frecuencia, False = ocultar subplot
SHOW_REGRESSION_CHANNEL = False   # True = mostrar canal de regresión en el gráfico

# ============================================================================
# ITERATION PARAMETERS
# ============================================================================
SHOW_CHART_DURING_ITERATION = True           # True = generate and open chart for each day during iteration



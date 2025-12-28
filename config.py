"""
Configuración global para detección de fractales en NQ (Nasdaq Futures)
"""
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN DE FECHAS (single day analysis)
# ============================================================================
# Opción 1: Fecha única (descomentar para usar una sola fecha)
DATE = "20251104"  # Fecha en formato YYYYMMDD
START_DATE = DATE
END_DATE = DATE

# ============================================================================
# CONFIGURACIÓN DE ITERACIÓN (iterate_all_days.py)
# ============================================================================
USE_ALL_DAYS_AVAILABLE = True               # True = procesar todos los días en data/, False = usar rango específico
ALL_DAYS_SEGMENT_START = "20241001"         # Fecha inicial del segmento (solo si USE_ALL_DAYS_AVAILABLE=False)
ALL_DAYS_SEGMENT_END = "20251031"           # Fecha final del segmento (solo si USE_ALL_DAYS_AVAILABLE=False)

# ============================================================================
# MAIN TRADING PARAMETERS VWAP MOMENTUM STRATEGY (Price Ejection - Green Dots)
# ============================================================================
ENABLE_VWAP_MOMENTUM_STRATEGY = True        # True = ejecutar estrategia, False = NO ejecutar
VWAP_MOMENTUM_TP_POINTS = 125.0             # Take profit in points
VWAP_MOMENTUM_SL_POINTS = 40.0            # Stop loss in points
VWAP_MOMENTUM_MAX_POSITIONS = 1             # Maximum number of positions open simultaneously

# ============================================================================
# CONFIGURACIÓN DE HORARIO DE TRADING 
# ============================================================================
# Filtro global general de horario de trading
VWAP_MOMENTUM_STRAT_START_HOUR = "00:00:00" # Hora de inicio de trading
VWAP_MOMENTUM_STRAT_END_HOUR = "22:59:59"   # Hora de fin de trading
# Filtro específico según hora del dia
# These filters work together (both must pass):
# 1. Generic time range filter: START_HOUR to END_HOUR (always active)
# 2. Specific hours filter: ALLOWED_HOURS (only if USE_SELECTED_ALLOWED_HOURS = True)
USE_SELECTED_ALLOWED_HOURS = False          # True = only trade in specific hours from list below, False = trade in any hour within START/END range
VWAP_MOMENTUM_ALLOWED_HOURS = [0, 1, 3, 4, 6, 10, 12, 13, 16, 17, 18]  # Best hours from backtesting (Expected: Sortino 0.11 -> 0.95) - Only used if USE_SELECTED_ALLOWED_HOURS = True

# ============================================================================
# FILTROS DE ENTRADA A FAVOR TENDENCIA VWAP MOMENTUM STRATEGY
# ============================================================================
# Trade only with the trend defined by VWAP FAST vs VWAP SLOW
USE_VWAP_SLOW_TREND_FILTER = False          # True = only trade with trend, False = ignore trend
# When enabled:
#   - LONG (BUY): only if VWAP_FAST > VWAP_SLOW (uptrend)
#   - SHORT (SELL): only if VWAP_FAST < VWAP_SLOW (downtrend)

# Global direction filter, ilter which trade directions are allowed (BUY and/or SELL)
VWAP_MOMENTUM_LONG_ALLOWED = True         # True = allow BUY trades, False = disable BUY
VWAP_MOMENTUM_SHORT_ALLOWED = True          # True = allow SELL trades, False = disable SELL

# ============================================================================
# FILTROS DE SALIDA VWAP MOMENTUM STRATEGY
# ============================================================================
# Salida basada en el indicador VWAP Slope, se para salir si la pendiente del indicador pierde fuerza
USE_VWAP_SLOPE_INDICATOR_STOP_LOSS = False   # True = cerrar posición cuando VWAP slope cruza por debajo del threshold bajo, False = usar solo SL en puntos

# ============================================================================
# FILTRO DE SALIDA POR TIEMPO VWAP MOMENTUM STRATEGY
# ===========================================================================
# mantenimiento de operación abierta mientras sigan apareciendo puntos verdes
USE_KEEP_PUSHING_GREEN_DOTS = True               # True = mantener operacion abierta mientras sigan apareciendo puntos verdes, False = no usar este filtro
TIME_OUT_AFTER_LAST_GREEN_DOT_MINUTES = 30       # Minutos para cerrar la operación después del último punto verde (si no hay nuevos puntos verdes)
KEEP_POSITION_OPEN_IF_MARKET_PRICE_OVER_LAST_DOT = True # True = keep position open if market price is over last green dot, False = no special handling

# IMPORTANT: When USE_TIME_IN_MARKET = True:
#   - TP (Take Profit) is DISABLED (unless USE_TP_ALLOWED_IN_TIME_IN_MARKET = True)
#   - SL (Stop Loss) is DISABLED (unless USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET = True)
#   - USE_VWAP_SLOPE_INDICATOR_STOP_LOSS is DISABLED
#   - Exit is by: TIME (JSON/fixed) OR TP (if enabled) OR SL (if enabled) - whatever happens FIRST
USE_TIME_IN_MARKET = False
# Time-in-Market JSON Optimization File
# When True, uses optimal duration per entry hour from JSON config generated by optimize_time_in_market.py
# When False, uses fixed TIME_IN_MARKET_MINUTES value above
USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE = False       # True = load duration from JSON by entry hour, False = use fixed TIME_IN_MARKET_MINUTES
TIME_IN_MARKET_MINUTES = 180                            # Exit time in minutes (180 = 3 hours, 9999 = EOD)

# Protective Stop Loss (optional but RECOMMENDED) - Se usa para limitar la pérdida y no esperar que finlice el tiempo
USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET = False           # True = apply protective stop loss, False = no stop loss during time-based exit
MAX_SL_ALLOWED_IN_TIME_IN_MARKET = 50                  # Maximum stop loss allowed in points (optimized for 2:1 TP/SL ratio)

# Take Profit in Time-in-Market mode (optional) - Se usa para cerrar la operación si se alcanza el TP antes de que finalice el tiempo
USE_TP_ALLOWED_IN_TIME_IN_MARKET = False             # True = close trade if TP is hit before time expires, False = ignore TP
TP_IN_TIME_IN_MARKET = 100                           # Take profit in points (2:1 ratio with SL = 100/50)

# ============================================================================
# TRAILING STOP LOSS PARAMETERS VWAP MOMENTUM STRATEGY
# ===========================================================================
# Trailing Stop Loss Parameters (Break-Even)
# When enabled, moves stop loss to break-even (or break-even + profit) after reaching trigger level
USE_TRAIL_CASH = False                              # True = enable trailing stop to break-even, False = disabled
TRAIL_CASH_TRIGGER_POINTS = 100                     # Trigger level in points - when profit reaches this, move SL to break-even
TRAIL_CASH_BREAK_EVEN_POINTS_PROFIT = 0             # Points of profit to lock in when trailing (0 = break-even, 10 = entry + 10 points)

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
# TRADING PARAMETERS GENERAL
# ============================================================================
POINT_VALUE = 20.0                          # Valor de cada punto en USD (NQ = $20)

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
SHOW_SLOW_VWAP = True       # True = mostrar VWAP Slow (verde)
VWAP_FAST = 50                   # Periodo para VWAP rápido (magenta)
VWAP_SLOW = 200               # Periodo para VWAP lento (verde)

PRICE_EJECTION_TRIGGER = 0.001          # Porcentaje mínimo de distancia entre precio y VWAP fast para trigger (0.001 = 0.1%)
OVER_PRICE_EJECTION_TRIGGER = 0.003     # Porcentaje para trigger de sobre-alejamiento (puntos rojos) (0.005 = 0.5%)

VWAP_SLOPE_DEGREE_WINDOW = 10                 # Window (in bars) to calculate VWAP slope at entry/exit

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

SHOW_SUBPLOT_VWAP_SLOPE_INDICATOR = True      # True = mostrar subplot de VWAP Slope, False = ocultar subplot
SHOW_VWAP_INDICATOR_CROSSOVER= True        # True = mostrar señales de cruce VWAP en el gráfico

# ============================================================================
# ITERATION PARAMETERS
# ============================================================================
SHOW_CHART_DURING_ITERATION = True           # True = generate and open chart for each day during iteration



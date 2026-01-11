"""
Configuración global para detección de fractales en NQ (Nasdaq Futures)
"""
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN DE FECHAS (single day analysis)
# ============================================================================
# Opción 1: Fecha única (descomentar para usar una sola fecha)
DATE = "20251211"  # Fecha en formato YYYYMMDD
START_DATE = DATE
END_DATE = DATE

# ============================================================================
# CONFIGURACIÓN DE ITERACIÓN (iterate_all_days.py)
# ============================================================================
USE_ALL_DAYS_AVAILABLE = False              # True = procesar todos los días en data/, False = usar rango específico
ALL_DAYS_SEGMENT_START = "20251001"         # Fecha inicial del segmento (solo si USE_ALL_DAYS_AVAILABLE=False)
ALL_DAYS_SEGMENT_END = "20251219"           # Fecha final del segmento (solo si USE_ALL_DAYS_AVAILABLE=False)

# ============================================================================
# MAIN TRADING PARAMETERS VWAP MOMENTUM STRATEGY (Price Ejection - Green Dots)
# ============================================================================
ENABLE_VWAP_MOMENTUM_STRATEGY = False        # True = ejecutar estrategia, False = NO ejecutar
VWAP_MOMENTUM_TP_POINTS = 125.0             # Take profit in points
VWAP_MOMENTUM_SL_POINTS = 75.0            # Stop loss in points
VWAP_MOMENTUM_MAX_POSITIONS = 1             # Maximum number of positions open simultaneously

# ============================================================================
# CONFIGURACIÓN DE HORARIO DE TRADING 
# ============================================================================
# Filtro global general de horario de trading
VWAP_MOMENTUM_STRAT_START_HOUR = "00:00:00" # Hora de inicio de trading
VWAP_MOMENTUM_STRAT_END_HOUR = "22:00:00"   # Hora de fin de trading
# Filtro específico según hora del dia
# These filters work together (both must pass):
# 1. Generic time range filter: START_HOUR to END_HOUR (always active)
# 2. Specific hours filter: ALLOWED_HOURS (only if USE_SELECTED_ALLOWED_HOURS = True)
USE_SELECTED_ALLOWED_HOURS = False          # True = only trade in specific hours from list below, False = trade in any hour within START/END range
VWAP_MOMENTUM_ALLOWED_HOURS = [15, 16]  # Optimized: Removed toxic hours (1, 2, 3, 9, 11, 14, 20)

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
# VWAP MOMENTUM STRATEGY GRID
# ===========================================================================
# Entry Grid Strategy (Multiple entries at different price levels)
USE_ENTRY_GRID = False                     # True = enable grid entry system, False = single entry only
GRID_STEP = 60                             # Distance between grid levels in points
NUMBER_OF_GRID_STEPS = 1                    # Number of additional limit orders to place
# Grid Logic:
#   - BUY: Places limit orders at entry_price - (GRID_STEP × 1), entry_price - (GRID_STEP × 2)
#   - SELL: Places limit orders at entry_price + (GRID_STEP × 1), entry_price + (GRID_STEP × 2)
#   - Grid orders do NOT count toward VWAP_MOMENTUM_MAX_POSITIONS
#   - All grid entries share the SAME stop loss level as main position (not calculated from grid fill price)
#   - Each grid entry has its own TP calculated from its fill price
# Example (BUY): Main entry 25000 → SL 24925 (25000-75)
#                Grid 1 fills at 24970 → SL 24925 (SAME as main), TP 25095 (24970+125)
#                Grid 2 fills at 24940 → SL 24925 (SAME as main), TP 25065 (24940+125)

# ============================================================================
# FILTROS DE SALIDA VWAP MOMENTUM STRATEGY
# ============================================================================
# Salida basada en el indicador VWAP Slope, se para salir si la pendiente del indicador pierde fuerza
USE_VWAP_SLOPE_INDICATOR_STOP_LOSS = False   # True = cerrar posición cuando VWAP slope cruza por debajo del threshold bajo, False = usar solo SL en puntos

# ============================================================================
# FILTRO DE SALIDA POR TIEMPO VWAP MOMENTUM STRATEGY
# ===========================================================================
# mantenimiento de operación abierta mientras sigan apareciendo puntos verdes
USE_KEEP_PUSHING_GREEN_DOTS = False               # True = mantener operacion abierta mientras sigan apareciendo puntos verdes, False = no usar este filtro
TIME_OUT_AFTER_LAST_GREEN_DOT_MINUTES = 45       # Minutos para cerrar la operación después del último punto verde (si no hay nuevos puntos verdes)
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
TRAIL_CASH_BREAK_EVEN_POINTS_PROFIT = 1            # Points of profit to lock in when trailing (0 = break-even, 10 = entry + 10 points)

# ATR Trailing Stop (Dynamic Volatility Based)
USE_ATR_TRAILING_STOP = False                       # True = use ATR based trailing stop, False = disabled
ATR_PERIOD = 21                                    # Period for ATR calculation
ATR_MULTIPLIER = 3                               # Multiplier for ATR to determine stop distance

# ============================================================================
# TRADING PARAMETERS VWAP CROSSOVER STRATEGY
# ============================================================================
ENABLE_VWAP_CROSSOVER_STRATEGY = False      # True = ejecutar estrategia, False = NO ejecutar
VWAP_CROSSOVER_TP_POINTS = 125.0              # Take profit in points
VWAP_CROSSOVER_SL_POINTS = 10.0              # Stop loss in points
VWAP_CROSSOVER_MAX_POSITIONS = 1            # Maximum number of positions open simultaneously
VWAP_CROSSOVER_START_HOUR = "00:01:00"      # Hora de inicio de trading
VWAP_CROSSOVER_END_HOUR = "22:00:00"        # Hora de fin de trading

# ============================================================================
# TRADING PARAMETERS VWAP PULLBACK STRATEGY
# ============================================================================
ENABLE_VWAP_PULLBACK_STRATEGY = False          # True = ejecutar estrategia, False = NO ejecutar
VWAP_PULLBACK_TP_POINTS = 125.0              # Take profit in points
VWAP_PULLBACK_SL_POINTS = 40.0               # Stop loss in points
VWAP_PULLBACK_MAX_POSITIONS = 1              # Maximum number of positions open simultaneously
VWAP_PULLBACK_START_HOUR = "00:01:00"        # Hora de inicio de trading
VWAP_PULLBACK_END_HOUR = "22:00:00"          # Hora de fin de trading

# ============================================================================
# TRADING PARAMETERS VWAP SQUARE STRATEGY (Rectangle Breakout)
# ============================================================================
ENABLE_VWAP_SQUARE_STRATEGY = False           # True = ejecutar estrategia, False = NO ejecutar
VWAP_SQUARE_TP_POINTS = 100.0                # Take profit in points
VWAP_SQUARE_SL_POINTS = 60.0                 # Stop loss in points
VWAP_SQUARE_MAX_POSITIONS = 1                # Maximum number of positions open simultaneously
VWAP_SQUARE_START_HOUR = "00:01:00"          # Hora de inicio de trading
VWAP_SQUARE_END_HOUR = "22:00:00"            # Hora de fin de trading
SQUARE_TALL_NARROW_THRESHOLD = 5.5           # Threshold for aspect ratio: price_per_bar > threshold = tall&narrow (chartreuse), else = perfect square (red)
VWAP_SQUARE_MIN_SPIKE = 50                   # Minimum rectangle height in points (y2-y1). 0 = take all. Filters out small noise rectangles       # Threshold for aspect ratio: price_per_bar > threshold = tall&narrow (chartreuse), else = perfect square (red)
VWAP_SQUARE_LISTENING_TIME = 60              # Minutes to listen for breakout after square closes
VWAP_SQUARE_SHIFT_POINTS = 0                 # Puntos adicionales de margen: BUY = MAX + shift, SELL = MIN - shift
USE_SQUARE_VWAP_SLOW_TREND_FILTER = True     # True = solo opera a favor de la tendencia (VWAP Fast vs Slow)

# ============================================================================
# TRADING PARAMETERS VWAP TIME STRATEGY (Specific Time Entry)
# ============================================================================
ENABLE_VWAP_TIME_STRATEGY = False              # True = ejecutar estrategia, False = NO ejecutar
VWAP_TIME_ENTRY = "17:00:00"                  # Hora exacta de entrada
VWAP_TIME_EXIT = "22:00:00"                   # Hora exacta de salida (Time-based exit)
VWAP_TIME_TP_POINTS = 400.0                   # Take profit in points (Optional, mainly time-based)
VWAP_TIME_SL_POINTS = 400.0                   # Stop loss in points (Optional)

# ============================================================================
# TRADING PARAMETERS VWAP WYCKOFF STRATEGY (Orange Dot Entry)
# ============================================================================
ENABLE_VWAP_WYCKOFF_STRATEGY = True           # True = ejecutar estrategia, False = NO ejecutar
START_ORANGE_DOT_WYCKOFF_TIME = "09:00:00"    # Hora de inicio para buscar Orange Dots
END_ORANGE_DOT_WYCKOFF_TIME = "15:15:00"      # Hora de fin para buscar Orange Dots
VWAP_WYCKOFF_EXIT_TIME = "15:29:00"           # Hora de cierre forzoso
TP_ORANGE_DOT_WYCKOFF = 325.0                 # Take profit
SL_ORANGE_DOT_WYCKOFF = 175.0                  # Stop loss
MAX_NUM_TRADES_PER_DAY = 99                    # Max trades per day
REVERSE_AT_EACH_ORANGE_DOT = False            # True = reverse at each orange dot, False = hold position until exit time

# ATR Trailing Stop for Wyckoff Strategy (Dynamic Volatility Based)
USE_WYCKOFF_ATR_TRAILING_STOP = True          # True = use ATR based trailing stop, False = use fixed stop
WYCKOFF_ATR_PERIOD = 21                        # Period for ATR calculation
WYCKOFF_ATR_MULTIPLIER = 10                    # Multiplier for ATR to determine stop distance

# OPENING RANGE CHANNEL
ENABLE_OPENING_RANGE_PLOT = False
OPENING_RANGE_START = "14:00:00"
OPENING_RANGE_END = "15:29:00"

# ATR Trailing Stop for Square Strategy (Dynamic Volatility Based)
USE_SQUARE_ATR_TRAILING_STOP = False          # True = use ATR based trailing stop, False = use fixed stop
SQUARE_ATR_PERIOD = 21                       # Period for ATR calculation
SQUARE_ATR_MULTIPLIER = 7                    # Multiplier for ATR to determine stop distance

# Rectangle-Based Initial Stop Loss
USE_OPOSITE_SIDE_OF_SQUARE_AS_STOP = True   # True = use opposite side of rectangle as initial stop, False = use fixed SL

# Shake Out Strategy (Failed Breakout Reversal)
USE_VWAP_SQUARE_SHAKE_OUT = True              # True = trade failed breakouts (shake outs), False = use normal breakout logic
VWAP_SQUARE_SHAKE_OUT_RETRACEMENT_PCT = 38    # Shake Out Retracement Confirmation (only used when USE_VWAP_SQUARE_SHAKE_OUT = True)
 # Percentage of rectangle height that must be retraced to confirm shake out
# How it works (only in SHAKE OUT mode):
# - GREEN rect: After breaking ABOVE y2, price must retrace down to: y2 - (rectangle_height * retracement_pct / 100)
# - RED rect: After breaking BELOW y1, price must retrace up to: y1 + (rectangle_height * retracement_pct / 100)
# Examples:
#   100 = full retracement (must reach opposite side of rectangle)
#   88 = 88% retracement from breakout level back towards rectangle
#   125 = 125% retracement (must go 25% beyond the opposite side)
# Retracement must occur within VWAP_SQUARE_LISTENING_TIME

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
VWAP_FAST = 100               # Periodo para VWAP rápido (magenta)
VWAP_SLOW = 200                  # Periodo para VWAP lento (verde)

PRICE_EJECTION_TRIGGER = 0.001         # Porcentaje mínimo de distancia entre precio y VWAP fast para trigger (0.001 = 0.1%)
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

SHOW_SUBPLOT_VWAP_SLOPE_INDICATOR = False      # True = mostrar subplot de VWAP Slope, False = ocultar subplot
SHOW_VWAP_INDICATOR_CROSSOVER= True        # True = mostrar señales de cruce VWAP en el gráfico
SHOW_ORANGE_DOT = True         # True = mostrar puntos naranjas (VWAP Slope crossover) en el gráfico de precio
SHOW_BLUE_SQUARE = True         # True = mostrar cuadrados azules (VWAP Slope crossdown) en el gráfico de precio
SHOW_GREEN_DOT = False          # True = mostrar puntos verdes (Price Ejection) en el gráfico de precio
SHOW_RED_DOT = False             # True = mostrar puntos rojos (OVER Price Ejection) en el gráfico de precio

PLOT_VWAP = True                 # True = dibujar indicador VWAP en el gráfico
SHOW_FAST_VWAP = True            # True = mostrar VWAP Fast (magenta)
SHOW_SLOW_VWAP = True            # True = mostrar VWAP Slow (verde)

# ============================================================================
# ITERATION PARAMETERS
# ============================================================================
SHOW_CHART_DURING_ITERATION = True             # True = generate and open chart for each day during iteration



"""
Configuración global para detección de fractales en Gold (GC)
"""
from pathlib import Path

# Rango de fechas a procesar/visualizar
START_DATE = "2025-02-02"
END_DATE = "2025-04-25"

# Parámetros de detección de fractales ZigZag
MIN_CHANGE_PCT_MINOR = 0.50    # 0.02% umbral para fractales pequeños
MIN_CHANGE_PCT_MAJOR = 2.1   # ubral para fractales grandes

# Directorios del proyecto
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FRACTALS_DIR = OUTPUTS_DIR / "fractals"


# Parámetros de agregación (no usado actualmente, datos ya vienen en OHLC)
AGGREGATION_WINDOW = 60  # 60 segundos (velas de 1 minuto)

# Parámetros RSI
RSI_PERIOD = 14  # Período para calcular RSI (estándar: 14, más alto = menos nervioso)
RSI_SMOOTH_PERIOD = 10  # Período para suavizar RSI con EMA (0 = sin suavizado)
RSI_OVERBOUGHT = 60  # Nivel de sobrecompra
RSI_OVERSOLD = 40  # Nivel de sobreventa

# Regla de resample para cálculo de RSI (ej: '15T', '1H').
# - Si RSI_RESAMPLE es None o cadena vacía => no se aplica resample
# - Si RSI_RESAMPLE es una cadena (ej: '1H' o '15T') => se usa esa regla
# - Si RSI_RESAMPLE es True => se usará la regla definida en RSI_RESAMPLE_TO_PERIOD
#    (p.ej. RSI_RESAMPLE_TO_PERIOD = '1H')
RSI_RESAMPLE = True
RSI_RESAMPLE_TO_PERIOD = '1H'  # Solo usada si RSI_RESAMPLE == True

# Parámetros Fibonacci
FIBO_LEVELS = [0.0, 0.382, 0.5, 0.618, 1.0]  # Niveles de retroceso estándar

# Mínimo tamaño de impulso (% del impulso medio) para considerar un movimiento
# Si el rango del movimiento es menor que MINIMUM_IMPULSE_FACTOR% del rango medio, se ignora
MINIMUM_IMPULSE_FACTOR = 60  # porcentaje (ej: 30 = 30%)


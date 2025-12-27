# NQ Fractals - Trading System with VWAP Strategies

Sistema de análisis técnico y trading automatizado para NQ (Nasdaq Futures) con detección de fractales ZigZag, estrategias VWAP y optimización de parámetros.

## Características Principales

- **Detección de Fractales ZigZag**: Identificación de picos y valles en múltiples timeframes (MINOR/MAJOR)
- **Estrategia VWAP Momentum**: Trading basado en price ejection desde VWAP (puntos verdes)
- **Estrategia VWAP Crossover**: Señales de entrada/salida basadas en cruces de VWAP fast/slow
- **Optimización de Parámetros**: Scripts para optimizar TP/SL y horarios de trading
- **Iteración Multi-Día**: Procesamiento automático de múltiples días con consolidación de resultados
- **Visualización Interactiva**: Gráficos HTML con Plotly para análisis detallado

## Instalación

```bash
pip install -r requirements.txt
```

## Estructura del Proyecto

```
factales_NQ/
├── config.py                      # Configuración centralizada
├── main_quant.py                  # Script principal para análisis individual
├── find_fractals.py               # Detección de fractales ZigZag
├── plot_day.py                    # Generación de gráficos interactivos
├── strat_vwap_momentum.py         # Estrategia VWAP Momentum (Price Ejection)
├── strat_vwap_crossover.py        # Estrategia VWAP Crossover
├── optimize_vwap_momentum.py      # Optimización de TP/SL
├── optimize_trading_hours.py      # Optimización de horarios de trading
├── iterate/
│   └── iterate_all_days.py        # Procesamiento multi-día con consolidación
├── utils/
│   ├── segregate_by_date.py       # Segregar CSV por fechas
│   └── normalize_csv_columns.py   # Normalizar columnas a minúsculas
├── data/                          # Datos tick-by-tick por día
│   └── time_and_sales_nq_YYYYMMDD.csv
└── outputs/
    ├── fractals/                  # CSVs de fractales detectados
    ├── charts/                    # Gráficos individuales por día
    ├── trading/                   # Reportes de estrategias
    └── optimization/              # Resultados de optimización
```

## Uso

### 1. Análisis de un Día Individual

```bash
python main_quant.py
```

Ejecuta el pipeline completo para la fecha configurada en `config.py`:
1. Carga datos tick-by-tick y convierte a OHLC (1 min)
2. Detecta fractales MINOR y MAJOR
3. Ejecuta estrategias de trading habilitadas
4. Genera gráfico interactivo con señales

### 2. Iteración Multi-Día

```bash
python iterate/iterate_all_days.py
```

Procesa múltiples días automáticamente:
- Detecta fractales para cada día
- Ejecuta estrategias habilitadas
- Consolida resultados en CSV y HTML
- Genera reporte agregado con métricas globales

**Configuración en `config.py`:**

```python
# Procesar todos los días disponibles
USE_ALL_DAYS_AVAILABLE = True

# O usar rango específico
USE_ALL_DAYS_AVAILABLE = False
ALL_DAYS_SEGMENT_START = "20241001"
ALL_DAYS_SEGMENT_END = "20251031"
```

### 3. Optimización de Parámetros

#### Optimizar TP/SL (Take Profit / Stop Loss)

```bash
python optimize_vwap_momentum.py
```

- Prueba múltiples combinaciones de TP y SL
- Analiza 42 combinaciones por defecto (7 TP × 6 SL)
- Rankea resultados por Sharpe Ratio
- Genera reporte HTML en `outputs/optimization/`

#### Optimizar Horarios de Trading

```bash
python optimize_trading_hours.py
```

- Analiza performance por hora del día (00:00 - 23:00)
- Identifica mejores horas por Sharpe Ratio, P&L, Win Rate
- Genera gráficos interactivos y tablas clasificatorias
- Guarda resultados en `outputs/optimization/`

## Configuración

Edita [`config.py`](config.py) para ajustar parámetros:

### Fechas y Rangos

```python
# Fecha individual (para main_quant.py)
DATE = "20251021"

# Iteración multi-día (para iterate_all_days.py)
USE_ALL_DAYS_AVAILABLE = True               # True = todos los días, False = rango específico
ALL_DAYS_SEGMENT_START = "20241001"         # Fecha inicio (si USE_ALL_DAYS_AVAILABLE=False)
ALL_DAYS_SEGMENT_END = "20251031"           # Fecha fin (si USE_ALL_DAYS_AVAILABLE=False)
```

### Estrategia VWAP Momentum (Price Ejection)

```python
ENABLE_VWAP_MOMENTUM_STRATEGY = True
VWAP_MOMENTUM_TP_POINTS = 125.0             # Take profit en puntos
VWAP_MOMENTUM_SL_POINTS = 75.0              # Stop loss en puntos
VWAP_MOMENTUM_MAX_POSITIONS = 1             # Posiciones simultáneas máximas
VWAP_MOMENTUM_START_HOUR = "00:00:00"       # Hora inicio trading
VWAP_MOMENTUM_END_HOUR = "22:00:00"         # Hora fin trading
```

### Estrategia VWAP Crossover

```python
ENABLE_VWAP_CROSSOVER_STRATEGY = False
VWAP_CROSSOVER_TP_POINTS = 5.0
VWAP_CROSSOVER_SL_POINTS = 9.0
VWAP_CROSSOVER_MAX_POSITIONS = 1
VWAP_CROSSOVER_START_HOUR = "16:30:00"
VWAP_CROSSOVER_END_HOUR = "22:00:00"
```

### Parámetros de Fractales ZigZag

```python
MIN_CHANGE_PCT_MINOR = 0.10   # 0.10% umbral fractales pequeños (~26 puntos en NQ)
MIN_CHANGE_PCT_MAJOR = 0.20   # 0.20% umbral fractales grandes (~52 puntos en NQ)
```

### Parámetros VWAP

```python
VWAP_FAST = 50                              # Periodo VWAP rápido
VWAP_SLOW = 100                             # Periodo VWAP lento
PRICE_EJECTION_TRIGGER = 0.001              # 0.1% distancia mínima para señal
OVER_PRICE_EJECTION_TRIGGER = 0.003         # 0.3% distancia para sobre-alejamiento
```

### Visualización

```python
PLOT_VWAP = True                            # Mostrar VWAP en gráfico
SHOW_FAST_VWAP = True                       # VWAP Fast (magenta)
SHOW_SLOW_VWAP = False                      # VWAP Slow (verde)
PLOT_MINOR_FRACTALS = False                 # Fractales MINOR
PLOT_MAJOR_FRACTALS = False                 # Fractales MAJOR
SHOW_CHART_DURING_ITERATION = True          # Generar gráficos en iteración
```

## Preparación de Datos

### Formato de Archivos CSV

Los archivos deben estar en formato europeo con estas columnas (minúsculas):
- `timestamp`: Fecha y hora (YYYY-MM-DD HH:MM:SS)
- `precio`: Precio de la transacción
- `volume`: Volumen de la transacción
- Separador: `;` (punto y coma)
- Decimal: `,` (coma)

### Normalizar Columnas

Si tus archivos usan mayúsculas (Timestamp, Precio, Volumen):

```bash
# Modo dry-run (solo muestra cambios)
python utils/normalize_csv_columns.py

# Aplicar cambios
python utils/normalize_csv_columns.py --apply
```

### Segregar por Fecha

Si tienes un CSV grande con múltiples días:

```bash
python utils/segregate_by_date.py
```

Creará archivos individuales: `time_and_sales_nq_YYYYMMDD.csv`

## Salidas

### Fractales CSV

```
outputs/fractals/
├── NQ_fractals_minor_YYYYMMDD.csv
├── NQ_fractals_major_YYYYMMDD.csv
└── NQ_consolidation_metrics_YYYYMMDD.csv
```

Formato:
```csv
timestamp,price,type,direction,tag
2025-10-21 09:31:00,26125.50,PICO,up,minor
2025-10-21 09:45:00,26098.25,VALLE,down,minor
```

### Reportes de Trading

```
outputs/trading/
├── summary_vwap_momentum_YYYYMMDD.html     # Reporte individual por día
└── all_days_summary_YYYYMMDD-YYYYMMDD.html # Consolidado multi-día
```

Incluye:
- Métricas de performance (Win Rate, Sharpe Ratio, Sortino, Profit Factor)
- Lista de trades con entrada/salida y P&L
- Gráficos de equity curve y drawdown

### Gráficos Interactivos

```
outputs/charts/
└── nq_YYYYMMDD.html
```

Incluye:
- Velas OHLC
- Fractales ZigZag (MINOR/MAJOR)
- VWAP Fast y Slow
- Señales de trading (puntos verdes/rojos)
- Subplot de volumen

### Optimización

```
outputs/optimization/
├── vwap_momentum_optimization_YYYYMMDD-YYYYMMDD.html  # TP/SL optimization
└── trading_hours_analysis_YYYYMMDD-YYYYMMDD.html      # Hourly analysis
```

## Métricas de Trading

- **Win Rate**: Porcentaje de trades ganadores
- **Sharpe Ratio**: Retorno ajustado por riesgo (mayor es mejor, >1.0 es bueno)
- **Sortino Ratio**: Similar a Sharpe pero solo penaliza volatilidad negativa
- **Profit Factor**: Ratio de ganancias brutas / pérdidas brutas (>1.5 es bueno)
- **Max Drawdown**: Mayor caída desde pico histórico
- **R:R Ratio**: Ratio riesgo/recompensa (TP/SL)

## Workflow Recomendado

1. **Preparar datos**: Segregar CSV y normalizar columnas
2. **Configurar estrategia**: Ajustar parámetros iniciales en `config.py`
3. **Optimizar TP/SL**: Ejecutar `optimize_vwap_momentum.py`
4. **Optimizar horarios**: Ejecutar `optimize_trading_hours.py`
5. **Actualizar config**: Usar parámetros óptimos encontrados
6. **Backtest completo**: Ejecutar `iterate/iterate_all_days.py` con todos los días
7. **Analizar resultados**: Revisar reportes HTML y ajustar estrategia

## Notas Técnicas

### Conversión Tick → OHLC

Los datos tick-by-tick se convierten automáticamente a barras OHLC de 1 minuto:
- `find_fractals.py` maneja la conversión usando `aggregate_ticks_to_ohlc()`
- Los CSVs originales permanecen sin modificar
- La conversión se hace en memoria durante el análisis

### Sin Look-Ahead Bias

- Los fractales se detectan sin usar información futura
- Alternancia garantizada: PICO → VALLE → PICO
- Las señales de trading solo usan datos disponibles en ese momento

### Compatibilidad

- Soporta tanto formato antiguo (Timestamp, Precio, Volumen) como nuevo (timestamp, precio, volume)
- Normalización automática a minúsculas en todas las operaciones
- Compatible con Windows/Linux/Mac

## Troubleshooting

### Error: "No data files found"

Verifica que los archivos CSV estén en `data/` con el formato:
- `time_and_sales_nq_YYYYMMDD.csv`

### Error: Column name mismatch

Ejecuta el normalizador:
```bash
python utils/normalize_csv_columns.py --apply
```

### Estrategia no genera trades

- Verifica que `ENABLE_VWAP_MOMENTUM_STRATEGY = True` en config.py
- Revisa los horarios de trading (`START_HOUR` / `END_HOUR`)
- Ajusta `PRICE_EJECTION_TRIGGER` si es muy restrictivo

## Contribuir

Este es un proyecto de investigación cuantitativa. Las mejoras sugeridas incluyen:

- Implementar más estrategias (RSI, MACD, Bollinger Bands)
- Añadir walk-forward optimization
- Integración con brokers (Interactive Brokers, TD Ameritrade)
- Machine Learning para clasificación de señales
- Optimización genética de parámetros

## Licencia

Proyecto personal de investigación. Uso educativo y de investigación.

**DISCLAIMER**: Este código es solo para fines educativos. El trading de futuros conlleva riesgos sustanciales. No use este código para trading real sin una comprensión completa de los riesgos involucrados.

# Sistema de Optimización de Time-in-Market

## 📋 Descripción

Este sistema permite optimizar la duración de permanencia en el mercado (time-in-market) para cada hora de entrada, basándose en análisis histórico y utilizando el Sharpe Ratio como criterio de optimización.

## 🎯 Características

- **Optimización por hora de entrada**: Cada hora del día (00-23) tiene su duración óptima
- **Criterio Sharpe Ratio**: Mejor balance entre retorno y riesgo
- **Configuración JSON**: Fácil de leer y usar en producción
- **Integración automática**: Se integra con `strat_vwap_momentum.py`
- **Fallback inteligente**: Si no hay configuración, usa duración fija

## 📁 Archivos del Sistema

### Scripts Principales

1. **`optimize_time_in_market.py`**
   - Analiza datos históricos
   - Prueba diferentes duraciones (1min, 5min, 15min, 1h, 2h, 3h, 4h, 5h, 6h, 8h, EOD)
   - Genera configuración óptima por hora
   - Guarda resultados en JSON, CSV y HTML

2. **`strat_vwap_momentum.py`**
   - Estrategia de trading VWAP Momentum
   - Integrado con sistema de optimización
   - Usa duración óptima según hora de entrada

3. **`show_optimal_durations.py`**
   - Muestra tabla resumen de configuración óptima
   - Ranking de mejores horas por Sharpe Ratio

4. **`example_use_optimal_duration.py`**
   - Ejemplos de cómo usar el sistema
   - Carga configuración por hora

### Archivos de Configuración

- **`config.py`**: Configuración global
  - `USE_TIME_IN_MARKET`: True/False
  - `USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE`: True/False
  - `TIME_IN_MARKET_MINUTES`: Duración fija (fallback)
  - `USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET`: True/False
  - `MAX_SL_ALLOWED_IN_TIME_IN_MARKET`: Puntos de stop loss protector

- **`outputs/optimization/optimal_time_in_market_config.json`**: Configuración óptima generada

## 🔧 Configuración

### En `config.py`:

```python
# Activar time-in-market
USE_TIME_IN_MARKET = True

# Opción 1: Usar optimización por JSON (RECOMENDADO)
USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE = True

# Opción 2: Usar duración fija
USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE = False
TIME_IN_MARKET_MINUTES = 180  # 3 horas

# Stop Loss protector (opcional)
USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET = True
MAX_SL_ALLOWED_IN_TIME_IN_MARKET = 100  # 100 puntos
```

## 🚀 Uso

### 1. Generar Configuración Óptima

```bash
python optimize_time_in_market.py
```

Esto generará:
- `outputs/optimization/optimal_time_in_market_config.json`
- `outputs/optimization/time_in_market_optimization.csv`
- `outputs/optimization/time_in_market_optimization.html`
- `outputs/optimization/time_in_market_by_hour.csv`

### 2. Ver Configuración Óptima

```bash
python show_optimal_durations.py
```

### 3. Usar en Trading

```bash
python strat_vwap_momentum.py
```

La estrategia automáticamente:
1. Detecta hora de entrada del trade
2. Carga duración óptima del JSON
3. Aplica esa duración para la salida

## 📊 Estructura del JSON

```json
{
  "metadata": {
    "generated_at": "2025-12-27 17:00:29",
    "optimization_criteria": "best_sharpe_ratio",
    "description": "Optimal time-in-market duration for each entry hour"
  },
  "optimal_durations": {
    "14": {
      "entry_hour": 14,
      "duration_label": "480min (8h)",
      "duration_minutes": 480,
      "sharpe_ratio": 27.67,
      "total_pnl_usd": -191810.0,
      "avg_pnl_usd": -781.77,
      "total_trades": 540,
      "win_rate": 47.14,
      "avg_win_usd": 3008.59,
      "avg_loss_usd": -3379.69,
      "avg_mae_usd": -4871.65,
      "avg_mfe_usd": 3629.65
    }
  }
}
```

## 🔍 Ejemplo de Código

```python
from optimize_time_in_market import load_optimal_duration
from datetime import datetime, timedelta

# Al entrar a un trade
entry_time = datetime.now()
entry_hour = entry_time.hour

# Cargar configuración óptima
config = load_optimal_duration(entry_hour)

if config:
    duration_minutes = config['duration_minutes']

    if duration_minutes == 'EOD':
        # Salir al final del día
        exit_time = get_end_of_day_time()
    else:
        # Salir después de X minutos
        exit_time = entry_time + timedelta(minutes=duration_minutes)

    print(f"Hora entrada: {entry_hour:02d}:00")
    print(f"Duración: {config['duration_label']}")
    print(f"Sharpe Ratio: {config['sharpe_ratio']:.2f}")
    print(f"Win Rate: {config['win_rate']:.1f}%")
```

## 📈 Jerarquía de Decisión

```
┌─────────────────────────────────────────┐
│ USE_TIME_IN_MARKET = True?              │
└────────────┬────────────────────────────┘
             │ Yes
             ▼
┌─────────────────────────────────────────┐
│ USE_TIME_IN_MARKET_JSON_OPTIMIZATION_   │
│ FILE = True?                             │
└────────┬───────────────────┬────────────┘
         │ Yes               │ No
         ▼                   ▼
┌────────────────┐   ┌──────────────────┐
│ Cargar JSON    │   │ Usar duración    │
│ por hora       │   │ fija             │
└────────┬───────┘   └────────┬─────────┘
         │                    │
         └──────────┬─────────┘
                    ▼
         ┌──────────────────────────┐
         │ USE_MAX_SL_ALLOWED_IN_   │
         │ TIME_IN_MARKET = True?   │
         └───────┬──────────────────┘
                 │ Yes
                 ▼
         ┌──────────────────────────┐
         │ Aplicar stop loss        │
         │ protector                │
         └──────────────────────────┘
```

## 📝 Notas Importantes

1. **Duración 'EOD'**: Significa "End of Day", sale en la última barra del día
2. **Fallback**: Si no encuentra configuración para una hora, usa `TIME_IN_MARKET_MINUTES`
3. **Stop Loss Protector**: Opcional, se aplica incluso con time-in-market
4. **Actualización**: Regenerar JSON periódicamente con nuevos datos

## 🎓 Mejores Horas (por Sharpe Ratio)

Según el análisis histórico:

| Rank | Hora  | Sharpe | Duración    | Win Rate | Avg P&L  |
|------|-------|--------|-------------|----------|----------|
| 1    | 08:00 | 319.33 | EOD         | 45.5%    | $1,385   |
| 2    | 07:00 | 170.58 | EOD         | 53.3%    | $1,267   |
| 3    | 14:00 | 27.67  | 480min (8h) | 47.1%    | -$782    |
| 4    | 03:00 | 18.64  | 480min (8h) | 77.5%    | $1,108   |
| 5    | 10:00 | 11.85  | 300min (5h) | 49.8%    | $33      |

**Nota**: Un Sharpe Ratio alto indica buen balance riesgo/retorno, no necesariamente el mayor P&L.

## 🔄 Workflow Recomendado

1. **Análisis inicial**: Ejecutar `optimize_time_in_market.py` con todos los datos históricos
2. **Revisar resultados**: Abrir `time_in_market_optimization.html` en navegador
3. **Verificar configuración**: Ejecutar `show_optimal_durations.py`
4. **Activar en config**: `USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE = True`
5. **Backtesting**: Probar con `strat_vwap_momentum.py`
6. **Actualización periódica**: Regenerar JSON cada mes/trimestre

## 📚 Referencias

- **Sharpe Ratio**: (Retorno Promedio - Tasa Libre Riesgo) / Desviación Estándar
- **MAE**: Maximum Adverse Excursion (peor momento del trade)
- **MFE**: Maximum Favorable Excursion (mejor momento del trade)
- **Win Rate**: Porcentaje de trades ganadores

# Gold Perdices - Análisis Cuantitativo

Sistema de análisis técnico para Gold (GC) con detección de fractales ZigZag, RSI y visualización interactiva.

Soporta análisis de rangos de fechas completos (2015-01-02 a 2025-04-25) o días individuales.

## Estructura del Proyecto

```
gold_perdices/
├── config.py                 # Configuración centralizada
├── main_quant.py            # Script principal - ejecutar este
├── find_fractals.py         # Detección de fractales ZigZag
├── plot_day.py              # Generación de gráficos con RSI
├── find_entries.py          # Detección de divergencias y señales
├── utils/
│   └── segregate_by_date.py # Segregar CSV por fechas
├── data/                    # Datos OHLC por día
│   └── gc_YYYY-MM-DD.csv
└── outputs/
    ├── fractals/            # CSVs de fractales detectados
    └── gc_YYYY-MM-DD.html   # Gráficos interactivos
```

## Uso

### Script Principal (Recomendado)

El script `main_quant.py` ejecuta el pipeline completo de análisis:

```bash
python main_quant.py
```

Esto ejecutará automáticamente para el rango de fechas configurado:
1. ✅ Carga de datos desde START_DATE hasta END_DATE
2. ✅ Detección de fractales MINOR y MAJOR en todo el rango
3. ✅ Cálculo de RSI
4. ✅ Detección de divergencias alcistas
5. ✅ Generación de gráfico interactivo

### Scripts Individuales

También puedes ejecutar cada módulo por separado (siguiendo este orden):

```bash
# 1. Primero: Detección de fractales (genera CSVs necesarios)
python find_fractals.py

# 2. Luego: Generar gráfico con divergencias
python plot_day.py
```

**Nota**: `find_entries.py` se puede ejecutar de forma independiente, pero requiere que existan los fractales generados previamente por `find_fractals.py`.

## Configuración

Edita `config.py` para cambiar parámetros:

```python
# Rango de fechas a analizar
START_DATE = "2015-01-02"    # Fecha inicial
END_DATE = "2025-04-25"      # Fecha final

# Umbrales de fractales ZigZag
MIN_CHANGE_PCT_MINOR = 0.09  # 0.09% para fractales pequeños
MIN_CHANGE_PCT_MAJOR = 0.25  # 0.25% para fractales grandes

# Parámetros RSI
RSI_PERIOD = 14              # Período del RSI
RSI_OVERBOUGHT = 70          # Nivel de sobrecompra
RSI_OVERSOLD = 30            # Nivel de sobreventa

# Parámetros de detección de divergencias
REQUIRE_DOWNTREND = True     # Requiere tendencia bajista MAJOR
REQUIRE_DIVERGENCE = True    # Requiere divergencia alcista
FIBO_LEVEL_FILTER = 0.5     # Nivel mínimo de Fibonacci
```

## Preparación de Datos

Si tienes un CSV grande con múltiples días:

```bash
python utils/segregate_by_date.py
```

Esto creará archivos individuales: `gc_YYYY-MM-DD.csv`

## Salidas

### Fractales CSV

Para rangos de fechas:
- `outputs/fractals/gc_fractals_minor_YYYY-MM-DD_YYYY-MM-DD.csv`
- `outputs/fractals/gc_fractals_major_YYYY-MM-DD_YYYY-MM-DD.csv`

Para días individuales (legacy):
- `outputs/fractals/gc_fractals_minor_YYYY-MM-DD.csv`
- `outputs/fractals/gc_fractals_major_YYYY-MM-DD.csv`

Formato:
```csv
timestamp,price,type,direction,tag
2015-01-02 14:21:00+01:00,1668.8,VALLE,down,major
```

### Gráfico Interactivo

Para rangos de fechas:
- `outputs/gc_YYYY-MM-DD_YYYY-MM-DD.html`

Para días individuales (legacy):
- `outputs/gc_YYYY-MM-DD.html`

Incluye:
- Línea de precio (gris)
- ZigZag MINOR (dodgerblue, 0.7 opacity)
- ZigZag MAJOR (azul)
- Picos (verde) y Valles (rojo)
- Niveles Fibonacci (naranja sólido para niveles clave, gris punteado para otros)
- RSI subplot con niveles de sobrecompra/sobreventa (sincronizado con zoom)

## Características

### Análisis de Rangos de Fechas
- ✅ Carga automática de múltiples días (2015-01-02 a 2025-04-25)
- ✅ Concatenación inteligente de datos
- ✅ Procesamiento continuo de fractales a través de múltiples días
- ✅ Compatibilidad con análisis de días individuales (legacy)

### Fractales ZigZag
- ✅ Sin look-ahead bias
- ✅ Alternancia garantizada (PICO → VALLE → PICO)
- ✅ Dos niveles: MINOR (0.09%) y MAJOR (0.25%)
- ✅ Detección continua a través de rangos de fechas

### RSI
- ✅ Cálculo estándar (período 14)
- ✅ Detección de fractales en el RSI
- ✅ Visualización en subplot sincronizado
- ✅ Detección de niveles de sobreventa

### Divergencias Alcistas
- ✅ Detección de divergencias dobles, triples y múltiples
- ✅ Comparación de fractales MINOR del precio con VALLES del RSI
- ✅ Filtrado por tendencia bajista MAJOR (opcional)
- ✅ Marcadores visuales en el gráfico (triángulos verdes)

### Visualización
- ✅ Gráficos interactivos con Plotly
- ✅ Zoom sincronizado entre precio y RSI
- ✅ Estilo minimalista profesional
- ✅ Soporte para visualización de rangos largos de datos

## TODO

- [ ] Añadir más indicadores (MACD, Bollinger Bands, EMA)
- [ ] Backtesting framework
- [ ] Análisis multi-día
- [ ] Exportar señales de trading a CSV
- [ ] Dashboard web con múltiples días

## Dependencias

```bash
pip install -r requirements.txt
```

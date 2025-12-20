# Gold Perdices - Análisis Cuantitativo

Sistema de análisis técnico para Gold (GC) con detección de fractales ZigZag y visualización interactiva.

Soporta análisis de rangos de fechas completos (2015-01-02 a 2025-04-25) o días individuales.

## Dependencias e INSTALACIÓN:

```bash
pip install -r requirements.txt
```


## Estructura del Proyecto

```
gold_perdices/
├── config.py                 # Configuración centralizada
├── main_quant.py            # Script principal - ejecutar este
├── find_fractals.py         # Detección de fractales ZigZag
├── plot_day.py              # Generación de gráficos
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
3. ✅ Generación de gráfico interactivo

### Scripts Individuales

También puedes ejecutar cada módulo por separado (siguiendo este orden):

```bash
# 1. Primero: Detección de fractales (genera CSVs necesarios)
python find_fractals.py

# 2. Luego: Generar gráfico
python plot_day.py
```

## Configuración

Edita `config.py` para cambiar parámetros:

```python
# Rango de fechas a analizar
START_DATE = "2015-01-02"    # Fecha inicial
END_DATE = "2025-04-25"      # Fecha final

# Umbrales de fractales ZigZag
MIN_CHANGE_PCT_MINOR = 0.09  # 0.09% para fractales pequeños
MIN_CHANGE_PCT_MAJOR = 0.25  # 0.25% para fractales grandes
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

### Visualización
- ✅ Gráficos interactivos con Plotly
- ✅ Línea de precio con fractales superpuestos
- ✅ Estilo minimalista profesional
- ✅ Soporte para visualización de rangos largos de datos

## TODO

- [ ] Añadir más indicadores (MACD, Bollinger Bands, EMA)
- [ ] Backtesting framework
- [ ] Análisis multi-día
- [ ] Exportar señales de trading a CSV
- [ ] Dashboard web con múltiples días


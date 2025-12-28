# VWAP Slope Crossover Visualization - Implementation Summary

**Fecha**: 2025-12-28
**Status**: ✅ IMPLEMENTED AND TESTED

---

## 🎯 OBJETIVO

Agregar visualización de puntos naranjas en el gráfico de precio cuando el indicador **VWAP Slope** cruza hacia arriba el nivel `VWAP_SLOPE_INDICATOR_HIGH_VALUE` (threshold alto, por defecto 0.6).

Esta funcionalidad ayuda a identificar visualmente los momentos en que la pendiente del VWAP Fast se acelera significativamente, indicando posible momentum fuerte en el mercado.

---

## 📋 IMPLEMENTACIÓN

### 1. **Nueva Variable de Configuración**

Ya existente en [config.py](config.py) (línea 137):

```python
SHOW_VWAP_INDICATOR_CROSSOVER = True  # True = mostrar señales de cruce VWAP en el gráfico
```

**Propósito**: Activar/desactivar la visualización de puntos naranjas de crossover en el gráfico de precio.

---

### 2. **Modificaciones en plot_day.py**

#### A. Import de la variable (línea 15):

```python
from config import (
    ...
    SHOW_VWAP_INDICATOR_CROSSOVER,
    ...
)
```

#### B. Detección de Crossovers (líneas 324-363):

```python
# Añadir puntos naranjas cuando VWAP Slope cruza hacia arriba el nivel HIGH_VALUE (crossover)
if SHOW_VWAP_INDICATOR_CROSSOVER and 'vwap_slope' in df.columns:
    # Detectar crossovers: cuando vwap_slope cruza de abajo hacia arriba el threshold HIGH_VALUE
    # Crossover ocurre cuando:
    # - Bar anterior: vwap_slope <= VWAP_SLOPE_INDICATOR_HIGH_VALUE
    # - Bar actual: vwap_slope > VWAP_SLOPE_INDICATOR_HIGH_VALUE

    df_crossover = df.copy()
    df_crossover['vwap_slope_prev'] = df_crossover['vwap_slope'].shift(1)

    # Condición de crossover
    crossover_condition = (
        (df_crossover['vwap_slope_prev'] <= VWAP_SLOPE_INDICATOR_HIGH_VALUE) &
        (df_crossover['vwap_slope'] > VWAP_SLOPE_INDICATOR_HIGH_VALUE) &
        (df_crossover['vwap_slope'].notna()) &
        (df_crossover['vwap_slope_prev'].notna())
    )

    df_crossover_points = df_crossover[crossover_condition].copy()

    if not df_crossover_points.empty:
        trace_crossover = go.Scatter(
            x=df_crossover_points['index'],
            y=df_crossover_points['close'],
            mode='markers',
            name=f'VWAP Slope Crossover (>{VWAP_SLOPE_INDICATOR_HIGH_VALUE})',
            marker=dict(
                color='orange',
                size=8,
                symbol='circle',
                line=dict(color='darkorange', width=1)
            ),
            hovertemplate='<b>VWAP Slope Crossover</b><br>Price: %{y:.2f}<br>Slope: %{customdata:.4f}<extra></extra>',
            customdata=df_crossover_points['vwap_slope']
        )
        fig.add_trace(trace_crossover, row=price_row, col=1)

        print(f"[INFO] VWAP Slope Crossover points detectados: {len(df_crossover_points)} (threshold: {VWAP_SLOPE_INDICATOR_HIGH_VALUE})")
    else:
        print(f"[INFO] No se detectaron VWAP Slope Crossovers (threshold: {VWAP_SLOPE_INDICATOR_HIGH_VALUE})")
```

---

## 🔍 LÓGICA DE DETECCIÓN DE CROSSOVERS

### Condiciones para un Crossover:

Un crossover (cruce hacia arriba) ocurre cuando se cumplen **TODAS** estas condiciones:

1. **Bar anterior**: `vwap_slope[n-1] <= VWAP_SLOPE_INDICATOR_HIGH_VALUE`
2. **Bar actual**: `vwap_slope[n] > VWAP_SLOPE_INDICATOR_HIGH_VALUE`
3. **Sin valores NaN**: Ambos valores deben ser válidos

### Ejemplo Visual:

```
Tiempo:      t-1    t      t+1    t+2
VWAP Slope:  0.55   0.65   0.70   0.58
Threshold:   0.60   0.60   0.60   0.60
             ----   ↑↑     ----   ----
Crossover:    NO    YES    NO     NO
```

En `t`, el slope cruza de 0.55 (por debajo del threshold 0.60) a 0.65 (por encima) → **CROSSOVER detectado** → Punto naranja en el precio.

---

## 🎨 CARACTERÍSTICAS VISUALES

### Puntos Naranjas (Orange Dots):

- **Color**: `orange` (relleno) con borde `darkorange`
- **Tamaño**: `8` (más grande que los green dots de price ejection que son `4`)
- **Símbolo**: `circle` (círculo sólido)
- **Posición**: Sobre la línea de precio (`y = close`)
- **Nombre en leyenda**: `"VWAP Slope Crossover (>0.6)"`

### Hover Information:

Al pasar el mouse sobre un punto naranja, se muestra:
```
VWAP Slope Crossover
Price: 26150.25
Slope: 0.6542
```

---

## 📊 RESULTADO DEL TEST (2025-11-03)

```bash
[INFO] VWAP Slope Crossover points detectados: 26 (threshold: 0.6)
```

**Interpretación**:
- En el día `20251103` se detectaron **26 cruces** del VWAP Slope sobre el nivel 0.6
- Estos 26 puntos naranjas aparecen en el gráfico de precio
- Indican momentos de alta aceleración de la pendiente del VWAP Fast

---

## 🔄 FLUJO DE TRABAJO

### Cuando `SHOW_VWAP_INDICATOR_CROSSOVER = True`:

```
1. Calcular VWAP Slope para todas las barras
   ↓
2. Detectar crossovers (slope cruza threshold hacia arriba)
   ↓
3. Marcar precio con punto naranja en cada crossover
   ↓
4. Mostrar en gráfico con hover info
```

### Cuando `SHOW_VWAP_INDICATOR_CROSSOVER = False`:

```
- No se ejecuta la detección de crossovers
- No se muestran puntos naranjas
- Gráfico muestra solo otros indicadores (green dots, etc.)
```

---

## 📍 UBICACIÓN EN EL GRÁFICO

Los puntos naranjas se agregan **después** de:
- VWAP Fast (magenta line)
- VWAP Slow (green line)
- VWAP Slope subplot (si está habilitado)

Y **antes** de:
- Price Ejection green dots
- Over Price Ejection red dots
- Trade markers

Esto asegura que los puntos naranjas sean visibles pero no obstruyan otros indicadores importantes.

---

## 💡 INTERPRETACIÓN PRÁCTICA

### ¿Qué significa un punto naranja?

Un punto naranja indica que **en ese momento**:

1. **La pendiente del VWAP Fast superó el umbral alto (0.6)**
   - Indica aceleración fuerte del precio
   - Posible inicio de momentum significativo

2. **Cambio de régimen de baja pendiente a alta pendiente**
   - Transición de consolidación/lateralización a movimiento direccional
   - Potencial oportunidad de entrada en dirección del momentum

3. **Correlación con Price Ejection**
   - Muchas veces coincide con green dots (price ejection)
   - Confirma señal de alejamiento del VWAP con pendiente fuerte

---

## 🎯 CASOS DE USO

### 1. **Confirmación de Señales de Entrada**

```
Si:
  - Green dot (price ejection) ✅
  - Orange dot (slope crossover) ✅
Entonces:
  - Señal de entrada FUERTE (precio alejado + pendiente acelerada)
```

### 2. **Detección de Inicio de Tendencias**

```
Orange dots consecutivos en la misma dirección
→ Posible inicio de tendencia fuerte
→ Mayor probabilidad de seguir en esa dirección
```

### 3. **Filtro de Falsas Señales**

```
Si:
  - Green dot (price ejection) ✅
  - NO orange dot (slope débil) ❌
Entonces:
  - Posible falsa señal (precio alejado pero sin momentum)
  - Considerar esperar confirmación
```

---

## ⚙️ PARÁMETROS RELACIONADOS

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `SHOW_VWAP_INDICATOR_CROSSOVER` | `True` | Activar/desactivar visualización de crossovers |
| `VWAP_SLOPE_INDICATOR_HIGH_VALUE` | `0.6` | Umbral para considerar pendiente "alta" |
| `VWAP_SLOPE_DEGREE_WINDOW` | `10` | Ventana de barras para calcular la pendiente |
| `VWAP_FAST` | `50` | Periodo del VWAP Fast usado para el slope |

**Relación**:
- `VWAP_SLOPE_DEGREE_WINDOW` determina la suavidad del slope
- `VWAP_SLOPE_INDICATOR_HIGH_VALUE` determina la sensibilidad de los crossovers
- `VWAP_FAST` define qué VWAP se usa para calcular el slope

---

## 📈 COMPARACIÓN CON OTROS INDICADORES

### Green Dots (Price Ejection):
- **Qué miden**: Distancia del precio respecto al VWAP Fast
- **Threshold**: 0.1% de distancia
- **Color**: Verde
- **Tamaño**: 4

### Orange Dots (Slope Crossover):
- **Qué miden**: Aceleración de la pendiente del VWAP Fast
- **Threshold**: 0.6 de slope
- **Color**: Naranja
- **Tamaño**: 8

### Red Dots (Over Price Ejection):
- **Qué miden**: Distancia extrema del precio respecto al VWAP Fast
- **Threshold**: 0.3% de distancia
- **Color**: Rojo
- **Tamaño**: 6

**Combinación ideal**: Green dot + Orange dot = Señal fuerte de entrada

---

## ✅ ARCHIVOS MODIFICADOS

1. **[plot_day.py](plot_day.py)**:
   - Línea 15: Import de `SHOW_VWAP_INDICATOR_CROSSOVER`
   - Líneas 324-363: Lógica de detección y visualización de crossovers

---

## 🧪 TEST RESULTS

**Fecha de test**: 2025-11-03
**Configuración**:
- `SHOW_VWAP_INDICATOR_CROSSOVER = True`
- `VWAP_SLOPE_INDICATOR_HIGH_VALUE = 0.6`
- `VWAP_SLOPE_DEGREE_WINDOW = 10`

**Resultados**:
```
✅ Crossovers detectados: 26
✅ Puntos naranjas visibles en el gráfico
✅ Hover info funcional
✅ Leyenda correcta
✅ No errores en ejecución
```

**Observaciones**:
- Los puntos naranjas aparecen principalmente durante movimientos rápidos de precio
- Correlación alta con green dots en zonas de momentum fuerte
- Útil para identificar aceleraciones de tendencia

---

## 🔄 PRÓXIMAS MEJORAS POTENCIALES

### 1. **Crossover Bidireccional**
Actualmente solo detecta cruces hacia **arriba**. Se podría agregar:
- Cruces hacia **abajo** (cuando slope cae por debajo del threshold)
- Diferentes colores para cruces up/down

### 2. **Múltiples Niveles de Threshold**
```python
VWAP_SLOPE_INDICATOR_MEDIUM_VALUE = 0.4  # Medium slope
VWAP_SLOPE_INDICATOR_HIGH_VALUE = 0.6    # High slope
VWAP_SLOPE_INDICATOR_EXTREME_VALUE = 0.8 # Extreme slope
```

### 3. **Filtro de Crossovers por Dirección**
Solo mostrar crossovers cuando:
- LONG: price > vwap_fast
- SHORT: price < vwap_fast

---

## 📝 CONFIGURACIÓN DASHBOARD

El parámetro `SHOW_VWAP_INDICATOR_CROSSOVER` se puede agregar al dashboard de configuración en una sección de "Visualización" junto con otros parámetros de display.

**Ubicación sugerida en dashboard**:
```
📊 PARÁMETROS DE VISUALIZACIÓN
- SHOW_SUBPLOT_VWAP_SLOPE_INDICATOR: True
- SHOW_VWAP_INDICATOR_CROSSOVER: True  ← NUEVO
- SHOW_FAST_VWAP: True
- SHOW_SLOW_VWAP: True
```

---

## 🎯 RESUMEN

**Antes**: El gráfico mostraba el VWAP Slope en un subplot separado, pero no había indicación directa en el precio de cuándo el slope cruzaba niveles importantes.

**Ahora**:
- ✅ Puntos naranjas en el precio marcan cruces del slope sobre el threshold alto
- ✅ Fácil identificación visual de momentos de alta aceleración
- ✅ Hover info muestra valor exacto del slope en cada crossover
- ✅ Configurable con `SHOW_VWAP_INDICATOR_CROSSOVER`

**Beneficio**: Mejora la identificación visual de señales de entrada de alta calidad (combinación de price ejection + slope crossover).

---

**Implementation completed successfully!** 🎉

**Test Results**: 26 crossovers detectados en 2025-11-03 ✅

# Dashboard Configuration - Jerarquía de Parámetros

**Fecha**: 2025-12-28
**Archivo**: `show_config_dashboard.py`

---

## 🎯 PROBLEMA IDENTIFICADO

El dashboard mostraba parámetros como "activos" (en verde con `True`) cuando en realidad **NO se utilizaban** debido a que un filtro superior estaba deshabilitado.

### Ejemplo del Problema:

```
USE_TIME_IN_MARKET = False (❌ Modo INACTIVO)
  ↓
USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE = True (✅ Mostraba como activo)
USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET = True (✅ Mostraba como activo)
TP_IN_TIME_IN_MARKET = 100 (✅ Mostraba como activo)
```

**Problema**: Estos parámetros están en `True` pero **NO SE USAN** porque `USE_TIME_IN_MARKET = False`.

---

## ✅ SOLUCIÓN IMPLEMENTADA

### 1. **Visualización con Jerarquía de Dependencias**

Ahora el dashboard muestra claramente cuando un parámetro está configurado pero **NO se usa** por el filtro superior:

- **Color gris** (alpha/desaturado) para parámetros inactivos
- **Fondo gris claro** para secciones deshabilitadas
- **Etiqueta ⚠️ "NO SE USA"** en la descripción
- **Opacidad reducida** (0.5-0.6) para elementos inactivos

### 2. **Nueva Clase CSS: `.inactive`**

Agregada clase CSS para valores que están en `True` pero no se aplican:

```css
.param-value.inactive {
    background: #f1f5f9;      /* Gris claro */
    color: #94a3b8;           /* Texto gris */
    border: 1px dashed #cbd5e1; /* Borde punteado */
}
```

### 3. **Lógica de Visualización Mejorada**

#### Diagrama de Flujo:

```python
# Paso 1: USE_TIME_IN_MARKET
<div class="flow-step {'active' if use_time_in_market else 'inactive'}">
    {"✅ Modo activo" if use_time_in_market else "❌ Modo INACTIVO → Parámetros de abajo NO SE USAN"}
</div>

# Paso 2: JSON Optimization (depende de USE_TIME_IN_MARKET)
<div class="flow-step {'inactive' if not use_time_in_market else ...}"
     style="{'opacity: 0.5; background: #f8fafc;' if not use_time_in_market else ''}">
    {("⚠️ NO SE USA (filtro superior deshabilitado)" if not use_time_in_market else ...)}
</div>
```

#### Tabla de Parámetros:

```python
<h3>{"✅ Time-in-Market (ACTIVO)" if use_time_in_market
     else "❌ Time-in-Market (DESHABILITADO - parámetros no se usan)"}</h3>

<table style="{'opacity: 1;' if use_time_in_market else 'opacity: 0.5; background: #f8fafc;'}">
    <tr style="{'opacity: 1;' if use_time_in_market else 'opacity: 0.6;'}">
        <td>USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE</td>
        <td>
            <span class="param-value {'inactive' if not use_time_in_market else ...}">
                {str(use_json_optimization)}
            </span> -
            {("⚠️ NO SE USA (USE_TIME_IN_MARKET=False)" if not use_time_in_market else ...)}
        </td>
    </tr>
</table>
```

---

## 📊 EJEMPLOS DE VISUALIZACIÓN

### Caso 1: `USE_TIME_IN_MARKET = False` (ACTUAL)

```
┌─────────────────────────────────────────────────────┐
│ ❌ Time-in-Market (DESHABILITADO - no se usan)     │
├─────────────────────────────────────────────────────┤
│ USE_TIME_IN_MARKET: False                          │
│   ❌ Modo INACTIVO → Todos los parámetros de       │
│      abajo NO SE USAN                               │
├─────────────────────────────────────────────────────┤
│ (Opacidad 0.5, fondo gris)                         │
│ USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE: True    │
│   ⚠️ NO SE USA (USE_TIME_IN_MARKET=False)          │
│                                                     │
│ USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET: True         │
│   ⚠️ NO SE USA (USE_TIME_IN_MARKET=False)          │
│                                                     │
│ TP_IN_TIME_IN_MARKET: 100                          │
│   ⚠️ NO SE USA (USE_TIME_IN_MARKET=False)          │
└─────────────────────────────────────────────────────┘
```

### Caso 2: `USE_TIME_IN_MARKET = True`

```
┌─────────────────────────────────────────────────────┐
│ ✅ Time-in-Market (ACTIVO)                         │
├─────────────────────────────────────────────────────┤
│ USE_TIME_IN_MARKET: True                           │
│   ✅ Modo activo                                    │
├─────────────────────────────────────────────────────┤
│ (Opacidad 1.0, colores normales)                   │
│ USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE: True    │
│   ✅ Carga desde JSON                               │
│                                                     │
│ USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET: True         │
│   ✅ SL protector habilitado                        │
│                                                     │
│ TP_IN_TIME_IN_MARKET: 100                          │
│   ✅ Se aplica (cierra si se alcanza)               │
└─────────────────────────────────────────────────────┘
```

---

## 🎨 ELEMENTOS VISUALES

### Estados de Parámetros:

1. **ACTIVO** (`.param-value.true`):
   - Fondo: Verde claro (`#d1fae5`)
   - Texto: Verde oscuro (`#065f46`)
   - Mensaje: "✅ [descripción]"

2. **INACTIVO por Filtro Superior** (`.param-value.inactive`):
   - Fondo: Gris claro (`#f1f5f9`)
   - Texto: Gris medio (`#94a3b8`)
   - Borde: Punteado (`1px dashed #cbd5e1`)
   - Mensaje: "⚠️ NO SE USA (filtro superior deshabilitado)"

3. **DESHABILITADO** (`.param-value.false`):
   - Fondo: Rojo claro (`#fee2e2`)
   - Texto: Rojo oscuro (`#991b1b`)
   - Mensaje: "❌ [descripción]"

### Secciones Completas:

- **Activas**: `opacity: 1`, fondo blanco
- **Inactivas**: `opacity: 0.5`, fondo gris (`#f8fafc`)

---

## 🔗 JERARQUÍA DE DEPENDENCIAS

### Flujo de Decisión:

```
┌────────────────────────────────────────┐
│ USE_TIME_IN_MARKET = ?                │
└────────────┬───────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
  False             True
    │                 │
    ▼                 ▼
┌──────────┐    ┌────────────────────────┐
│ TP/SL    │    │ Time-in-Market Mode   │
│ Mode     │    │                        │
│ ACTIVO   │    │ - JSON optimization    │
│          │    │ - Protective SL        │
│          │    │ - Optional TP          │
└──────────┘    └────────────────────────┘
```

### Parámetros que Dependen de `USE_TIME_IN_MARKET = True`:

1. `USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE`
2. `TIME_IN_MARKET_MINUTES`
3. `USE_TP_ALLOWED_IN_TIME_IN_MARKET`
4. `TP_IN_TIME_IN_MARKET`
5. `USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET`
6. `MAX_SL_ALLOWED_IN_TIME_IN_MARKET`

**Si `USE_TIME_IN_MARKET = False`**: TODOS estos parámetros se muestran con estilo "inactivo" y mensaje "⚠️ NO SE USA".

---

## 📝 CÓDIGO MODIFICADO

### Archivos Actualizados:

1. **`show_config_dashboard.py`**:
   - Líneas 309-313: Nuevo estilo CSS `.param-value.inactive`
   - Líneas 474-502: Diagrama de flujo con opacidad condicional
   - Líneas 520-550: Tabla Time-in-Market con estados inactivos
   - Líneas 552-578: Tabla TP/SL con opacidad inversa

---

## ✅ BENEFICIOS

1. **Claridad Visual**: El usuario ve inmediatamente qué parámetros se están usando realmente
2. **Prevención de Errores**: Evita confusión sobre parámetros que están en `True` pero no se aplican
3. **Jerarquía Clara**: El flujo de decisión muestra las dependencias entre parámetros
4. **Documentación Visual**: El dashboard es autoexplicativo sobre la lógica de configuración

---

## 🚀 RESULTADO FINAL

El dashboard ahora refleja **exactamente** cómo funciona el código:

- Si `USE_TIME_IN_MARKET = False` → Usa TP/SL tradicional (125pts/75pts)
- Si `USE_TIME_IN_MARKET = True` → Usa tiempo de mercado con opcionales TP/SL protectores

**No más ambigüedad**: El estado visual coincide 100% con la lógica real del algoritmo.

---

## 📖 DOCUMENTACIÓN RELACIONADA

- [config.py](config.py) - Configuración principal
- [strat_vwap_momentum.py](strat_vwap_momentum.py) - Lógica de estrategia
- [TREND_FILTER_IMPLEMENTATION.md](TREND_FILTER_IMPLEMENTATION.md) - Filtro de tendencia
- [FILTERS_IMPLEMENTATION_SUMMARY.md](FILTERS_IMPLEMENTATION_SUMMARY.md) - Resumen de filtros

---

**Actualización completada exitosamente!** ✅

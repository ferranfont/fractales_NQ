# NinjaTrader Strategy - Grid Entry & Time Management Features

## 📋 Resumen de Nuevas Funcionalidades

La estrategia `AAvwap_momentum.cs` ha sido actualizada con dos funcionalidades críticas:

### 1. **Grid Entry System** (Sistema de Entradas en Grid)
### 2. **Close All Trades at Time** (Cierre Automático por Hora)

---

## 🔢 1. GRID ENTRY SYSTEM

### ¿Qué es?

El sistema de Grid permite colocar **múltiples órdenes límite** a diferentes niveles de precio después de la entrada principal. Esto permite:

- **Promediar el precio de entrada** si el mercado retrocede
- **Aumentar la posición** en niveles favorables
- **Mejorar el riesgo/recompensa** general

### Parámetros Configurables (Grupo 5: Grid Entry System)

| Parámetro | Tipo | Rango | Default | Descripción |
|-----------|------|-------|---------|-------------|
| **Use Grid Entry** | bool | True/False | `False` | Activa/desactiva el sistema de grid |
| **Grid Step (Points)** | int | 1-∞ | `60` | Distancia en puntos entre cada nivel de grid |
| **Number of Grid Steps** | int | 1-10 | `1` | Cantidad de órdenes límite adicionales |

### Cómo Funciona

#### **LONG Entry Example:**
```
Main Entry: 20000 (Green Dot Signal)
Grid Step: 60 points
Number of Steps: 2

Grid Orders:
- Grid 1: Limit BUY at 19940 (20000 - 60)
- Grid 2: Limit BUY at 19880 (20000 - 120)
```

#### **SHORT Entry Example:**
```
Main Entry: 20000 (Red Dot Signal)
Grid Step: 60 points
Number of Steps: 2

Grid Orders:
- Grid 1: Limit SELL at 20060 (20000 + 60)
- Grid 2: Limit SELL at 20120 (20000 + 120)
```

### 🔴 IMPORTANTE: Stop Loss Compartido

**Todas las entradas de grid comparten el MISMO nivel de Stop Loss de la posición principal.**

#### Ejemplo Práctico (LONG):
```
Main Entry: 20000
SL Points: 75
Main SL Level: 19925 (20000 - 75)

Grid 1 fills at: 19940
- TP: 20065 (19940 + 125)  ← Calculado desde SU fill
- SL: 19925 (SAME as main)  ← NO es 19865 (19940-75)

Grid 2 fills at: 19880
- TP: 20005 (19880 + 125)  ← Calculado desde SU fill
- SL: 19925 (SAME as main)  ← NO es 19805 (19880-75)
```

**Beneficio:** Evita que las entradas grid tengan SL demasiado amplios.

### Visualización en Chart

- **Niveles de Grid:** Líneas horizontales punteadas (verde para LONG, rojo para SHORT)
- **Órdenes activas:** Visibles en el DOM de NinjaTrader

---

## ⏰ 2. CLOSE ALL TRADES AT TIME

### ¿Qué es?

Cierra automáticamente **todas las posiciones abiertas** a una hora específica del día. Útil para:

- **Evitar riesgo nocturno** (no dejar posiciones overnight)
- **Control de exposición** fuera de horario óptimo
- **Gestión de riesgo** en eventos de alta volatilidad

### Parámetros Configurables (Grupo 6: Time Management)

| Parámetro | Tipo | Rango | Default | Descripción |
|-----------|------|-------|---------|-------------|
| **Close All at Time** | bool | True/False | `False` | Activa/desactiva cierre automático |
| **Close All Hour** | int | 0-23 | `22` | Hora de cierre (formato 24h) |
| **Close All Minute** | int | 0-59 | `0` | Minuto de cierre |

### Cómo Funciona

#### Ejemplo 1: Cierre a las 22:00 (10 PM)
```
Close All Hour: 22
Close All Minute: 0

→ A las 22:00:00, cierra todas las posiciones (LONG o SHORT)
→ Cancela todas las órdenes grid pendientes
```

#### Ejemplo 2: Cierre a las 15:30 (3:30 PM)
```
Close All Hour: 15
Close All Minute: 30

→ A las 15:30:00, cierra todas las posiciones
→ Útil para evitar eventos de alta volatilidad (cierre de sesión)
```

### Comportamiento

1. **Verifica cada barra** si se alcanzó la hora de cierre
2. **Cierra al mercado** todas las posiciones abiertas
3. **Cancela órdenes pendientes** de grid automáticamente
4. **Señal de salida:** "Time_Close"

---

## 📊 CONFIGURACIÓN RECOMENDADA

### Perfil Conservador (Control de Riesgo)
```
Grid Entry System:
✅ Use Grid Entry: True
   Grid Step: 90 points  (más espaciado = menos fills)
   Number of Steps: 1    (solo 1 nivel adicional)

Time Management:
✅ Close All at Time: True
   Close All Hour: 22    (10 PM - antes de overnight)
   Close All Minute: 0
```

### Perfil Agresivo (Máximo P&L)
```
Grid Entry System:
✅ Use Grid Entry: True
   Grid Step: 60 points  (más denso = más fills)
   Number of Steps: 2    (2 niveles adicionales)

Time Management:
❌ Close All at Time: False  (deja correr hasta TP/SL)
```

### Perfil Sin Grid (Opción B del análisis)
```
Grid Entry System:
❌ Use Grid Entry: False

Time Management:
✅ Close All at Time: True
   Close All Hour: 22
   Close All Minute: 0
```

---

## 🔧 INSTALACIÓN EN NINJATRADER 8

### Paso 1: Importar Estrategia
1. Abre NinjaTrader 8
2. Tools → Import → NinjaScript Add-On
3. Selecciona `AAvwap_momentum.cs`
4. Compila (F5 en NinjaScript Editor)

### Paso 2: Configurar en Chart
1. Aplica la estrategia a un chart de NQ
2. Ve a Strategy Parameters
3. Configura los grupos:
   - **1. VWAP Parameters**
   - **2. Exit Parameters**
   - **3. Entry Filters**
   - **4. Trading Hours**
   - **5. Grid Entry System** ← NUEVO
   - **6. Time Management** ← NUEVO

### Paso 3: Validar Configuración
- Activa `TraceOrders = true` para debugging
- Revisa Output Window para ver órdenes grid
- Verifica en DOM que las órdenes límite se colocan correctamente

---

## ⚠️ ADVERTENCIAS IMPORTANTES

### 1. **Gestión de Riesgo con Grid**
- Cada entrada grid **aumenta tu exposición**
- Con 1 contrato main + 2 grid steps = **3 contratos máximo**
- Ajusta tu tamaño de posición en consecuencia

### 2. **Slippage en Cierre por Tiempo**
- El cierre automático usa **órdenes de mercado**
- Puede haber slippage si el mercado está volátil
- Considera cerrar 5-10 minutos ANTES de eventos importantes

### 3. **Grid en Mercados Rápidos**
- En alta volatilidad, todos los grid steps pueden llenar RÁPIDO
- Puedes terminar con posición 3x más grande de lo esperado
- Usa `Number of Grid Steps = 1` en días de NFP, FOMC, CPI

### 4. **Compatibilidad con Python Config**
- Los parámetros coinciden con `config.py`:
  - `UseGridEntry` ↔ `USE_ENTRY_GRID`
  - `GridStepPoints` ↔ `GRID_STEP`
  - `NumberOfGridSteps` ↔ `NUMBER_OF_GRID_STEPS`
- Mantén sincronizadas ambas configuraciones para backtests consistentes

---

## 📈 EJEMPLOS DE USO

### Escenario 1: Trading Diurno Conservador
```
Use Grid Entry: True
Grid Step: 90
Number of Steps: 1

Close All at Time: True
Close All Hour: 21
Close All Minute: 30

→ Resultado: 1 grid adicional, cierre a 9:30 PM
→ Exposición máxima: 2 contratos
→ Sin riesgo overnight
```

### Escenario 2: Trading Agresivo 24h
```
Use Grid Entry: True
Grid Step: 60
Number of Steps: 2

Close All at Time: False

→ Resultado: 2 grid adicionales, sin cierre automático
→ Exposición máxima: 3 contratos
→ Trades pueden correr toda la noche hasta TP/SL
```

### Escenario 3: Sin Grid, Solo Time Close
```
Use Grid Entry: False

Close All at Time: True
Close All Hour: 22
Close All Minute: 0

→ Resultado: Entrada única, cierre a 10 PM
→ Exposición máxima: 1 contrato
→ Máximo control de riesgo
```

---

## 🐛 TROUBLESHOOTING

### Problema: Las órdenes grid no se colocan
**Solución:**
1. Verifica que `Use Grid Entry = True`
2. Revisa Output Window para errores de orden
3. Confirma que tienes suficiente margen para múltiples contratos

### Problema: El cierre automático no funciona
**Solución:**
1. Verifica que `Use Close All at Time = True`
2. Confirma que la hora está en formato 24h (22 = 10 PM, NO "22:00 PM")
3. Revisa que `Calculate = OnBarClose` (por defecto)

### Problema: SL de grid muy amplio
**Solución:**
- Esto es NORMAL y CORRECTO
- Grid entries usan el SL de la posición principal
- NO calculan SL desde su propio fill price
- Ejemplo: Grid fill 19940, main SL 19925 → SL solo 15 puntos (no 75)

---

## 📞 SOPORTE

Para preguntas o problemas:
1. Revisa este README
2. Comprueba logs en NinjaTrader Output Window
3. Verifica configuración Python en `config.py` para consistencia

---

## 🎯 RESUMEN RÁPIDO

**Grid Entry:**
- ✅ Múltiples entradas límite a diferentes niveles
- ✅ SL compartido por todas las entradas (nivel de main position)
- ✅ TP individual calculado desde cada fill
- ✅ Configurable: ON/OFF, steps, distancia

**Time Close:**
- ✅ Cierre automático a hora específica
- ✅ Cancela órdenes pendientes
- ✅ Control total de exposición temporal

**Beneficios combinados:**
- 🎯 Mejor precio promedio de entrada
- 🛡️ Control estricto de riesgo temporal
- 📊 Flexibilidad total de configuración
- 🔄 Compatible con backtest Python

---

**Versión:** 2.0
**Fecha:** 2026-01-02
**Autor:** Claude Code
**Estrategia Base:** VWAP Momentum (Green/Red Dots)

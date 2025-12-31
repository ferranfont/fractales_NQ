# Sistema de Doble Filtro Horario - Explicación

## 🎯 CONCEPTO

El sistema ahora tiene **DOS filtros horarios que trabajan JUNTOS** (no son excluyentes):

1. **Filtro Genérico** (rango horario amplio) - SIEMPRE ACTIVO
2. **Filtro Específico** (horas óptimas) - OPCIONAL

---

## ⚙️ CONFIGURACIÓN

### Filtro 1: Rango Horario Genérico (SIEMPRE ACTIVO)

```python
VWAP_MOMENTUM_STRAT_START_HOUR = "00:00:00"  # Inicio
VWAP_MOMENTUM_STRAT_END_HOUR = "22:59:59"    # Fin
```

**Propósito**: Define una ventana amplia de trading (ej: "no operar durante la noche asiática")

**Ejemplos de uso**:
- `"09:30:00"` a `"16:00:00"` → Solo sesión regular de USA
- `"00:00:00"` a `"22:59:59"` → Todo el día excepto última hora
- `"08:00:00"` a `"20:00:00"` → Horario extendido

---

### Filtro 2: Horas Óptimas (OPCIONAL)

```python
USE_ONLY_MOMENTUM_ALLOWED_HOURS = True  # True = activar filtro específico
VWAP_MOMENTUM_ALLOWED_HOURS = [0, 1, 3, 4, 6, 10, 12, 13, 16, 17, 18]
```

**Propósito**: Dentro del rango genérico, solo operar en las horas más rentables

**Modos**:
- `USE_ONLY_MOMENTUM_ALLOWED_HOURS = True` → Usa lista de horas óptimas
- `USE_ONLY_MOMENTUM_ALLOWED_HOURS = False` → Solo usa rango genérico

---

## 🔄 CÓMO FUNCIONAN JUNTOS (Lógica AND)

Los filtros se aplican en **CASCADA** - ambos deben cumplirse:

### Paso 1: Filtro Genérico
```python
# Hora actual debe estar entre START_HOUR y END_HOUR
if current_time >= "00:00:00" AND current_time <= "22:59:59":
    # ✅ Pasa al siguiente filtro
else:
    # ❌ Rechazar entrada
```

### Paso 2: Filtro Específico (solo si está activado)
```python
if USE_ONLY_MOMENTUM_ALLOWED_HOURS == True:
    if current_hour in [0, 1, 3, 4, 6, 10, 12, 13, 16, 17, 18]:
        # ✅ Hora permitida - ejecutar trade
    else:
        # ❌ Hora no óptima - rechazar entrada
else:
    # ✅ Filtro específico desactivado - ejecutar trade
```

---

## 📊 EJEMPLOS PRÁCTICOS

### Ejemplo 1: Filtro Específico ACTIVADO

**Config**:
```python
VWAP_MOMENTUM_STRAT_START_HOUR = "00:00:00"
VWAP_MOMENTUM_STRAT_END_HOUR = "22:59:59"
USE_ONLY_MOMENTUM_ALLOWED_HOURS = True
VWAP_MOMENTUM_ALLOWED_HOURS = [0, 1, 3, 4, 6, 10, 12, 13, 16, 17, 18]
```

**Resultado**:
| Hora | Filtro Genérico | Filtro Específico | ¿Opera? |
|------|----------------|-------------------|---------|
| 00:00 | ✅ (dentro 00-22) | ✅ (en lista) | **SÍ** |
| 01:00 | ✅ (dentro 00-22) | ✅ (en lista) | **SÍ** |
| 02:00 | ✅ (dentro 00-22) | ❌ (no en lista) | **NO** |
| 10:00 | ✅ (dentro 00-22) | ✅ (en lista) | **SÍ** |
| 20:00 | ✅ (dentro 00-22) | ❌ (no en lista) | **NO** |
| 23:00 | ❌ (fuera 00-22) | N/A | **NO** |

---

### Ejemplo 2: Filtro Específico DESACTIVADO

**Config**:
```python
VWAP_MOMENTUM_STRAT_START_HOUR = "09:30:00"
VWAP_MOMENTUM_STRAT_END_HOUR = "16:00:00"
USE_ONLY_MOMENTUM_ALLOWED_HOURS = False  # ⬅️ DESACTIVADO
```

**Resultado**:
| Hora | Filtro Genérico | Filtro Específico | ¿Opera? |
|------|----------------|-------------------|---------|
| 08:00 | ❌ (antes 09:30) | N/A | **NO** |
| 09:30 | ✅ (dentro 09:30-16:00) | ✅ (desactivado) | **SÍ** |
| 10:00 | ✅ (dentro 09:30-16:00) | ✅ (desactivado) | **SÍ** |
| 14:00 | ✅ (dentro 09:30-16:00) | ✅ (desactivado) | **SÍ** |
| 16:00 | ✅ (dentro 09:30-16:00) | ✅ (desactivado) | **SÍ** |
| 17:00 | ❌ (después 16:00) | N/A | **NO** |

---

### Ejemplo 3: Combinación Restrictiva

**Config**:
```python
VWAP_MOMENTUM_STRAT_START_HOUR = "09:00:00"
VWAP_MOMENTUM_STRAT_END_HOUR = "17:00:00"
USE_ONLY_MOMENTUM_ALLOWED_HOURS = True
VWAP_MOMENTUM_ALLOWED_HOURS = [10, 13, 16]
```

**Resultado**:
| Hora | Filtro Genérico | Filtro Específico | ¿Opera? |
|------|----------------|-------------------|---------|
| 08:00 | ❌ (antes 09:00) | N/A | **NO** |
| 09:00 | ✅ (dentro 09-17) | ❌ (no en lista) | **NO** |
| 10:00 | ✅ (dentro 09-17) | ✅ (en lista) | **SÍ** ✅ |
| 11:00 | ✅ (dentro 09-17) | ❌ (no en lista) | **NO** |
| 13:00 | ✅ (dentro 09-17) | ✅ (en lista) | **SÍ** ✅ |
| 16:00 | ✅ (dentro 09-17) | ✅ (en lista) | **SÍ** ✅ |
| 17:00 | ✅ (dentro 09-17) | ❌ (no en lista) | **NO** |
| 18:00 | ❌ (después 17:00) | N/A | **NO** |

**Solo opera 3 horas**: 10:00, 13:00, 16:00

---

## 🎛️ CASOS DE USO

### Caso 1: Máxima Restricción (Actual - Sortino Optimized)
```python
VWAP_MOMENTUM_STRAT_START_HOUR = "00:00:00"
VWAP_MOMENTUM_STRAT_END_HOUR = "22:59:59"
USE_ONLY_MOMENTUM_ALLOWED_HOURS = True
VWAP_MOMENTUM_ALLOWED_HOURS = [0, 1, 3, 4, 6, 10, 12, 13, 16, 17, 18]
```
**Resultado**: Solo opera 11 horas específicas (las mejores según backtesting)

---

### Caso 2: Solo Horario Regular USA
```python
VWAP_MOMENTUM_STRAT_START_HOUR = "09:30:00"
VWAP_MOMENTUM_STRAT_END_HOUR = "16:00:00"
USE_ONLY_MOMENTUM_ALLOWED_HOURS = False
```
**Resultado**: Opera toda la sesión regular (6.5 horas continuas)

---

### Caso 3: Sesión Regular + Filtro Específico
```python
VWAP_MOMENTUM_STRAT_START_HOUR = "09:30:00"
VWAP_MOMENTUM_STRAT_END_HOUR = "16:00:00"
USE_ONLY_MOMENTUM_ALLOWED_HOURS = True
VWAP_MOMENTUM_ALLOWED_HOURS = [10, 12, 13, 16]
```
**Resultado**: Solo opera 4 horas dentro de la sesión regular

---

### Caso 4: Evitar Horas de Asia
```python
VWAP_MOMENTUM_STRAT_START_HOUR = "06:00:00"  # 6 AM EST
VWAP_MOMENTUM_STRAT_END_HOUR = "22:00:00"    # 10 PM EST
USE_ONLY_MOMENTUM_ALLOWED_HOURS = True
VWAP_MOMENTUM_ALLOWED_HOURS = [6, 10, 12, 13, 16, 17, 18]
```
**Resultado**: Evita horas nocturnas + filtra horas óptimas

---

## 💡 VENTAJAS DEL SISTEMA DUAL

### ✅ Flexibilidad
- Puedes definir una ventana amplia (ej: horario USA) y luego refinar con horas específicas
- No necesitas cambiar el rango genérico si solo quieres probar diferentes horas óptimas

### ✅ Compatibilidad
- El código antiguo sigue funcionando (solo usa filtro genérico)
- El nuevo filtro es totalmente opcional

### ✅ Testing
- Fácil activar/desactivar el filtro específico para A/B testing
- Puedes comparar "todas las horas en rango" vs "solo horas óptimas"

### ✅ Mantenimiento
- `START_HOUR/END_HOUR` → Define política general de trading
- `ALLOWED_HOURS` → Define optimización basada en datos

---

## 🔧 CÓDIGO INTERNO

### Lógica de Filtrado (strat_vwap_momentum.py)

```python
# Parsear rango horario genérico
start_time = datetime.strptime(START_TRADING_HOUR, "%H:%M:%S").time()
end_time = datetime.strptime(END_TRADING_HOUR, "%H:%M:%S").time()

for idx, bar in df.iterrows():
    current_time = bar['timestamp'].time()

    # FILTRO 1: Rango genérico (siempre activo)
    within_trading_hours = start_time <= current_time <= end_time

    if open_position is None and within_trading_hours:
        # FILTRO 2: Horas específicas (opcional)
        if USE_ONLY_MOMENTUM_ALLOWED_HOURS:
            entry_hour = bar['timestamp'].hour
            if entry_hour not in VWAP_MOMENTUM_ALLOWED_HOURS:
                continue  # Rechazar esta hora

        # Si llega aquí: ambos filtros OK → buscar señal
        if bar['short_signal'] and VWAP_MOMENTUM_SHORT_ALLOWED:
            enter_short()
```

---

## 📊 ESTADO ACTUAL

**Configuración Activa**:
```python
# Filtro genérico: todo el día menos última hora
VWAP_MOMENTUM_STRAT_START_HOUR = "00:00:00"
VWAP_MOMENTUM_STRAT_END_HOUR = "22:59:59"

# Filtro específico: ACTIVADO con horas óptimas
USE_ONLY_MOMENTUM_ALLOWED_HOURS = True
VWAP_MOMENTUM_ALLOWED_HOURS = [0, 1, 3, 4, 6, 10, 12, 13, 16, 17, 18]

# Dirección: solo SHORT
VWAP_MOMENTUM_LONG_ALLOWED = False
VWAP_MOMENTUM_SHORT_ALLOWED = True
```

**Resultado**: Opera solo en 11 horas específicas, solo trades SHORT

---

## 🎯 RESUMEN

| Componente | Función | Status |
|-----------|---------|--------|
| **START_HOUR/END_HOUR** | Filtro genérico (rango amplio) | Siempre activo |
| **USE_ONLY_MOMENTUM_ALLOWED_HOURS** | Activador del filtro específico | True/False |
| **ALLOWED_HOURS** | Lista de horas óptimas | Solo si anterior = True |
| **Lógica** | AND (ambos deben cumplirse) | Cascada |

**Puedes usar**:
- ✅ Solo filtro genérico (`USE_ONLY_MOMENTUM_ALLOWED_HOURS = False`)
- ✅ Ambos filtros juntos (`USE_ONLY_MOMENTUM_ALLOWED_HOURS = True`)
- ❌ Solo filtro específico (siempre necesitas el rango genérico)

**Ventaja**: Máxima flexibilidad sin perder compatibilidad hacia atrás.

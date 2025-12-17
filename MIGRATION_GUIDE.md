# Migration Guide: Single Day → Date Range Analysis

## Overview

The system has been updated to support date range analysis (2015-01-02 to 2025-04-25) instead of single-day analysis. Legacy single-day functions are still available for backward compatibility.

## Key Changes

### 1. Configuration ([config.py](config.py))

**Before:**
```python
DIA = "2015-01-05"
```

**After:**
```python
START_DATE = "2015-01-02"
END_DATE = "2025-04-25"
```

### 2. Main Execution ([main_quant.py](main_quant.py))

**Before:**
```python
python main_quant.py  # Analyzed DIA = "2015-01-05"
```

**After:**
```python
python main_quant.py  # Analyzes START_DATE to END_DATE
```

The system now uses `main_quant_range(START_DATE, END_DATE)` instead of `main_quant(DIA)`.

### 3. New Functions

#### [find_fractals.py](find_fractals.py)
- **New:** `load_date_range(start_date, end_date)` - Loads and concatenates CSVs for the date range
- **New:** `process_fractals_range(start_date, end_date)` - Processes fractals for date range
- **Legacy:** `process_fractals(dia)` - Still available for single-day analysis

#### [analyze_rsi.py](analyze_rsi.py)
- **New:** `analyze_rsi_levels_range(df, start_date, end_date)` - Analyzes RSI for DataFrame
- **Legacy:** `analyze_rsi_levels(dia)` - Still available for single-day analysis

#### [analyze_fibonacci.py](analyze_fibonacci.py)
- **New:** `analyze_fibonacci_range(df_fractals_major, start_date, end_date)` - Analyzes Fibonacci for DataFrame
- **Legacy:** `analyze_fibonacci(dia)` - Still available for single-day analysis

#### [plot_day.py](plot_day.py)
- **New:** `plot_range_chart(df, df_fractals_minor, df_fractals_major, start_date, end_date, ...)` - Plots date range
- **Legacy:** `plot_day_chart(dia, ...)` - Still available for single-day plotting

## Data Flow

### New Date Range Pipeline

```
1. main_quant_range(START_DATE, END_DATE)
   ↓
2. process_fractals_range()
   → load_date_range() → Loads all CSVs in range
   → detect_fractals() → Detects fractals on combined data
   → Returns: df, df_fractals_minor, df_fractals_major
   ↓
3. analyze_rsi_levels_range(df from step 2)
   → calculate_rsi() → Computes RSI
   → Returns: df_with_rsi, statistics
   ↓
4. analyze_fibonacci_range(df_fractals_major from step 2)
   → calculate_fibonacci_levels() → Computes Fibonacci levels
   → Returns: fibo_levels dict
   ↓
5. plot_range_chart(df_with_rsi, fractals, ...)
   → Creates interactive Plotly chart
   → Saves as gc_START-DATE_END-DATE.html
```

### Legacy Single Day Pipeline

```
1. main_quant(DIA)
   ↓
2. process_fractals(DIA)
   → Loads single CSV
   → Detects fractals
   ↓
3. analyze_rsi_levels(DIA)
   → Loads single CSV
   → Calculates RSI
   ↓
4. analyze_fibonacci(DIA)
   → Loads fractals CSV
   → Calculates Fibonacci
   ↓
5. plot_day_chart(DIA, ...)
   → Creates chart
   → Saves as gc_DIA.html
```

## Output Files

### Date Range Outputs
- `outputs/fractals/gc_fractals_minor_2015-01-02_2025-04-25.csv`
- `outputs/fractals/gc_fractals_major_2015-01-02_2025-04-25.csv`
- `outputs/gc_2015-01-02_2025-04-25.html`

### Legacy Single Day Outputs
- `outputs/fractals/gc_fractals_minor_2015-01-05.csv`
- `outputs/fractals/gc_fractals_major_2015-01-05.csv`
- `outputs/gc_2015-01-05.html`

## Migration Steps

If you want to analyze a specific date range:

1. **Edit [config.py](config.py):**
   ```python
   START_DATE = "2024-01-01"
   END_DATE = "2024-12-31"
   ```

2. **Run the pipeline:**
   ```bash
   python main_quant.py
   ```

If you want to analyze a single day (legacy):

1. **Use the old function directly:**
   ```python
   from main_quant import main_quant
   result = main_quant("2015-01-05")
   ```

## Breaking Changes

None! The old single-day functions are still available and functional. The system defaults to date range analysis when running `main_quant.py` directly.

## Benefits of Date Range Analysis

1. **Continuous Fractal Detection:** Fractals are detected across day boundaries, providing more accurate swing points
2. **Better Fibonacci Levels:** Uses the last 2 MAJOR fractals from the entire range, not just a single day
3. **Comprehensive RSI Analysis:** RSI statistics calculated across the entire period
4. **Single Chart:** One interactive chart showing all data for the period
5. **Performance:** Processes all data in one pass instead of day-by-day

## Technical Notes

- The `load_date_range()` function automatically handles missing dates (weekends, holidays)
- DataFrames are concatenated with `ignore_index=True` to ensure continuous indexing
- RSI calculation handles the concatenated DataFrame correctly with rolling windows
- Fractal detection works seamlessly across the concatenated data
- The ZigZag algorithm maintains state across the entire date range

## Example Usage

### Analyze Full Historical Range
```python
# In config.py
START_DATE = "2015-01-02"
END_DATE = "2025-04-25"

# Run
python main_quant.py
```

### Analyze Specific Year
```python
# In config.py
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"

# Run
python main_quant.py
```

### Analyze Single Day (Legacy)
```python
from main_quant import main_quant
result = main_quant("2024-05-30")
```

### Run Individual Modules
```bash
# All modules now use START_DATE and END_DATE from config
python find_fractals.py
python analyze_rsi.py
python analyze_fibonacci.py
python plot_day.py
```

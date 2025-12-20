"""
Script principal de análisis cuantitativo para Gold (GC)
Orquesta la ejecución de:
1. Detección de fractales (find_fractals.py)
2. Generación de gráfico (plot_day.py)
"""
from pathlib import Path
from config import (
    START_DATE, END_DATE, DATA_DIR,
    REQUIRE_DOWNTREND, REQUIRE_DIVERGENCE, FIBO_LEVEL_FILTER,
    RSI_PERIOD, RSI_SMOOTH_PERIOD, RSI_RESAMPLE, RSI_RESAMPLE_TO_PERIOD
)
from find_fractals import process_fractals_range
from plot_day import plot_range_chart, calculate_rsi


def main_quant_range(start_date: str, end_date: str):
    """
    Ejecuta el pipeline completo de análisis cuantitativo para un rango de fechas

    Args:
        start_date: Fecha inicial en formato YYYY-MM-DD
        end_date: Fecha final en formato YYYY-MM-DD
    """
    print("\n" + "="*70)
    print("ANÁLISIS CUANTITATIVO - Gold (GC)")
    print("="*70)
    print(f"Rango: {start_date} -> {end_date}")
    print("="*70 + "\n")
 
    # 1. Procesar fractales
    print("\n" + "-"*70)
    print("PASO 1: DETECCIÓN DE FRACTALES")
    print("-"*70)
    fractals_result = process_fractals_range(start_date, end_date)
    if fractals_result is None:
        print("[ERROR] Fallo en detección de fractales")
        return None

    # 2. Calcular RSI
    print("\n" + "-"*70)
    print("PASO 2: CÁLCULO RSI")
    print("-"*70)
    df = fractals_result['df']

    # Determinar regla efectiva de resample
    if isinstance(RSI_RESAMPLE, bool) and RSI_RESAMPLE:
        rsi_resample_rule = RSI_RESAMPLE_TO_PERIOD
    elif isinstance(RSI_RESAMPLE, str) and RSI_RESAMPLE:
        rsi_resample_rule = RSI_RESAMPLE
    else:
        rsi_resample_rule = None

    df['rsi'] = calculate_rsi(df, period=RSI_PERIOD, smooth_period=RSI_SMOOTH_PERIOD,
                              resample_rule=rsi_resample_rule)
    df_valid = df.dropna(subset=['rsi'])

    rsi_min = df_valid['rsi'].min()
    rsi_max = df_valid['rsi'].max()
    rsi_mean = df_valid['rsi'].mean()

    print(f"RSI calculado - Min: {rsi_min:.2f}, Max: {rsi_max:.2f}, Mean: {rsi_mean:.2f}")

    # Fibonacci functionality removed
    fibo_result = None

    # 3. Detectar divergencias y señales de entrada
    print("\n" + "-"*70)
    print("PASO 3: DETECCIÓN DE DIVERGENCIAS")
    print("-"*70)
    from find_entries import find_entry_signals
    from config import FRACTALS_DIR
    import pandas as pd

    divergences = find_entry_signals(
        df,
        fractals_result['df_fractals_major'],
        df_fractals_minor=fractals_result['df_fractals_minor'],
        fibo_levels=fibo_result,
        require_downtrend=REQUIRE_DOWNTREND,
        fibo_level_filter=FIBO_LEVEL_FILTER,
        require_divergence=REQUIRE_DIVERGENCE
    )

    # Guardar divergencias en CSV
    if not divergences.empty:
        output_filename = f"gc_divergences_{start_date}_{end_date}.csv"
        output_path = FRACTALS_DIR / output_filename
        divergences.to_csv(output_path, index=False)
        print(f"\n[OK] Divergencias guardadas en: {output_path}")
    else:
        print("\n[INFO] No se encontraron divergencias")

    # 4. Generar gráfico con toda la información
    print("\n" + "-"*70)
    print("PASO 4: GENERACIÓN DE GRÁFICO")
    print("-"*70)
    plot_result = plot_range_chart(
        df,
        fractals_result['df_fractals_minor'],
        fractals_result['df_fractals_major'],
        start_date,
        end_date,
        rsi_levels=None,
        fibo_levels=fibo_result,
        divergences=divergences
    )
    if plot_result is None:
        print("[ERROR] Fallo en generación de gráfico")
        return None

    # 5. Resumen final
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    print(f"Rango analizado: {start_date} -> {end_date}")
    print(f"Registros procesados: {fractals_result['total_records']}")
    print(f"Fractales MINOR detectados: {fractals_result['minor_count']}")
    print(f"Fractales MAJOR detectados: {fractals_result['major_count']}")
    print(f"RSI medio: {rsi_mean:.2f}")
    if not divergences.empty:
        num_unique_divs = divergences['divergence_id'].nunique()
        print(f"Divergencias alcistas detectadas: {num_unique_divs}")
    else:
        print("Divergencias alcistas detectadas: 0")
    print(f"Gráfico generado: {plot_result['output_path']}")
    print("="*70 + "\n")

    return {
        'start_date': start_date,
        'end_date': end_date,
        'fractals': fractals_result,
        'rsi_mean': rsi_mean,
        'plot': plot_result
    }


def main_quant(dia: str):
    """
    DEPRECATED: Ejecuta el pipeline completo de análisis cuantitativo para un día
    Esta función se mantiene por compatibilidad pero se recomienda usar main_quant_range()

    Args:
        dia: Fecha en formato YYYY-MM-DD
    """
    print("\n[WARNING] Esta función está deprecada. Use main_quant_range() en su lugar.")
    return None


if __name__ == "__main__":
    print("\nIniciando análisis cuantitativo...\n")
    result = main_quant_range(START_DATE, END_DATE)

    if result:
        print("[OK] Análisis completado exitosamente\n")
    else:
        print("[ERROR] El análisis finalizó con errores\n")

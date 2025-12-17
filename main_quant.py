"""
Script principal de análisis cuantitativo para Gold (GC)
Orquesta la ejecución de:
1. Detección de fractales (find_fractals.py)
2. Análisis RSI (analyze_rsi.py)
3. Análisis Fibonacci Retracements (analyze_fibonacci.py)
4. Generación de gráfico (plot_day.py)
"""
from pathlib import Path
from config import START_DATE, END_DATE, DATA_DIR
from find_fractals import process_fractals_range
from analyze_rsi import analyze_rsi_levels_range
from analyze_fibonacci import analyze_fibonacci_range
from plot_day import plot_range_chart


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

    # 2. Analizar niveles RSI (usa el dataframe del paso anterior)
    print("\n" + "-"*70)
    print("PASO 2: ANÁLISIS RSI")
    print("-"*70)
    rsi_result = analyze_rsi_levels_range(fractals_result['df'], start_date, end_date)
    if rsi_result is None:
        print("[ERROR] Fallo en análisis RSI")
        return None

    # 3. Analizar Fibonacci (usa los fractales MAJOR del paso 1)
    print("\n" + "-"*70)
    print("PASO 3: ANÁLISIS FIBONACCI")
    print("-"*70)
    fibo_result = analyze_fibonacci_range(fractals_result['df_fractals_major'], start_date, end_date)
    if fibo_result is None:
        print("[WARNING] No se pudo calcular Fibonacci, continuando sin él...")
        fibo_result = None

    # 4. Generar gráfico con toda la información (usa el df con RSI del paso 2)
    print("\n" + "-"*70)
    print("PASO 4: GENERACIÓN DE GRÁFICO")
    print("-"*70)
    plot_result = plot_range_chart(
        rsi_result['df_with_rsi'],
        fractals_result['df_fractals_minor'],
        fractals_result['df_fractals_major'],
        start_date,
        end_date,
        rsi_levels=rsi_result,
        fibo_levels=fibo_result
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
    print(f"RSI medio: {rsi_result['rsi_mean']:.2f}")
    print(f"Momentos de sobrecompra: {rsi_result['overbought_count']}")
    print(f"Momentos de sobreventa: {rsi_result['oversold_count']}")
    if fibo_result:
        print(f"Fibonacci - Movimientos alcistas detectados: {fibo_result['total_moves']}")
        if fibo_result['total_moves'] > 0:
            for idx, move in enumerate(fibo_result['upward_moves'], 1):
                print(f"  Movimiento #{idx}: {move['swing_low']:.2f} -> {move['swing_high']:.2f} (Rango: {move['range']:.2f})")
    print(f"Gráfico generado: {plot_result['output_path']}")
    print("="*70 + "\n")

    return {
        'start_date': start_date,
        'end_date': end_date,
        'fractals': fractals_result,
        'rsi': rsi_result,
        'fibonacci': fibo_result,
        'plot': plot_result
    }


def main_quant(dia: str):
    """
    DEPRECATED: Ejecuta el pipeline completo de análisis cuantitativo para un día
    Esta función se mantiene por compatibilidad pero se recomienda usar main_quant_range()

    Args:
        dia: Fecha en formato YYYY-MM-DD
    """
    from find_fractals import process_fractals
    from analyze_rsi import analyze_rsi_levels
    from analyze_fibonacci import analyze_fibonacci
    from plot_day import plot_day_chart

    print("\n" + "="*70)
    print("ANÁLISIS CUANTITATIVO - Gold (GC)")
    print("="*70)
    print(f"Día: {dia}")
    print("="*70 + "\n")

    # 1. Verificar que existe el archivo CSV
    csv_path = DATA_DIR / f"gc_{dia}.csv"
    if not csv_path.exists():
        print(f"[ERROR] No existe el archivo CSV para {dia}: {csv_path}")
        print("Abortando análisis.")
        return None

    print(f"[OK] Archivo encontrado: {csv_path.name}\n")

    # 2. Procesar fractales
    print("\n" + "-"*70)
    print("PASO 1: DETECCIÓN DE FRACTALES")
    print("-"*70)
    fractals_result = process_fractals(dia)
    if fractals_result is None:
        print("[ERROR] Fallo en detección de fractales")
        return None

    # 3. Analizar niveles RSI
    print("\n" + "-"*70)
    print("PASO 2: ANÁLISIS RSI")
    print("-"*70)
    rsi_result = analyze_rsi_levels(dia)
    if rsi_result is None:
        print("[ERROR] Fallo en análisis RSI")
        return None

    # 4. Analizar Fibonacci
    print("\n" + "-"*70)
    print("PASO 3: ANÁLISIS FIBONACCI")
    print("-"*70)
    fibo_result = analyze_fibonacci(dia)
    if fibo_result is None:
        print("[WARNING] No se pudo calcular Fibonacci, continuando sin él...")
        fibo_result = None

    # 5. Generar gráfico con toda la información
    print("\n" + "-"*70)
    print("PASO 4: GENERACIÓN DE GRÁFICO")
    print("-"*70)
    plot_result = plot_day_chart(dia, rsi_levels=rsi_result, fibo_levels=fibo_result)
    if plot_result is None:
        print("[ERROR] Fallo en generación de gráfico")
        return None

    # 6. Resumen final
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    print(f"Día analizado: {dia}")
    print(f"Registros procesados: {fractals_result['total_records']}")
    print(f"Fractales MINOR detectados: {fractals_result['minor_count']}")
    print(f"Fractales MAJOR detectados: {fractals_result['major_count']}")
    print(f"RSI medio: {rsi_result['rsi_mean']:.2f}")
    print(f"Momentos de sobrecompra: {rsi_result['overbought_count']}")
    print(f"Momentos de sobreventa: {rsi_result['oversold_count']}")
    if fibo_result:
        # Legacy function still uses old structure with single range
        if 'range' in fibo_result:
            print(f"Fibonacci - Swing Range: {fibo_result['range']:.2f} ({fibo_result['swing_low']:.2f} - {fibo_result['swing_high']:.2f})")
    print(f"Gráfico generado: {plot_result['output_path']}")
    print("="*70 + "\n")

    return {
        'dia': dia,
        'fractals': fractals_result,
        'rsi': rsi_result,
        'fibonacci': fibo_result,
        'plot': plot_result
    }


if __name__ == "__main__":
    print("\nIniciando análisis cuantitativo...\n")
    result = main_quant_range(START_DATE, END_DATE)

    if result:
        print("[OK] Análisis completado exitosamente\n")
    else:
        print("[ERROR] El análisis finalizó con errores\n")

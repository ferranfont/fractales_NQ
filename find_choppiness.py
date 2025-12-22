"""
Cálculo de métricas para análisis de consolidación en fractales
Mide: Rango de precio, ATR de fractales, y tiempo entre fractales
"""
import pandas as pd


def calculate_fractal_metrics(df_fractals, price_range_period=7):
    """
    Calcula métricas de fractales para análisis de consolidación

    Args:
        df_fractals: DataFrame con columnas ['timestamp', 'price', 'type']
        price_range_period: Número de fractales para calcular rango y ATR

    Returns:
        DataFrame con columnas adicionales:
        - 'time_from_prev_minutes': Minutos desde el fractal anterior
        - 'price_diff_from_prev': Distancia en precio desde fractal anterior
        - 'fractal_atr_n': ATR de los últimos N fractales
        - 'price_range_n': Rango (max-min) de los últimos N fractales
        - 'atr_threshold_120': ATR × 1.20 (umbral de consolidación)
        - 'frequency_inverse': 1/tiempo (mayor valor = mayor frecuencia)
        - 'cumulative_frequency_n': Suma acumulada de frecuencias en ventana N
        - 'avg_time_between_fractals_n': Promedio de tiempo entre fractales en ventana N
    """
    df = df_fractals.copy()

    # Asegurar que timestamp es datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 1. Tiempo desde el fractal anterior (en minutos)
    df['time_from_prev_minutes'] = df['timestamp'].diff().dt.total_seconds() / 60.0

    # 2. Distancia en precio desde el fractal anterior
    df['price_diff_from_prev'] = df['price'].diff().abs()

    # 3. ATR de fractales (promedio de distancias de últimos N fractales)
    df['fractal_atr_n'] = df['price_diff_from_prev'].rolling(window=price_range_period).mean()

    # 4. Rango de precio de últimos N fractales (max - min)
    price_max_n = df['price'].rolling(window=price_range_period).max()
    price_min_n = df['price'].rolling(window=price_range_period).min()
    df['price_range_n'] = price_max_n - price_min_n

    # 5. Umbral de consolidación (ATR × 1.20)
    df['atr_threshold_120'] = df['fractal_atr_n'] * 1.20

    # 6. Frecuencia acumulativa de fractales
    # Invertir el tiempo (1/time) para que menor tiempo = mayor frecuencia
    # IMPORTANTE: Usar una ventana pequeña fija (3) para detección inmediata,
    # independiente del parámetro price_range_period que solo afecta ATR/rango
    FREQUENCY_WINDOW = 3  # Ventana pequeña para respuesta inmediata
    df['frequency_inverse'] = 1.0 / df['time_from_prev_minutes']
    df['cumulative_frequency_n'] = df['frequency_inverse'].rolling(window=FREQUENCY_WINDOW).sum()

    # 7. Promedio de tiempo entre fractales (ventana pequeña independiente)
    df['avg_time_between_fractals_n'] = df['time_from_prev_minutes'].rolling(window=FREQUENCY_WINDOW).mean()

    return df


def print_consolidation_table(df_metrics, max_rows=30):
    """
    Imprime tabla formateada de métricas de consolidación

    Args:
        df_metrics: DataFrame con métricas calculadas
        max_rows: Número máximo de filas a mostrar
    """
    # Seleccionar columnas para la tabla
    table_cols = [
        'timestamp', 'type', 'price',
        'time_from_prev_minutes', 'price_diff_from_prev',
        'price_range_n', 'fractal_atr_n', 'atr_threshold_120',
        'cumulative_frequency_n', 'avg_time_between_fractals_n'
    ]

    df_table = df_metrics[table_cols].copy()

    # Formatear para impresión
    print("\n" + "="*170)
    print("TABLA DE MÉTRICAS DE FRACTALES")
    print("="*170)
    print(f"{'#':<4} {'Timestamp':<20} {'Type':<6} {'Price':<8} {'Time(min)':<10} "
          f"{'PriceDiff':<10} {'Range(N)':<10} {'ATR(N)':<10} {'ATR×1.20':<10} "
          f"{'CumFreq(N)':<12} {'AvgTime(N)':<12}")
    print("-"*170)

    for idx, row in df_table.head(max_rows).iterrows():
        time_val = f"{row['time_from_prev_minutes']:.1f}" if pd.notna(row['time_from_prev_minutes']) else "N/A"
        price_diff = f"{row['price_diff_from_prev']:.2f}" if pd.notna(row['price_diff_from_prev']) else "N/A"
        range_val = f"{row['price_range_n']:.2f}" if pd.notna(row['price_range_n']) else "N/A"
        atr_val = f"{row['fractal_atr_n']:.2f}" if pd.notna(row['fractal_atr_n']) else "N/A"
        threshold = f"{row['atr_threshold_120']:.2f}" if pd.notna(row['atr_threshold_120']) else "N/A"
        cum_freq = f"{row['cumulative_frequency_n']:.4f}" if pd.notna(row['cumulative_frequency_n']) else "N/A"
        avg_time = f"{row['avg_time_between_fractals_n']:.1f}" if pd.notna(row['avg_time_between_fractals_n']) else "N/A"

        print(f"{idx:<4} {str(row['timestamp']):<20} {row['type']:<6} {row['price']:<8.1f} "
              f"{time_val:<10} {price_diff:<10} {range_val:<10} {atr_val:<10} {threshold:<10} "
              f"{cum_freq:<12} {avg_time:<12}")

    if len(df_table) > max_rows:
        print(f"... ({len(df_table) - max_rows} filas más)")

    print("="*170)
    print(f"\nTotal fractales: {len(df_table)}")
    print("\nLeyenda:")
    print("  - Time(min): Minutos desde el fractal anterior")
    print("  - PriceDiff: Distancia en precio desde fractal anterior")
    print("  - Range(N): Rango (max-min) de los últimos N fractales")
    print("  - ATR(N): ATR (promedio de distancias) de los últimos N fractales")
    print("  - ATR×1.20: Umbral de consolidación (ATR × 1.20)")
    print("  - CumFreq(N): Frecuencia acumulada (suma de 1/tiempo) en ventana N")
    print("  - AvgTime(N): Promedio de tiempo entre fractales en ventana N")
    print("="*170 + "\n")


if __name__ == "__main__":
    from find_fractals import process_fractals_range
    from config import START_DATE, END_DATE, CONSOLIDATION_PRICE_RANGE_PERIOD

    print("="*70)
    print("TEST: Cálculo de Métricas de Consolidación")
    print("="*70)
    print(f"Periodo: {START_DATE} -> {END_DATE}")

    # Procesar fractales
    fractals_result = process_fractals_range(START_DATE, END_DATE)
    if fractals_result is None:
        print("[ERROR] No se pudieron procesar fractales")
        exit(1)

    # Calcular métricas
    df_metrics = calculate_fractal_metrics(
        fractals_result['df_fractals_minor'],
        price_range_period=CONSOLIDATION_PRICE_RANGE_PERIOD
    )

    # Imprimir tabla
    print_consolidation_table(df_metrics, max_rows=30)

    print("[OK] Test completado")

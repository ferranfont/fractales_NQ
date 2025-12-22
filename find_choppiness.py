"""
Cálculo SIMPLE de tiempo entre fractales - SIN rolling windows
Solo calcula: tiempo desde fractal anterior en SEGUNDOS
"""
import pandas as pd
from config import TRIGGER_THRESHOLD, TRIGGER_PERIODS


def calculate_fractal_metrics(df_fractals):
    """
    Calcula métricas SIMPLES de fractales sin ventanas móviles

    Args:
        df_fractals: DataFrame con columnas ['timestamp', 'price', 'type']

    Returns:
        DataFrame con columnas adicionales:
        - 'time_from_prev_seconds': Segundos desde el fractal anterior
        - 'price_diff_from_prev': Distancia en precio desde fractal anterior
    """
    df = df_fractals.copy()

    # Asegurar que timestamp es datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 1. Tiempo desde el fractal anterior (en SEGUNDOS)
    df['time_from_prev_seconds'] = df['timestamp'].diff().dt.total_seconds()

    # 2. Distancia en precio desde el fractal anterior
    df['price_diff_from_prev'] = df['price'].diff().abs()

    # 3. Calcular frecuencia INVERTIDA (para trigger de consolidación)
    # Invertir: valores bajos de tiempo -> valores ALTOS de frecuencia
    max_time = df['time_from_prev_seconds'].max()
    df['inverted_frequency'] = max_time - df['time_from_prev_seconds']

    # 4. Trigger de consolidación: frecuencia > TRIGGER_THRESHOLD durante TRIGGER_PERIODS fractales consecutivos
    # Parámetros definidos en config.py
    # Marcar fractales donde inverted_frequency > TRIGGER_THRESHOLD
    df['above_threshold'] = (df['inverted_frequency'] > TRIGGER_THRESHOLD).astype(int)

    # Contar cuántos fractales consecutivos están por encima del umbral
    df['consecutive_above'] = df['above_threshold'].rolling(window=TRIGGER_PERIODS).sum()

    # Trigger activo cuando hay 2 o más periodos consecutivos por encima de 200
    df['choppiness_trigger'] = (df['consecutive_above'] >= TRIGGER_PERIODS).astype(int)

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
        'time_from_prev_seconds', 'price_diff_from_prev', 'inverted_frequency', 'choppiness_trigger'
    ]

    df_table = df_metrics[table_cols].copy()

    # Formatear para impresión
    print("\n" + "="*130)
    print("TABLA DE MÉTRICAS DE FRACTALES (SIMPLE)")
    print("="*130)
    print(f"{'#':<4} {'Timestamp':<25} {'Type':<6} {'Price':<10} {'Time(seg)':<12} {'PriceDiff':<12} {'InvFreq':<10} {'Trigger':<8}")
    print("-"*130)

    for idx, row in df_table.head(max_rows).iterrows():
        time_val = f"{row['time_from_prev_seconds']:.0f}" if pd.notna(row['time_from_prev_seconds']) else "N/A"
        price_diff = f"{row['price_diff_from_prev']:.2f}" if pd.notna(row['price_diff_from_prev']) else "N/A"
        inv_freq = f"{row['inverted_frequency']:.0f}" if pd.notna(row['inverted_frequency']) else "N/A"
        trigger = "YES" if row['choppiness_trigger'] == 1 else "NO"

        print(f"{idx:<4} {str(row['timestamp']):<25} {row['type']:<6} {row['price']:<10.1f} "
              f"{time_val:<12} {price_diff:<12} {inv_freq:<10} {trigger:<8}")

    if len(df_table) > max_rows:
        print(f"... ({len(df_table) - max_rows} filas más)")

    print("="*130)
    print(f"\nTotal fractales: {len(df_table)}")
    print(f"Fractales con trigger activo: {df_table['choppiness_trigger'].sum()}")
    print("\nLeyenda:")
    print("  - Time(seg): Segundos desde el fractal anterior")
    print("  - PriceDiff: Distancia en precio desde fractal anterior")
    print("  - InvFreq: Frecuencia invertida (alto = consolidación)")
    print(f"  - Trigger: YES = consolidación activa (InvFreq > {TRIGGER_THRESHOLD:,} durante {TRIGGER_PERIODS}+ fractales)")
    print("="*130 + "\n")


if __name__ == "__main__":
    from find_fractals import process_fractals_range
    from config import START_DATE, END_DATE

    print("="*70)
    print("TEST: Cálculo SIMPLE de Métricas de Fractales")
    print("="*70)
    print(f"Periodo: {START_DATE} -> {END_DATE}")

    # Procesar fractales
    fractals_result = process_fractals_range(START_DATE, END_DATE)
    if fractals_result is None:
        print("[ERROR] No se pudieron procesar fractales")
        exit(1)

    # Calcular métricas SIMPLES
    df_metrics = calculate_fractal_metrics(fractals_result['df_fractals_minor'])

    # Imprimir tabla
    print_consolidation_table(df_metrics, max_rows=30)

    print("[OK] Test completado")

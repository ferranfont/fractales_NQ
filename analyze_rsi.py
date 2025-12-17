"""
Análisis de niveles RSI para Gold (GC)
"""
import pandas as pd
from pathlib import Path
from config import (
    DATA_DIR, START_DATE, END_DATE,
    RSI_PERIOD, RSI_SMOOTH_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD,
    RSI_RESAMPLE, RSI_RESAMPLE_TO_PERIOD
)


def calculate_rsi(df, period=14, smooth_period=0, resample_rule=None):
    """
    Calcula el RSI (Relative Strength Index) con suavizado opcional.

    Si se especifica `resample_rule` (ej: '15T', '1H'), se crea un DataFrame temporal
    resampleado por la regla dada usando la columna 'timestamp' para agrupar, se calcula
    el RSI en ese timeframe superior, y luego se mapea hacia atrás a cada fila original
    usando `merge_asof` (cada fila recibe el RSI del último bucket resampleado previo).

    Args:
        df: DataFrame con columna 'close' y 'timestamp' (timestamp puede ser string)
        period: Período para el cálculo (default 14)
        smooth_period: Período para suavizar con EMA (0 = sin suavizado)
        resample_rule: String de resample (ej: '15T', '1H') o None

    Returns:
        Series con valores RSI suavizados alineados con el índice del DataFrame original
    """
    # Si no hay regla de resample, calcular directamente sobre la serie de closes
    if not resample_rule:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Aplicar suavizado con EMA si smooth_period > 0
        if smooth_period > 0:
            rsi = rsi.ewm(span=smooth_period, adjust=False).mean()

        return rsi

    # --- Si hay resample: crear dataframe temporal solo para el cálculo del RSI ---
    # Convertir timestamps a datetime de forma segura y preparar series
    temp = df.copy()
    # Forzar parse seguro a datetime UTC y convertir errores a NaT
    temp['timestamp_dt'] = pd.to_datetime(temp['timestamp'], errors='coerce', utc=True)
    # Eliminar filas sin timestamp válido
    temp = temp.dropna(subset=['timestamp_dt']).sort_values('timestamp_dt')
    if temp.empty:
        return pd.Series([pd.NA] * len(df), index=df.index)

    # Normalizar regla de resample (usar minúsculas para evitar warnings con 'H')
    if isinstance(resample_rule, str):
        rr = resample_rule.lower()
    else:
        rr = resample_rule

    # Resample de la columna 'close' usando último valor del bucket; asegurar DatetimeIndex
    close_series = temp.set_index('timestamp_dt')['close']
    if not isinstance(close_series.index, (pd.DatetimeIndex, pd.TimedeltaIndex, pd.PeriodIndex)):
        close_series.index = pd.to_datetime(close_series.index, errors='coerce', utc=True)
        close_series = close_series.dropna()

    if close_series.empty:
        return pd.Series([pd.NA] * len(df), index=df.index)

    close_resampled = close_series.resample(rr).last().dropna()
    if close_resampled.empty:
        # No hay suficientes datos para resample
        return pd.Series([pd.NA] * len(df), index=df.index)

    # Calcular RSI sobre la serie resampleada
    delta = close_resampled.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi_res = 100 - (100 / (1 + rs))

    if smooth_period > 0:
        rsi_res = rsi_res.ewm(span=smooth_period, adjust=False).mean()

    # Mapear el RSI resampleado de vuelta a cada fila original usando merge_asof
    rsi_df = rsi_res.rename('rsi_resampled').reset_index()
    rsi_df.columns = ['timestamp_resample', 'rsi_resampled']

    temp_merge = temp[['timestamp_dt']].copy()
    temp_merge = temp_merge.reset_index().rename(columns={'index': 'orig_index'})

    # merge_asof requiere que ambos estén ordenados
    rsi_df = rsi_df.sort_values('timestamp_resample')
    temp_merge = temp_merge.sort_values('timestamp_dt')

    merged = pd.merge_asof(temp_merge, rsi_df,
                           left_on='timestamp_dt', right_on='timestamp_resample',
                           direction='backward')

    # Construir serie alineada con el índice del df original
    rsi_mapped = pd.Series(data=merged['rsi_resampled'].values, index=merged['orig_index'])
    rsi_mapped = rsi_mapped.reindex(df.index)

    return rsi_mapped


def analyze_rsi_levels_range(df: pd.DataFrame, start_date: str, end_date: str) -> dict:
    """
    Analiza los niveles RSI para un DataFrame con rango de fechas

    Args:
        df: DataFrame con datos OHLC
        start_date: Fecha inicial en formato YYYY-MM-DD
        end_date: Fecha final en formato YYYY-MM-DD

    Returns:
        dict con información de niveles RSI o None si hay error
    """
    print("="*70)
    print("ANÁLISIS RSI - Gold (GC)")
    print("="*70)
    print(f"\nRango: {start_date} -> {end_date}")
    print(f"RSI Period: {RSI_PERIOD}")
    print(f"Overbought: {RSI_OVERBOUGHT}")
    print(f"Oversold: {RSI_OVERSOLD}")
    print("-"*70)

    # Verificar columnas
    if 'close' not in df.columns:
        print(f"[ERROR] Falta columna 'close'")
        return None

    print(f"\n[INFO] Procesando {len(df)} registros")

    # Determinar regla efectiva de resample según configuración
    if isinstance(RSI_RESAMPLE, bool) and RSI_RESAMPLE is True:
        effective_resample = RSI_RESAMPLE_TO_PERIOD
        print(f"[INFO] RSI resample enabled via flag; using RSI_RESAMPLE_TO_PERIOD={effective_resample}")
    elif isinstance(RSI_RESAMPLE, str) and RSI_RESAMPLE:
        effective_resample = RSI_RESAMPLE
        print(f"[INFO] RSI resample rule from RSI_RESAMPLE: {effective_resample}")
    else:
        effective_resample = None
        print(f"[INFO] RSI resample disabled")

    df['rsi'] = calculate_rsi(df, period=RSI_PERIOD, smooth_period=RSI_SMOOTH_PERIOD, resample_rule=effective_resample)

    # Eliminar valores NaN
    df_valid = df.dropna(subset=['rsi'])

    # Encontrar niveles de sobrecompra y sobreventa
    overbought_moments = df_valid[df_valid['rsi'] >= RSI_OVERBOUGHT]
    oversold_moments = df_valid[df_valid['rsi'] <= RSI_OVERSOLD]

    # Estadísticas
    rsi_min = df_valid['rsi'].min()
    rsi_max = df_valid['rsi'].max()
    rsi_mean = df_valid['rsi'].mean()

    print("\n" + "="*70)
    print("RESUMEN RSI")
    print("="*70)
    print(f"RSI Mínimo: {rsi_min:.2f}")
    print(f"RSI Máximo: {rsi_max:.2f}")
    print(f"RSI Medio: {rsi_mean:.2f}")
    print(f"Momentos de sobrecompra (>={RSI_OVERBOUGHT}): {len(overbought_moments)}")
    print(f"Momentos de sobreventa (<={RSI_OVERSOLD}): {len(oversold_moments)}")
    print("="*70)

    return {
        'start_date': start_date,
        'end_date': end_date,
        'rsi_min': rsi_min,
        'rsi_max': rsi_max,
        'rsi_mean': rsi_mean,
        'overbought_count': len(overbought_moments),
        'oversold_count': len(oversold_moments),
        'overbought_threshold': RSI_OVERBOUGHT,
        'oversold_threshold': RSI_OVERSOLD,
        'df_with_rsi': df
    }


def analyze_rsi_levels(dia: str) -> dict:
    """
    Analiza los niveles RSI para un día específico

    Args:
        dia: Fecha en formato YYYY-MM-DD

    Returns:
        dict con información de niveles RSI o None si hay error
    """
    print("="*70)
    print("ANÁLISIS RSI - Gold (GC)")
    print("="*70)
    print(f"\nDía a procesar: {dia}")
    print(f"RSI Period: {RSI_PERIOD}")
    print(f"Overbought: {RSI_OVERBOUGHT}")
    print(f"Oversold: {RSI_OVERSOLD}")
    print("-"*70)

    # Leer archivo del día
    csv_path = DATA_DIR / f"gc_{dia}.csv"
    if not csv_path.exists():
        print(f"\n[ERROR] Archivo no encontrado: {csv_path}")
        return None

    print(f"\n[INFO] Cargando datos de: {csv_path.name}")
    df = pd.read_csv(csv_path)
    print(f"[OK] Cargados {len(df)} registros")

    # Verificar columnas
    if 'close' not in df.columns:
        print(f"[ERROR] Falta columna 'close'")
        return None

    # Determinar regla efectiva de resample según configuración
    if isinstance(RSI_RESAMPLE, bool) and RSI_RESAMPLE is True:
        effective_resample = RSI_RESAMPLE_TO_PERIOD
        print(f"[INFO] RSI resample enabled via flag; using RSI_RESAMPLE_TO_PERIOD={effective_resample}")
    elif isinstance(RSI_RESAMPLE, str) and RSI_RESAMPLE:
        effective_resample = RSI_RESAMPLE
        print(f"[INFO] RSI resample rule from RSI_RESAMPLE: {effective_resample}")
    else:
        effective_resample = None
        print(f"[INFO] RSI resample disabled")

    df['rsi'] = calculate_rsi(df, period=RSI_PERIOD, resample_rule=effective_resample)

    # Eliminar valores NaN
    df_valid = df.dropna(subset=['rsi'])

    # Encontrar niveles de sobrecompra y sobreventa
    overbought_moments = df_valid[df_valid['rsi'] >= RSI_OVERBOUGHT]
    oversold_moments = df_valid[df_valid['rsi'] <= RSI_OVERSOLD]

    # Estadísticas
    rsi_min = df_valid['rsi'].min()
    rsi_max = df_valid['rsi'].max()
    rsi_mean = df_valid['rsi'].mean()

    print("\n" + "="*70)
    print("RESUMEN RSI")
    print("="*70)
    print(f"RSI Mínimo: {rsi_min:.2f}")
    print(f"RSI Máximo: {rsi_max:.2f}")
    print(f"RSI Medio: {rsi_mean:.2f}")
    print(f"Momentos de sobrecompra (>={RSI_OVERBOUGHT}): {len(overbought_moments)}")
    print(f"Momentos de sobreventa (<={RSI_OVERSOLD}): {len(oversold_moments)}")
    print("="*70)

    return {
        'dia': dia,
        'rsi_min': rsi_min,
        'rsi_max': rsi_max,
        'rsi_mean': rsi_mean,
        'overbought_count': len(overbought_moments),
        'oversold_count': len(oversold_moments),
        'overbought_threshold': RSI_OVERBOUGHT,
        'oversold_threshold': RSI_OVERSOLD
    }


def main():
    """
    Función principal de ejecución standalone
    """
    from find_fractals import load_date_range

    # Cargar datos del rango
    df = load_date_range(START_DATE, END_DATE)
    if df is None:
        return

    result = analyze_rsi_levels_range(df, START_DATE, END_DATE)
    if result is None:
        return


if __name__ == "__main__":
    main()

"""
Cálculo del indicador VWAP (Volume Weighted Average Price)
"""
import pandas as pd


def calculate_vwap(df, period=50):
    """
    Calcula VWAP con ventana móvil (rolling VWAP)

    Args:
        df: DataFrame con columnas ['high', 'low', 'close', 'volume']
        period: Periodo de la ventana móvil (default: 50)

    Returns:
        Series con valores de VWAP
    """

    df = df.copy()

    # Calcular precio típico (Typical Price)
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3

    # Calcular volumen * precio típico
    df['tp_volume'] = df['typical_price'] * df['volume']

    # Calcular VWAP con ventana móvil
    # VWAP = Suma(Typical Price * Volume) / Suma(Volume)
    df['vwap'] = (
        df['tp_volume'].rolling(window=period).sum() /
        df['volume'].rolling(window=period).sum()
    )

    return df['vwap']


if __name__ == "__main__":
    from find_fractals import load_date_range
    from config import START_DATE, END_DATE, VWAP_FAST, VWAP_SLOW

    print("="*70)
    print("TEST: Cálculo de VWAP")
    print("="*70)
    print(f"Periodo: {START_DATE} -> {END_DATE}")
    print(f"Ventana VWAP Fast: {VWAP_FAST} periodos")
    print(f"Ventana VWAP Slow: {VWAP_SLOW} periodos")

    # Cargar datos
    df = load_date_range(START_DATE, END_DATE)
    if df is None:
        print("[ERROR] No se pudieron cargar datos")
        exit(1)

    # Calcular ambos VWAPs
    df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)
    df['vwap_slow'] = calculate_vwap(df, period=VWAP_SLOW)

    # Mostrar primeros resultados
    print("\nPrimeros 20 registros con VWAP:")
    print(df[['timestamp', 'close', 'volume', 'vwap_fast', 'vwap_slow']].head(20))

    # Estadísticas VWAP Fast
    print(f"\nEstadísticas VWAP Fast ({VWAP_FAST} periodos):")
    print(f"  Media: {df['vwap_fast'].mean():.2f}")
    print(f"  Min: {df['vwap_fast'].min():.2f}")
    print(f"  Max: {df['vwap_fast'].max():.2f}")
    print(f"  Registros con VWAP válido: {df['vwap_fast'].notna().sum()}")

    # Estadísticas VWAP Slow
    print(f"\nEstadísticas VWAP Slow ({VWAP_SLOW} periodos):")
    print(f"  Media: {df['vwap_slow'].mean():.2f}")
    print(f"  Min: {df['vwap_slow'].min():.2f}")
    print(f"  Max: {df['vwap_slow'].max():.2f}")
    print(f"  Registros con VWAP válido: {df['vwap_slow'].notna().sum()}")

    print(f"\nRegistros totales: {len(df)}")
    print("\n[OK] Test completado")

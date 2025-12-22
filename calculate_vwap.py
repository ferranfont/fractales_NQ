"""
Cálculo del indicador VWAP (Volume Weighted Average Price)
"""
import pandas as pd
from config import VWAP_PERIOD


def calculate_vwap(df, period=None):
    """
    Calcula VWAP con ventana móvil (rolling VWAP)

    Args:
        df: DataFrame con columnas ['high', 'low', 'close', 'volume']
        period: Periodo de la ventana móvil (default: VWAP_PERIOD desde config)

    Returns:
        Series con valores de VWAP
    """
    if period is None:
        period = VWAP_PERIOD

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
    from config import START_DATE, END_DATE

    print("="*70)
    print("TEST: Cálculo de VWAP")
    print("="*70)
    print(f"Periodo: {START_DATE} -> {END_DATE}")
    print(f"Ventana VWAP: {VWAP_PERIOD} periodos")

    # Cargar datos
    df = load_date_range(START_DATE, END_DATE)
    if df is None:
        print("[ERROR] No se pudieron cargar datos")
        exit(1)

    # Calcular VWAP
    df['vwap'] = calculate_vwap(df)

    # Mostrar primeros resultados
    print("\nPrimeros 20 registros con VWAP:")
    print(df[['timestamp', 'close', 'volume', 'vwap']].head(20))

    # Estadísticas
    print(f"\nEstadísticas VWAP:")
    print(f"  Media: {df['vwap'].mean():.2f}")
    print(f"  Min: {df['vwap'].min():.2f}")
    print(f"  Max: {df['vwap'].max():.2f}")
    print(f"  Registros con VWAP válido: {df['vwap'].notna().sum()}")
    print(f"  Registros totales: {len(df)}")

    print("\n[OK] Test completado")

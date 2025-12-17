"""
Análisis de niveles Fibonacci Retracement para Gold (GC)
Calcula niveles de retroceso basándose en los últimos 2 fractales MAJOR
"""
import pandas as pd
from pathlib import Path
from config import FRACTALS_DIR, START_DATE, END_DATE, FIBO_LEVELS, MINIMUM_IMPULSE_FACTOR


def calculate_fibonacci_levels(high_price: float, low_price: float, levels: list) -> dict:
    """
    Calcula niveles de Fibonacci retracement

    Args:
        high_price: Precio máximo (swing high)
        low_price: Precio mínimo (swing low)
        levels: Lista de niveles Fibonacci (ej: [0.236, 0.382, 0.5, 0.618])

    Returns:
        dict con niveles de precio calculados
    """
    diff = high_price - low_price
    fibo_prices = {}

    for level in levels:
        # Fibonacci retracement desde el high
        price = high_price - (diff * level)
        fibo_prices[level] = round(price, 2)

    return fibo_prices


def analyze_fibonacci_range(df_fractals_major: pd.DataFrame, start_date: str, end_date: str) -> dict:
    """
    Analiza niveles Fibonacci para TODOS los movimientos alcistas (VALLE -> PICO) en fractales MAJOR

    Args:
        df_fractals_major: DataFrame con fractales MAJOR del rango
        start_date: Fecha inicial en formato YYYY-MM-DD
        end_date: Fecha final en formato YYYY-MM-DD

    Returns:
        dict con lista de movimientos alcistas y sus niveles Fibonacci
    """
    print("="*70)
    print("ANÁLISIS FIBONACCI - Gold (GC) - SOLO MOVIMIENTOS ALCISTAS")
    print("="*70)
    print(f"\nRango: {start_date} -> {end_date}")
    print(f"Niveles: {FIBO_LEVELS}")
    print(f"Método: Todos los movimientos VALLE -> PICO en MAJOR")
    print(f"Minimum impulse factor: {MINIMUM_IMPULSE_FACTOR}% (ignore moves smaller than this % of average)")
    print("-"*70)

    if len(df_fractals_major) < 2:
        print(f"\n[ERROR] Se necesitan al menos 2 fractales MAJOR")
        print(f"Hay solo {len(df_fractals_major)} fractal(es)")
        return None

    # Identificar TODOS los movimientos alcistas (VALLE -> PICO)
    upward_moves = []

    # Track accepted moves' ranges to compute running average
    accepted_ranges = []

    for i in range(len(df_fractals_major) - 1):
        current = df_fractals_major.iloc[i]
        next_fractal = df_fractals_major.iloc[i + 1]

        # Solo movimientos alcistas: VALLE -> PICO
        if current['type'] == 'VALLE' and next_fractal['type'] == 'PICO':
            swing_low = current['price']
            swing_high = next_fractal['price']
            swing_low_ts = current['timestamp']
            swing_high_ts = next_fractal['timestamp']

            move_range = abs(swing_high - swing_low)

            # Determinar current average (si existe)
            if accepted_ranges:
                running_avg = sum(accepted_ranges) / len(accepted_ranges)
            else:
                running_avg = None

            # Si no hay running_avg todavía, aceptamos el primer movimiento
            if running_avg is None:
                threshold = 0.0
            else:
                threshold = (MINIMUM_IMPULSE_FACTOR / 100.0) * running_avg

            # Mostrar info parcial y decidir aceptar o no
            if running_avg is None:
                print(f"Movimiento provisional #{i+1}: {swing_low:.2f} -> {swing_high:.2f} (Rango: {move_range:.2f}) | Average: n/a -> ACEPTADO por ser el primero")
                accept = True
            else:
                print(f"Movimiento provisional #{i+1}: {swing_low:.2f} -> {swing_high:.2f} (Rango: {move_range:.2f}) | Threshold: {threshold:.2f} ({MINIMUM_IMPULSE_FACTOR}% del avg {running_avg:.2f})")
                accept = move_range >= threshold

            if not accept:
                print(f"  [SKIP] Movimiento ignorado porque su rango {move_range:.2f} < threshold {threshold:.2f}")
                # No añadimos a accepted_ranges ni a upward_moves
                continue

            # Si aceptado, calcular niveles Fibonacci para este movimiento
            fibo_levels = calculate_fibonacci_levels(swing_high, swing_low, FIBO_LEVELS)

            # Determinar el timestamp de fin del retroceso (siguiente fractal MAJOR si existe)
            retracement_end_ts = None
            if i + 2 < len(df_fractals_major):
                retracement_end_ts = df_fractals_major.iloc[i + 2]['timestamp']

            move = {
                'swing_low': swing_low,
                'swing_high': swing_high,
                'swing_low_timestamp': swing_low_ts,
                'swing_high_timestamp': swing_high_ts,
                'retracement_end_timestamp': retracement_end_ts,
                'range': move_range,
                'levels': fibo_levels,
                'move_index': i
            }

            upward_moves.append(move)
            accepted_ranges.append(move_range)

    if not upward_moves:
        print(f"\n[WARNING] No se encontraron movimientos alcistas (VALLE -> PICO)")
        return None

    print(f"\n[INFO] Encontrados {len(upward_moves)} movimientos alcistas")
    print("\n" + "="*70)
    print("MOVIMIENTOS ALCISTAS Y NIVELES FIBONACCI")
    print("="*70)

    for idx, move in enumerate(upward_moves, 1):
        print(f"\n--- Movimiento #{idx} ---")
        print(f"  Swing Low:  {move['swing_low']:.2f} @ {move['swing_low_timestamp']}")
        print(f"  Swing High: {move['swing_high']:.2f} @ {move['swing_high_timestamp']}")
        print(f"  Rango: {move['range']:.2f}")
        print(f"  Niveles Fibonacci:")
        for level, price in sorted(move['levels'].items(), reverse=True):
            level_pct = level * 100
            print(f"    {level_pct:5.1f}% -> {price:8.2f}")

    # Resumen de rangos aceptados
    if accepted_ranges:
        avg_range = sum(accepted_ranges) / len(accepted_ranges)
        print("\n" + "="*70)
        print(f"Rango medio (aceptado): {avg_range:.2f} | Movimientos aceptados: {len(accepted_ranges)}")
    else:
        print("\n" + "="*70)
        print("No hay movimientos aceptados para calcular rango medio")

    print("="*70)

    return {
        'start_date': start_date,
        'end_date': end_date,
        'upward_moves': upward_moves,
        'total_moves': len(upward_moves),
        'avg_accepted_range': (sum(accepted_ranges) / len(accepted_ranges)) if accepted_ranges else None
    }


def analyze_fibonacci(dia: str) -> dict:
    """
    Analiza niveles Fibonacci para un día específico basándose en fractales MAJOR

    Args:
        dia: Fecha en formato YYYY-MM-DD

    Returns:
        dict con información de niveles Fibonacci o None si hay error
    """
    print("="*70)
    print("ANÁLISIS FIBONACCI - Gold (GC)")
    print("="*70)
    print(f"\nDía a procesar: {dia}")
    print(f"Niveles: {FIBO_LEVELS}")
    print(f"Método: Últimos 2 fractales MAJOR")
    print("-"*70)

    # Cargar fractales MAJOR
    fractal_major_path = FRACTALS_DIR / f"gc_fractals_major_{dia}.csv"

    if not fractal_major_path.exists():
        print(f"\n[ERROR] No se encontraron fractales MAJOR para {dia}")
        print(f"Ejecuta primero find_fractals.py")
        return None

    df_fractals = pd.read_csv(fractal_major_path)

    if len(df_fractals) < 2:
        print(f"\n[ERROR] Se necesitan al menos 2 fractales MAJOR")
        print(f"Hay solo {len(df_fractals)} fractal(es)")
        return None

    # Obtener los últimos dos fractales (último swing)
    last_two = df_fractals.tail(2)

    prices = last_two['price'].values
    types = last_two['type'].values
    timestamps = last_two['timestamp'].values

    # Determinar cuál es PICO y cuál es VALLE
    if types[0] == 'PICO' and types[1] == 'VALLE':
        swing_high = prices[0]
        swing_low = prices[1]
        swing_high_ts = timestamps[0]
        swing_low_ts = timestamps[1]
        direction = 'down'  # Movimiento bajista
    elif types[0] == 'VALLE' and types[1] == 'PICO':
        swing_low = prices[0]
        swing_high = prices[1]
        swing_low_ts = timestamps[0]
        swing_high_ts = timestamps[1]
        direction = 'up'  # Movimiento alcista
    else:
        print(f"\n[ERROR] Fractales consecutivos del mismo tipo: {types[0]} -> {types[1]}")
        return None

    # Antes de calcular niveles, comprobar mínimo impulso según histórico en el archivo
    # Construir lista de todos movimientos VALLE->PICO en el archivo para calcular un promedio histórico
    historical_ranges = []
    for i in range(len(df_fractals) - 1):
        a = df_fractals.iloc[i]
        b = df_fractals.iloc[i + 1]
        if a['type'] == 'VALLE' and b['type'] == 'PICO':
            historical_ranges.append(abs(b['price'] - a['price']))

    # Excluir el último movimiento actual para obtener promedio histórico previo
    if len(historical_ranges) >= 2:
        hist_avg = sum(historical_ranges[:-1]) / (len(historical_ranges) - 1)
    else:
        hist_avg = None

    current_range = abs(swing_high - swing_low)

    if hist_avg is None:
        print(f"[INFO] No hay promedio histórico suficiente (aceptando movimiento actual)")
        accept = True
    else:
        threshold = (MINIMUM_IMPULSE_FACTOR / 100.0) * hist_avg
        print(f"[INFO] Current range: {current_range:.2f} | Historical avg: {hist_avg:.2f} | Threshold ({MINIMUM_IMPULSE_FACTOR}%): {threshold:.2f}")
        accept = current_range >= threshold

    if not accept:
        print(f"\n[SKIP] Movimiento ignorado: rango {current_range:.2f} < threshold {threshold:.2f}")
        return {
            'dia': dia,
            'skipped': True,
            'range': current_range,
            'threshold': (threshold if hist_avg is not None else None)
        }

    # Calcular niveles Fibonacci
    fibo_levels = calculate_fibonacci_levels(swing_high, swing_low, FIBO_LEVELS)

    print(f"\n[INFO] Swing High: {swing_high:.2f} @ {swing_high_ts}")
    print(f"[INFO] Swing Low: {swing_low:.2f} @ {swing_low_ts}")
    print(f"[INFO] Dirección: {direction.upper()}")
    print(f"[INFO] Rango: {abs(swing_high - swing_low):.2f}")

    print("\n" + "="*70)
    print("NIVELES FIBONACCI CALCULADOS")
    print("="*70)
    for level, price in sorted(fibo_levels.items(), reverse=True):
        level_pct = level * 100
        print(f"  {level_pct:5.1f}% -> {price:8.2f}")
    print("="*70)

    return {
        'dia': dia,
        'swing_high': swing_high,
        'swing_low': swing_low,
        'swing_high_timestamp': swing_high_ts,
        'swing_low_timestamp': swing_low_ts,
        'direction': direction,
        'range': abs(swing_high - swing_low),
        'levels': fibo_levels,
        'historical_avg_range': hist_avg
    }


def main():
    """
    Función principal de ejecución standalone
    """
    # Cargar fractales MAJOR del rango
    date_range_str = f"{START_DATE}_{END_DATE}"
    fractal_major_path = FRACTALS_DIR / f"gc_fractals_major_{date_range_str}.csv"

    if not fractal_major_path.exists():
        print(f"[ERROR] No se encontraron fractales MAJOR para el rango")
        print(f"Ejecuta primero find_fractals.py")
        return

    df_fractals_major = pd.read_csv(fractal_major_path)
    result = analyze_fibonacci_range(df_fractals_major, START_DATE, END_DATE)
    if result is None:
        return


if __name__ == "__main__":
    main()

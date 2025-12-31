"""
Find rectangles based on VWAP Slope crossovers
- Start (x1): Orange dot (VWAP Slope crossover UP through HIGH_VALUE)
- End (x2): Blue square (VWAP Slope crossdown through HIGH_VALUE)
- Bottom (y1): min price in range
- Top (y2): max price in range
"""
import pandas as pd
import numpy as np
from config import VWAP_SLOPE_INDICATOR_HIGH_VALUE, VWAP_SLOPE_DEGREE_WINDOW, SQUARE_TALL_NARROW_THRESHOLD


def find_vwap_slope_rectangles(df):
    """
    Find rectangles based on VWAP Slope crossover/crossdown events

    Args:
        df: DataFrame with OHLCV data and vwap_slope column

    Returns:
        List of dictionaries with rectangle coordinates:
        [
            {
                'x1_index': int,      # Start index (orange dot)
                'x2_index': int,      # End index (blue square)
                'x1_time': datetime,  # Start timestamp
                'x2_time': datetime,  # End timestamp
                'y1': float,          # Min price in range
                'y2': float,          # Max price in range
                'slope_at_start': float,
                'slope_at_end': float
            },
            ...
        ]
    """
    # Calculate VWAP Slope if not already present
    # IMPORTANT: Must use exact same calculation as plot_day.py for synchronization
    if 'vwap_slope' not in df.columns or df['vwap_slope'].isna().all():
        from calculate_vwap import calculate_vwap
        from config import VWAP_FAST

        if 'vwap_fast' not in df.columns or df['vwap_fast'].isna().all():
            df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)

        # Calculate slope using rolling().apply() with strict window check
        # This MUST match plot_day.py calculation exactly
        df['vwap_slope'] = df['vwap_fast'].rolling(window=VWAP_SLOPE_DEGREE_WINDOW).apply(
            lambda x: abs(np.polyfit(np.arange(len(x)), x, 1)[0]) if len(x) == VWAP_SLOPE_DEGREE_WINDOW else np.nan,
            raw=False
        )

    # Debug: Print info about vwap_slope to verify it's being used correctly
    print(f"[INFO] VWAP Slope calculation: {df['vwap_slope'].notna().sum()} valid values out of {len(df)} bars")

    # Detect crossover (orange dots) and crossdown (blue squares)
    df_with_prev = df.copy()
    df_with_prev['vwap_slope_prev'] = df_with_prev['vwap_slope'].shift(1)

    # Crossover UP: previous <= HIGH_VALUE and current > HIGH_VALUE
    crossover_condition = (
        (df_with_prev['vwap_slope_prev'] <= VWAP_SLOPE_INDICATOR_HIGH_VALUE) &
        (df_with_prev['vwap_slope'] > VWAP_SLOPE_INDICATOR_HIGH_VALUE) &
        (df_with_prev['vwap_slope'].notna()) &
        (df_with_prev['vwap_slope_prev'].notna())
    )

    # Crossdown: previous > HIGH_VALUE and current <= HIGH_VALUE
    crossdown_condition = (
        (df_with_prev['vwap_slope_prev'] > VWAP_SLOPE_INDICATOR_HIGH_VALUE) &
        (df_with_prev['vwap_slope'] <= VWAP_SLOPE_INDICATOR_HIGH_VALUE) &
        (df_with_prev['vwap_slope'].notna()) &
        (df_with_prev['vwap_slope_prev'].notna())
    )

    # Get indices of crossovers and crossdowns
    crossover_indices = df_with_prev[crossover_condition].index.tolist()
    crossdown_indices = df_with_prev[crossdown_condition].index.tolist()

    print(f"[INFO] Found {len(crossover_indices)} crossover points (orange dots)")
    print(f"[INFO] Found {len(crossdown_indices)} crossdown points (blue squares)")

    # Match crossovers with subsequent crossdowns to form rectangles
    rectangles = []

    for crossover_idx in crossover_indices:
        # Find the next crossdown after this crossover
        subsequent_crossdowns = [cd_idx for cd_idx in crossdown_indices if cd_idx > crossover_idx]

        if not subsequent_crossdowns:
            # No crossdown found after this crossover, skip
            continue

        # Use the first crossdown after the crossover
        crossdown_idx = subsequent_crossdowns[0]

        # Get the range of data between crossover and crossdown
        range_data = df.loc[crossover_idx:crossdown_idx]

        if len(range_data) < 2:
            continue

        # Find min and max prices in this range
        y_min = range_data['low'].min()
        y_max = range_data['high'].max()

        # Get timestamps
        x1_time = df.loc[crossover_idx, 'timestamp']
        x2_time = df.loc[crossdown_idx, 'timestamp']

        # Get slopes at start and end
        slope_at_start = df.loc[crossover_idx, 'vwap_slope']
        slope_at_end = df.loc[crossdown_idx, 'vwap_slope']

        # Get initial and final prices
        initial_price = df.loc[crossover_idx, 'close']
        final_price = df.loc[crossdown_idx, 'close']

        # Calculate classification metrics
        bars_in_range = len(range_data)
        price_range = y_max - y_min
        price_per_bar = price_range / bars_in_range if bars_in_range > 0 else 0

        # Classify based on aspect ratio AND price trend direction
        # Tall & Narrow rectangles (price_per_bar > threshold) are colored by trend:
        #   - Uptrend (final > initial): chartreuse green
        #   - Downtrend (final < initial): red
        # Consolidation rectangles (price_per_bar <= threshold): orange
        if price_per_bar > SQUARE_TALL_NARROW_THRESHOLD:
            # Tall & Narrow - check trend direction
            if final_price > initial_price:
                rect_type = 'tall_narrow_up'  # Chartreuse green (uptrend)
            else:
                rect_type = 'tall_narrow_down'  # Red (downtrend)
        else:
            rect_type = 'consolidation'  # Orange (perfect square/consolidation)

        rectangles.append({
            'x1_index': crossover_idx,
            'x2_index': crossdown_idx,
            'x1_time': x1_time,
            'x2_time': x2_time,
            'y1': y_min,
            'y2': y_max,
            'slope_at_start': slope_at_start,
            'slope_at_end': slope_at_end,
            'bars_in_range': bars_in_range,
            'price_range': price_range,
            'price_per_bar': price_per_bar,
            'initial_price': initial_price,
            'final_price': final_price,
            'type': rect_type
        })

    print(f"[INFO] Created {len(rectangles)} rectangles from crossover/crossdown pairs")

    return rectangles


def print_rectangles_summary(rectangles):
    """Print summary of rectangles found"""
    if not rectangles:
        print("[INFO] No rectangles found")
        return

    print("\n" + "="*80)
    print("VWAP SLOPE RECTANGLES SUMMARY")
    print("="*80)
    print(f"Total rectangles: {len(rectangles)}")

    # Calculate statistics
    avg_bars = sum(r['bars_in_range'] for r in rectangles) / len(rectangles)
    avg_price_range = sum(r['price_range'] for r in rectangles) / len(rectangles)

    # Classification breakdown
    tall_narrow_up = [r for r in rectangles if r['type'] == 'tall_narrow_up']
    tall_narrow_down = [r for r in rectangles if r['type'] == 'tall_narrow_down']
    consolidation = [r for r in rectangles if r['type'] == 'consolidation']

    print(f"\nClassification (aspect ratio + trend direction):")
    print(f"  - Tall & Narrow UPTREND (chartreuse green): {len(tall_narrow_up)} rectangles (ratio > {SQUARE_TALL_NARROW_THRESHOLD} + price rising)")
    print(f"  - Tall & Narrow DOWNTREND (red): {len(tall_narrow_down)} rectangles (ratio > {SQUARE_TALL_NARROW_THRESHOLD} + price falling)")
    print(f"  - Consolidation (orange): {len(consolidation)} rectangles (ratio <= {SQUARE_TALL_NARROW_THRESHOLD})")
    print(f"Average bars per rectangle: {avg_bars:.1f}")
    print(f"Average price range: {avg_price_range:.2f} points")

    print("\nFirst 5 rectangles:")
    print("-"*80)
    for i, rect in enumerate(rectangles[:5], 1):
        print(f"{i}. Start: {rect['x1_time']} (idx={rect['x1_index']}) -> "
              f"End: {rect['x2_time']} (idx={rect['x2_index']})")
        print(f"   Price range: {rect['y1']:.2f} - {rect['y2']:.2f} "
              f"({rect['price_range']:.2f} points, {rect['bars_in_range']} bars)")
        print(f"   Initial: {rect['initial_price']:.2f} -> Final: {rect['final_price']:.2f}")
        print(f"   Type: {rect['type'].upper()}")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Test the rectangle detection
    from find_fractals import load_date_range
    from config import START_DATE, END_DATE

    print("Testing rectangle detection...")
    print(f"Loading data for: {START_DATE}")

    df = load_date_range(START_DATE, END_DATE)

    if df is not None:
        rectangles = find_vwap_slope_rectangles(df)
        print_rectangles_summary(rectangles)
    else:
        print("[ERROR] Could not load data")

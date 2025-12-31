"""
REALTIME Rectangle Detection - Close GREEN/RED rectangles as soon as threshold is met
- Don't wait for blue square on volatile moves
- Close rectangle immediately when price_per_bar > SQUARE_TALL_NARROW_THRESHOLD
- Filter out rectangles below VWAP_SQUARE_MIN_SPIKE minimum height
- Orange consolidation rectangles still require blue square completion
"""
import pandas as pd
import numpy as np
from config import (
    VWAP_SLOPE_INDICATOR_HIGH_VALUE,
    VWAP_SLOPE_DEGREE_WINDOW,
    SQUARE_TALL_NARROW_THRESHOLD,
    VWAP_SQUARE_MIN_SPIKE
)


def find_vwap_slope_rectangles_realtime(df):
    """
    Find rectangles with REALTIME closing for GREEN/RED patterns

    GREEN/RED rectangles close immediately when price_per_bar > threshold
    ORANGE rectangles still wait for blue square (consolidation pattern)

    Args:
        df: DataFrame with OHLCV data and vwap_slope column

    Returns:
        List of rectangles with realtime detection
    """
    # Calculate VWAP Slope if not already present
    if 'vwap_slope' not in df.columns or df['vwap_slope'].isna().all():
        from calculate_vwap import calculate_vwap
        from config import VWAP_FAST

        if 'vwap_fast' not in df.columns or df['vwap_fast'].isna().all():
            df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)

        df['vwap_slope'] = df['vwap_fast'].rolling(window=VWAP_SLOPE_DEGREE_WINDOW).apply(
            lambda x: abs(np.polyfit(np.arange(len(x)), x, 1)[0]) if len(x) == VWAP_SLOPE_DEGREE_WINDOW else np.nan,
            raw=False
        )

    print(f"[INFO] REALTIME Rectangle Detection: {df['vwap_slope'].notna().sum()} valid VWAP slope values")

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

    crossover_indices = df_with_prev[crossover_condition].index.tolist()
    crossdown_indices = df_with_prev[crossdown_condition].index.tolist()

    print(f"[INFO] Found {len(crossover_indices)} crossover points (orange dots)")
    print(f"[INFO] Found {len(crossdown_indices)} crossdown points (blue squares)")

    # Track pending rectangles and completed rectangles
    pending_rectangles = []  # Rectangles waiting to be closed
    completed_rectangles = []

    green_early_close = 0
    red_early_close = 0
    orange_normal_close = 0
    filtered_small = 0  # Count of rectangles filtered due to MIN_SPIKE

    # Iterate through all bars chronologically
    for idx in df.index:
        current_time = df.loc[idx, 'timestamp']

        # Check if this bar is a crossover (orange dot) - START new rectangle
        if idx in crossover_indices:
            pending_rectangles.append({
                'start_idx': idx,
                'start_time': current_time,
                'start_price': df.loc[idx, 'close']
            })

        # Check if this bar is a crossdown (blue square) - CLOSE any pending rectangles
        if idx in crossdown_indices:
            # Close all pending rectangles that haven't been closed yet
            for pending in pending_rectangles:
                if pending.get('closed', False):
                    continue

                # Get range data
                range_data = df.loc[pending['start_idx']:idx]

                if len(range_data) < 2:
                    pending['closed'] = True
                    continue

                # Calculate metrics
                y_min = range_data['low'].min()
                y_max = range_data['high'].max()
                bars_in_range = len(range_data)
                price_range = y_max - y_min
                price_per_bar = price_range / bars_in_range if bars_in_range > 0 else 0

                initial_price = pending['start_price']
                final_price = df.loc[idx, 'close']

                # FILTER: Check minimum spike height
                if VWAP_SQUARE_MIN_SPIKE > 0 and price_range < VWAP_SQUARE_MIN_SPIKE:
                    # Rectangle too small, skip it
                    filtered_small += 1
                    pending['closed'] = True
                    continue

                # Classify - if still below threshold, it's ORANGE consolidation
                if price_per_bar <= SQUARE_TALL_NARROW_THRESHOLD:
                    rect_type = 'consolidation'
                    orange_normal_close += 1
                else:
                    # Should have been closed earlier (tall & narrow)
                    if final_price > initial_price:
                        rect_type = 'tall_narrow_up'
                    else:
                        rect_type = 'tall_narrow_down'

                completed_rectangles.append({
                    'x1_index': pending['start_idx'],
                    'x2_index': idx,
                    'x1_time': pending['start_time'],
                    'x2_time': current_time,
                    'y1': y_min,
                    'y2': y_max,
                    'slope_at_start': df.loc[pending['start_idx'], 'vwap_slope'],
                    'slope_at_end': df.loc[idx, 'vwap_slope'],
                    'bars_in_range': bars_in_range,
                    'price_range': price_range,
                    'price_per_bar': price_per_bar,
                    'initial_price': initial_price,
                    'final_price': final_price,
                    'type': rect_type,
                    'closed_by': 'blue_square'
                })

                pending['closed'] = True

        # REALTIME CHECK: Check all pending rectangles to see if they should close EARLY
        for pending in pending_rectangles:
            if pending.get('closed', False):
                continue

            # Skip the start bar itself
            if idx <= pending['start_idx']:
                continue

            # Get current range
            range_data = df.loc[pending['start_idx']:idx]

            if len(range_data) < 2:
                continue

            # Calculate current metrics
            y_min = range_data['low'].min()
            y_max = range_data['high'].max()
            bars_in_range = len(range_data)
            price_range = y_max - y_min
            price_per_bar = price_range / bars_in_range if bars_in_range > 0 else 0

            # EARLY CLOSE CONDITION: price_per_bar > threshold
            if price_per_bar > SQUARE_TALL_NARROW_THRESHOLD:
                # FILTER: Check minimum spike height before closing early
                if VWAP_SQUARE_MIN_SPIKE > 0 and price_range < VWAP_SQUARE_MIN_SPIKE:
                    # Rectangle too small, don't close early (let it continue or close at blue square)
                    continue

                initial_price = pending['start_price']
                final_price = df.loc[idx, 'close']

                # Classify as GREEN or RED
                if final_price > initial_price:
                    rect_type = 'tall_narrow_up'
                    green_early_close += 1
                else:
                    rect_type = 'tall_narrow_down'
                    red_early_close += 1

                completed_rectangles.append({
                    'x1_index': pending['start_idx'],
                    'x2_index': idx,
                    'x1_time': pending['start_time'],
                    'x2_time': current_time,
                    'y1': y_min,
                    'y2': y_max,
                    'slope_at_start': df.loc[pending['start_idx'], 'vwap_slope'],
                    'slope_at_end': df.loc[idx, 'vwap_slope'],
                    'bars_in_range': bars_in_range,
                    'price_range': price_range,
                    'price_per_bar': price_per_bar,
                    'initial_price': initial_price,
                    'final_price': final_price,
                    'type': rect_type,
                    'closed_by': 'early_threshold'
                })

                pending['closed'] = True

    print(f"[INFO] REALTIME Rectangle Detection Complete:")
    print(f"  - {green_early_close} GREEN rectangles (closed EARLY when threshold met)")
    print(f"  - {red_early_close} RED rectangles (closed EARLY when threshold met)")
    print(f"  - {orange_normal_close} ORANGE rectangles (closed normally at blue square)")
    if VWAP_SQUARE_MIN_SPIKE > 0:
        print(f"  - {filtered_small} rectangles FILTERED (height < {VWAP_SQUARE_MIN_SPIKE} pts)")
    print(f"  - Total: {len(completed_rectangles)} rectangles")

    return completed_rectangles


def print_rectangles_summary(rectangles):
    """Print summary of rectangles found"""
    if not rectangles:
        print("[INFO] No rectangles found")
        return

    print("\n" + "="*80)
    print("REALTIME VWAP SLOPE RECTANGLES SUMMARY")
    print("="*80)
    print(f"Total rectangles: {len(rectangles)}")

    # Calculate statistics
    avg_bars = sum(r['bars_in_range'] for r in rectangles) / len(rectangles)
    avg_price_range = sum(r['price_range'] for r in rectangles) / len(rectangles)

    # Classification breakdown
    tall_narrow_up = [r for r in rectangles if r['type'] == 'tall_narrow_up']
    tall_narrow_down = [r for r in rectangles if r['type'] == 'tall_narrow_down']
    consolidation = [r for r in rectangles if r['type'] == 'consolidation']

    # Early close breakdown
    early_close = [r for r in rectangles if r.get('closed_by') == 'early_threshold']
    blue_square_close = [r for r in rectangles if r.get('closed_by') == 'blue_square']

    print(f"\nClassification (aspect ratio + trend direction):")
    print(f"  - Tall & Narrow UPTREND (green): {len(tall_narrow_up)} rectangles")
    print(f"  - Tall & Narrow DOWNTREND (red): {len(tall_narrow_down)} rectangles")
    print(f"  - Consolidation (orange): {len(consolidation)} rectangles")

    print(f"\nClosing Method:")
    print(f"  - Early close (threshold met): {len(early_close)} rectangles")
    print(f"  - Blue square close: {len(blue_square_close)} rectangles")

    print(f"\nAverage bars per rectangle: {avg_bars:.1f}")
    print(f"Average price range: {avg_price_range:.2f} points")

    print("\nFirst 5 rectangles:")
    print("-"*80)
    for i, rect in enumerate(rectangles[:5], 1):
        close_method = "EARLY" if rect.get('closed_by') == 'early_threshold' else "BLUE SQ"
        print(f"{i}. [{close_method}] {rect['type'].upper()}")
        print(f"   Start: {rect['x1_time']} -> End: {rect['x2_time']}")
        print(f"   Price range: {rect['y1']:.2f} - {rect['y2']:.2f} ({rect['price_range']:.2f} pts, {rect['bars_in_range']} bars)")
        print(f"   Ratio: {rect['price_per_bar']:.2f} (threshold: {SQUARE_TALL_NARROW_THRESHOLD})")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Test the realtime rectangle detection
    from find_fractals import load_date_range
    from config import START_DATE, END_DATE

    print("Testing REALTIME rectangle detection...")
    print(f"Loading data for: {START_DATE}")

    df = load_date_range(START_DATE, END_DATE)

    if df is not None:
        rectangles = find_vwap_slope_rectangles_realtime(df)
        print_rectangles_summary(rectangles)
    else:
        print("[ERROR] Could not load data")

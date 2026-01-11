"""
Analyze VWAP Band Reversal Signals (Blue Dots) Across All Days
Detects: Close beyond 3σ → Cross back through 2σ
Tracks statistics: count, times, price levels, min/max movements
"""

import pandas as pd
from pathlib import Path
import sys
from datetime import datetime
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    DATA_DIR, OUTPUTS_DIR,
    VWAP_FAST, VWAP_BANDS_START_TIME,
    VWAP_TIME_ENTRY,
    USE_ALL_DAYS_AVAILABLE, ALL_DAYS_SEGMENT_START, ALL_DAYS_SEGMENT_END
)
from find_fractals import load_date_range
from calculate_vwap import calculate_vwap

print("="*80)
print("BAND REVERSAL ANALYSIS - DETECTING BLUE DOT SIGNALS")
print("="*80)
print()

# ============================================================================
# STEP 1: SCAN DATA FOLDER FOR AVAILABLE DATES
# ============================================================================
csv_files = list(DATA_DIR.glob("time_and_sales_nq_*.csv"))
print(f"[INFO] Found {len(csv_files)} CSV files in data folder")

if len(csv_files) == 0:
    print("[ERROR] No data files found")
    sys.exit(1)

# Extract dates from filenames
import re
date_pattern = re.compile(r"time_and_sales_nq_(\d{8})\.csv")
available_dates = []

for csv_file in csv_files:
    match = date_pattern.search(csv_file.name)
    if match:
        date_str = match.group(1)
        available_dates.append(date_str)

available_dates.sort()

# Apply segment filter if needed
if not USE_ALL_DAYS_AVAILABLE:
    available_dates = [
        date for date in available_dates
        if ALL_DAYS_SEGMENT_START <= date <= ALL_DAYS_SEGMENT_END
    ]

print(f"[INFO] Processing {len(available_dates)} dates from {available_dates[0]} to {available_dates[-1]}")
print()

# ============================================================================
# STEP 2: ANALYZE EACH DATE FOR BAND REVERSAL SIGNALS
# ============================================================================
all_blue_dots = []

for i, date_str in enumerate(available_dates, 1):
    print(f"[{i}/{len(available_dates)}] Analyzing {date_str}...")

    try:
        # Load data for this date
        df = load_date_range(date_str, date_str)

        if df.empty:
            print(f"  [WARN] No data for {date_str}")
            continue

        # Ensure timestamp column exists
        if 'timestamp' not in df.columns:
            print(f"  [ERROR] No timestamp column in data for {date_str}")
            continue

        # Calculate VWAP
        df = calculate_vwap(df, period=VWAP_FAST)

        # Re-check timestamp after VWAP calculation
        if 'timestamp' not in df.columns:
            print(f"  [ERROR] timestamp column lost after VWAP calculation for {date_str}")
            continue

        # Calculate VWAP bands
        bands_start_time = pd.to_datetime(VWAP_BANDS_START_TIME).time()
        df_bands = df[df['timestamp'].dt.time >= bands_start_time].copy()

        if df_bands.empty:
            print(f"  [WARN] No data after {VWAP_BANDS_START_TIME} for {date_str}")
            continue

        print(f"  [DEBUG] Total bars after {VWAP_BANDS_START_TIME}: {len(df_bands)}")

        # Calculate standard deviation bands
        df_bands['price_deviation'] = df_bands['close'] - df_bands['vwap_fast']
        std_dev = df_bands['price_deviation'].expanding().std()

        # Bands
        upper_band_2sigma = df_bands['vwap_fast'] + 2 * std_dev
        lower_band_2sigma = df_bands['vwap_fast'] - 2 * std_dev
        upper_band_3sigma = df_bands['vwap_fast'] + 3 * std_dev
        lower_band_3sigma = df_bands['vwap_fast'] - 3 * std_dev

        # Filter data AFTER Entry Time (if configured)
        if VWAP_TIME_ENTRY:
            entry_time = pd.to_datetime(VWAP_TIME_ENTRY).time()
            df_after_entry = df_bands[df_bands['timestamp'].dt.time > entry_time].copy()
            print(f"  [DEBUG] Bars after entry time {VWAP_TIME_ENTRY}: {len(df_after_entry)}")
        else:
            df_after_entry = df_bands.copy()
            print(f"  [DEBUG] No entry time filter - using all {len(df_after_entry)} bars")

        if df_after_entry.empty:
            print(f"  [INFO] No data after entry time for {date_str}")
            continue

        # Add bands to dataframe
        df_after_entry['upper_2sigma'] = upper_band_2sigma[df_after_entry.index]
        df_after_entry['lower_2sigma'] = lower_band_2sigma[df_after_entry.index]
        df_after_entry['upper_3sigma'] = upper_band_3sigma[df_after_entry.index]
        df_after_entry['lower_3sigma'] = lower_band_3sigma[df_after_entry.index]

        # Check if 3σ is ever touched
        upper_3sigma_touches = (df_after_entry['close'] > df_after_entry['upper_3sigma']).sum()
        lower_3sigma_touches = (df_after_entry['close'] < df_after_entry['lower_3sigma']).sum()
        print(f"  [DEBUG] 3σ touches - Upper: {upper_3sigma_touches}, Lower: {lower_3sigma_touches}")

        # Estado de seguimiento
        touched_upper_3sigma = False
        touched_lower_3sigma = False
        plotted_upper_dot = False
        plotted_lower_dot = False

        upper_3sigma_touch_price = None
        lower_3sigma_touch_price = None
        upper_3sigma_touch_time = None
        lower_3sigma_touch_time = None

        for idx, row in df_after_entry.iterrows():
            close_price = row['close']

            # BEARISH reversal: Close ABOVE upper 3σ, then cross down through upper 2σ
            if close_price > row['upper_3sigma']:
                if not touched_upper_3sigma:
                    upper_3sigma_touch_price = close_price
                    upper_3sigma_touch_time = row['timestamp']
                touched_upper_3sigma = True
                plotted_upper_dot = False

            if touched_upper_3sigma and not plotted_upper_dot and close_price < row['upper_2sigma']:
                # Blue dot detected!
                price_move = upper_3sigma_touch_price - close_price  # How much it reversed
                pct_move = (price_move / upper_3sigma_touch_price) * 100 if upper_3sigma_touch_price > 0 else 0

                all_blue_dots.append({
                    'date': date_str,
                    'signal_type': 'BEARISH',
                    'signal_time': row['timestamp'],
                    'signal_price': close_price,
                    'extreme_touch_price': upper_3sigma_touch_price,
                    'extreme_touch_time': upper_3sigma_touch_time,
                    'price_movement': price_move,
                    'pct_movement': pct_move,
                    'vwap_fast': row['vwap_fast'],
                    'band_3sigma': row['upper_3sigma'],
                    'band_2sigma': row['upper_2sigma']
                })

                print(f"  [BLUE DOT BEARISH] {row['timestamp'].time()} - ${close_price:.2f} (reversed {price_move:.2f} pts / {pct_move:.1f}%)")
                plotted_upper_dot = True

            # BULLISH reversal: Close BELOW lower 3σ, then cross up through lower 2σ
            if close_price < row['lower_3sigma']:
                if not touched_lower_3sigma:
                    lower_3sigma_touch_price = close_price
                    lower_3sigma_touch_time = row['timestamp']
                touched_lower_3sigma = True
                plotted_lower_dot = False

            if touched_lower_3sigma and not plotted_lower_dot and close_price > row['lower_2sigma']:
                # Blue dot detected!
                price_move = close_price - lower_3sigma_touch_price  # How much it reversed
                pct_move = (price_move / lower_3sigma_touch_price) * 100 if lower_3sigma_touch_price > 0 else 0

                all_blue_dots.append({
                    'date': date_str,
                    'signal_type': 'BULLISH',
                    'signal_time': row['timestamp'],
                    'signal_price': close_price,
                    'extreme_touch_price': lower_3sigma_touch_price,
                    'extreme_touch_time': lower_3sigma_touch_time,
                    'price_movement': price_move,
                    'pct_movement': pct_move,
                    'vwap_fast': row['vwap_fast'],
                    'band_3sigma': row['lower_3sigma'],
                    'band_2sigma': row['lower_2sigma']
                })

                print(f"  [BLUE DOT BULLISH] {row['timestamp'].time()} - ${close_price:.2f} (reversed {price_move:.2f} pts / {pct_move:.1f}%)")
                plotted_lower_dot = True

    except Exception as e:
        print(f"  [ERROR] Failed to analyze {date_str}: {e}")
        continue

print()
print("="*80)
print("CONSOLIDATION & STATISTICS")
print("="*80)
print()

# ============================================================================
# STEP 3: SAVE RESULTS AND GENERATE STATISTICS
# ============================================================================
if len(all_blue_dots) == 0:
    print("[WARN] No blue dot signals detected in any date")
    sys.exit(0)

# Convert to DataFrame
df_blue_dots = pd.DataFrame(all_blue_dots)

# Save to CSV
output_file = OUTPUTS_DIR / "band_reversal_analysis.csv"
df_blue_dots.to_csv(output_file, index=False, sep=';', decimal=',')
print(f"[OK] Saved {len(df_blue_dots)} blue dot signals to: {output_file.name}")

# Calculate statistics
total_signals = len(df_blue_dots)
bullish_signals = len(df_blue_dots[df_blue_dots['signal_type'] == 'BULLISH'])
bearish_signals = len(df_blue_dots[df_blue_dots['signal_type'] == 'BEARISH'])

# Price movement stats
avg_price_move = df_blue_dots['price_movement'].mean()
max_price_move = df_blue_dots['price_movement'].max()
min_price_move = df_blue_dots['price_movement'].min()

avg_pct_move = df_blue_dots['pct_movement'].mean()
max_pct_move = df_blue_dots['pct_movement'].max()
min_pct_move = df_blue_dots['pct_movement'].min()

# Bullish stats
if bullish_signals > 0:
    bullish_df = df_blue_dots[df_blue_dots['signal_type'] == 'BULLISH']
    bullish_avg_move = bullish_df['price_movement'].mean()
    bullish_avg_pct = bullish_df['pct_movement'].mean()
    bullish_max_move = bullish_df['price_movement'].max()
    bullish_min_move = bullish_df['price_movement'].min()

# Bearish stats
if bearish_signals > 0:
    bearish_df = df_blue_dots[df_blue_dots['signal_type'] == 'BEARISH']
    bearish_avg_move = bearish_df['price_movement'].mean()
    bearish_avg_pct = bearish_df['pct_movement'].mean()
    bearish_max_move = bearish_df['price_movement'].max()
    bearish_min_move = bearish_df['price_movement'].min()

# Daily stats
daily_stats = df_blue_dots.groupby('date').agg({
    'signal_type': 'count',
    'price_movement': ['mean', 'max', 'min'],
    'pct_movement': ['mean', 'max', 'min']
}).reset_index()
daily_stats.columns = ['date', 'total_signals', 'avg_price_move', 'max_price_move', 'min_price_move',
                       'avg_pct_move', 'max_pct_move', 'min_pct_move']

# Print summary
print()
print("SUMMARY STATISTICS")
print("-"*80)
print(f"Total Blue Dot Signals:     {total_signals}")
print(f"  - Bullish (LONG entry):   {bullish_signals}")
print(f"  - Bearish (SHORT entry):  {bearish_signals}")
print()
print(f"Average Price Movement:     {avg_price_move:.2f} points ({avg_pct_move:.2f}%)")
print(f"Maximum Price Movement:     {max_price_move:.2f} points ({max_pct_move:.2f}%)")
print(f"Minimum Price Movement:     {min_price_move:.2f} points ({min_pct_move:.2f}%)")
print()

if bullish_signals > 0:
    print("BULLISH SIGNALS:")
    print(f"  Count:                    {bullish_signals}")
    print(f"  Avg Movement:             {bullish_avg_move:.2f} points ({bullish_avg_pct:.2f}%)")
    print(f"  Max Movement:             {bullish_max_move:.2f} points")
    print(f"  Min Movement:             {bullish_min_move:.2f} points")
    print()

if bearish_signals > 0:
    print("BEARISH SIGNALS:")
    print(f"  Count:                    {bearish_signals}")
    print(f"  Avg Movement:             {bearish_avg_move:.2f} points ({bearish_avg_pct:.2f}%)")
    print(f"  Max Movement:             {bearish_max_move:.2f} points")
    print(f"  Min Movement:             {bearish_min_move:.2f} points")
    print()

print("TOP 10 DAYS BY SIGNAL COUNT:")
print("-"*80)
top_days = daily_stats.nlargest(10, 'total_signals')
for _, day in top_days.iterrows():
    print(f"{day['date']}: {int(day['total_signals'])} signals (avg move: {day['avg_price_move']:.2f} pts / {day['avg_pct_move']:.2f}%)")

print()
print("="*80)
print(f"Analysis complete. Results saved to: {output_file.name}")
print("="*80)

"""
VWAP Band Reversal Strategy (Blue Dot Strategy)
Enters when price shows extreme deviation (3σ) then mean reverts through 2σ band.

Logic:
- LONG Entry: Close < lower 3σ band, then crosses back > lower 2σ band
- SHORT Entry: Close > upper 3σ band, then crosses back < upper 2σ band
- Exit: TP, SL, or Time-based exit
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, time
from config import (
    DATE, START_DATE, END_DATE,
    ENABLE_VWAP_BAND_REVERSAL_STRATEGY,
    VWAP_BAND_REVERSAL_START_TIME, VWAP_BAND_REVERSAL_EXIT_TIME,
    VWAP_BAND_REVERSAL_TP_POINTS, VWAP_BAND_REVERSAL_SL_POINTS,
    VWAP_FAST, VWAP_BANDS_START_TIME, DATA_DIR, OUTPUTS_DIR,
    MAX_NUM_TRADES_PER_DAY
)
from show_config_dashboard import update_dashboard

# Auto-update configuration dashboard
update_dashboard()

# Check if strategy is enabled
if not ENABLE_VWAP_BAND_REVERSAL_STRATEGY:
    print("\n" + "="*80)
    print("VWAP BAND REVERSAL STRATEGY - DISABLED")
    print("="*80)
    exit(0)

# ============================================================================
# STRATEGY CONFIGURATION
# ============================================================================
TRADING_DIR = OUTPUTS_DIR / "trading"
TRADING_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = TRADING_DIR / f"tracking_record_vwap_band_reversal_{DATE}.csv"
POINT_VALUE = 20.0

print("="*80)
print("VWAP BAND REVERSAL STRATEGY - ENABLED")
print("="*80)
print(f"Configuration:")
print(f"  - Signal Detection: Close beyond 3-sigma -> Cross back through 2-sigma")
print(f"  - Signal Window: After {VWAP_BAND_REVERSAL_START_TIME}")
print(f"  - Exit Time: {VWAP_BAND_REVERSAL_EXIT_TIME}")
print(f"  - TP/SL: {VWAP_BAND_REVERSAL_TP_POINTS}/{VWAP_BAND_REVERSAL_SL_POINTS} points")
print(f"  - Max Trades Per Day: {MAX_NUM_TRADES_PER_DAY}")

# ============================================================================
# LOAD DATA
# ============================================================================
from find_fractals import load_date_range
from calculate_vwap import calculate_vwap

print(f"\n[INFO] Loading data for {START_DATE} to {END_DATE}...")
df = load_date_range(START_DATE, END_DATE)

if df.empty:
    print("[ERROR] No data loaded")
    exit(1)

# Calculate VWAP Fast
df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)

# Calculate VWAP bands starting from VWAP_BANDS_START_TIME
bands_start_time = pd.to_datetime(VWAP_BANDS_START_TIME).time()
df_bands = df[df['timestamp'].dt.time >= bands_start_time].copy()

if df_bands.empty:
    print(f"[ERROR] No data after {VWAP_BANDS_START_TIME}")
    exit(1)

# Calculate standard deviation bands
df_bands['price_deviation'] = df_bands['close'] - df_bands['vwap_fast']
std_dev = df_bands['price_deviation'].expanding().std()

# Create band columns
df_bands['upper_2sigma'] = df_bands['vwap_fast'] + 2 * std_dev
df_bands['lower_2sigma'] = df_bands['vwap_fast'] - 2 * std_dev
df_bands['upper_3sigma'] = df_bands['vwap_fast'] + 3 * std_dev
df_bands['lower_3sigma'] = df_bands['vwap_fast'] - 3 * std_dev

# Merge bands back to main dataframe
df = df.merge(
    df_bands[['timestamp', 'upper_2sigma', 'lower_2sigma', 'upper_3sigma', 'lower_3sigma']],
    on='timestamp',
    how='left'
)

# ============================================================================
# STRATEGY EXECUTION
# ============================================================================
trades = []
open_position = None

# Parse times
signal_start_time_obj = pd.to_datetime(VWAP_BAND_REVERSAL_START_TIME).time()
exit_time_obj = pd.to_datetime(VWAP_BAND_REVERSAL_EXIT_TIME).time()

# Track 3σ touches
touched_upper_3sigma = False
touched_lower_3sigma = False
upper_3sigma_touch_price = None
lower_3sigma_touch_price = None

print(f"\n[INFO] Processing band reversal signals...")

for idx, bar in df.iterrows():
    current_time = bar['timestamp'].time()
    close_price = bar['close']

    # Skip if bands not available yet
    if pd.isna(bar['upper_3sigma']) or pd.isna(bar['lower_3sigma']):
        continue

    # Check exits if position is open
    if open_position:
        direction = open_position['direction']
        entry_price = open_position['entry_price']
        tp_price = open_position['tp_price']
        sl_price = open_position['sl_price']

        # Time-based exit
        if current_time >= exit_time_obj:
            exit_price = close_price
            pnl = (exit_price - entry_price) if direction == 'BUY' else (entry_price - exit_price)
            pnl_usd = pnl * POINT_VALUE

            trades.append({
                'entry_time': open_position['entry_time'],
                'exit_time': bar['timestamp'],
                'direction': direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'pnl_usd': pnl_usd,
                'exit_reason': 'time_exit',
                'tp_price': tp_price,
                'sl_price': sl_price,
                'time_in_market': (bar['timestamp'] - open_position['entry_time']).total_seconds()/60
            })

            print(f"[EXIT TIME] {current_time} {direction} @ {exit_price:.2f} | PnL: {pnl:+.2f} pts (${pnl_usd:+,.2f})")
            open_position = None
            continue

        # TP/SL exits
        if direction == 'BUY':
            # TP
            if close_price >= tp_price:
                exit_price = tp_price
                pnl = exit_price - entry_price
                pnl_usd = pnl * POINT_VALUE

                trades.append({
                    'entry_time': open_position['entry_time'],
                    'exit_time': bar['timestamp'],
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_usd': pnl_usd,
                    'exit_reason': 'tp_exit',
                    'tp_price': tp_price,
                    'sl_price': sl_price,
                    'time_in_market': (bar['timestamp'] - open_position['entry_time']).total_seconds()/60
                })

                print(f"[EXIT TP] {current_time} {direction} @ {exit_price:.2f} | PnL: {pnl:+.2f} pts (${pnl_usd:+,.2f})")
                open_position = None
                continue

            # SL
            if close_price <= sl_price:
                exit_price = sl_price
                pnl = exit_price - entry_price
                pnl_usd = pnl * POINT_VALUE

                trades.append({
                    'entry_time': open_position['entry_time'],
                    'exit_time': bar['timestamp'],
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_usd': pnl_usd,
                    'exit_reason': 'sl_exit',
                    'tp_price': tp_price,
                    'sl_price': sl_price,
                    'time_in_market': (bar['timestamp'] - open_position['entry_time']).total_seconds()/60
                })

                print(f"[EXIT SL] {current_time} {direction} @ {exit_price:.2f} | PnL: {pnl:+.2f} pts (${pnl_usd:+,.2f})")
                open_position = None
                continue

        else:  # SELL
            # TP
            if close_price <= tp_price:
                exit_price = tp_price
                pnl = entry_price - exit_price
                pnl_usd = pnl * POINT_VALUE

                trades.append({
                    'entry_time': open_position['entry_time'],
                    'exit_time': bar['timestamp'],
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_usd': pnl_usd,
                    'exit_reason': 'tp_exit',
                    'tp_price': tp_price,
                    'sl_price': sl_price,
                    'time_in_market': (bar['timestamp'] - open_position['entry_time']).total_seconds()/60
                })

                print(f"[EXIT TP] {current_time} {direction} @ {exit_price:.2f} | PnL: {pnl:+.2f} pts (${pnl_usd:+,.2f})")
                open_position = None
                continue

            # SL
            if close_price >= sl_price:
                exit_price = sl_price
                pnl = entry_price - exit_price
                pnl_usd = pnl * POINT_VALUE

                trades.append({
                    'entry_time': open_position['entry_time'],
                    'exit_time': bar['timestamp'],
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_usd': pnl_usd,
                    'exit_reason': 'sl_exit',
                    'tp_price': tp_price,
                    'sl_price': sl_price,
                    'time_in_market': (bar['timestamp'] - open_position['entry_time']).total_seconds()/60
                })

                print(f"[EXIT SL] {current_time} {direction} @ {exit_price:.2f} | PnL: {pnl:+.2f} pts (${pnl_usd:+,.2f})")
                open_position = None
                continue

    # Check for entry signals (only if no position open)
    if open_position is None:
        # Check max trades per day
        if len(trades) >= MAX_NUM_TRADES_PER_DAY:
            continue

        # Only look for signals after signal start time
        if current_time < signal_start_time_obj:
            continue

        # BEARISH signal: Close ABOVE upper 3σ, then cross down through upper 2σ
        if close_price > bar['upper_3sigma']:
            touched_upper_3sigma = True
            upper_3sigma_touch_price = close_price

        if touched_upper_3sigma and close_price < bar['upper_2sigma']:
            # SHORT entry signal
            direction = 'SELL'
            entry_price = close_price
            tp_price = entry_price - VWAP_BAND_REVERSAL_TP_POINTS
            sl_price = entry_price + VWAP_BAND_REVERSAL_SL_POINTS

            open_position = {
                'direction': direction,
                'entry_time': bar['timestamp'],
                'entry_price': entry_price,
                'tp_price': tp_price,
                'sl_price': sl_price
            }

            print(f"[ENTRY SHORT] {current_time} @ {entry_price:.2f} (Blue Dot Bearish) | TP: {tp_price:.2f} | SL: {sl_price:.2f}")
            touched_upper_3sigma = False  # Reset
            continue

        # BULLISH signal: Close BELOW lower 3σ, then cross up through lower 2σ
        if close_price < bar['lower_3sigma']:
            touched_lower_3sigma = True
            lower_3sigma_touch_price = close_price

        if touched_lower_3sigma and close_price > bar['lower_2sigma']:
            # LONG entry signal
            direction = 'BUY'
            entry_price = close_price
            tp_price = entry_price + VWAP_BAND_REVERSAL_TP_POINTS
            sl_price = entry_price - VWAP_BAND_REVERSAL_SL_POINTS

            open_position = {
                'direction': direction,
                'entry_time': bar['timestamp'],
                'entry_price': entry_price,
                'tp_price': tp_price,
                'sl_price': sl_price
            }

            print(f"[ENTRY LONG] {current_time} @ {entry_price:.2f} (Blue Dot Bullish) | TP: {tp_price:.2f} | SL: {sl_price:.2f}")
            touched_lower_3sigma = False  # Reset
            continue

# Save trades
if trades:
    df_trades = pd.DataFrame(trades)
    df_trades.to_csv(OUTPUT_FILE, index=False, sep=';', decimal=',')

    # Calculate Summary
    total_pnl_pts = df_trades['pnl'].sum()
    total_pnl_usd = df_trades['pnl_usd'].sum()

    print(f"\n[OK] Strategy executed successfully")
    print(f"[OK] Total trades: {len(df_trades)}")
    print(f"[OK] Total P&L: {total_pnl_pts:+.2f} pts (${total_pnl_usd:+,.2f})")
    print(f"[OK] Saved to: {OUTPUT_FILE.name}")
else:
    print(f"\n[INFO] No trades generated for {DATE}")

print("[OK] Strategy execution complete")

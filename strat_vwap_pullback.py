"""
VWAP Pullback Strategy (Price Ejection Pullback - Green Dots with Trend Filter)
Strategy based on price ejection pullbacks within trend:
- LONG (BUY): Green dot BELOW VWAP Fast when VWAP Fast > VWAP Slow (buy the dip in uptrend)
- SHORT (SELL): Green dot ABOVE VWAP Fast when VWAP Fast < VWAP Slow (sell the rally in downtrend)
- Fixed TP and SL from config
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, time
from config import (
    DATE, START_DATE, END_DATE,
    VWAP_FAST, VWAP_SLOW, PRICE_EJECTION_TRIGGER,
    DATA_DIR, OUTPUTS_DIR, POINT_VALUE,
    ENABLE_VWAP_PULLBACK_STRATEGY,
    VWAP_PULLBACK_TP_POINTS, VWAP_PULLBACK_SL_POINTS,
    VWAP_PULLBACK_MAX_POSITIONS,
    VWAP_PULLBACK_START_HOUR, VWAP_PULLBACK_END_HOUR
)
from calculate_vwap import calculate_vwap
from show_config_dashboard import update_dashboard

# Auto-update configuration dashboard
update_dashboard()

# Map to shorter names for compatibility
TP_POINTS = VWAP_PULLBACK_TP_POINTS
SL_POINTS = VWAP_PULLBACK_SL_POINTS
MAXIMUM_POSITIONS_OPEN = VWAP_PULLBACK_MAX_POSITIONS
START_TRADING_HOUR = VWAP_PULLBACK_START_HOUR
END_TRADING_HOUR = VWAP_PULLBACK_END_HOUR

# ============================================================================
# CHECK IF STRATEGY IS ENABLED
# ============================================================================
if not ENABLE_VWAP_PULLBACK_STRATEGY:
    print("\n" + "="*80)
    print("VWAP PULLBACK STRATEGY - DISABLED")
    print("="*80)
    print("\n[INFO] Strategy is disabled in config.py")
    print("[INFO] Set ENABLE_VWAP_PULLBACK_STRATEGY = True to enable")
    print("="*80 + "\n")
    exit(0)

# ============================================================================
# STRATEGY CONFIGURATION
# ============================================================================
TRADING_DIR = OUTPUTS_DIR / "trading"
TRADING_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = TRADING_DIR / f"tracking_record_vwap_pullback_{DATE}.csv"

# Parse trading time range
start_time = datetime.strptime(START_TRADING_HOUR, "%H:%M:%S").time()
end_time = datetime.strptime(END_TRADING_HOUR, "%H:%M:%S").time()

# Calculate day of week
date_obj = datetime.strptime(DATE, "%Y%m%d")
day_of_week = date_obj.isoweekday()
day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
day_name = day_names[day_of_week]

# ============================================================================
# PRINT STRATEGY HEADER
# ============================================================================
print("\n" + "="*80)
print("VWAP PULLBACK STRATEGY - Price Ejection Pullback with Trend Filter")
print("="*80)
print(f"\nDate: {DATE} ({day_name})")
print(f"Trading Hours: {START_TRADING_HOUR} to {END_TRADING_HOUR}")
print(f"\nStrategy Parameters:")
print(f"  - Take Profit: {TP_POINTS} points (${TP_POINTS * POINT_VALUE:.0f})")
print(f"  - Stop Loss: {SL_POINTS} points (${SL_POINTS * POINT_VALUE:.0f})")
print(f"  - Max Positions: {MAXIMUM_POSITIONS_OPEN}")
print(f"  - VWAP Fast Period: {VWAP_FAST}")
print(f"  - VWAP Slow Period: {VWAP_SLOW}")
print(f"  - Price Ejection Trigger: {PRICE_EJECTION_TRIGGER*100:.1f}%")
print(f"  - Point Value: ${POINT_VALUE:.0f} per point")
print(f"\nEntry Logic (Pullback with Trend Filter):")
print(f"  - LONG: Green dot BELOW VWAP Fast + VWAP Fast > VWAP Slow (buy dip in uptrend)")
print(f"  - SHORT: Green dot ABOVE VWAP Fast + VWAP Fast < VWAP Slow (sell rally in downtrend)")
print("="*80 + "\n")

# ============================================================================
# LOAD DATA
# ============================================================================
from find_fractals import load_date_range

print(f"[INFO] Loading data for date: {DATE}")
df = load_date_range(START_DATE, END_DATE)

if df is None:
    print("[ERROR] Could not load data")
    exit(1)

print(f"[OK] Data loaded: {len(df)} bars")

# ============================================================================
# CALCULATE INDICATORS
# ============================================================================
# Calculate VWAP Fast
df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)

# Calculate VWAP Slow (required for trend filter)
df['vwap_slow'] = calculate_vwap(df, period=VWAP_SLOW)

# Calculate price-VWAP distance (this creates the green dots)
df['price_vwap_distance'] = abs((df['close'] - df['vwap_fast']) / df['vwap_fast'])

# Detect price ejection signals (green dots)
df['price_ejection'] = (df['price_vwap_distance'] > PRICE_EJECTION_TRIGGER) & (df['vwap_fast'].notna())

# Detect when price is above or below VWAP
df['price_above_vwap'] = (df['close'] > df['vwap_fast']).astype(bool)
df['price_below_vwap'] = (df['close'] < df['vwap_fast']).astype(bool)

# Detect trend based on VWAP Fast vs VWAP Slow
df['uptrend'] = (df['vwap_fast'] > df['vwap_slow']) & (df['vwap_slow'].notna())
df['downtrend'] = (df['vwap_fast'] < df['vwap_slow']) & (df['vwap_slow'].notna())

# Entry signals (PULLBACK LOGIC):
# LONG: Green dot BELOW VWAP (pullback) + VWAP Fast > VWAP Slow (uptrend) = Buy the dip
# SHORT: Green dot ABOVE VWAP (pullback) + VWAP Fast < VWAP Slow (downtrend) = Sell the rally
df['long_signal'] = df['price_ejection'] & df['price_below_vwap'] & df['uptrend']
df['short_signal'] = df['price_ejection'] & df['price_above_vwap'] & df['downtrend']

print(f"[INFO] VWAP Fast calculated (period={VWAP_FAST})")
print(f"[INFO] VWAP Slow calculated (period={VWAP_SLOW})")
print(f"[INFO] Price ejection signals (green dots): {df['price_ejection'].sum()}")
print(f"[INFO] LONG entry signals (green dots below VWAP in uptrend): {df['long_signal'].sum()}")
print(f"[INFO] SHORT entry signals (green dots above VWAP in downtrend): {df['short_signal'].sum()}")

# ============================================================================
# STRATEGY EXECUTION
# ============================================================================
trades = []
open_position = None

print(f"\n[INFO] Processing trades...")

for idx, bar in df.iterrows():
    current_time = bar['timestamp'].time()

    # Check if within trading hours
    within_trading_hours = start_time <= current_time <= end_time

    # ========================================================================
    # EXIT LOGIC - Check if we should exit an open position
    # ========================================================================
    if open_position is not None:
        direction = open_position['direction']
        entry_price = open_position['entry_price']
        tp_price = open_position['tp_price']
        sl_price = open_position['sl_price']

        exit_reason = None
        exit_price = None

        if direction == 'BUY':
            # LONG position: TP when price goes up, SL when price goes down
            if bar['high'] >= tp_price:
                exit_reason = 'tp_exit'
                exit_price = tp_price
            elif bar['low'] <= sl_price:
                exit_reason = 'sl_exit'
                exit_price = sl_price
        else:  # SELL
            # SHORT position: TP when price goes down, SL when price goes up
            if bar['low'] <= tp_price:
                exit_reason = 'tp_exit'
                exit_price = tp_price
            elif bar['high'] >= sl_price:
                exit_reason = 'sl_exit'
                exit_price = sl_price

        # Close position if exit condition met
        if exit_reason:
            if direction == 'BUY':
                pnl_points = exit_price - entry_price
            else:
                pnl_points = entry_price - exit_price

            pnl_usd = pnl_points * POINT_VALUE

            trades.append({
                'direction': direction,
                'entry_time': open_position['entry_time'],
                'entry_price': entry_price,
                'exit_time': bar['timestamp'],
                'exit_price': exit_price,
                'pnl': pnl_points,
                'pnl_usd': pnl_usd,
                'exit_reason': exit_reason,
                'entry_vwap_fast': open_position['entry_vwap_fast'],
                'entry_vwap_slow': open_position['entry_vwap_slow']
            })

            open_position = None

    # ========================================================================
    # ENTRY LOGIC - Check if we should enter a new position
    # ========================================================================
    if open_position is None and within_trading_hours:
        # LONG signal: Green dot below VWAP in uptrend (buy the dip)
        if bar['long_signal']:
            entry_price = bar['close']
            tp_price = entry_price + TP_POINTS
            sl_price = entry_price - SL_POINTS

            open_position = {
                'direction': 'BUY',
                'entry_time': bar['timestamp'],
                'entry_price': entry_price,
                'entry_vwap_fast': bar['vwap_fast'],
                'entry_vwap_slow': bar['vwap_slow'],
                'tp_price': tp_price,
                'sl_price': sl_price
            }

        # SHORT signal: Green dot above VWAP in downtrend (sell the rally)
        elif bar['short_signal']:
            entry_price = bar['close']
            tp_price = entry_price - TP_POINTS  # TP is below entry for shorts
            sl_price = entry_price + SL_POINTS  # SL is above entry for shorts

            open_position = {
                'direction': 'SELL',
                'entry_time': bar['timestamp'],
                'entry_price': entry_price,
                'entry_vwap_fast': bar['vwap_fast'],
                'entry_vwap_slow': bar['vwap_slow'],
                'tp_price': tp_price,
                'sl_price': sl_price
            }

# Close any remaining open position at end of day
if open_position is not None:
    last_bar = df.iloc[-1]
    direction = open_position['direction']
    entry_price = open_position['entry_price']
    exit_price = last_bar['close']

    if direction == 'BUY':
        pnl_points = exit_price - entry_price
    else:
        pnl_points = entry_price - exit_price

    pnl_usd = pnl_points * POINT_VALUE

    trades.append({
        'direction': direction,
        'entry_time': open_position['entry_time'],
        'entry_price': entry_price,
        'exit_time': last_bar['timestamp'],
        'exit_price': exit_price,
        'pnl': pnl_points,
        'pnl_usd': pnl_usd,
        'exit_reason': 'eod_exit',
        'entry_vwap_fast': open_position['entry_vwap_fast'],
        'entry_vwap_slow': open_position['entry_vwap_slow']
    })

    open_position = None

# ============================================================================
# SAVE RESULTS
# ============================================================================
if len(trades) > 0:
    df_trades = pd.DataFrame(trades)
    df_trades.to_csv(OUTPUT_FILE, index=False, sep=';', decimal=',')

    print(f"\n[OK] Strategy completed: {len(trades)} trades executed")
    print(f"[OK] Trades saved to: {OUTPUT_FILE}")

    # Statistics
    profit_trades = df_trades[df_trades['exit_reason'] == 'tp_exit']
    stop_trades = df_trades[df_trades['exit_reason'] == 'sl_exit']
    eod_trades = df_trades[df_trades['exit_reason'] == 'eod_exit']

    total_pnl = df_trades['pnl'].sum()
    total_pnl_usd = df_trades['pnl_usd'].sum()

    total_trades = len(df_trades)
    profit_count = len(profit_trades)
    stop_count = len(stop_trades)
    eod_count = len(eod_trades)
    denom = profit_count + stop_count
    win_rate = (profit_count / denom * 100) if denom > 0 else 0.0

    avg_points = total_pnl / total_trades if total_trades > 0 else 0.0
    avg_usd = total_pnl_usd / total_trades if total_trades > 0 else 0.0

    # Breakdown by direction
    buy_trades = df_trades[df_trades['direction'] == 'BUY']
    sell_trades = df_trades[df_trades['direction'] == 'SELL']
    buy_pnl_usd = buy_trades['pnl_usd'].sum() if len(buy_trades) > 0 else 0.0
    sell_pnl_usd = sell_trades['pnl_usd'].sum() if len(sell_trades) > 0 else 0.0

    print("\n" + "="*80)
    print("TEST RESULTS - VWAP PULLBACK STRATEGY")
    print("="*80)
    print(f"Date: {DATE}")
    print(f"Total trades: {total_trades}")
    print(f"Exit breakdown: {profit_count} TP / {stop_count} SL / {eod_count} EOD")
    print(f"Win rate: {win_rate:.1f}% ({profit_count} profits / {stop_count} stops)")
    print(f"Total P&L: {total_pnl:+.0f} points (${total_pnl_usd:,.0f})")
    print(f"Average per trade: {avg_points:+.2f} points (${avg_usd:,.2f})")
    print(f"BUY trades: {len(buy_trades)} (${buy_pnl_usd:,.0f})")
    print(f"SELL trades: {len(sell_trades)} (${sell_pnl_usd:,.0f})")
    print("="*80 + "\n")

else:
    print(f"\n[INFO] No trades executed")
    print(f"[INFO] No output file generated")

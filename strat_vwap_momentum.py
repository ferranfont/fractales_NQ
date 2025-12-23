"""
VWAP Momentum Strategy
Simple strategy based on price ejection from VWAP Fast:
- BUY when price crosses above VWAP Fast (green dots)
- SELL when price crosses below VWAP Fast (green dots)
- Fixed TP and SL from config
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, time
from config import (
    DATE, START_DATE, END_DATE,
    TP_POINTS, SL_POINTS, MAXIMUM_POSITIONS_OPEN,
    START_TRADING_HOUR, END_TRADING_HOUR,
    VWAP_FAST, PRICE_EJECTION_TRIGGER,
    DATA_DIR, OUTPUTS_DIR
)

# ============================================================================
# STRATEGY CONFIGURATION
# ============================================================================
TRADING_DIR = OUTPUTS_DIR / "trading"
TRADING_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = TRADING_DIR / f"trading_vwap_momentum_{DATE}.csv"
POINT_VALUE = 20.0  # USD value per point for NQ futures

# Parse trading time range
start_time = datetime.strptime(START_TRADING_HOUR, "%H:%M:%S").time()
end_time = datetime.strptime(END_TRADING_HOUR, "%H:%M:%S").time()

print("="*80)
print("VWAP MOMENTUM STRATEGY")
print("="*80)
print(f"\nConfiguration:")
print(f"  - Date: {DATE}")
print(f"  - Take Profit: {TP_POINTS} points (${TP_POINTS * POINT_VALUE:.0f})")
print(f"  - Stop Loss: {SL_POINTS} points (${SL_POINTS * POINT_VALUE:.0f})")
print(f"  - Max Positions: {MAXIMUM_POSITIONS_OPEN}")
print(f"  - VWAP Fast Period: {VWAP_FAST}")
print(f"  - Price Ejection Trigger: {PRICE_EJECTION_TRIGGER*100:.1f}%")
print(f"  - Trading Hours: {START_TRADING_HOUR} to {END_TRADING_HOUR}")
print(f"  - Point Value: ${POINT_VALUE:.0f} per point")

# ============================================================================
# LOAD DATA
# ============================================================================
# Load tick data and aggregate to OHLC
from find_fractals import load_date_range

print(f"\n[INFO] Loading data for {START_DATE} to {END_DATE}...")
df = load_date_range(START_DATE, END_DATE)

if df is None:
    print("[ERROR] No data loaded")
    exit(1)

print(f"[OK] Loaded {len(df):,} bars")

# Calculate VWAP Fast
from calculate_vwap import calculate_vwap
df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)

# Calculate price-VWAP distance
df['price_vwap_distance'] = abs((df['close'] - df['vwap_fast']) / df['vwap_fast'])

# Detect crossovers
df['price_above_vwap'] = (df['close'] > df['vwap_fast']).astype(bool)
df['cross_above'] = (df['price_above_vwap']) & (~df['price_above_vwap'].shift(1).fillna(False))
df['cross_below'] = (~df['price_above_vwap']) & (df['price_above_vwap'].shift(1).fillna(False))

print(f"[INFO] VWAP Fast calculated")
print(f"[INFO] Cross above signals: {df['cross_above'].sum()}")
print(f"[INFO] Cross below signals: {df['cross_below'].sum()}")

# ============================================================================
# STRATEGY EXECUTION
# ============================================================================
trades = []
open_position = None

print(f"\n[INFO] Processing trades...")

for idx, bar in df.iterrows():
    current_time = bar['timestamp'].time()

    # Check if within trading hours
    if not (start_time <= current_time <= end_time):
        continue

    # Skip if VWAP not available
    if pd.isna(bar['vwap_fast']):
        continue

    # Check if we have an open position - manage exit
    if open_position is not None:
        direction = open_position['direction']
        entry_price = open_position['entry_price']
        tp_price = open_position['tp_price']
        sl_price = open_position['sl_price']

        # Check exit conditions
        exit_reason = None
        exit_price = None

        if direction == 'BUY':
            # Check TP (price goes up)
            if bar['high'] >= tp_price:
                exit_reason = 'profit'
                exit_price = tp_price
            # Check SL (price goes down)
            elif bar['low'] <= sl_price:
                exit_reason = 'stop'
                exit_price = sl_price

        else:  # SELL
            # Check TP (price goes down)
            if bar['low'] <= tp_price:
                exit_reason = 'profit'
                exit_price = tp_price
            # Check SL (price goes up)
            elif bar['high'] >= sl_price:
                exit_reason = 'stop'
                exit_price = sl_price

        # Close position if exit triggered
        if exit_reason:
            if direction == 'BUY':
                pnl = exit_price - entry_price
            else:  # SELL
                pnl = entry_price - exit_price

            pnl_usd = pnl * POINT_VALUE

            trades.append({
                'entry_time': open_position['entry_time'],
                'exit_time': bar['timestamp'],
                'direction': direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'entry_vwap': open_position['entry_vwap'],
                'exit_vwap': bar['vwap_fast'],
                'tp_price': tp_price,
                'sl_price': sl_price,
                'exit_reason': exit_reason,
                'pnl': pnl,
                'pnl_usd': pnl_usd
            })

            open_position = None
            continue

    # Check for new entry signals (only if no position open)
    if open_position is None and MAXIMUM_POSITIONS_OPEN > 0:
        # BUY signal: Cross above VWAP
        if bar['cross_above']:
            entry_price = bar['close']
            tp_price = entry_price + TP_POINTS
            sl_price = entry_price - SL_POINTS

            open_position = {
                'entry_time': bar['timestamp'],
                'direction': 'BUY',
                'entry_price': entry_price,
                'entry_vwap': bar['vwap_fast'],
                'tp_price': tp_price,
                'sl_price': sl_price
            }

        # SELL signal: Cross below VWAP
        elif bar['cross_below']:
            entry_price = bar['close']
            tp_price = entry_price - TP_POINTS
            sl_price = entry_price + SL_POINTS

            open_position = {
                'entry_time': bar['timestamp'],
                'direction': 'SELL',
                'entry_price': entry_price,
                'entry_vwap': bar['vwap_fast'],
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
        pnl = exit_price - entry_price
    else:  # SELL
        pnl = entry_price - exit_price

    pnl_usd = pnl * POINT_VALUE

    trades.append({
        'entry_time': open_position['entry_time'],
        'exit_time': last_bar['timestamp'],
        'direction': direction,
        'entry_price': entry_price,
        'exit_price': exit_price,
        'entry_vwap': open_position['entry_vwap'],
        'exit_vwap': last_bar['vwap_fast'],
        'tp_price': open_position['tp_price'],
        'sl_price': open_position['sl_price'],
        'exit_reason': 'eod',
        'pnl': pnl,
        'pnl_usd': pnl_usd
    })

# ============================================================================
# SAVE RESULTS
# ============================================================================
if len(trades) > 0:
    df_trades = pd.DataFrame(trades)

    # Add sequential trade ID (starting from 1)
    df_trades.insert(0, 'trade_id', range(1, len(df_trades) + 1))

    # Save to CSV
    df_trades.to_csv(OUTPUT_FILE, index=False, sep=';', decimal=',')

    print(f"\n[OK] Strategy completed: {len(trades)} trades executed")
    print(f"[OK] Trades saved to: {OUTPUT_FILE}")

    # Statistics
    profit_trades = df_trades[df_trades['exit_reason'] == 'profit']
    stop_trades = df_trades[df_trades['exit_reason'] == 'stop']
    eod_trades = df_trades[df_trades['exit_reason'] == 'eod']

    total_pnl = df_trades['pnl'].sum()
    total_pnl_usd = df_trades['pnl_usd'].sum()

    print("\n" + "="*80)
    print("STRATEGY STATISTICS")
    print("="*80)
    print(f"Total trades: {len(df_trades)}")
    print(f"  - PROFIT exits: {len(profit_trades)} ({len(profit_trades)/len(df_trades)*100:.1f}%)")
    print(f"  - STOP exits: {len(stop_trades)} ({len(stop_trades)/len(df_trades)*100:.1f}%)")
    print(f"  - EOD exits: {len(eod_trades)} ({len(eod_trades)/len(df_trades)*100:.1f}%)")

    print(f"\nTotal P&L: {total_pnl:.2f} points (${total_pnl_usd:,.2f})")
    print(f"Average P&L per trade: {total_pnl/len(df_trades):.2f} points (${total_pnl_usd/len(df_trades):,.2f})")

    # Breakdown by direction
    buy_trades = df_trades[df_trades['direction'] == 'BUY']
    sell_trades = df_trades[df_trades['direction'] == 'SELL']

    print(f"\nBUY trades: {len(buy_trades)}")
    if len(buy_trades) > 0:
        buy_pnl = buy_trades['pnl'].sum()
        buy_pnl_usd = buy_trades['pnl_usd'].sum()
        print(f"  - P&L: {buy_pnl:.2f} points (${buy_pnl_usd:,.2f})")
        print(f"  - Profit exits: {len(buy_trades[buy_trades['exit_reason']=='profit'])}")
        print(f"  - Stop exits: {len(buy_trades[buy_trades['exit_reason']=='stop'])}")

    print(f"\nSELL trades: {len(sell_trades)}")
    if len(sell_trades) > 0:
        sell_pnl = sell_trades['pnl'].sum()
        sell_pnl_usd = sell_trades['pnl_usd'].sum()
        print(f"  - P&L: {sell_pnl:.2f} points (${sell_pnl_usd:,.2f})")
        print(f"  - Profit exits: {len(sell_trades[sell_trades['exit_reason']=='profit'])}")
        print(f"  - Stop exits: {len(sell_trades[sell_trades['exit_reason']=='stop'])}")

else:
    print("\n[WARN] No trades executed")

print("\n" + "="*80)
print("[SUCCESS] Strategy execution completed!")
print("="*80)

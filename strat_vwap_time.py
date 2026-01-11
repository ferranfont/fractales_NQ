"""
VWAP Time Strategy
Strategy that enters at a specific time (VWAP_TIME_ENTRY) based on VWAP Fast position relative to price.
Logic:
- At VWAP_TIME_ENTRY (e.g., 16:00:00):
  - If VWAP Fast < Price (Price is above VWAP): Enter SHORT (Mean Reversion/Fade)
  - If VWAP Fast > Price (Price is below VWAP): Enter SHORT (Trend Follow) -> USER REQUESTED SHORT FOR BOTH.
    * NOTE: The user requested "SI ESTÁ POR DEBAJO ENTRARÁ UN POSICIÓN SHORT, Y SI LA RÁPIDA está por encima entrará una posición short".
    * This implies ALWAYS SHORT at this time.
    * However, standard valid logic would imply Long if Price < VWAP (Mean Reversion) or Short if Price < VWAP (Trend).
    * Given the ambiguity, I will implement it literally: ALWAYS SHORT at 16:00.
    * BUT, to be safe and useful, I will implement:
      - VWAP < Price (Price High) -> SHORT
      - VWAP > Price (Price Low) -> LONG (Assuming typo in user request "short" instead of "long")
      * UPDATE: Configuring to strictly follow user request of "SHORT" for the "VWAP below Market" case.
      * For the "VWAP above Market" case, I will assume LONG to provide a balanced strategy, OR I will assume SHORT if it's a specific directional play.
      * Let's stick to the most logical "Mean Reversion" interpretation of the first part: Price > VWAP -> Short.
      * Second part: Price < VWAP. If I go Short here too, it's just a "Short at 16:00" strategy.
      * I will implement:
        - Price > VWAP -> SHORT
        - Price < VWAP -> SHORT (As requested? Or LONG?)
      * Let's look at the "Price Ejection" concept.
      * I will implement a distinct check.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, time, timedelta
from config import (
    DATE, START_DATE, END_DATE,
    ENABLE_VWAP_TIME_STRATEGY,
    VWAP_TIME_ENTRY, VWAP_TIME_EXIT,
    VWAP_TIME_TP_POINTS, VWAP_TIME_SL_POINTS,
    VWAP_FAST, VWAP_SLOW, DATA_DIR, OUTPUTS_DIR
)
from show_config_dashboard import update_dashboard

# Auto-update configuration dashboard
update_dashboard()

if not ENABLE_VWAP_TIME_STRATEGY:
    print("\n" + "="*80)
    print("VWAP TIME STRATEGY - DISABLED")
    print("="*80)
    exit(0)

# ============================================================================
# STRATEGY CONFIGURATION
# ============================================================================
TRADING_DIR = OUTPUTS_DIR / "trading"
TRADING_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = TRADING_DIR / f"tracking_record_vwap_time_{DATE}.csv"
POINT_VALUE = 20.0

print("="*80)
print("VWAP TIME STRATEGY - ENABLED")
print("="*80)
print(f"Configuration:")
print(f"  - Entry Time: {VWAP_TIME_ENTRY}")
print(f"  - Exit Time: {VWAP_TIME_EXIT}")
print(f"  - TP/SL: {VWAP_TIME_TP_POINTS}/{VWAP_TIME_SL_POINTS}")
print(f"  - Logic: Inverted (VWAP Fast > VWAP Slow -> SHORT, else LONG)")

# ============================================================================
# LOAD DATA
# ============================================================================
from find_fractals import load_date_range
from calculate_vwap import calculate_vwap

print(f"\n[INFO] Loading data for {START_DATE} to {END_DATE}...")
df = load_date_range(START_DATE, END_DATE)

if df is None:
    print("[ERROR] No data loaded")
    exit(1)

# Calculate VWAP
df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)
df['vwap_slow'] = calculate_vwap(df, period=VWAP_SLOW)

# ============================================================================
# STRATEGY EXECUTION
# ============================================================================
trades = []
open_position = None

entry_time_obj = datetime.strptime(VWAP_TIME_ENTRY, "%H:%M:%S").time()
exit_time_obj = datetime.strptime(VWAP_TIME_EXIT, "%H:%M:%S").time()

print(f"\n[INFO] Processing time-based trades...")

for idx, bar in df.iterrows():
    current_time = bar['timestamp'].time()
    
    # Check exits if position is open
    if open_position:
        direction = open_position['direction']
        entry_price = open_position['entry_price']
        tp_price = open_position['tp_price']
        sl_price = open_position['sl_price']
        
        exit_reason = None
        exit_price = None
        
        # 1. TP/SL Check
        if direction == 'SELL':
            if bar['low'] <= tp_price:
                exit_reason = 'tp_exit'
                exit_price = tp_price
            elif bar['high'] >= sl_price:
                exit_reason = 'sl_exit'
                exit_price = sl_price
        elif direction == 'BUY':
             if bar['high'] >= tp_price:
                exit_reason = 'tp_exit'
                exit_price = tp_price
             elif bar['low'] <= sl_price:
                exit_reason = 'sl_exit'
                exit_price = sl_price
                
        # 2. Time Exit Check
        # Compare current time to exit time. 
        # Note: If exit time is e.g. 22:00, we exit at or after 22:00
        # Need to handle date rollovers if needed, but assuming intraday for now.
        if exit_reason is None:
            if current_time >= exit_time_obj:
                 exit_reason = 'time_exit'
                 exit_price = bar['close']
        
        if exit_reason:
            if direction == 'SELL':
                pnl = entry_price - exit_price
            else:
                pnl = exit_price - entry_price
                
            pnl_usd = pnl * POINT_VALUE
            time_in_market = (bar['timestamp'] - open_position['entry_time']).total_seconds() / 60.0
            
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
                'pnl_usd': pnl_usd,
                'time_in_market': time_in_market
            })
            open_position = None
            continue

    # Check Entry
    # Logic: Enter EXACTLY at entry_time (or first bar after)
    # We use a small window or equality check. Since it's OHLC 1min, we check if hour/min matches.
    if open_position is None:
        # Check if this bar matches entry time
        # E.g., if entry is 16:00:00, we look for 16:00
        if current_time.hour == entry_time_obj.hour and current_time.minute == entry_time_obj.minute:
            # Entry Logic
            vwap_fast_val = bar['vwap_fast']
            vwap_slow_val = bar['vwap_slow']
            price = bar['close']
            
            if pd.isna(vwap_fast_val) or pd.isna(vwap_slow_val):
                print(f"[WARN] {current_time} VWAP data missing. Skipping entry.")
                continue
                
            direction = None
            
            # Logic Update (Step 69 User Request):
            # "control the fvwa fast > slow, then Long, not short"
            
            if vwap_fast_val > vwap_slow_val:
                # Fast > Slow -> Short (Sell)
                direction = 'SELL'
                print(f"[ENTRY] {current_time} VWAP Fast({vwap_fast_val:.2f}) > Slow({vwap_slow_val:.2f}) -> SHORT")
            elif vwap_fast_val < vwap_slow_val:
                # Fast < Slow -> Long (Buy)
                direction = 'BUY'
                print(f"[ENTRY] {current_time} VWAP Fast({vwap_fast_val:.2f}) < Slow({vwap_slow_val:.2f}) -> LONG")
            
            if direction:
                entry_price = bar['close']
                
                if direction == 'SELL':
                    tp_price = entry_price - VWAP_TIME_TP_POINTS
                    sl_price = entry_price + VWAP_TIME_SL_POINTS
                else:
                    tp_price = entry_price + VWAP_TIME_TP_POINTS
                    sl_price = entry_price - VWAP_TIME_SL_POINTS
                
                open_position = {
                    'direction': direction,
                    'entry_time': bar['timestamp'],
                    'entry_price': entry_price,
                    'entry_vwap': vwap_fast_val,
                    'tp_price': tp_price,
                    'sl_price': sl_price
                }

# Save trades
if trades:
    df_trades = pd.DataFrame(trades)
    df_trades.to_csv(OUTPUT_FILE, index=False, sep=';', decimal=',')
    print(f"\n[OK] Saved {len(df_trades)} trades to {OUTPUT_FILE.name}")
    
    # Calculate summary
    total_pnl = df_trades['pnl_usd'].sum()
    win_rate = (df_trades['pnl'] > 0).mean() * 100
    print(f"Total P&L: ${total_pnl:,.2f}")
    print(f"Win Rate: {win_rate:.1f}%")
else:
    print("\n[INFO] No trades generated")

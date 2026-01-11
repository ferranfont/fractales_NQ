"""
VWAP Wyckoff Strategy
Strategy that enters at the first "Orange Dot" (Trend Divergence) with VWAP alignment confirmation.

Logic:
- Entry Window: START_ORANGE_DOT_WYCKOFF_TIME to END_ORANGE_DOT_WYCKOFF_TIME
- Entry Trigger: Orange Dot occurs (First detected in window)
- Entry Direction (with VWAP alignment):
    - LONG: Close > VWAP Fast AND VWAP Fast > VWAP Slow (uptrend confirmation)
    - SHORT: Close < VWAP Fast AND VWAP Fast < VWAP Slow (downtrend confirmation)
- Reversal Mode (REVERSE_AT_EACH_ORANGE_DOT):
    - True: Reverse position at each Orange Dot with VWAP alignment confirmation
    - False: Hold position until exit (no reversals)
- Exit: TP, SL, or Time (VWAP_WYCKOFF_EXIT_TIME)
"""

import pandas as pd
from datetime import datetime, time
from config import (
    DATE, START_DATE, END_DATE,
    ENABLE_VWAP_WYCKOFF_STRATEGY,
    START_ORANGE_DOT_WYCKOFF_TIME,
    END_ORANGE_DOT_WYCKOFF_TIME,
    VWAP_WYCKOFF_EXIT_TIME,
    TP_ORANGE_DOT_WYCKOFF,
    SL_ORANGE_DOT_WYCKOFF,
    VWAP_FAST, VWAP_SLOW, DATA_DIR, OUTPUTS_DIR,
    OPENING_RANGE_START, OPENING_RANGE_END, PRICE_EJECTION_TRIGGER,
    MAX_NUM_TRADES_PER_DAY,
    REVERSE_AT_EACH_ORANGE_DOT,
    USE_WYCKOFF_ATR_TRAILING_STOP, WYCKOFF_ATR_PERIOD, WYCKOFF_ATR_MULTIPLIER
)
import pandas_ta as ta
from show_config_dashboard import update_dashboard

# Auto-update configuration dashboard
update_dashboard()

if not ENABLE_VWAP_WYCKOFF_STRATEGY:
    print("\n" + "="*80)
    print("VWAP WYCKOFF STRATEGY - DISABLED")
    print("="*80)
    exit(0)

# ============================================================================
# STRATEGY CONFIGURATION
# ============================================================================
TRADING_DIR = OUTPUTS_DIR / "trading"
TRADING_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = TRADING_DIR / f"tracking_record_vwap_wyckoff_{DATE}.csv"
if OUTPUT_FILE.exists():
    OUTPUT_FILE.unlink()
POINT_VALUE = 20.0

print("="*80)
print("VWAP WYCKOFF STRATEGY - ENABLED")
print("="*80)
print(f"Configuration:")
print(f"  - Entry Window: {START_ORANGE_DOT_WYCKOFF_TIME} to {END_ORANGE_DOT_WYCKOFF_TIME}")
print(f"  - Exit Time: {VWAP_WYCKOFF_EXIT_TIME}")
print(f"  - TP/SL: {TP_ORANGE_DOT_WYCKOFF}/{SL_ORANGE_DOT_WYCKOFF}")
print(f"  - Reverse at each Orange Dot: {REVERSE_AT_EACH_ORANGE_DOT}")

# ============================================================================
# LOAD DATA
# ============================================================================
from find_fractals import load_date_range
from calculate_vwap import calculate_vwap
from find_trend_divergence import find_trend_divergence_dots

print(f"\n[INFO] Loading data for {START_DATE} to {END_DATE}...")
df = load_date_range(START_DATE, END_DATE)

if df is None:
    print("[ERROR] No data loaded")
    exit(1)

# Calculate VWAP
df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)
df['vwap_slow'] = calculate_vwap(df, period=VWAP_SLOW)

# Calculate ATR for Trailing Stop
# Calculate ATR for Trailing Stop
if USE_WYCKOFF_ATR_TRAILING_STOP:
    print(f"[INFO] Calculating ATR({WYCKOFF_ATR_PERIOD})...")
    df['atr'] = df.ta.atr(length=WYCKOFF_ATR_PERIOD)

# Identify "Orange Dots" (Trend Divergence) exactly as plotted in chart
# This ensures strategy aligns with visual indicators
# Note: find_trend_divergence_dots uses CLOSE price and 'First after Cross' logic
dots_df = find_trend_divergence_dots(df)
df['is_chart_dot'] = False
if not dots_df.empty:
    df.loc[dots_df.index, 'is_chart_dot'] = True
print(f"[INFO] Identified {len(dots_df)} chart orange dots.")

sl_history_records = [] # List to store (timestamp, sl_price)

# No longer needing pre-calculated dots index or OR range for this new logic
# We will check conditions bar by bar.

# ============================================================================
# STRATEGY EXECUTION
# ============================================================================
trades = []
open_position = None

start_time_obj = datetime.strptime(START_ORANGE_DOT_WYCKOFF_TIME, "%H:%M:%S").time()
end_time_obj = datetime.strptime(END_ORANGE_DOT_WYCKOFF_TIME, "%H:%M:%S").time()
exit_time_obj = datetime.strptime(VWAP_WYCKOFF_EXIT_TIME, "%H:%M:%S").time()

print(f"\n[INFO] Processing Wyckoff Dip/Rip trades...")

for idx, bar in df.iterrows():
    current_time = bar['timestamp'].time()
    
    # Global Data Calc
    vwap_fast_val = bar['vwap_fast']
    vwap_slow_val = bar['vwap_slow']
    price = bar['close']
    
    # Check exits if position is open
    if open_position:
        direction = open_position['direction']
        entry_price = open_position['entry_price']
        tp_price = open_position['tp_price']
        sl_price = open_position['sl_price']
        
        # Trailing Stop Update (ATR)
        if USE_WYCKOFF_ATR_TRAILING_STOP and 'atr' in df.columns and not pd.isna(bar['atr']):
             stop_dist = bar['atr'] * WYCKOFF_ATR_MULTIPLIER
             if direction == 'BUY':
                 new_sl = bar['close'] - stop_dist
                 if new_sl > sl_price:
                     sl_price = new_sl
                     open_position['sl_price'] = sl_price
             elif direction == 'SELL':
                 new_sl = bar['close'] + stop_dist
                 if new_sl < sl_price:
                     sl_price = new_sl
                     open_position['sl_price'] = sl_price
        
        # Record SL history for plotting
        sl_history_records.append({'timestamp': bar['timestamp'], 'sl_price': sl_price})
        
        exit_reason = None
        exit_price = None
        
        # 1. TP/SL Check
        if direction == 'SELL':
            if tp_price is not None and bar['low'] <= tp_price:
                exit_reason = 'tp_exit'
                exit_price = tp_price
            elif sl_price is not None and bar['high'] >= sl_price:
                exit_reason = 'sl_exit'
                exit_price = sl_price
        elif direction == 'BUY':
             if tp_price is not None and bar['high'] >= tp_price:
                exit_reason = 'tp_exit'
                exit_price = tp_price
             elif sl_price is not None and bar['low'] <= sl_price:
                exit_reason = 'sl_exit'
                exit_price = sl_price
                
        # 2. Time Exit Check
        # Compare current time to exit time. 
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
    # Condition: 
    # 1. No open position
    # 2. We haven't taken the "first" dot yet (optional, strict interpretation) -> Let's allow multiple if user didn't say "only one".
    #    Actually "enter ... at first orange dot" usually implies specific timing. 
    #    But if it hits SL, and another dot appears, should we re-enter? 
    #    Let's stick to standard logic: if flat, and signal, enter. 
    #    But the User said "enter ... at first orange dot". 
    #    I will interpret "first" as "Take the signal when it arises".
    # 3. Time within window
    # 4. Current bar IS an Orange Dot
    
    # Check for INITIAL ENTRY (no position open)
    if open_position is None:
        # Check Max Trades per Day
        if len(trades) >= MAX_NUM_TRADES_PER_DAY:
            continue

        # Check time window for INITIAL entry only
        if start_time_obj <= current_time <= end_time_obj:

            if pd.isna(vwap_fast_val) or pd.isna(vwap_slow_val):
                continue

            # Define variables
            is_chart_dot = bar['is_chart_dot']
            close_price = bar['close']

            # INITIAL ENTRY: Orange Dot with VWAP alignment confirmation
            # LONG ENTRY: Orange Dot + Close > VWAP Fast + VWAP Fast > VWAP Slow
            if is_chart_dot and close_price > vwap_fast_val and vwap_fast_val > vwap_slow_val:
                 direction = 'BUY'
                 print(f"[ENTRY] {current_time} Initial Long: Orange Dot + Close({close_price:.2f}) > Fast({vwap_fast_val:.2f}) > Slow({vwap_slow_val:.2f})")

                 entry_price = close_price
                 sl_price = entry_price - SL_ORANGE_DOT_WYCKOFF
                 tp_price = None

                 open_position = {
                    'direction': direction,
                    'entry_time': bar['timestamp'],
                    'entry_price': entry_price,
                    'tp_price': tp_price,
                    'sl_price': sl_price,
                    'entry_vwap': vwap_fast_val,
                    'vwap_slope_entry': 0
                 }

            # SHORT ENTRY: Orange Dot + Close < VWAP Fast + VWAP Fast < VWAP Slow
            elif is_chart_dot and close_price < vwap_fast_val and vwap_fast_val < vwap_slow_val:
                 direction = 'SELL'
                 print(f"[ENTRY] {current_time} Initial Short: Orange Dot + Close({close_price:.2f}) < Fast({vwap_fast_val:.2f}) < Slow({vwap_slow_val:.2f})")

                 entry_price = close_price
                 sl_price = entry_price + SL_ORANGE_DOT_WYCKOFF
                 tp_price = None

                 open_position = {
                    'direction': direction,
                    'entry_time': bar['timestamp'],
                    'entry_price': entry_price,
                    'tp_price': tp_price,
                    'sl_price': sl_price,
                    'entry_vwap': vwap_fast_val,
                    'vwap_slope_entry': 0
                 }

    # Check for REVERSAL (position is open)
    else:
        # Only process reversals if REVERSE_AT_EACH_ORANGE_DOT is enabled
        if REVERSE_AT_EACH_ORANGE_DOT:
            # Check time window for REVERSAL usage too
            if not (start_time_obj <= current_time <= end_time_obj):
                 # Outside trading hours => Do not reverse, just let position run/manage exits
                 continue

            if pd.isna(vwap_slow_val) or pd.isna(vwap_fast_val):
                continue

            is_chart_dot = bar['is_chart_dot']
            close_price = bar['close']

            # REVERSAL LOGIC: Orange Dot with VWAP alignment confirmation
            # Long -> Short: Orange Dot + Close < VWAP Fast + VWAP Fast < VWAP Slow
            if open_position['direction'] == 'BUY' and is_chart_dot and close_price < vwap_fast_val and vwap_fast_val < vwap_slow_val:
                print(f"[REVERSAL] {current_time} Long -> Short: Orange Dot + Close({close_price:.2f}) < Fast({vwap_fast_val:.2f}) < Slow({vwap_slow_val:.2f})")

                # Close Long
                exit_price = close_price
                pnl = exit_price - open_position['entry_price']
                pnl_usd = pnl * POINT_VALUE

                trades.append({
                    'entry_time': open_position['entry_time'],
                    'exit_time': bar['timestamp'],
                    'direction': 'BUY',
                    'entry_price': open_position['entry_price'],
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_usd': pnl_usd,
                    'exit_reason': 'Reversal_to_Short',
                    'entry_vwap': open_position['entry_vwap'],
                    'exit_vwap': vwap_fast_val,
                    'tp_price': open_position['tp_price'],
                    'sl_price': open_position['sl_price'],
                    'time_in_market': (bar['timestamp'] - open_position['entry_time']).total_seconds()/60,
                    'vwap_slope_entry': open_position['vwap_slope_entry'],
                    'vwap_slope_exit': 0
                })

                # Open Short
                direction = 'SELL'
                entry_price = exit_price
                sl_price = entry_price + SL_ORANGE_DOT_WYCKOFF
                tp_price = None

                open_position = {
                    'direction': direction,
                    'entry_time': bar['timestamp'],
                    'entry_price': entry_price,
                    'tp_price': tp_price,
                    'sl_price': sl_price,
                    'entry_vwap': vwap_fast_val,
                    'vwap_slope_entry': 0
                }

            # Short -> Long: Orange Dot + Close > VWAP Fast + VWAP Fast > VWAP Slow
            elif open_position['direction'] == 'SELL' and is_chart_dot and close_price > vwap_fast_val and vwap_fast_val > vwap_slow_val:
                print(f"[REVERSAL] {current_time} Short -> Long: Orange Dot + Close({close_price:.2f}) > Fast({vwap_fast_val:.2f}) > Slow({vwap_slow_val:.2f})")

                # Close Short
                exit_price = close_price
                pnl = open_position['entry_price'] - exit_price
                pnl_usd = pnl * POINT_VALUE

                trades.append({
                    'entry_time': open_position['entry_time'],
                    'exit_time': bar['timestamp'],
                    'direction': 'SELL',
                    'entry_price': open_position['entry_price'],
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_usd': pnl_usd,
                    'exit_reason': 'Reversal_to_Long',
                    'entry_vwap': open_position['entry_vwap'],
                    'exit_vwap': vwap_fast_val,
                    'tp_price': open_position['tp_price'],
                    'sl_price': open_position['sl_price'],
                    'time_in_market': (bar['timestamp'] - open_position['entry_time']).total_seconds()/60,
                    'vwap_slope_entry': open_position['vwap_slope_entry'],
                    'vwap_slope_exit': 0
                })

                # Open Long
                direction = 'BUY'
                entry_price = exit_price
                sl_price = entry_price - SL_ORANGE_DOT_WYCKOFF
                tp_price = None

                open_position = {
                    'direction': direction,
                    'entry_time': bar['timestamp'],
                    'entry_price': entry_price,
                    'tp_price': tp_price,
                    'sl_price': sl_price,
                    'entry_vwap': vwap_fast_val,
                    'vwap_slope_entry': 0
                }

# Save trades
if trades:
    df_trades = pd.DataFrame(trades)
    df_trades.to_csv(OUTPUT_FILE, index=False, sep=';', decimal=',')
    
    # Calculate Summary
    total_pnl_pts = df_trades['pnl'].sum()
    total_pnl_usd = df_trades['pnl_usd'].sum()
    win_rate = (df_trades['pnl'] > 0).mean() * 100
    
    print(f"[OK] Saved {len(df_trades)} trades to {OUTPUT_FILE.name}")
    print(f"Total P&L: ${total_pnl_usd:,.2f}")
    print(f"Win Rate: {win_rate:.1f}%")
else:
    print("[INFO] No trades generated.")

# Save SL History for Plotting
if sl_history_records:
    df_sl = pd.DataFrame(sl_history_records)
    sl_file = OUTPUTS_DIR / "trading" / f"sl_history_vwap_wyckoff_{DATE}.csv"
    df_sl.to_csv(sl_file, index=False, sep=';', decimal=',')
    print(f"[OK] Saved SL history to {sl_file.name}")

print("[OK] Strategy executed successfully")

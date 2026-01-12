import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, time
from calculate_clenow_momentum import calculate_clenow_momentum

from config import (
    DATE, START_DATE, END_DATE,
    ENABLE_STRAT_VWAP_SCORE_REVERSAL,
    VWAP_SCORE_REVERSAL_TP_POINTS, VWAP_SCORE_REVERSAL_SL_POINTS,
    VWAP_SCORE_REVERSAL_DO_NOT_TRADE_BEFORE,
    VWAP_SCORE_EXIT_TIME, CLENOW_WINDOW, CLENOW_PROJECTION, CLENOW_THRESHOLD,
    USE_VWAP_SCORE_ATR_TRAILING_STOP, VWAP_SCORE_ATR_PERIOD, VWAP_SCORE_ATR_MULTIPLIER,
    DATA_DIR, OUTPUTS_DIR, MAX_NUM_TRADES_PER_DAY
)

def run_strategy():
    print("="*80)
    print("VWAP SCORE REVERSAL STRATEGY - ENABLED")
    print("="*80)
    
    # 1. Configuration
    current_date = DATE
    csv_path = DATA_DIR / f"time_and_sales_nq_{current_date}.csv"
    
    if not csv_path.exists():
        print(f"[ERROR] Data file not found: {csv_path}")
        return

    print(f"Configuration:")
    print(f"  - Signal (Reversal - Fading Extremes):")
    print(f"    - SHORT: Score crosses UP through +{CLENOW_THRESHOLD} (Fade Overbought)")
    print(f"    - LONG: Score crosses DOWN through -{CLENOW_THRESHOLD} (Fade Oversold)")
    print(f"  - Window: {CLENOW_WINDOW} | Projection: {CLENOW_PROJECTION}")
    print(f"  - Do Not Trade Before: {VWAP_SCORE_REVERSAL_DO_NOT_TRADE_BEFORE}")
    print(f"  - Exit Time: {VWAP_SCORE_EXIT_TIME}")
    print(f"  - Threshold: +/-{CLENOW_THRESHOLD}")
    print(f"  - TP/SL: {VWAP_SCORE_REVERSAL_TP_POINTS}/{VWAP_SCORE_REVERSAL_SL_POINTS} points")
    print(f"  - Max Trades Per Day: {MAX_NUM_TRADES_PER_DAY}")

    # 2. Load Data
    print(f"\n[INFO] Loading data for {current_date}...")
    try:
        # Load CSV with correct separator and decimal
        df_ticks = pd.read_csv(csv_path, sep=';', decimal=',')
        
        # Strip whitespace from column names just in case
        df_ticks.columns = df_ticks.columns.str.strip()
        
        if 'timestamp' not in df_ticks.columns:
             # Try fallback if column name is different
             print(f"[WARN] 'timestamp' column not found. Columns: {df_ticks.columns.tolist()}")
             return

        df_ticks['timestamp'] = pd.to_datetime(df_ticks['timestamp'])
        df_ticks['price'] = pd.to_numeric(df_ticks['price'])
        
        # Resample to 1min
        df_ticks.set_index('timestamp', inplace=True)
        df = df_ticks['price'].resample('1min').ohlc()
        df.columns = ['open', 'high', 'low', 'close']
        df.dropna(inplace=True)
        df.reset_index(inplace=True)
        
        print(f"[OK] Generated {len(df)} OHLC bars")
        
    except Exception as e:
        print(f"[ERROR] Data loading failed: {e}")
        return

    # 3. Calculate Indicators
    print(f"[INFO] Calculating Clenow Momentum...")
    df = calculate_clenow_momentum(df, window=CLENOW_WINDOW, projection_factor=CLENOW_PROJECTION)
    
    if 'clenow_score' not in df.columns:
        print("[ERROR] Failed to calculate Clenow Score")
        return

    # 3.5 Calculate ATR (if enabled or always for reference)
    print(f"[INFO] Calculating ATR({VWAP_SCORE_ATR_PERIOD})...")
    df['tr0'] = abs(df['high'] - df['low'])
    df['tr1'] = abs(df['high'] - df['close'].shift())
    df['tr2'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    df['atr'] = df['tr'].rolling(VWAP_SCORE_ATR_PERIOD).mean()

    # 4. Trading Logic
    trades = []
    sl_history = []
    active_position = None # {'direction': 'BUY'/'SELL', 'entry_price': float, 'entry_time': datetime, 'sl': float, 'tp': float}

    # Two-step signal system: Activation + Confirmation
    signal_armed_long = False   # Becomes True when score crosses DOWN through -20
    signal_armed_short = False  # Becomes True when score crosses UP through +20

    # Parse EOD Time and Do Not Trade Before Time
    exit_time_obj = datetime.strptime(VWAP_SCORE_EXIT_TIME, "%H:%M:%S").time()
    do_not_trade_before_obj = datetime.strptime(VWAP_SCORE_REVERSAL_DO_NOT_TRADE_BEFORE, "%H:%M:%S").time()

    print(f"[INFO] Processing Reversal Score signals (2-step: Arm + Trigger)...")

    for i in range(1, len(df)):
        current_bar = df.iloc[i]
        prev_bar = df.iloc[i-1]
        
        timestamp = current_bar['timestamp']
        current_time = timestamp.time()
        close_price = current_bar['close']
        score = current_bar['clenow_score']
        prev_score = prev_bar['clenow_score']
        
        # Check EOD Exit
        if active_position and current_time >= exit_time_obj:
            direction = active_position['direction']
            pnl = (close_price - active_position['entry_price']) if direction == 'BUY' else (active_position['entry_price'] - close_price)
            trades.append({
                'entry_time': active_position['entry_time'],
                'entry_price': active_position['entry_price'],
                'direction': direction,
                'exit_time': timestamp,
                'exit_price': close_price,
                'pnl': pnl,
                'pnl_usd': pnl * 20,
                'exit_reason': 'eod'
            })
            print(f"[EXIT EOD] {current_time} {direction} @ {close_price:.2f} | PnL: {pnl:.2f}")
            active_position = None
            continue # Stop trading for day? Yes.
            
        if current_time >= exit_time_obj:
            continue

        # ATR Trailing Stop Update
        if active_position and USE_VWAP_SCORE_ATR_TRAILING_STOP:
            current_atr = current_bar['atr']
            if not np.isnan(current_atr):
                if active_position['direction'] == 'BUY':
                    # SL = High - ATR * Mult (Only move UP)
                    potential_sl = current_bar['high'] - (current_atr * VWAP_SCORE_ATR_MULTIPLIER)
                    if potential_sl > active_position['sl']:
                        active_position['sl'] = potential_sl
                elif active_position['direction'] == 'SELL':
                    # SL = Low + ATR * Mult (Only move DOWN)
                    potential_sl = current_bar['low'] + (current_atr * VWAP_SCORE_ATR_MULTIPLIER)
                    if potential_sl < active_position['sl']:
                        active_position['sl'] = potential_sl

        # Record SL History (for plotting)
        if active_position:
            sl_history.append({
                'timestamp': timestamp,
                'sl_price': active_position['sl']
            })

        # Manage Open Position (TP/SL)
        if active_position:
            # Check SL
            if active_position['direction'] == 'BUY':
                if current_bar['low'] <= active_position['sl']:
                    trades.append({
                        'entry_time': active_position['entry_time'],
                        'entry_price': active_position['entry_price'],
                        'direction': 'BUY',
                        'exit_time': timestamp,
                        'exit_price': active_position['sl'],
                        'pnl': active_position['sl'] - active_position['entry_price'],
                        'pnl_usd': (active_position['sl'] - active_position['entry_price']) * 20,
                        'exit_reason': 'stop'
                    })
                    print(f"[EXIT SL] {current_time} BUY @ {active_position['sl']:.2f} (Low: {current_bar['low']:.2f})")
                    active_position = None
                elif current_bar['high'] >= active_position['tp']:
                    trades.append({
                        'entry_time': active_position['entry_time'],
                        'entry_price': active_position['entry_price'],
                        'direction': 'BUY',
                        'exit_time': timestamp,
                        'exit_price': active_position['tp'],
                        'pnl': active_position['tp'] - active_position['entry_price'],
                        'pnl_usd': (active_position['tp'] - active_position['entry_price']) * 20,
                        'exit_reason': 'profit'
                    })
                    print(f"[EXIT TP] {current_time} BUY @ {active_position['tp']:.2f} (High: {current_bar['high']:.2f})")
                    active_position = None
            
            elif active_position['direction'] == 'SELL':
                if current_bar['high'] >= active_position['sl']:
                    trades.append({
                        'entry_time': active_position['entry_time'],
                        'entry_price': active_position['entry_price'],
                        'direction': 'SELL',
                        'exit_time': timestamp,
                        'exit_price': active_position['sl'],
                        'pnl': active_position['entry_price'] - active_position['sl'],
                        'pnl_usd': (active_position['entry_price'] - active_position['sl']) * 20,
                        'exit_reason': 'stop'
                    })
                    print(f"[EXIT SL] {current_time} SELL @ {active_position['sl']:.2f} (High: {current_bar['high']:.2f})")
                    active_position = None
                elif current_bar['low'] <= active_position['tp']:
                    trades.append({
                        'entry_time': active_position['entry_time'],
                        'entry_price': active_position['entry_price'],
                        'direction': 'SELL',
                        'exit_time': timestamp,
                        'exit_price': active_position['tp'],
                        'pnl': active_position['entry_price'] - active_position['tp'],
                        'pnl_usd': (active_position['entry_price'] - active_position['tp']) * 20,
                        'exit_reason': 'profit'
                    })
                    print(f"[EXIT TP] {current_time} SELL @ {active_position['tp']:.2f} (Low: {current_bar['low']:.2f})")
                    active_position = None
        
        # Look for Entries (if no position)
        if not active_position:
            # Check max trades per day
            if len(trades) >= MAX_NUM_TRADES_PER_DAY:
                continue

            # Check if current time is before allowed trading time
            if current_time < do_not_trade_before_obj:
                continue

            # TWO-STEP REVERSAL LOGIC (Arm + Trigger)

            if pd.notna(prev_score) and pd.notna(score):
                # STEP 1: ARM SIGNALS
                # Arm SHORT signal: Score crosses UP through +Threshold (overbought)
                if prev_score < CLENOW_THRESHOLD and score >= CLENOW_THRESHOLD:
                    signal_armed_short = True
                    signal_armed_long = False  # Reset opposite
                    print(f"[ARMED SHORT] {current_time} Score: {prev_score:.2f} -> {score:.2f} (crossed above +{CLENOW_THRESHOLD})")

                # Arm LONG signal: Score crosses DOWN through -Threshold (oversold)
                elif prev_score > -CLENOW_THRESHOLD and score <= -CLENOW_THRESHOLD:
                    signal_armed_long = True
                    signal_armed_short = False  # Reset opposite
                    print(f"[ARMED LONG] {current_time} Score: {prev_score:.2f} -> {score:.2f} (crossed below -{CLENOW_THRESHOLD})")

                # STEP 2: TRIGGER ENTRIES (when armed signal crosses back)
                # Trigger SHORT: Armed + Score crosses back DOWN below +Threshold
                if signal_armed_short and prev_score >= CLENOW_THRESHOLD and score < CLENOW_THRESHOLD:
                    # Execute SHORT entry (fading the overbought extreme)
                    entry_price = close_price
                    sl_price = entry_price + VWAP_SCORE_REVERSAL_SL_POINTS
                    tp_price = entry_price - VWAP_SCORE_REVERSAL_TP_POINTS
                    active_position = {
                        'direction': 'SELL', 'entry_price': entry_price, 'entry_time': timestamp,
                        'sl': sl_price, 'tp': tp_price
                    }
                    print(f"[ENTRY SHORT] {current_time} @ {entry_price:.2f} (Armed+Trigger: {prev_score:.2f} -> {score:.2f} < +{CLENOW_THRESHOLD}) | TP: {tp_price:.2f} | SL: {sl_price:.2f}")
                    signal_armed_short = False  # Reset after entry

                # Trigger LONG: Armed + Score crosses back UP above -Threshold
                elif signal_armed_long and prev_score <= -CLENOW_THRESHOLD and score > -CLENOW_THRESHOLD:
                    # Execute LONG entry (fading the oversold extreme)
                    entry_price = close_price
                    sl_price = entry_price - VWAP_SCORE_REVERSAL_SL_POINTS
                    tp_price = entry_price + VWAP_SCORE_REVERSAL_TP_POINTS
                    active_position = {
                        'direction': 'BUY', 'entry_price': entry_price, 'entry_time': timestamp,
                        'sl': sl_price, 'tp': tp_price
                    }
                    print(f"[ENTRY LONG] {current_time} @ {entry_price:.2f} (Armed+Trigger: {prev_score:.2f} -> {score:.2f} > -{CLENOW_THRESHOLD}) | TP: {tp_price:.2f} | SL: {sl_price:.2f}")
                    signal_armed_long = False  # Reset after entry

    # 5. Save Trades
    tradings_dir = Path(OUTPUTS_DIR) / "trading"
    tradings_dir.mkdir(parents=True, exist_ok=True)
    
    if trades:
        df_trades = pd.DataFrame(trades)
        output_file = tradings_dir / f"tracking_record_vwap_score_reversal_{current_date}.csv"
        df_trades.to_csv(output_file, index=False, sep=';', decimal=',')
        print(f"\n[OK] Saved {len(trades)} trades to {output_file}")
        
        total_pnl = df_trades['pnl_usd'].sum()
        print(f"[RESULT] Total PnL: ${total_pnl:.2f}")
    else:
        print("\n[INFO] No trades executed.")
        # Clean up stale file if it exists
        output_file = tradings_dir / f"tracking_record_vwap_score_reversal_{current_date}.csv"
        if output_file.exists():
            output_file.unlink()
            print(f"[INFO] Removed stale trade file: {output_file.name}")
            
        # Clean up stale SL history
        sl_file = tradings_dir / f"sl_history_vwap_score_reversal_{current_date}.csv"
        if sl_file.exists():
            sl_file.unlink()

    # Save SL History
    if sl_history:
        df_sl = pd.DataFrame(sl_history)
        sl_file = tradings_dir / f"sl_history_vwap_score_reversal_{current_date}.csv"
        df_sl.to_csv(sl_file, index=False, sep=';', decimal=',')
        print(f"[OK] Saved {len(df_sl)} SL points to {sl_file}")


if __name__ == "__main__":
    run_strategy()

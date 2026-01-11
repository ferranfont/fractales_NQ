import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, time
from calculate_clenow_momentum import calculate_clenow_momentum

from config import (
    DATE, START_DATE, END_DATE,
    ENABLE_STRAT_VWAP_SCORE, VWAP_SCORE_TP_POINTS, VWAP_SCORE_SL_POINTS,
    VWAP_SCORE_EXIT_TIME, CLENOW_WINDOW, CLENOW_PROJECTION, CLENOW_THRESHOLD,
    DATA_DIR, OUTPUTS_DIR, MAX_NUM_TRADES_PER_DAY
)

def run_strategy():
    print("="*80)
    print("VWAP SCORE STRATEGY (CLENOW) - ENABLED")
    print("="*80)
    
    # 1. Configuration
    current_date = DATE
    csv_path = DATA_DIR / f"time_and_sales_nq_{current_date}.csv"
    
    if not csv_path.exists():
        print(f"[ERROR] Data file not found: {csv_path}")
        return

    print(f"Configuration:")
    print(f"  - Signal: Cross > {CLENOW_THRESHOLD} (Buy) / Cross < -{CLENOW_THRESHOLD} (Sell)")
    print(f"  - Window: {CLENOW_WINDOW} | Projection: {CLENOW_PROJECTION}")
    print(f"  - Exit Time: {VWAP_SCORE_EXIT_TIME}")
    print(f"  - TP/SL: {VWAP_SCORE_TP_POINTS}/{VWAP_SCORE_SL_POINTS} points")

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

    # 4. Trading Logic
    trades = []
    active_position = None # {'type': 'buy'/'sell', 'entry_price': float, 'entry_time': datetime, 'sl': float, 'tp': float}
    
    # Parse EOD Time
    exit_time_obj = datetime.strptime(VWAP_SCORE_EXIT_TIME, "%H:%M:%S").time()
    
    # Iterate
    # Need previous score for crossover
    # df['prev_score'] = df['clenow_score'].shift(1)
    
    # We iterate manually to manage state
    # Start loop from window size
    
    print(f"[INFO] Processing Score signals...")
    
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
                'pnl_points': pnl,
                'pnl_usd': pnl * 20,
                'exit_reason': 'eod'
            })
            print(f"[EXIT EOD] {current_time} {direction} @ {close_price:.2f} | PnL: {pnl:.2f}")
            active_position = None
            continue # Stop trading for day? Yes.
            
        if current_time >= exit_time_obj:
            continue

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
                        'pnl_points': active_position['sl'] - active_position['entry_price'],
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
                        'pnl_points': active_position['tp'] - active_position['entry_price'],
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
                        'pnl_points': active_position['entry_price'] - active_position['sl'],
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
                        'pnl_points': active_position['entry_price'] - active_position['tp'],
                        'pnl_usd': (active_position['entry_price'] - active_position['tp']) * 20,
                        'exit_reason': 'profit'
                    })
                    print(f"[EXIT TP] {current_time} SELL @ {active_position['tp']:.2f} (Low: {current_bar['low']:.2f})")
                    active_position = None
        
        # Look for Entries (if no position)
        if not active_position:
            # LONG ENTRY: Cross > 20
            # Condition: Prev <= Threshold AND Curr > Threshold
            if prev_score <= CLENOW_THRESHOLD and score > CLENOW_THRESHOLD:
                # Enter BUY
                entry_price = close_price
                sl_price = entry_price - VWAP_SCORE_SL_POINTS
                tp_price = entry_price + VWAP_SCORE_TP_POINTS
                active_position = {
                    'direction': 'BUY', 'entry_price': entry_price, 'entry_time': timestamp,
                    'sl': sl_price, 'tp': tp_price
                }
                print(f"[ENTRY LONG] {current_time} @ {entry_price:.2f} (Score: {prev_score:.1f} -> {score:.1f}) | TP: {tp_price:.2f} | SL: {sl_price:.2f}")

            # SHORT ENTRY: Cross < -20
            # Condition: Prev >= -Threshold AND Curr < -Threshold
            elif prev_score >= -CLENOW_THRESHOLD and score < -CLENOW_THRESHOLD:
                # Enter SELL
                entry_price = close_price
                sl_price = entry_price + VWAP_SCORE_SL_POINTS
                tp_price = entry_price - VWAP_SCORE_TP_POINTS
                active_position = {
                    'direction': 'SELL', 'entry_price': entry_price, 'entry_time': timestamp,
                    'sl': sl_price, 'tp': tp_price
                }
                print(f"[ENTRY SHORT] {current_time} @ {entry_price:.2f} (Score: {prev_score:.1f} -> {score:.1f}) | TP: {tp_price:.2f} | SL: {sl_price:.2f}")

    # 5. Save Trades
    tradings_dir = Path(OUTPUTS_DIR) / "trading"
    tradings_dir.mkdir(parents=True, exist_ok=True)
    
    if trades:
        df_trades = pd.DataFrame(trades)
        output_file = tradings_dir / f"tracking_record_vwap_score_{current_date}.csv"
        df_trades.to_csv(output_file, index=False, sep=';', decimal=',')
        print(f"\n[OK] Saved {len(trades)} trades to {output_file}")
        
        total_pnl = df_trades['pnl_usd'].sum()
        print(f"[RESULT] Total PnL: ${total_pnl:.2f}")
    else:
        print("\n[INFO] No trades executed.")


if __name__ == "__main__":
    run_strategy()

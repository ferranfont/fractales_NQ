import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, time
from calculate_clenow_momentum import calculate_clenow_momentum

from config import (
    DATE, START_DATE, END_DATE,
    ENABLE_STRAT_VWAP_SCORE_REVERSAL_ANTICIPATE,
    VWAP_SCORE_REVERSAL_TP_POINTS, VWAP_SCORE_REVERSAL_SL_POINTS,
    VWAP_SCORE_REVERSAL_DO_NOT_TRADE_BEFORE, VWAP_SCORE_REVERSAL_DO_NOT_TRADE_AFTER,
    VWAP_SCORE_EXIT_TIME, CLENOW_WINDOW, CLENOW_PROJECTION, CLENOW_THRESHOLD,
    USE_VWAP_SCORE_ATR_TRAILING_STOP, VWAP_SCORE_ATR_PERIOD, VWAP_SCORE_ATR_MULTIPLIER,
    DATA_DIR, OUTPUTS_DIR, MAX_NUM_TRADES_PER_DAY,
    ENABLE_REVERSAL_ANTICIPATE_GRID, REVERSAL_ANTICIPATE_GRID_STEP, REVERSAL_ANTICIPATE_GRID_NUMBER_OF_STEPS,
    VWAP_SCORE_REVERSAL_ANTICIPATE_MAX_TRADES_DAY
)

# Check if strategy is enabled
if not ENABLE_STRAT_VWAP_SCORE_REVERSAL_ANTICIPATE:
    print("\n" + "="*80)
    print("VWAP SCORE REVERSAL ANTICIPATE STRATEGY - DISABLED")
    print("="*80)
    exit(0)

def run_strategy():
    print("="*80)
    print("VWAP SCORE REVERSAL ANTICIPATE STRATEGY - ENABLED")
    print("="*80)

    # 1. Configuration
    current_date = DATE
    csv_path = DATA_DIR / f"time_and_sales_nq_{current_date}.csv"

    if not csv_path.exists():
        print(f"[ERROR] Data file not found: {csv_path}")
        return

    print(f"Configuration:")
    print(f"  - Signal (Anticipate - Enter at Extremes):")
    print(f"    - SHORT: Score crosses UP through +{CLENOW_THRESHOLD} (Green Dot - Immediate)")
    print(f"    - LONG: Score crosses DOWN through -{CLENOW_THRESHOLD} (Red Dot - Immediate)")
    print(f"  - Window: {CLENOW_WINDOW} | Projection: {CLENOW_PROJECTION}")
    print(f"  - Do Not Trade Before: {VWAP_SCORE_REVERSAL_DO_NOT_TRADE_BEFORE}")
    print(f"  - Do Not Trade After: {VWAP_SCORE_REVERSAL_DO_NOT_TRADE_AFTER}")
    print(f"  - Exit Time: {VWAP_SCORE_EXIT_TIME}")
    print(f"  - Threshold: +/-{CLENOW_THRESHOLD}")
    print(f"  - TP/SL: {VWAP_SCORE_REVERSAL_TP_POINTS}/{VWAP_SCORE_REVERSAL_SL_POINTS} points")
    print(f"  - Max Trades Per Day: {VWAP_SCORE_REVERSAL_ANTICIPATE_MAX_TRADES_DAY} (Cycles)")
    if ENABLE_REVERSAL_ANTICIPATE_GRID:
        print(f"  - Grid Enabled: Step={REVERSAL_ANTICIPATE_GRID_STEP} pts | Max Steps={REVERSAL_ANTICIPATE_GRID_NUMBER_OF_STEPS}")

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

    # 4. Trading Logic with Grid Entry System
    trades = []
    sl_history = []

    # Grid entry system: track multiple positions with average price
    active_positions = []  # List of {'entry_price': float, 'entry_time': datetime}
    current_direction = None  # 'BUY' or 'SELL' - tracks current trade direction
    current_sl = None
    current_tp = None
    last_grid_entry_price = None  # Track last entry price for grid spacing
    
    # Track completed trade cycles (entry -> exit = 1 cycle, regardless of grid additions)
    completed_trade_cycles = 0

    # Parse EOD Time and Do Not Trade Before/After Time
    exit_time_obj = datetime.strptime(VWAP_SCORE_EXIT_TIME, "%H:%M:%S").time()
    do_not_trade_before_obj = datetime.strptime(VWAP_SCORE_REVERSAL_DO_NOT_TRADE_BEFORE, "%H:%M:%S").time()
    do_not_trade_after_obj = datetime.strptime(VWAP_SCORE_REVERSAL_DO_NOT_TRADE_AFTER, "%H:%M:%S").time()

    print(f"[INFO] Processing Anticipate Score signals (1-step: Immediate Entry)...")

    for i in range(1, len(df)):
        current_bar = df.iloc[i]
        prev_bar = df.iloc[i-1]

        timestamp = current_bar['timestamp']
        current_time = timestamp.time()
        close_price = current_bar['close']
        score = current_bar['clenow_score']
        prev_score = prev_bar['clenow_score']

        # Look for Initial Entries (if no position)
        if not active_positions:
            # Check max trades per day (limit by COMPLETED CYCLES)
            if completed_trade_cycles >= VWAP_SCORE_REVERSAL_ANTICIPATE_MAX_TRADES_DAY:
                continue

            # Check if current time is within allowed trading window
            if current_time < do_not_trade_before_obj or current_time > do_not_trade_after_obj:
                continue

        # Check EOD Exit
        if active_positions and current_time >= exit_time_obj:
            # Calculate average entry price
            avg_entry = sum(p['entry_price'] for p in active_positions) / len(active_positions)

            # Calculate total PnL based on average entry for all positions
            if current_direction == 'BUY':
                total_pnl = (close_price - avg_entry) * len(active_positions)
            else:  # SELL
                total_pnl = (avg_entry - close_price) * len(active_positions)

            # Record exit for each position
            for pos in active_positions:
                pos_pnl = (close_price - pos['entry_price']) if current_direction == 'BUY' else (pos['entry_price'] - close_price)
                trades.append({
                    'entry_time': pos['entry_time'],
                    'entry_price': pos['entry_price'],
                    'direction': current_direction,
                    'exit_time': timestamp,
                    'exit_price': close_price,
                    'pnl': pos_pnl,
                    'pnl_usd': pos_pnl * 20,
                    'exit_reason': 'eod'
                })

            print(f"[EXIT EOD] {current_time} {current_direction} x{len(active_positions)} @ {close_price:.2f} | Avg Entry: {avg_entry:.2f} | Total PnL: {total_pnl:.2f}")
            completed_trade_cycles += 1
            active_positions = []
            current_direction = None
            current_sl = None
            current_tp = None
            last_grid_entry_price = None
            continue # Stop trading for day

        if current_time >= exit_time_obj:
            continue

        # ATR Trailing Stop Update (uses average price)
        if active_positions and USE_VWAP_SCORE_ATR_TRAILING_STOP:
            current_atr = current_bar['atr']
            if not np.isnan(current_atr):
                if current_direction == 'BUY':
                    # SL = High - ATR * Mult (Only move UP)
                    potential_sl = current_bar['high'] - (current_atr * VWAP_SCORE_ATR_MULTIPLIER)
                    if potential_sl > current_sl:
                        current_sl = potential_sl
                elif current_direction == 'SELL':
                    # SL = Low + ATR * Mult (Only move DOWN)
                    potential_sl = current_bar['low'] + (current_atr * VWAP_SCORE_ATR_MULTIPLIER)
                    if potential_sl < current_sl:
                        current_sl = potential_sl

        # Record SL History (for plotting)
        if active_positions:
            sl_history.append({
                'timestamp': timestamp,
                'sl_price': current_sl
            })

        # Grid Entry Logic - Add positions when price moves against us
        if active_positions and ENABLE_REVERSAL_ANTICIPATE_GRID:
            # Check if we can add more positions
            if len(active_positions) <= REVERSAL_ANTICIPATE_GRID_NUMBER_OF_STEPS:
                if current_direction == 'BUY':
                    # LONG: Add if price drops GRID_STEP points from last entry
                    if close_price <= last_grid_entry_price - REVERSAL_ANTICIPATE_GRID_STEP:
                        # Add new LONG position
                        active_positions.append({
                            'entry_price': close_price,
                            'entry_time': timestamp
                        })
                        last_grid_entry_price = close_price

                        # Recalculate TP/SL based on new average
                        avg_entry = sum(p['entry_price'] for p in active_positions) / len(active_positions)
                        current_sl = avg_entry - VWAP_SCORE_REVERSAL_SL_POINTS
                        current_tp = avg_entry + VWAP_SCORE_REVERSAL_TP_POINTS

                        print(f"[GRID ADD LONG] {current_time} @ {close_price:.2f} | Position #{len(active_positions)} | New Avg: {avg_entry:.2f} | TP: {current_tp:.2f} | SL: {current_sl:.2f}")

                elif current_direction == 'SELL':
                    # SHORT: Add if price rises GRID_STEP points from last entry
                    if close_price >= last_grid_entry_price + REVERSAL_ANTICIPATE_GRID_STEP:
                        # Add new SHORT position
                        active_positions.append({
                            'entry_price': close_price,
                            'entry_time': timestamp
                        })
                        last_grid_entry_price = close_price

                        # Recalculate TP/SL based on new average
                        avg_entry = sum(p['entry_price'] for p in active_positions) / len(active_positions)
                        current_sl = avg_entry + VWAP_SCORE_REVERSAL_SL_POINTS
                        current_tp = avg_entry - VWAP_SCORE_REVERSAL_TP_POINTS

                        print(f"[GRID ADD SHORT] {current_time} @ {close_price:.2f} | Position #{len(active_positions)} | New Avg: {avg_entry:.2f} | TP: {current_tp:.2f} | SL: {current_sl:.2f}")

        # Manage Open Position (TP/SL) - All positions exit together
        if active_positions:
            # Check SL
            if current_direction == 'BUY':
                if current_bar['low'] <= current_sl:
                    # Calculate average entry
                    avg_entry = sum(p['entry_price'] for p in active_positions) / len(active_positions)

                    # Record exit for each position
                    for pos in active_positions:
                        pos_pnl = current_sl - pos['entry_price']
                        trades.append({
                            'entry_time': pos['entry_time'],
                            'entry_price': pos['entry_price'],
                            'direction': 'BUY',
                            'exit_time': timestamp,
                            'exit_price': current_sl,
                            'pnl': pos_pnl,
                            'pnl_usd': pos_pnl * 20,
                            'exit_reason': 'stop'
                        })

                    total_pnl = (current_sl - avg_entry) * len(active_positions)
                    print(f"[EXIT SL] {current_time} BUY x{len(active_positions)} @ {current_sl:.2f} (Low: {current_bar['low']:.2f}) | Avg Entry: {avg_entry:.2f} | Total PnL: {total_pnl:.2f}")
                    completed_trade_cycles += 1
                    active_positions = []
                    current_direction = None
                    current_sl = None
                    current_tp = None
                    last_grid_entry_price = None

                elif current_bar['high'] >= current_tp:
                    # Calculate average entry
                    avg_entry = sum(p['entry_price'] for p in active_positions) / len(active_positions)

                    # Record exit for each position
                    for pos in active_positions:
                        pos_pnl = current_tp - pos['entry_price']
                        trades.append({
                            'entry_time': pos['entry_time'],
                            'entry_price': pos['entry_price'],
                            'direction': 'BUY',
                            'exit_time': timestamp,
                            'exit_price': current_tp,
                            'pnl': pos_pnl,
                            'pnl_usd': pos_pnl * 20,
                            'exit_reason': 'profit'
                        })

                    total_pnl = (current_tp - avg_entry) * len(active_positions)
                    print(f"[EXIT TP] {current_time} BUY x{len(active_positions)} @ {current_tp:.2f} (High: {current_bar['high']:.2f}) | Avg Entry: {avg_entry:.2f} | Total PnL: {total_pnl:.2f}")
                    completed_trade_cycles += 1
                    active_positions = []
                    current_direction = None
                    current_sl = None
                    current_tp = None
                    last_grid_entry_price = None

            elif current_direction == 'SELL':
                if current_bar['high'] >= current_sl:
                    # Calculate average entry
                    avg_entry = sum(p['entry_price'] for p in active_positions) / len(active_positions)

                    # Record exit for each position
                    for pos in active_positions:
                        pos_pnl = pos['entry_price'] - current_sl
                        trades.append({
                            'entry_time': pos['entry_time'],
                            'entry_price': pos['entry_price'],
                            'direction': 'SELL',
                            'exit_time': timestamp,
                            'exit_price': current_sl,
                            'pnl': pos_pnl,
                            'pnl_usd': pos_pnl * 20,
                            'exit_reason': 'stop'
                        })

                    total_pnl = (avg_entry - current_sl) * len(active_positions)
                    print(f"[EXIT SL] {current_time} SELL x{len(active_positions)} @ {current_sl:.2f} (High: {current_bar['high']:.2f}) | Avg Entry: {avg_entry:.2f} | Total PnL: {total_pnl:.2f}")
                    completed_trade_cycles += 1
                    active_positions = []
                    current_direction = None
                    current_sl = None
                    current_tp = None
                    last_grid_entry_price = None

                elif current_bar['low'] <= current_tp:
                    # Calculate average entry
                    avg_entry = sum(p['entry_price'] for p in active_positions) / len(active_positions)

                    # Record exit for each position
                    for pos in active_positions:
                        pos_pnl = pos['entry_price'] - current_tp
                        trades.append({
                            'entry_time': pos['entry_time'],
                            'entry_price': pos['entry_price'],
                            'direction': 'SELL',
                            'exit_time': timestamp,
                            'exit_price': current_tp,
                            'pnl': pos_pnl,
                            'pnl_usd': pos_pnl * 20,
                            'exit_reason': 'profit'
                        })

                    total_pnl = (avg_entry - current_tp) * len(active_positions)
                    print(f"[EXIT TP] {current_time} SELL x{len(active_positions)} @ {current_tp:.2f} (Low: {current_bar['low']:.2f}) | Avg Entry: {avg_entry:.2f} | Total PnL: {total_pnl:.2f}")
                    completed_trade_cycles += 1
                    active_positions = []
                    current_direction = None
                    current_sl = None
                    current_tp = None
                    last_grid_entry_price = None

        # Look for Initial Entries (if no position)
        if not active_positions:
            # Check max trades per day (count signal groups not individual positions)
            completed_signals = len(set(t['entry_time'] for t in trades if 'entry_time' in t))
            if completed_signals >= MAX_NUM_TRADES_PER_DAY:
                continue

            # Check if current time is within allowed trading window
            if current_time < do_not_trade_before_obj or current_time > do_not_trade_after_obj:
                continue

            # ONE-STEP ANTICIPATE LOGIC (Immediate Entry at Threshold Cross)

            if pd.notna(prev_score) and pd.notna(score):
                # SHORT ENTRY: Score crosses UP through +Threshold (Green Dot - Immediate)
                if prev_score < CLENOW_THRESHOLD and score >= CLENOW_THRESHOLD:
                    # Execute SHORT entry immediately (anticipating reversal)
                    entry_price = close_price
                    current_sl = entry_price + VWAP_SCORE_REVERSAL_SL_POINTS
                    current_tp = entry_price - VWAP_SCORE_REVERSAL_TP_POINTS
                    current_direction = 'SELL'
                    active_positions.append({
                        'entry_price': entry_price,
                        'entry_time': timestamp
                    })
                    last_grid_entry_price = entry_price

                    print(f"[ENTRY SHORT ANTICIPATE] {current_time} @ {entry_price:.2f} (Green Dot: {prev_score:.2f} -> {score:.2f} >= +{CLENOW_THRESHOLD}) | TP: {current_tp:.2f} | SL: {current_sl:.2f}")

                # LONG ENTRY: Score crosses DOWN through -Threshold (Red Dot - Immediate)
                elif prev_score > -CLENOW_THRESHOLD and score <= -CLENOW_THRESHOLD:
                    # Execute LONG entry immediately (anticipating reversal)
                    entry_price = close_price
                    current_sl = entry_price - VWAP_SCORE_REVERSAL_SL_POINTS
                    current_tp = entry_price + VWAP_SCORE_REVERSAL_TP_POINTS
                    current_direction = 'BUY'
                    active_positions.append({
                        'entry_price': entry_price,
                        'entry_time': timestamp
                    })
                    last_grid_entry_price = entry_price

                    print(f"[ENTRY LONG ANTICIPATE] {current_time} @ {entry_price:.2f} (Red Dot: {prev_score:.2f} -> {score:.2f} <= -{CLENOW_THRESHOLD}) | TP: {current_tp:.2f} | SL: {current_sl:.2f}")

    # 5. Save Trades
    tradings_dir = Path(OUTPUTS_DIR) / "trading"
    tradings_dir.mkdir(parents=True, exist_ok=True)

    if trades:
        df_trades = pd.DataFrame(trades)
        output_file = tradings_dir / f"tracking_record_vwap_score_reversal_anticipate_{current_date}.csv"
        df_trades.to_csv(output_file, index=False, sep=';', decimal=',')
        print(f"\n[OK] Saved {len(trades)} trades to {output_file}")

        total_pnl = df_trades['pnl_usd'].sum()
        print(f"[RESULT] Total PnL: ${total_pnl:.2f}")
    else:
        print("\n[INFO] No trades executed.")
        # Clean up stale file if it exists
        output_file = tradings_dir / f"tracking_record_vwap_score_reversal_anticipate_{current_date}.csv"
        if output_file.exists():
            output_file.unlink()
            print(f"[INFO] Removed stale trade file: {output_file.name}")

        # Clean up stale SL history
        sl_file = tradings_dir / f"sl_history_vwap_score_reversal_anticipate_{current_date}.csv"
        if sl_file.exists():
            sl_file.unlink()

    # Save SL History
    if sl_history:
        df_sl = pd.DataFrame(sl_history)
        sl_file = tradings_dir / f"sl_history_vwap_score_reversal_anticipate_{current_date}.csv"
        df_sl.to_csv(sl_file, index=False, sep=';', decimal=',')
        print(f"[OK] Saved {len(df_sl)} SL points to {sl_file}")


if __name__ == "__main__":
    run_strategy()

"""
VWAP Square Strategy (Rectangle Breakout)
Strategy based on breakouts from VWAP Slope rectangles:
- LONG (BUY): Price crosses UP through rectangle MAX (y2) within LISTENING_TIME after square closes
- SHORT (SELL): Price crosses DOWN through rectangle MIN (y1) within LISTENING_TIME after square closes
- Fixed TP and SL from config
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, time, timedelta
from config import (
    DATE, START_DATE, END_DATE,
    DATA_DIR, OUTPUTS_DIR, POINT_VALUE,
    ENABLE_VWAP_SQUARE_STRATEGY,
    VWAP_SQUARE_TP_POINTS, VWAP_SQUARE_SL_POINTS,
    VWAP_SQUARE_MAX_POSITIONS,
    VWAP_SQUARE_START_HOUR, VWAP_SQUARE_END_HOUR,
    VWAP_SQUARE_LISTENING_TIME,
    VWAP_SQUARE_SHIFT_POINTS,
    VWAP_SQUARE_MIN_SPIKE,
    USE_SQUARE_VWAP_SLOW_TREND_FILTER,
    USE_SQUARE_ATR_TRAILING_STOP, SQUARE_ATR_PERIOD, SQUARE_ATR_MULTIPLIER,
    USE_OPOSITE_SIDE_OF_SQUARE_AS_STOP,
    USE_VWAP_SQUARE_SHAKE_OUT,
    VWAP_SQUARE_SHAKE_OUT_RETRACEMENT_PCT,
    VWAP_FAST, VWAP_SLOW
)
from show_config_dashboard import update_dashboard

# Auto-update configuration dashboard
update_dashboard()

# Map to shorter names for compatibility
TP_POINTS = VWAP_SQUARE_TP_POINTS
SL_POINTS = VWAP_SQUARE_SL_POINTS
MAXIMUM_POSITIONS_OPEN = VWAP_SQUARE_MAX_POSITIONS
START_TRADING_HOUR = VWAP_SQUARE_START_HOUR
END_TRADING_HOUR = VWAP_SQUARE_END_HOUR
LISTENING_TIME_MINUTES = VWAP_SQUARE_LISTENING_TIME
SHIFT_POINTS = VWAP_SQUARE_SHIFT_POINTS

# ============================================================================
# CHECK IF STRATEGY IS ENABLED
# ============================================================================
if not ENABLE_VWAP_SQUARE_STRATEGY:
    print("\n" + "="*80)
    print("VWAP SQUARE STRATEGY - DISABLED")
    print("="*80)
    print("\n[INFO] Strategy is disabled in config.py")
    print("[INFO] Set ENABLE_VWAP_SQUARE_STRATEGY = True to enable")
    print("="*80 + "\n")
    exit(0)

# ============================================================================
# STRATEGY CONFIGURATION
# ============================================================================
TRADING_DIR = OUTPUTS_DIR / "trading"
TRADING_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = TRADING_DIR / f"tracking_record_vwap_square_{DATE}.csv"

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
print("VWAP SQUARE STRATEGY - Rectangle Breakout")
print("="*80)
print(f"\nDate: {DATE} ({day_name})")
print(f"Trading Hours: {START_TRADING_HOUR} to {END_TRADING_HOUR}")
print(f"\nStrategy Parameters:")
print(f"  - Take Profit: {TP_POINTS} points (${TP_POINTS * POINT_VALUE:.0f})")
if USE_SQUARE_ATR_TRAILING_STOP:
    print(f"  - Stop Loss: ATR Trailing (Period={SQUARE_ATR_PERIOD}, Multiplier={SQUARE_ATR_MULTIPLIER})")
else:
    print(f"  - Stop Loss: {SL_POINTS} points (${SL_POINTS * POINT_VALUE:.0f}) - FIXED")
if USE_OPOSITE_SIDE_OF_SQUARE_AS_STOP:
    print(f"  - Initial Stop: Opposite side of rectangle (GREEN=y1 min, RED=y2 max)")
    print(f"               Then switch to trailing stop when it's better")
print(f"  - Max Positions: {MAXIMUM_POSITIONS_OPEN}")
print(f"  - Listening Time: {LISTENING_TIME_MINUTES} minutes after square closes")
print(f"  - Shift Points: {SHIFT_POINTS} points (entry margin)")
if VWAP_SQUARE_MIN_SPIKE > 0:
    print(f"  - Min Spike Filter: {VWAP_SQUARE_MIN_SPIKE} points (filters small rectangles)")
else:
    print(f"  - Min Spike Filter: DISABLED (all rectangle sizes accepted)")
print(f"  - Point Value: ${POINT_VALUE:.0f} per point")
print(f"  - Trend Filter: {'ENABLED (VWAP Fast vs Slow)' if USE_SQUARE_VWAP_SLOW_TREND_FILTER else 'DISABLED'}")
print(f"  - Shake Out Mode: {'ENABLED (trade failed breakouts)' if USE_VWAP_SQUARE_SHAKE_OUT else 'DISABLED (normal breakout)'}")
print(f"\nEntry Logic ({'SHAKE OUT - Retracement Confirmation' if USE_VWAP_SQUARE_SHAKE_OUT else 'NORMAL - Breakout'}):")
if USE_VWAP_SQUARE_SHAKE_OUT:
    # Shake out mode: require retracement before entry in rectangle direction
    print(f"  - GREEN rectangles (tall_narrow_up):")
    print(f"    > BUY LONG: Price breaks UPPER, retraces {VWAP_SQUARE_SHAKE_OUT_RETRACEMENT_PCT}%, then re-breaks UPPER")
    if USE_SQUARE_VWAP_SLOW_TREND_FILTER:
        print(f"    > Only in UPTREND (VWAP Fast > VWAP Slow)")
    print(f"  - RED rectangles (tall_narrow_down):")
    print(f"    > SELL SHORT: Price breaks LOWER, retraces {VWAP_SQUARE_SHAKE_OUT_RETRACEMENT_PCT}%, then re-breaks LOWER")
    if USE_SQUARE_VWAP_SLOW_TREND_FILTER:
        print(f"    > Only in DOWNTREND (VWAP Fast < VWAP Slow)")
else:
    # Normal breakout mode
    print(f"  - GREEN rectangles (tall_narrow_up):")
    if SHIFT_POINTS > 0:
        print(f"    > BUY when price breaks UPPER limit + {SHIFT_POINTS} pts within {LISTENING_TIME_MINUTES} min")
    else:
        print(f"    > BUY when price breaks UPPER limit within {LISTENING_TIME_MINUTES} min")
    if USE_SQUARE_VWAP_SLOW_TREND_FILTER:
        print(f"    > Only in UPTREND (VWAP Fast > VWAP Slow)")
    print(f"  - RED rectangles (tall_narrow_down):")
    if SHIFT_POINTS > 0:
        print(f"    > SELL when price breaks LOWER limit - {SHIFT_POINTS} pts within {LISTENING_TIME_MINUTES} min")
    else:
        print(f"    > SELL when price breaks LOWER limit within {LISTENING_TIME_MINUTES} min")
    if USE_SQUARE_VWAP_SLOW_TREND_FILTER:
        print(f"    > Only in DOWNTREND (VWAP Fast < VWAP Slow)")
print(f"  - ORANGE rectangles (consolidation): IGNORED (no trades)")
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
# CALCULATE VWAP INDICATORS FOR TREND FILTER
# ============================================================================
if USE_SQUARE_VWAP_SLOW_TREND_FILTER:
    from calculate_vwap import calculate_vwap

    print(f"[INFO] Calculating VWAP indicators for trend filter...")

    # Calculate VWAP Fast and Slow if not already present
    if 'vwap_fast' not in df.columns or df['vwap_fast'].isna().all():
        df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)

    if 'vwap_slow' not in df.columns or df['vwap_slow'].isna().all():
        df['vwap_slow'] = calculate_vwap(df, period=VWAP_SLOW)

    # Determine trend direction
    df['uptrend'] = (df['vwap_fast'] > df['vwap_slow']) & (df['vwap_slow'].notna())
    df['downtrend'] = (df['vwap_fast'] < df['vwap_slow']) & (df['vwap_slow'].notna())

    uptrend_bars = df['uptrend'].sum()
    downtrend_bars = df['downtrend'].sum()

    print(f"[OK] Trend filter enabled:")
    print(f"  - Uptrend bars (VWAP Fast > VWAP Slow): {uptrend_bars}")
    print(f"  - Downtrend bars (VWAP Fast < VWAP Slow): {downtrend_bars}")
    print(f"  - BUY trades: only in uptrend")
    print(f"  - SELL trades: only in downtrend")
else:
    print(f"[INFO] Trend filter DISABLED - trading all breakouts")

# ============================================================================
# CALCULATE ATR FOR TRAILING STOP (if enabled)
# ============================================================================
if USE_SQUARE_ATR_TRAILING_STOP:
    from calculate_atr import calculate_atr

    print(f"[INFO] Calculating ATR for trailing stop...")
    print(f"  - ATR Period: {SQUARE_ATR_PERIOD}")
    print(f"  - ATR Multiplier: {SQUARE_ATR_MULTIPLIER}")

    df['atr'] = calculate_atr(df, period=SQUARE_ATR_PERIOD)
    atr_valid_bars = df['atr'].notna().sum()

    print(f"[OK] ATR calculated: {atr_valid_bars} valid values")
else:
    print(f"[INFO] Using FIXED stop loss: {SL_POINTS} points")

# ============================================================================
# FIND RECTANGLES - REALTIME METHOD
# ============================================================================
from find_rectangles_realtime import find_vwap_slope_rectangles_realtime

print(f"[INFO] Finding VWAP Slope rectangles (REALTIME METHOD)...")
print(f"[INFO] Rectangles close EARLY when price_per_bar > threshold (no wait for blue square)")
rectangles = find_vwap_slope_rectangles_realtime(df)

if not rectangles:
    print("[WARN] No rectangles found, cannot execute strategy")
    print("[INFO] No trades will be generated")
    exit(0)

print(f"[OK] Found {len(rectangles)} rectangles")

# ============================================================================
# PREPARE BREAKOUT ZONES
# ============================================================================
# NEW LOGIC:
# - Only create BUY zones for GREEN rectangles (tall_narrow_up) - upper breakout only
# - Only create SELL zones for RED rectangles (tall_narrow_down) - lower breakout only
# - IGNORE ORANGE rectangles (consolidation) completely

breakout_zones = []

green_count = 0
red_count = 0
orange_ignored = 0

for rect in rectangles:
    rect_type = rect.get('type', 'consolidation')

    # Skip orange consolidation rectangles completely
    if rect_type == 'consolidation':
        orange_ignored += 1
        continue

    # Rectangle closes at x2_time (blue square)
    close_time = rect['x2_time']

    # Listening period extends LISTENING_TIME_MINUTES after close
    listening_end_time = close_time + timedelta(minutes=LISTENING_TIME_MINUTES)

    # GREEN rectangle: BUY on upper breakout (y2), but only after lower (y1) is tested
    if rect_type == 'tall_narrow_up':
        rectangle_height = rect['y2'] - rect['y1']

        if USE_VWAP_SQUARE_SHAKE_OUT:
            # Shake out mode: wait for upper break, then after retracement, enter LONG at retracement level
            direction = 'BUY'
            test_level = rect['y2'] + SHIFT_POINTS  # First: price must break upper

            # Calculate retracement level (how far down price must go to confirm shake out)
            retracement_distance = rectangle_height * (VWAP_SQUARE_SHAKE_OUT_RETRACEMENT_PCT / 100.0)
            retracement_level = rect['y2'] - retracement_distance
            entry_level = retracement_level  # Enter at the retracement level, not at rectangle boundary
        else:
            # Normal mode: wait for lower touch, then enter LONG on upper break
            direction = 'BUY'
            test_level = rect['y1']  # First: price must touch/test lower boundary
            entry_level = rect['y2'] + SHIFT_POINTS  # Then: enter LONG when breaks upper
            retracement_level = None  # Not used in normal mode

        breakout_zones.append({
            'start_time': close_time,
            'end_time': listening_end_time,
            'breakout_level': entry_level,  # Final entry level
            'direction': direction,
            'rect_type': 'tall_narrow_up',
            'rect_index': rectangles.index(rect),
            'rect_y1': rect['y1'],  # Store rectangle min
            'rect_y2': rect['y2'],  # Store rectangle max
            'consumed': False,
            # Two-step entry tracking
            'requires_test': True,  # Must test opposite side first
            'test_level': test_level,  # Level that must be touched first
            'test_triggered': False,  # True when test level is touched
            # Shake out retracement tracking
            'retracement_level': retracement_level,  # Level that confirms shake out (only in shake out mode)
            'retracement_triggered': False  # True when price reaches retracement level
        })
        green_count += 1

    # RED rectangle: SELL on lower breakout (y1), but only after upper (y2) is tested
    elif rect_type == 'tall_narrow_down':
        rectangle_height = rect['y2'] - rect['y1']

        if USE_VWAP_SQUARE_SHAKE_OUT:
            # Shake out mode: wait for lower break, then after retracement, enter SHORT at retracement level
            direction = 'SELL'
            test_level = rect['y1'] - SHIFT_POINTS  # First: price must break lower

            # Calculate retracement level (how far up price must go to confirm shake out)
            retracement_distance = rectangle_height * (VWAP_SQUARE_SHAKE_OUT_RETRACEMENT_PCT / 100.0)
            retracement_level = rect['y1'] + retracement_distance
            entry_level = retracement_level  # Enter at the retracement level, not at rectangle boundary
        else:
            # Normal mode: wait for upper touch, then enter SHORT on lower break
            direction = 'SELL'
            test_level = rect['y2']  # First: price must touch/test upper boundary
            entry_level = rect['y1'] - SHIFT_POINTS  # Then: enter SHORT when breaks lower
            retracement_level = None  # Not used in normal mode

        breakout_zones.append({
            'start_time': close_time,
            'end_time': listening_end_time,
            'breakout_level': entry_level,  # Final entry level
            'direction': direction,
            'rect_type': 'tall_narrow_down',
            'rect_index': rectangles.index(rect),
            'rect_y1': rect['y1'],  # Store rectangle min
            'rect_y2': rect['y2'],  # Store rectangle max
            'consumed': False,
            # Two-step entry tracking
            'requires_test': True,  # Must test opposite side first
            'test_level': test_level,  # Level that must be touched first
            'test_triggered': False,  # True when test level is touched
            # Shake out retracement tracking
            'retracement_level': retracement_level,  # Level that confirms shake out (only in shake out mode)
            'retracement_triggered': False  # True when price reaches retracement level
        })

        red_count += 1

print(f"[INFO] Created {len(breakout_zones)} breakout listening zones:")
print(f"  - {green_count} GREEN rectangles (BUY on upper breakout)")
print(f"  - {red_count} RED rectangles (SELL on lower breakout)")
print(f"  - {orange_ignored} ORANGE rectangles (IGNORED)")

# ============================================================================
# STRATEGY EXECUTION
# ============================================================================
trades = []
open_position = None
sl_history = []  # Track trailing stop evolution for visualization

print(f"\n[INFO] Processing trades...")

for idx, bar in df.iterrows():
    current_time = bar['timestamp']
    current_time_only = current_time.time()

    # Check if within trading hours
    within_trading_hours = start_time <= current_time_only <= end_time

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

        # Update trailing stop if enabled
        if USE_SQUARE_ATR_TRAILING_STOP and not pd.isna(bar['atr']):
            atr_distance = bar['atr'] * SQUARE_ATR_MULTIPLIER

            if direction == 'BUY':
                # For LONG: Trailing stop = highest price since entry - ATR distance
                if 'highest_since_entry' not in open_position:
                    open_position['highest_since_entry'] = bar['high']
                    open_position['using_trail'] = True
                else:
                    open_position['highest_since_entry'] = max(open_position['highest_since_entry'], bar['high'])

                # Update trailing stop (only moves up, never down)
                new_trail_stop = open_position['highest_since_entry'] - atr_distance
                sl_price = max(sl_price, new_trail_stop)
                open_position['sl_price'] = sl_price

            else:  # SELL
                # For SHORT: Trailing stop = lowest price since entry + ATR distance
                if 'lowest_since_entry' not in open_position:
                    open_position['lowest_since_entry'] = bar['low']
                    open_position['using_trail'] = True
                else:
                    open_position['lowest_since_entry'] = min(open_position['lowest_since_entry'], bar['low'])

                # Update trailing stop (only moves down, never up)
                new_trail_stop = open_position['lowest_since_entry'] + atr_distance
                sl_price = min(sl_price, new_trail_stop)
                open_position['sl_price'] = sl_price

            # Record trailing stop history for visualization
            sl_history.append({
                'timestamp': current_time,
                'sl_price': sl_price,
                'direction': direction
            })

        # Check exit conditions
        if direction == 'BUY':
            # LONG position: TP when price goes up, SL when price goes down
            if bar['high'] >= tp_price:
                exit_reason = 'tp_exit'
                exit_price = tp_price
            elif bar['low'] <= sl_price:
                # Tag as trail_stop if using ATR trailing, otherwise sl_exit
                if USE_SQUARE_ATR_TRAILING_STOP and open_position.get('using_trail', False):
                    exit_reason = 'trail_stop'
                else:
                    exit_reason = 'sl_exit'
                exit_price = sl_price
        else:  # SELL
            # SHORT position: TP when price goes down, SL when price goes up
            if bar['low'] <= tp_price:
                exit_reason = 'tp_exit'
                exit_price = tp_price
            elif bar['high'] >= sl_price:
                # Tag as trail_stop if using ATR trailing, otherwise sl_exit
                if USE_SQUARE_ATR_TRAILING_STOP and open_position.get('using_trail', False):
                    exit_reason = 'trail_stop'
                else:
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
                'exit_time': current_time,
                'exit_price': exit_price,
                'pnl': pnl_points,
                'pnl_usd': pnl_usd,
                'exit_reason': exit_reason,
                'breakout_level': open_position['breakout_level'],
                'rectangle_index': open_position['rectangle_index']
            })

            open_position = None

    # ========================================================================
    # ENTRY LOGIC - Check if we should enter a new position
    # ========================================================================
    if open_position is None and within_trading_hours:
        # Check all active breakout zones at current time
        for zone in breakout_zones:
            # Check if current time is within listening period
            if zone['start_time'] <= current_time <= zone['end_time']:

                # Skip if rectangle already consumed
                if zone['consumed']:
                    continue

                # Get previous bar for crossover detection
                if idx > 0:
                    prev_bar = df.loc[idx - 1]

                    zone_direction = zone['direction']
                    breakout_level = zone['breakout_level']

                    # TWO-STEP (or THREE-STEP for shake out) ENTRY PROCESS
                    # Step 1: Check if test level has been touched
                    if not zone['test_triggered']:
                        test_level = zone['test_level']

                        # Check if price touched the test level
                        if USE_VWAP_SQUARE_SHAKE_OUT:
                            # Shake out: test level must be BROKEN (with crossover)
                            if zone['rect_type'] == 'tall_narrow_up':
                                # GREEN rect: check if price broke ABOVE y2
                                test_touched = prev_bar['high'] < test_level and bar['high'] >= test_level
                            else:  # tall_narrow_down
                                # RED rect: check if price broke BELOW y1
                                test_touched = prev_bar['low'] > test_level and bar['low'] <= test_level
                        else:
                            # Normal: test level just needs to be TOUCHED (no crossover needed)
                            if zone['rect_type'] == 'tall_narrow_up':
                                # GREEN rect: check if price touched y1 (lower)
                                test_touched = bar['low'] <= test_level
                            else:  # tall_narrow_down
                                # RED rect: check if price touched y2 (upper)
                                test_touched = bar['high'] >= test_level

                        if test_touched:
                            # Mark test as triggered - now can wait for retracement (shake out) or entry (normal)
                            zone['test_triggered'] = True

                        # Don't check for entry yet - need to wait for test
                        continue

                    # Step 2 (SHAKE OUT MODE ONLY): Check if retracement level has been reached
                    # When price touches the retracement level, ENTER IMMEDIATELY (like a limit order)
                    if USE_VWAP_SQUARE_SHAKE_OUT:
                        retracement_level = zone['retracement_level']
                        entry_triggered = False

                        # Check if price has REACHED (touched or exceeded) the retracement level
                        if zone['rect_type'] == 'tall_narrow_up':
                            # GREEN rect: ENTER LONG when price retraces down and touches retracement level
                            entry_triggered = bar['low'] <= retracement_level
                        else:  # tall_narrow_down
                            # RED rect: ENTER SHORT when price retraces up and touches retracement level
                            entry_triggered = bar['high'] >= retracement_level

                        if not entry_triggered:
                            # Price hasn't reached retracement level yet, skip this zone
                            continue
                        # If we reach here, price touched retracement level - ENTER NOW

                    else:
                        # NORMAL MODE (not shake out): Check for breakout crossover
                        # For BUY: price crosses UP through entry level
                        if zone_direction == 'BUY':
                            entry_triggered = prev_bar['high'] < breakout_level and bar['high'] >= breakout_level
                        # For SELL: price crosses DOWN through entry level
                        else:  # SELL
                            entry_triggered = prev_bar['low'] > breakout_level and bar['low'] <= breakout_level

                        if not entry_triggered:
                            # Price hasn't crossed entry level yet, skip this zone
                            continue

                    # If we reach here, entry condition is met - check trend filter (if enabled)
                    allow_trade = True
                    if USE_SQUARE_VWAP_SLOW_TREND_FILTER:
                        # For BUY: only allow in uptrend
                        if zone_direction == 'BUY':
                            allow_trade = bar.get('uptrend', False)
                        # For SELL: only allow in downtrend
                        else:  # SELL
                            allow_trade = bar.get('downtrend', False)

                    # Execute trade if allowed
                    if allow_trade:
                        # Set entry price and TP/SL based on direction
                        entry_price = breakout_level

                        if zone_direction == 'BUY':
                            tp_price = entry_price + TP_POINTS
                            # For BUY: use opposite side (y1 = min) if enabled
                            if USE_OPOSITE_SIDE_OF_SQUARE_AS_STOP:
                                sl_price = zone['rect_y1']  # Rectangle minimum
                            else:
                                sl_price = entry_price - SL_POINTS
                        else:  # SELL
                            tp_price = entry_price - TP_POINTS
                            # For SELL: use opposite side (y2 = max) if enabled
                            if USE_OPOSITE_SIDE_OF_SQUARE_AS_STOP:
                                sl_price = zone['rect_y2']  # Rectangle maximum
                            else:
                                sl_price = entry_price + SL_POINTS

                        open_position = {
                            'direction': zone_direction,
                            'entry_time': current_time,
                            'entry_price': entry_price,
                            'tp_price': tp_price,
                            'sl_price': sl_price,
                            'breakout_level': breakout_level,
                            'rectangle_index': zone['rect_index']
                        }
                        # Mark zone as consumed since we entered a trade
                        zone['consumed'] = True
                        break  # Only take first breakout

    # ========================================================================
    # CONSUME ZONES - Mark zones as consumed if price touches the level
    # ========================================================================
    # IMPORTANT: Once price touches a breakout level, the zone is consumed
    # and can never be used again (level is no longer "virgin")
    # This runs AFTER entry logic to allow crossovers to be detected first
    #
    # EXCEPTION: In shake out mode, zones are NOT consumed when entry level is touched
    # because we need price to RETURN to that level for the re-breakout entry
    if open_position is None:  # Only consume if we didn't just enter a trade
        for zone in breakout_zones:
            if zone['consumed']:
                continue

            # Check if current time is within listening period
            if zone['start_time'] <= current_time <= zone['end_time']:
                # Skip consumption check for shake out zones - they need the full 3-step process
                if USE_VWAP_SQUARE_SHAKE_OUT:
                    continue  # Don't consume shake out zones based on price touching entry level

                zone_direction = zone['direction']
                breakout_level = zone['breakout_level']

                # Check if price has touched/crossed the virgin level
                level_touched = False

                if zone_direction == 'BUY':
                    # For BUY zone: level is touched if price reaches upper breakout
                    level_touched = bar['high'] >= breakout_level
                else:  # SELL
                    # For SELL zone: level is touched if price reaches lower breakout
                    level_touched = bar['low'] <= breakout_level

                # If level touched, consume the zone (can never be used again)
                if level_touched:
                    zone['consumed'] = True

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
        'breakout_level': open_position['breakout_level'],
        'rectangle_index': open_position['rectangle_index']
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
    trail_trades = df_trades[df_trades['exit_reason'] == 'trail_stop']
    eod_trades = df_trades[df_trades['exit_reason'] == 'eod_exit']

    total_pnl = df_trades['pnl'].sum()
    total_pnl_usd = df_trades['pnl_usd'].sum()

    total_trades = len(df_trades)
    profit_count = len(profit_trades)
    stop_count = len(stop_trades)
    trail_count = len(trail_trades)
    eod_count = len(eod_trades)
    denom = profit_count + stop_count + trail_count
    win_rate = (profit_count / denom * 100) if denom > 0 else 0.0

    avg_points = total_pnl / total_trades if total_trades > 0 else 0.0
    avg_usd = total_pnl_usd / total_trades if total_trades > 0 else 0.0

    # Breakdown by direction
    buy_trades = df_trades[df_trades['direction'] == 'BUY']
    sell_trades = df_trades[df_trades['direction'] == 'SELL']
    buy_pnl_usd = buy_trades['pnl_usd'].sum() if len(buy_trades) > 0 else 0.0
    sell_pnl_usd = sell_trades['pnl_usd'].sum() if len(sell_trades) > 0 else 0.0

    print("\n" + "="*80)
    print("TEST RESULTS - VWAP SQUARE STRATEGY")
    print("="*80)
    print(f"Date: {DATE}")
    print(f"Total trades: {total_trades}")
    if USE_SQUARE_ATR_TRAILING_STOP:
        print(f"Exit breakdown: {profit_count} TP / {stop_count} SL / {trail_count} TRAIL / {eod_count} EOD")
        print(f"Win rate: {win_rate:.1f}% ({profit_count} profits / {stop_count + trail_count} stops)")
    else:
        print(f"Exit breakdown: {profit_count} TP / {stop_count} SL / {eod_count} EOD")
        print(f"Win rate: {win_rate:.1f}% ({profit_count} profits / {stop_count} stops)")
    print(f"Total P&L: {total_pnl:+.0f} points (${total_pnl_usd:,.0f})")
    print(f"Average per trade: {avg_points:+.2f} points (${avg_usd:,.2f})")
    print(f"BUY trades: {len(buy_trades)} (${buy_pnl_usd:,.0f})")
    print(f"SELL trades: {len(sell_trades)} (${sell_pnl_usd:,.0f})")
    print("="*80 + "\n")

    # Save trailing stop history for visualization (if using ATR trailing stop)
    if USE_SQUARE_ATR_TRAILING_STOP and len(sl_history) > 0:
        df_sl = pd.DataFrame(sl_history)
        sl_history_file = OUTPUTS_DIR / "trading" / f"sl_history_vwap_square_{DATE}.csv"
        df_sl.to_csv(sl_history_file, index=False, sep=';', decimal=',')
        print(f"[OK] Trailing stop history saved: {sl_history_file.name} ({len(df_sl)} points)")

else:
    print(f"\n[INFO] No trades executed")
    print(f"[INFO] No output file generated")

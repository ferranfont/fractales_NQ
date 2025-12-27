"""
VWAP Momentum Strategy (Price Ejection - Green Dots)
Simple strategy based on price ejection from VWAP Fast:
- LONG when price ejects from VWAP (green dot signal)
- Fixed TP and SL from config
- Only LONG positions (no SHORT)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, time
from config import (
    DATE, START_DATE, END_DATE,
    VWAP_MOMENTUM_TP_POINTS, VWAP_MOMENTUM_SL_POINTS, VWAP_MOMENTUM_MAX_POSITIONS,
    VWAP_MOMENTUM_START_HOUR, VWAP_MOMENTUM_END_HOUR,
    VWAP_FAST, PRICE_EJECTION_TRIGGER, VWAP_SLOPE_DEGREE_WINDOW,
    DATA_DIR, OUTPUTS_DIR,
    ENABLE_VWAP_MOMENTUM_STRATEGY,
    USE_VWAP_SLOPE_INDICATOR_STOP_LOSS, VWAP_SLOPE_INDICATOR_LOW_VALUE
)

# Map to shorter names for compatibility
TP_POINTS = VWAP_MOMENTUM_TP_POINTS
SL_POINTS = VWAP_MOMENTUM_SL_POINTS
MAXIMUM_POSITIONS_OPEN = VWAP_MOMENTUM_MAX_POSITIONS
START_TRADING_HOUR = VWAP_MOMENTUM_START_HOUR
END_TRADING_HOUR = VWAP_MOMENTUM_END_HOUR

# ============================================================================
# CHECK IF STRATEGY IS ENABLED
# ============================================================================
if not ENABLE_VWAP_MOMENTUM_STRATEGY:
    print("\n" + "="*80)
    print("VWAP MOMENTUM STRATEGY - DISABLED")
    print("="*80)
    print("\n[INFO] Strategy is disabled in config.py")
    print("[INFO] Set ENABLE_VWAP_MOMENTUM_STRATEGY = True to enable")
    print("="*80 + "\n")
    exit(0)

# ============================================================================
# STRATEGY CONFIGURATION
# ============================================================================
TRADING_DIR = OUTPUTS_DIR / "trading"
TRADING_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = TRADING_DIR / f"tracking_record_vwap_momentum_{DATE}.csv"
POINT_VALUE = 20.0  # USD value per point for NQ futures

# Parse trading time range
start_time = datetime.strptime(START_TRADING_HOUR, "%H:%M:%S").time()
end_time = datetime.strptime(END_TRADING_HOUR, "%H:%M:%S").time()

# Calculate day of week (1=Monday, 7=Sunday)
date_obj = datetime.strptime(DATE, "%Y%m%d")
day_of_week = date_obj.isoweekday()  # 1=Monday, 2=Tuesday, ..., 7=Sunday
day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
day_name = day_names[day_of_week]

print("="*80)
print("VWAP MOMENTUM STRATEGY - ENABLED")
print("="*80)
print(f"\nConfiguration:")
print(f"  - Date: {DATE} ({day_name}, DoW={day_of_week})")
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

# ============================================================================
# HELPER FUNCTION: Calculate VWAP Slope
# ============================================================================
def calculate_vwap_slope_at_bar(df, bar_idx, window=VWAP_SLOPE_DEGREE_WINDOW):
    """
    Calculate VWAP slope at a specific bar using linear regression over window bars.

    Args:
        df: DataFrame with 'vwap_fast' column
        bar_idx: Index of the current bar
        window: Number of bars to look back for slope calculation

    Returns:
        slope: VWAP slope (points per bar), 0 if insufficient data
    """
    # Get the position in the dataframe
    bar_position = df.index.get_loc(bar_idx)

    # Need at least window bars
    if bar_position < window - 1:
        return 0.0

    # Get last 'window' bars including current bar
    start_pos = bar_position - window + 1
    end_pos = bar_position + 1

    vwap_window = df.iloc[start_pos:end_pos]['vwap_fast'].values

    # Check for NaN values
    if pd.isna(vwap_window).any():
        return 0.0

    # Simple linear regression: slope = (y2 - y1) / (x2 - x1)
    # Using first and last point for simplicity
    slope = (vwap_window[-1] - vwap_window[0]) / (window - 1)

    return slope

# ============================================================================
# CALCULATE INDICATORS
# ============================================================================
# Calculate VWAP Fast
from calculate_vwap import calculate_vwap
df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)

# Pre-calculate VWAP Slope for all bars (ABSOLUTE VALUE for exit logic)
print(f"[INFO] Calculating VWAP Slope for all bars...")
df['vwap_slope'] = [abs(calculate_vwap_slope_at_bar(df, idx, window=VWAP_SLOPE_DEGREE_WINDOW)) for idx in df.index]
print(f"[OK] VWAP Slope calculated for {len(df[df['vwap_slope'].notna()])} bars")

# Calculate price-VWAP distance (this creates the green dots)
df['price_vwap_distance'] = abs((df['close'] - df['vwap_fast']) / df['vwap_fast'])

# Detect price ejection signals (green dots)
# Green dot appears when price is ejected from VWAP (distance > PRICE_EJECTION_TRIGGER)
df['price_ejection'] = (df['price_vwap_distance'] > PRICE_EJECTION_TRIGGER) & (df['vwap_fast'].notna())

# Detect when price is above or below VWAP
df['price_above_vwap'] = (df['close'] > df['vwap_fast']).astype(bool)
df['price_below_vwap'] = (df['close'] < df['vwap_fast']).astype(bool)

# Entry signals:
# LONG: Green dot AND price above VWAP (bullish ejection)
# SHORT: Green dot AND price below VWAP (bearish ejection)
df['long_signal'] = df['price_ejection'] & df['price_above_vwap']
df['short_signal'] = df['price_ejection'] & df['price_below_vwap']

print(f"[INFO] VWAP Fast calculated")
print(f"[INFO] Price ejection signals (green dots): {df['price_ejection'].sum()}")
print(f"[INFO] LONG entry signals (green dots above VWAP): {df['long_signal'].sum()}")
print(f"[INFO] SHORT entry signals (green dots below VWAP): {df['short_signal'].sum()}")

# ============================================================================
# STRATEGY EXECUTION
# ============================================================================
trades = []
open_position = None

print(f"\n[INFO] Processing trades...")

for idx, bar in df.iterrows():
    current_time = bar['timestamp'].time()
    within_trading_hours = start_time <= current_time <= end_time

    # Skip if VWAP not available
    if pd.isna(bar['vwap_fast']):
        continue

    # Check if we have an open position - manage exit
    # IMPORTANT: Always process exits, even outside trading hours
    if open_position is not None:
        direction = open_position['direction']
        entry_price = open_position['entry_price']
        tp_price = open_position['tp_price']
        sl_price = open_position['sl_price']

        # Check exit conditions
        exit_reason = None
        exit_price = None

        # PRIORITY 1: Check regular TP/SL first (highest priority)
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

        # PRIORITY 2: Check VWAP Slope Indicator Stop Loss (if enabled)
        # ONLY triggers if:
        # 1. No TP/SL has been hit yet
        # 2. Position is currently in LOSS (not profit)
        # 3. VWAP slope crosses below threshold
        if exit_reason is None and USE_VWAP_SLOPE_INDICATOR_STOP_LOSS and not pd.isna(bar['vwap_slope']):
            # Calculate current P&L to check if we're in loss
            if direction == 'BUY':
                current_pnl = bar['close'] - entry_price
            else:  # SELL
                current_pnl = entry_price - bar['close']

            # Only apply slope exit if position is in LOSS
            if current_pnl < 0:
                # Get previous bar's vwap_slope to detect crossing
                if idx > 0:
                    prev_idx = df.index[df.index.get_loc(idx) - 1]
                    prev_slope = df.loc[prev_idx, 'vwap_slope']

                    # Check if VWAP slope crossed BELOW the low threshold
                    if not pd.isna(prev_slope):
                        if prev_slope >= VWAP_SLOPE_INDICATOR_LOW_VALUE and bar['vwap_slope'] < VWAP_SLOPE_INDICATOR_LOW_VALUE:
                            exit_reason = 'slope_exit'
                            exit_price = bar['close']

        # Close position if exit triggered
        if exit_reason:
            # Calculate P&L (different for LONG vs SHORT)
            if direction == 'BUY':
                pnl = exit_price - entry_price
            else:  # SELL
                pnl = entry_price - exit_price

            pnl_usd = pnl * POINT_VALUE

            # Calculate time in market (in minutes)
            time_in_market = (bar['timestamp'] - open_position['entry_time']).total_seconds() / 60.0

            # Calculate VWAP slope at exit
            vwap_slope_exit = calculate_vwap_slope_at_bar(df, idx, VWAP_SLOPE_DEGREE_WINDOW)

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
                'time_in_market': time_in_market,
                'vwap_slope_entry': open_position['vwap_slope_entry'],
                'vwap_slope_exit': vwap_slope_exit
            })

            open_position = None
            continue

    # Check for new entry signals (only if no position open AND within trading hours)
    if open_position is None and MAXIMUM_POSITIONS_OPEN > 0 and within_trading_hours:
        # LONG signal: Price ejection (green dot) above VWAP
        if bar['long_signal']:
            entry_price = bar['close']
            tp_price = entry_price + TP_POINTS
            sl_price = entry_price - SL_POINTS

            # Calculate VWAP slope at entry
            vwap_slope_entry = calculate_vwap_slope_at_bar(df, idx, VWAP_SLOPE_DEGREE_WINDOW)

            open_position = {
                'direction': 'BUY',
                'entry_time': bar['timestamp'],
                'entry_price': entry_price,
                'entry_vwap': bar['vwap_fast'],
                'tp_price': tp_price,
                'sl_price': sl_price,
                'vwap_slope_entry': vwap_slope_entry
            }

        # SHORT signal: Price ejection (green dot) below VWAP
        elif bar['short_signal']:
            entry_price = bar['close']
            tp_price = entry_price - TP_POINTS  # TP is below entry for shorts
            sl_price = entry_price + SL_POINTS  # SL is above entry for shorts

            # Calculate VWAP slope at entry
            vwap_slope_entry = calculate_vwap_slope_at_bar(df, idx, VWAP_SLOPE_DEGREE_WINDOW)

            open_position = {
                'direction': 'SELL',
                'entry_time': bar['timestamp'],
                'entry_price': entry_price,
                'entry_vwap': bar['vwap_fast'],
                'tp_price': tp_price,
                'sl_price': sl_price,
                'vwap_slope_entry': vwap_slope_entry
            }

# Close any remaining open position at end of day
if open_position is not None:
    last_bar = df.iloc[-1]
    direction = open_position['direction']
    entry_price = open_position['entry_price']
    exit_price = last_bar['close']

    # Calculate P&L based on direction
    if direction == 'BUY':
        pnl = exit_price - entry_price
    else:  # SELL
        pnl = entry_price - exit_price

    pnl_usd = pnl * POINT_VALUE

    # Calculate time in market (in minutes)
    time_in_market = (last_bar['timestamp'] - open_position['entry_time']).total_seconds() / 60.0

    # Calculate VWAP slope at exit (using last bar's index)
    last_bar_idx = df.index[-1]
    vwap_slope_exit = calculate_vwap_slope_at_bar(df, last_bar_idx, VWAP_SLOPE_DEGREE_WINDOW)

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
        'exit_reason': 'eod_exit',
        'pnl': pnl,
        'pnl_usd': pnl_usd,
        'time_in_market': time_in_market,
        'vwap_slope_entry': open_position['vwap_slope_entry'],
        'vwap_slope_exit': vwap_slope_exit
    })

# ============================================================================
# SAVE RESULTS
# ============================================================================
if len(trades) > 0:
    df_trades = pd.DataFrame(trades)

    # Add sequential trade ID (starting from 1)
    df_trades.insert(0, 'trade_id', range(1, len(df_trades) + 1))

    # Add day of week column (1=Monday, 7=Sunday)
    df_trades.insert(1, 'day_of_week', day_of_week)

    # Save to CSV
    df_trades.to_csv(OUTPUT_FILE, index=False, sep=';', decimal=',')

    print(f"\n[OK] Strategy completed: {len(trades)} trades executed")
    print(f"[OK] Trades saved to: {OUTPUT_FILE}")

    # Statistics
    profit_trades = df_trades[df_trades['exit_reason'] == 'tp_exit']
    stop_trades = df_trades[df_trades['exit_reason'] == 'sl_exit']
    slope_exit_trades = df_trades[df_trades['exit_reason'] == 'slope_exit']
    eod_trades = df_trades[df_trades['exit_reason'] == 'eod_exit']

    total_pnl = df_trades['pnl'].sum()
    total_pnl_usd = df_trades['pnl_usd'].sum()

    # Formatted Test Results summary (compact table-style)
    total_trades = len(df_trades)
    profit_count = len(profit_trades)
    stop_count = len(stop_trades)
    slope_exit_count = len(slope_exit_trades)
    eod_count = len(eod_trades)
    denom = profit_count + stop_count + slope_exit_count
    win_rate = (profit_count / denom * 100) if denom > 0 else 0.0

    avg_points = total_pnl / total_trades if total_trades > 0 else 0.0
    avg_usd = total_pnl_usd / total_trades if total_trades > 0 else 0.0

    # Breakdown by direction
    buy_trades = df_trades[df_trades['direction'] == 'BUY']
    sell_trades = df_trades[df_trades['direction'] == 'SELL']
    buy_pnl_usd = buy_trades['pnl_usd'].sum() if len(buy_trades) > 0 else 0.0
    sell_pnl_usd = sell_trades['pnl_usd'].sum() if len(sell_trades) > 0 else 0.0

    print("\n" + "Test Results (" + DATE + "):" )
    print("Total trades: {:d}".format(total_trades))
    print("Exit breakdown: {} TP / {} SL / {} Slope / {} EOD".format(profit_count, stop_count, slope_exit_count, eod_count))
    print("Win rate: {0:.1f}% ({1} profits / {2} stops+slope)".format(win_rate, profit_count, stop_count + slope_exit_count))
    print("Total P&L: {0:+.0f} points (${1:,.0f})".format(total_pnl, total_pnl_usd))
    print("Average per trade: {0:+.2f} points (${1:,.2f})".format(avg_points, avg_usd))
    print("BUY trades: {:d} (${:,.0f})".format(len(buy_trades), buy_pnl_usd))
    print("SELL trades: {:d} (${:,.0f})".format(len(sell_trades), sell_pnl_usd))

    print("\nThe strategy is ready to use")

    # Generate an HTML summary file and open it automatically
    try:
        import webbrowser
        from datetime import timedelta

        # Prepare metrics
        df_trades_sorted = df_trades.sort_values('entry_time').copy()
        start_period = df_trades_sorted['entry_time'].min()
        end_period = df_trades_sorted['exit_time'].max()
        exposure_days = (end_period.date() - start_period.date()).days + 1
        trades_per_day = total_trades / exposure_days if exposure_days > 0 else 0

        # Durations
        durations = (pd.to_datetime(df_trades_sorted['exit_time']) - pd.to_datetime(df_trades_sorted['entry_time'])).dt.total_seconds()
        avg_duration_min = durations.mean() / 60 if len(durations) > 0 else 0
        median_duration_min = durations.median() / 60 if len(durations) > 0 else 0

        # Performance metrics
        median_profit_usd = df_trades['pnl_usd'].median()
        std_profit_usd = df_trades['pnl_usd'].std()
        gross_profit = df_trades[df_trades['pnl'] > 0]['pnl_usd'].sum()
        gross_loss = df_trades[df_trades['pnl'] < 0]['pnl_usd'].sum()
        profit_factor = (gross_profit / abs(gross_loss)) if gross_loss != 0 else float('inf')

        # Win/Loss
        winners = profit_count
        losers = stop_count + slope_exit_count
        avg_winner = df_trades[df_trades['pnl'] > 0]['pnl_usd'].mean() if winners > 0 else 0
        avg_loser = df_trades[df_trades['pnl'] < 0]['pnl_usd'].mean() if losers > 0 else 0
        largest_winner = df_trades['pnl_usd'].max()
        largest_loser = df_trades['pnl_usd'].min()

        # Overall ratio calculation (for Winners/Losers count)
        overall_ratio = avg_winner / abs(avg_loser) if avg_loser != 0 else 0
        overall_ratio_str = f"1:{int(round(overall_ratio))}" if overall_ratio > 0 else "N/A"

        # Avg Winner/Loser ratio calculation
        avg_ratio = avg_winner / abs(avg_loser) if avg_loser != 0 else 0
        avg_ratio_str = f"1:{avg_ratio:.2f}" if avg_loser != 0 else "N/A"

        # Risk metrics - max drawdown from cumulative pnl
        cum_pnl = df_trades_sorted['pnl_usd'].cumsum()
        running_max = cum_pnl.cummax()
        drawdown = cum_pnl - running_max
        max_drawdown = drawdown.min() if not drawdown.empty else 0

        # Additional risk ratios: Sharpe (per-trade), Sortino, Ulcer Index
        try:
            import numpy as np
            mean_return = df_trades['pnl_usd'].mean()
            std_return = df_trades['pnl_usd'].std()

            # Sharpe Ratio: avoid division by zero
            if std_return and not np.isnan(std_return) and std_return > 0.01:
                sharpe_ratio = mean_return / std_return
            else:
                sharpe_ratio = 0.0

            # Sortino Ratio: only use downside volatility
            downside = df_trades[df_trades['pnl_usd'] < 0]['pnl_usd']
            if len(downside) > 0:
                downside_std = downside.std()
                # Avoid division by zero or very small values
                if downside_std and not np.isnan(downside_std) and downside_std > 0.01:
                    sortino_ratio = mean_return / downside_std
                else:
                    sortino_ratio = 0.0
            else:
                # No losing trades - set to 0 instead of inf
                sortino_ratio = 0.0

            # Ulcer Index: use % drawdowns from running max of cumulative P&L
            dd_pct = (running_max - cum_pnl) / running_max.replace(0, np.nan)
            dd_pct = dd_pct.fillna(0)
            ulcer_index = np.sqrt((dd_pct ** 2).mean()) * 100
        except Exception:
            sharpe_ratio = 0.0
            sortino_ratio = 0.0
            ulcer_index = 0.0

        # Build cumulative P&L chart (Plotly)
        try:
            import plotly.graph_objects as go
            import plotly.io as pio

            x_vals = pd.to_datetime(df_trades_sorted['exit_time']).astype(str).tolist()
            y_vals = cum_pnl.tolist()
            chart_color = 'green' if len(y_vals) > 0 and y_vals[-1] >= 0 else 'red'
            fill_color = 'rgba(0,200,0,0.15)' if chart_color == 'green' else 'rgba(200,0,0,0.15)'

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', line=dict(color=chart_color, width=2), fill='tozeroy', fillcolor=fill_color, name='Cumulative P&L'))
            fig.update_layout(margin=dict(l=20,r=20,t=10,b=20), height=270, showlegend=False, template='plotly_white')

            # Make this chart HTML self-contained by inlining plotly.js so the summary file opens reliably offline
            chart_div = pio.to_html(fig, include_plotlyjs=True, full_html=False)
        except Exception as e:
            chart_div = f"<div class='alert alert-warning'>Failed to generate chart: {e}</div>"

        # Calculate LONG/SHORT breakdown
        long_trades = df_trades[df_trades['direction'] == 'BUY']
        short_trades = df_trades[df_trades['direction'] == 'SELL']

        # LONG stats
        long_total = len(long_trades)
        long_winners = len(long_trades[long_trades['exit_reason'] == 'profit'])
        long_losers = len(long_trades[long_trades['exit_reason'] == 'stop'])
        long_win_rate = (long_winners / (long_winners + long_losers) * 100) if (long_winners + long_losers) > 0 else 0
        long_pnl = long_trades['pnl_usd'].sum()
        long_avg = long_trades['pnl_usd'].mean() if long_total > 0 else 0

        # LONG ratio calculation
        long_avg_winner = long_trades[long_trades['pnl_usd'] > 0]['pnl_usd'].mean() if long_winners > 0 else 0
        long_avg_loser = long_trades[long_trades['pnl_usd'] < 0]['pnl_usd'].mean() if long_losers > 0 else 0
        long_ratio = long_avg_winner / abs(long_avg_loser) if long_avg_loser != 0 else 0
        long_ratio_str = f"1:{int(round(long_ratio))}" if long_ratio > 0 else "N/A"

        # SHORT stats
        short_total = len(short_trades)
        short_winners = len(short_trades[short_trades['exit_reason'] == 'profit'])
        short_losers = len(short_trades[short_trades['exit_reason'] == 'stop'])
        short_win_rate = (short_winners / (short_winners + short_losers) * 100) if (short_winners + short_losers) > 0 else 0
        short_pnl = short_trades['pnl_usd'].sum()
        short_avg = short_trades['pnl_usd'].mean() if short_total > 0 else 0

        # SHORT ratio calculation
        short_avg_winner = short_trades[short_trades['pnl_usd'] > 0]['pnl_usd'].mean() if short_winners > 0 else 0
        short_avg_loser = short_trades[short_trades['pnl_usd'] < 0]['pnl_usd'].mean() if short_losers > 0 else 0
        short_ratio = short_avg_winner / abs(short_avg_loser) if short_avg_loser != 0 else 0
        short_ratio_str = f"1:{int(round(short_ratio))}" if short_ratio > 0 else "N/A"

        # Build HTML (Bootstrap 4 CDN)
        html = f"""
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
            <title>Strategy Summary - {DATE} ({day_name})</title>
            <style>
                body {{ padding: 16px; background: #f7f7f7; font-family: Arial, Helvetica, sans-serif; }}
                .card {{ margin-bottom: 8px; border-radius: 6px; }}
                .card .value {{ font-weight: 700; font-size: 0.95rem; }}
                .compact .card-body p {{ margin-bottom: 6px; font-size: 0.88rem; }}
                .compact .card-header {{ padding: .35rem .65rem; font-size: .88rem; }}
                .small-muted {{ font-size: .9rem; color: #555; margin-bottom: 6px; }}
            </style>
        </head>
        <body>
        <div class="container">
            <h3 class="text-center" style="font-size:1.25rem; margin-bottom:4px;">STRATEGY VWAP MOMENTUM</h3>
            <p class="text-center small-muted mb-2" style="margin-bottom:4px;"><strong>{DATE}</strong> ({day_name}, DoW={day_of_week})</p>
            <p class="text-center small-muted mb-2" style="margin-bottom:4px;"><strong>TP:</strong> {TP_POINTS} pts &nbsp;|&nbsp; <strong>SL:</strong> {SL_POINTS} pts &nbsp;|&nbsp; <strong>Hours:</strong> {START_TRADING_HOUR} - {END_TRADING_HOUR}</p>

            <div class="row compact">
                <div class="col-md-6">
                    <div class="card compact">
                        <div class="card-header bg-primary text-white">GENERAL</div>
                        <div class="card-body">
                            <p>Total Trades: <span class="value">{total_trades}</span></p>
                            <p>Periodo: <span class="value">{start_period} - {end_period}</span></p>
                            <p>Exposure Days: <span class="value">{exposure_days}</span></p>
                            <p>Trades per Day: <span class="value">{trades_per_day:.2f}</span></p>
                            <p>Avg Duration: <span class="value">{avg_duration_min:.2f} min</span></p>
                            <p>Median Duration: <span class="value">{median_duration_min:.2f} min</span></p>
                        </div>
                    </div>
                </div>

                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-info text-white">PERFORMANCE</div>
                        <div class="card-body">
                            <p>Total Profit: <span class="value">${total_pnl_usd:,.2f}</span></p>
                            <p>Avg Profit: <span class="value">${(total_pnl_usd/total_trades if total_trades>0 else 0):,.2f}</span></p>
                            <p>Median Profit: <span class="value">${median_profit_usd:,.2f}</span></p>
                            <p>Std Profit: <span class="value">${std_profit_usd:,.2f}</span></p>
                            <p>Profit Factor: <span class="value">{profit_factor:.2f}</span></p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-success text-white">WIN/LOSS</div>
                        <div class="card-body">
                            <p>Win Rate: <span class="value">{win_rate:.1f}%</span></p>
                            <p>Winners / Losers: <span class="value">{winners} / {losers}</span> (Ratio: {overall_ratio_str})</p>
                            <p>Gross Profit: <span class="value">${gross_profit:,.2f}</span></p>
                            <p>Gross Loss: <span class="value">${gross_loss:,.2f}</span></p>
                            <p>Avg Winner: <span class="value">${avg_winner:,.2f}</span></p>
                            <p>Avg Loser: <span class="value">${avg_loser:,.2f}</span></p>
                            <p>Avg Winner / Avg Loser: <span class="value">(Ratio: {avg_ratio_str})</span></p>
                            <p>Largest Winner: <span class="value">${largest_winner:,.2f}</span></p>
                            <p>Largest Loser: <span class="value">${largest_loser:,.2f}</span></p>
                        </div>
                    </div>
                </div>

                <div class="col-md-6">
                    <div class="card compact">
                        <div class="card-header bg-danger text-white">RISK METRICS</div>
                        <div class="card-body">
                            <p>Max Drawdown: <span class="value">${max_drawdown:,.2f}</span></p>
                            <p>Sharpe Ratio: <span class="value">{sharpe_ratio:.2f}</span></p>
                            <p>Sortino Ratio: <span class="value">{sortino_ratio:.2f}</span></p>
                            <p>Ulcer Index: <span class="value">{ulcer_index:.2f}</span></p>
                        </div>
                    </div>

                    <div class="card compact mt-2">
                        <div class="card-header bg-warning text-dark">EXIT REASONS</div>
                        <div class="card-body">
                            <p>TARGET exits: <span class="value">{profit_count} ({(profit_count/total_trades*100 if total_trades>0 else 0):.1f}%)</span></p>
                            <p>STOP exits: <span class="value">{stop_count} ({(stop_count/total_trades*100 if total_trades>0 else 0):.1f}%)</span></p>
                            <p>EOD exits: <span class="value">{eod_count} ({(eod_count/total_trades*100 if total_trades>0 else 0):.1f}%)</span></p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-2 compact">
                <div class="col-md-6">
                    <div class="card compact">
                        <div class="card-header" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white;">LONG ENTRIES (BUY)</div>
                        <div class="card-body">
                            <p>Total LONG: <span class="value">{long_total}</span></p>
                            <p>Win Rate: <span class="value">{long_win_rate:.1f}%</span></p>
                            <p>Winners / Losers: <span class="value">{long_winners} / {long_losers}</span> (Ratio: {long_ratio_str})</p>
                            <p>Total P&L: <span class="value" style="color: {'green' if long_pnl >= 0 else 'red'}">${long_pnl:,.2f}</span></p>
                            <p>Avg P&L: <span class="value" style="color: {'green' if long_avg >= 0 else 'red'}">${long_avg:,.2f}</span></p>
                        </div>
                    </div>
                </div>

                <div class="col-md-6">
                    <div class="card compact">
                        <div class="card-header" style="background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); color: white;">SHORT ENTRIES (SELL)</div>
                        <div class="card-body">
                            <p>Total SHORT: <span class="value">{short_total}</span></p>
                            <p>Win Rate: <span class="value">{short_win_rate:.1f}%</span></p>
                            <p>Winners / Losers: <span class="value">{short_winners} / {short_losers}</span> (Ratio: {short_ratio_str})</p>
                            <p>Total P&L: <span class="value" style="color: {'green' if short_pnl >= 0 else 'red'}">${short_pnl:,.2f}</span></p>
                            <p>Avg P&L: <span class="value" style="color: {'green' if short_avg >= 0 else 'red'}">${short_avg:,.2f}</span></p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-3 compact">
                <div class="col-12">
                    <div class="card compact" id="cum-pnl">
                        <div class="card-header bg-secondary text-white">CUMULATIVE P&amp;L</div>
                        <div class="card-body">{chart_div}</div>
                    </div>
                </div>
            </div>

        </div>
        <script>try{{document.getElementById('cum-pnl').scrollIntoView({{behavior:'smooth',block:'center'}});}}catch(e){{}}</script>
        </body>
        </html>
        """

        # Save HTML (self-contained: inlines plotly.js so it opens reliably)
        summary_path = TRADING_DIR / f"summary_vwap_momentum_{DATE}.html"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"[INFO] Summary HTML saved to: {summary_path}")

    except Exception as e:
        print(f"[WARN] Failed to generate HTML summary: {e}")

else:
    print("\n[WARN] No trades executed")

print("\n" + "="*80)
print("[SUCCESS] Strategy execution completed!")
print("="*80)

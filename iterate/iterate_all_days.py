"""
Iterate through all available days in data folder and consolidate trading results
Creates:
- all_days_tracking_{first_date}-{last_date}.csv (consolidated trades)
- all_days_summary_{first_date}-{last_date}.html (consolidated summary)
"""

import pandas as pd
from pathlib import Path
import re
from datetime import datetime
import sys
import plotly.graph_objects as go
import plotly.io as pio

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    DATA_DIR, OUTPUTS_DIR, ENABLE_VWAP_MOMENTUM_STRATEGY,
    USE_ALL_DAYS_AVAILABLE, ALL_DAYS_SEGMENT_START, ALL_DAYS_SEGMENT_END,
    SHOW_CHART_DURING_ITERATION,
    VWAP_MOMENTUM_START_HOUR, VWAP_MOMENTUM_END_HOUR,
    VWAP_MOMENTUM_TP_POINTS, VWAP_MOMENTUM_SL_POINTS
)

# ============================================================================
# STEP 1: SCAN DATA FOLDER FOR AVAILABLE DATES
# ============================================================================
print("\n" + "="*80)
print("ITERATION SCRIPT - SCANNING AVAILABLE DATES")
print("="*80 + "\n")

# Find all CSV files matching pattern time_and_sales_nq_YYYYMMDD.csv
csv_files = list(DATA_DIR.glob("time_and_sales_nq_*.csv"))
print(f"[INFO] Found {len(csv_files)} CSV files in data folder")

if len(csv_files) == 0:
    print("[ERROR] No data files found")
    sys.exit(1)

# Extract dates from filenames using regex
date_pattern = re.compile(r"time_and_sales_nq_(\d{8})\.csv")
available_dates = []

for csv_file in csv_files:
    match = date_pattern.search(csv_file.name)
    if match:
        date_str = match.group(1)
        available_dates.append(date_str)

# Sort dates chronologically
available_dates.sort()

print(f"[INFO] Extracted {len(available_dates)} dates")
print(f"[INFO] Full date range: {available_dates[0]} to {available_dates[-1]}")

# Apply segment filter if needed
if USE_ALL_DAYS_AVAILABLE:
    print(f"[INFO] USE_ALL_DAYS_AVAILABLE = True - processing all available dates")
else:
    print(f"[INFO] USE_ALL_DAYS_AVAILABLE = False - applying segment filter")
    print(f"[INFO] Requested range: {ALL_DAYS_SEGMENT_START} to {ALL_DAYS_SEGMENT_END}")

    # Filter dates within the requested range
    filtered_dates = [
        date for date in available_dates
        if ALL_DAYS_SEGMENT_START <= date <= ALL_DAYS_SEGMENT_END
    ]

    if len(filtered_dates) == 0:
        print(f"[ERROR] No dates found in specified segment range")
        print(f"[INFO] Available dates range from {available_dates[0]} to {available_dates[-1]}")
        sys.exit(1)

    # Update available_dates with filtered list
    available_dates = filtered_dates

    print(f"[INFO] Filtered to {len(available_dates)} dates")
    print(f"[INFO] Actual segment range: {available_dates[0]} to {available_dates[-1]}")

    # Show if requested range was adjusted
    if available_dates[0] != ALL_DAYS_SEGMENT_START:
        print(f"[INFO] Start date adjusted from {ALL_DAYS_SEGMENT_START} to {available_dates[0]} (first available)")
    if available_dates[-1] != ALL_DAYS_SEGMENT_END:
        print(f"[INFO] End date adjusted from {ALL_DAYS_SEGMENT_END} to {available_dates[-1]} (last available)")

print(f"[INFO] Dates to process: {', '.join(available_dates[:5])}{'...' if len(available_dates) > 5 else ''}\n")

# ============================================================================
# STEP 2: ITERATE THROUGH EACH DATE AND RUN STRATEGY
# ============================================================================
print("="*80)
print("PROCESSING DATES")
print("="*80 + "\n")

# We'll collect all trades here
all_trades = []
trading_dir = OUTPUTS_DIR / "trading"

for i, date_str in enumerate(available_dates, 1):
    print(f"\n[{i}/{len(available_dates)}] Processing date: {date_str}")
    print("-"*80)

    # Run strategy directly using subprocess with modified config
    try:
        import subprocess
        import sys

        # Check if strategy is enabled
        if not ENABLE_VWAP_MOMENTUM_STRATEGY:
            print(f"[INFO] Strategy disabled, no trades to collect")
            continue

        # Prepare the script path
        project_root = Path(__file__).parent.parent
        strategy_script = project_root / "strat_vwap_momentum.py"

        if not strategy_script.exists():
            print(f"[ERROR] Strategy file not found: {strategy_script}")
            continue

        # Temporarily modify config.py to set the date
        config_file = project_root / "config.py"

        # Read current config
        with open(config_file, 'r', encoding='utf-8') as f:
            config_content = f.read()

        # Backup original DATE line
        import re
        original_date_match = re.search(r'^DATE = "(\d{8})"', config_content, re.MULTILINE)
        if not original_date_match:
            print(f"[ERROR] Could not find DATE in config.py")
            continue

        original_date = original_date_match.group(1)

        # Replace DATE with current iteration date
        modified_content = re.sub(
            r'^DATE = "\d{8}"',
            f'DATE = "{date_str}"',
            config_content,
            count=1,
            flags=re.MULTILINE
        )

        # Keep SHOW_SUMMARY_DURING_ITERATION and SHOW_CHART_DURING_ITERATION as configured
        # These control whether to open browser windows and generate charts for each day
        # No modification needed - respect user configuration

        # Write modified config
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        try:
            # Execute the strategy
            result = subprocess.run(
                [sys.executable, str(strategy_script)],
                capture_output=True,
                text=True,
                cwd=str(project_root)
            )

            if result.returncode == 0:
                print(f"[OK] Strategy executed for {date_str}")

                # Load the tracking record CSV for this date
                csv_file = trading_dir / f"tracking_record_vwap_momentum_{date_str}.csv"

                if csv_file.exists():
                    df_day = pd.read_csv(csv_file, sep=';', decimal=',')
                    if len(df_day) > 0:
                        print(f"[OK] Collected {len(df_day)} trades from {date_str}")
                        all_trades.append(df_day)
                    else:
                        print(f"[INFO] No trades generated for {date_str}")
                else:
                    print(f"[INFO] No tracking record found for {date_str}")

                # Generate chart if enabled
                if SHOW_CHART_DURING_ITERATION:
                    plot_script = project_root / "plot_day.py"
                    if plot_script.exists():
                        print(f"[INFO] Generating chart for {date_str}...")
                        plot_result = subprocess.run(
                            [sys.executable, str(plot_script)],
                            capture_output=True,
                            text=True,
                            cwd=str(project_root)
                        )
                        if plot_result.returncode == 0:
                            print(f"[OK] Chart generated for {date_str}")
                        else:
                            print(f"[WARN] Chart generation failed for {date_str}")
                    else:
                        print(f"[WARN] plot_day.py not found, skipping chart generation")
            else:
                print(f"[WARN] Strategy returned code {result.returncode} for {date_str}")
                if result.stderr:
                    print(f"[ERROR] {result.stderr[:200]}")

        finally:
            # Restore original config
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)

    except Exception as e:
        print(f"[ERROR] Exception processing {date_str}: {e}")
        import traceback
        traceback.print_exc()
        continue

print("\n" + "="*80)
print("CONSOLIDATION")
print("="*80 + "\n")

# ============================================================================
# STEP 3: CONSOLIDATE ALL TRADES INTO SINGLE CSV
# ============================================================================
if len(all_trades) == 0:
    print("[WARN] No trades collected from any date")
    print("[INFO] Exiting without creating consolidated files\n")
    sys.exit(0)

# Concatenate all trade dataframes
df_all = pd.concat(all_trades, ignore_index=True)

# Create output filenames with all_days_ prefix
first_date = available_dates[0]
last_date = available_dates[-1]
consolidated_csv = trading_dir / f"all_days_tracking_{first_date}-{last_date}.csv"

# Save consolidated CSV
df_all.to_csv(consolidated_csv, index=False, sep=';', decimal=',')
print(f"[OK] Consolidated CSV saved: {consolidated_csv}")
print(f"[INFO] Total trades: {len(df_all)}")

# ============================================================================
# STEP 4: GENERATE CONSOLIDATED HTML SUMMARY
# ============================================================================
print("\n" + "-"*80)
print("GENERATING CONSOLIDATED SUMMARY")
print("-"*80 + "\n")

# Calculate statistics
total_trades = len(df_all)

# Filter by actual P&L instead of exit_reason (more accurate for all exit types)
winning_trades = df_all[df_all['pnl_usd'] > 0]
losing_trades = df_all[df_all['pnl_usd'] < 0]
breakeven_trades = df_all[df_all['pnl_usd'] == 0]

total_pnl = df_all['pnl'].sum()
total_pnl_usd = df_all['pnl_usd'].sum()
avg_pnl_usd = total_pnl_usd / total_trades if total_trades > 0 else 0

profit_count = len(winning_trades)
stop_count = len(losing_trades)
breakeven_count = len(breakeven_trades)

# Win rate based on actual wins vs losses (excluding breakeven)
denom = profit_count + stop_count
win_rate = (profit_count / denom * 100) if denom > 0 else 0.0

# Use winning_trades and losing_trades for consistency
profit_trades = winning_trades
stop_trades = losing_trades

# Calculate BUY vs SELL statistics
buy_trades = df_all[df_all['direction'] == 'BUY']
sell_trades = df_all[df_all['direction'] == 'SELL']
buy_pnl_usd = buy_trades['pnl_usd'].sum() if len(buy_trades) > 0 else 0.0
sell_pnl_usd = sell_trades['pnl_usd'].sum() if len(sell_trades) > 0 else 0.0

# Calculate Winner/Loser ratio (count)
if profit_count > 0 and stop_count > 0:
    if profit_count >= stop_count:
        ratio_str = f"{profit_count // stop_count}:1"
    else:
        ratio_str = f"1:{stop_count // profit_count}"
else:
    ratio_str = "N/A"

# Calculate Avg Winner / Avg Loser ratio
avg_winner = profit_trades['pnl_usd'].mean() if profit_count > 0 else 0.0
avg_loser = abs(stop_trades['pnl_usd'].mean()) if stop_count > 0 else 0.0

if avg_loser > 0:
    avg_win_loss_ratio = avg_winner / avg_loser
    avg_ratio_str = f"1:{avg_win_loss_ratio:.2f}"
else:
    avg_ratio_str = "N/A"

# WIN/LOSS Analysis
gross_profit = profit_trades['pnl_usd'].sum() if len(profit_trades) > 0 else 0.0
gross_loss = stop_trades['pnl_usd'].sum() if len(stop_trades) > 0 else 0.0
avg_winner = profit_trades['pnl_usd'].mean() if len(profit_trades) > 0 else 0.0
avg_loser = stop_trades['pnl_usd'].mean() if len(stop_trades) > 0 else 0.0
largest_winner = profit_trades['pnl_usd'].max() if len(profit_trades) > 0 else 0.0
largest_loser = stop_trades['pnl_usd'].min() if len(stop_trades) > 0 else 0.0

# Calculate avg ratio
avg_ratio = avg_winner / abs(avg_loser) if avg_loser != 0 else 0
avg_ratio_str = f"1:{int(round(avg_ratio))}" if avg_loser != 0 else "N/A"

# Calculate GLOBAL risk metrics
import numpy as np

# Sort trades by time for cumulative calculations
df_sorted_global = df_all.sort_values(['entry_time'])
cum_pnl_global = df_sorted_global['pnl_usd'].cumsum()
running_max_global = cum_pnl_global.cummax()
drawdown_global = cum_pnl_global - running_max_global
max_dd_global = drawdown_global.min() if not drawdown_global.empty else 0

# Sharpe Ratio
mean_return_global = df_all['pnl_usd'].mean()
std_return_global = df_all['pnl_usd'].std()
if std_return_global and not np.isnan(std_return_global) and std_return_global > 0.01:
    sharpe_global = mean_return_global / std_return_global
else:
    sharpe_global = 0.0

# Sortino Ratio
downside_global = df_all[df_all['pnl_usd'] < 0]['pnl_usd']
if len(downside_global) > 0:
    downside_std_global = downside_global.std()
    if downside_std_global and not np.isnan(downside_std_global) and downside_std_global > 0.01:
        sortino_global = mean_return_global / downside_std_global
    else:
        sortino_global = 0.0
else:
    sortino_global = 0.0

# Ulcer Index
dd_pct_global = (running_max_global - cum_pnl_global) / running_max_global.replace(0, np.nan)
dd_pct_global = dd_pct_global.fillna(0)
ulcer_global = np.sqrt((dd_pct_global ** 2).mean()) * 100

# Print summary to console
print(f"Total trades: {total_trades}")
print(f"Win rate: {win_rate:.1f}% ({profit_count} profits / {stop_count} stops)")
print(f"Total P&L: {total_pnl:+.0f} points (${total_pnl_usd:,.0f})")
print(f"Average per trade: ${avg_pnl_usd:+.2f}")
print(f"BUY trades: {len(buy_trades)} (${buy_pnl_usd:,.0f})")
print(f"SELL trades: {len(sell_trades)} (${sell_pnl_usd:,.0f})")

# ============================================================================
# GENERATE CHARTS FOR HTML SUMMARY
# ============================================================================
# 1. EQUITY CURVE (Cumulative P&L)
equity_chart_div = ""
try:
    # Sort trades by time to calculate cumulative P&L
    df_sorted = df_all.sort_values(['entry_time'])
    cum_pnl = df_sorted['pnl_usd'].cumsum()

    # Extract dates for hover info
    trade_dates = pd.to_datetime(df_sorted['entry_time']).dt.strftime('%Y-%m-%d %H:%M').values

    # Create equity curve chart
    fig_equity = go.Figure()

    # Determine color based on final P&L
    line_color = '#28a745' if cum_pnl.iloc[-1] >= 0 else '#dc3545'
    fill_color = 'rgba(40, 167, 69, 0.3)' if cum_pnl.iloc[-1] >= 0 else 'rgba(220, 53, 69, 0.3)'

    fig_equity.add_trace(go.Scatter(
        x=list(range(1, len(cum_pnl) + 1)),
        y=cum_pnl.values,
        mode='lines',
        line=dict(color=line_color, width=2),
        fill='tozeroy',
        fillcolor=fill_color,
        name='Cumulative P&L',
        customdata=trade_dates,
        hovertemplate='Date: %{customdata}<br>Trade #%{x}<br>P&L: $%{y:,.2f}<extra></extra>'
    ))

    fig_equity.update_layout(
        title='Equity Curve - Cumulative P&L',
        xaxis_title='Trade Number',
        yaxis_title='Cumulative P&L (USD)',
        margin=dict(l=50, r=50, t=50, b=50),
        height=400,
        template='plotly_white',
        hovermode='x unified'
    )

    equity_chart_div = pio.to_html(fig_equity, include_plotlyjs=True, full_html=False)
except Exception as e:
    equity_chart_div = f"<div class='alert alert-warning'>Failed to generate equity curve: {e}</div>"

# 2. DAILY PROFIT HISTOGRAM
daily_histogram_div = ""
try:
    # Extract date from entry_time and group by date
    df_all['date'] = pd.to_datetime(df_all['entry_time']).dt.date
    daily_pnl = df_all.groupby('date')['pnl_usd'].sum().reset_index()
    daily_pnl = daily_pnl.sort_values('date')

    # Create colors based on profit/loss
    colors = ['#28a745' if pnl >= 0 else '#dc3545' for pnl in daily_pnl['pnl_usd']]

    fig_daily = go.Figure()

    fig_daily.add_trace(go.Bar(
        x=daily_pnl['date'].astype(str),
        y=daily_pnl['pnl_usd'],
        marker_color=colors,
        name='Daily P&L',
        hovertemplate='Date: %{x}<br>P&L: $%{y:,.2f}<extra></extra>'
    ))

    fig_daily.update_layout(
        title='Daily Profit/Loss Distribution',
        xaxis_title='Date',
        yaxis_title='P&L (USD)',
        margin=dict(l=50, r=50, t=50, b=100),
        height=400,
        template='plotly_white',
        xaxis=dict(tickangle=-45),
        showlegend=False
    )

    # Add zero line
    fig_daily.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    daily_histogram_div = pio.to_html(fig_daily, include_plotlyjs=False, full_html=False)
except Exception as e:
    daily_histogram_div = f"<div class='alert alert-warning'>Failed to generate daily histogram: {e}</div>"

# ============================================================================
# GENERATE HTML SUMMARY
# ============================================================================
# Build daily summary table
daily_summary_html = ""
try:
    # Group by date to get daily statistics
    df_all['date'] = pd.to_datetime(df_all['entry_time']).dt.date
    daily_stats = []

    for date in sorted(df_all['date'].unique()):
        day_trades = df_all[df_all['date'] == date]

        # Calculate daily statistics
        total_trades_day = len(day_trades)
        profits_day = len(day_trades[day_trades['exit_reason'] == 'profit'])
        stops_day = len(day_trades[day_trades['exit_reason'] == 'stop'])
        win_rate_day = (profits_day / (profits_day + stops_day) * 100) if (profits_day + stops_day) > 0 else 0

        total_pnl_day = day_trades['pnl_usd'].sum()
        avg_pnl_day = day_trades['pnl_usd'].mean()

        buy_trades_day = len(day_trades[day_trades['direction'] == 'BUY'])
        sell_trades_day = len(day_trades[day_trades['direction'] == 'SELL'])

        buy_pnl_day = day_trades[day_trades['direction'] == 'BUY']['pnl_usd'].sum() if buy_trades_day > 0 else 0
        sell_pnl_day = day_trades[day_trades['direction'] == 'SELL']['pnl_usd'].sum() if sell_trades_day > 0 else 0

        # Get day of week
        day_of_week = day_trades.iloc[0]['day_of_week']
        day_names_map = {1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat', 7: 'Sun'}
        day_name_short = day_names_map.get(day_of_week, '')

        # Calculate risk metrics for the day
        import numpy as np

        # Max Drawdown
        day_trades_sorted = day_trades.sort_values(['entry_time'])
        cum_pnl_day = day_trades_sorted['pnl_usd'].cumsum()
        running_max_day = cum_pnl_day.cummax()
        drawdown_day = cum_pnl_day - running_max_day
        max_dd_day = drawdown_day.min() if not drawdown_day.empty else 0

        # Sharpe Ratio
        mean_return_day = day_trades['pnl_usd'].mean()
        std_return_day = day_trades['pnl_usd'].std()
        if std_return_day and not np.isnan(std_return_day) and std_return_day > 0.01:
            sharpe_day = mean_return_day / std_return_day
        else:
            sharpe_day = 0.0

        # Sortino Ratio
        downside_day = day_trades[day_trades['pnl_usd'] < 0]['pnl_usd']
        if len(downside_day) > 0:
            downside_std_day = downside_day.std()
            if downside_std_day and not np.isnan(downside_std_day) and downside_std_day > 0.01:
                sortino_day = mean_return_day / downside_std_day
            else:
                sortino_day = 0.0
        else:
            sortino_day = 0.0

        # Ulcer Index
        dd_pct_day = (running_max_day - cum_pnl_day) / running_max_day.replace(0, np.nan)
        dd_pct_day = dd_pct_day.fillna(0)
        ulcer_day = np.sqrt((dd_pct_day ** 2).mean()) * 100

        daily_stats.append({
            'date': date,
            'day_name': day_name_short,
            'total_trades': total_trades_day,
            'profits': profits_day,
            'stops': stops_day,
            'win_rate': win_rate_day,
            'total_pnl': total_pnl_day,
            'avg_pnl': avg_pnl_day,
            'buy_trades': buy_trades_day,
            'sell_trades': sell_trades_day,
            'buy_pnl': buy_pnl_day,
            'sell_pnl': sell_pnl_day,
            'max_dd': max_dd_day,
            'sharpe': sharpe_day,
            'sortino': sortino_day,
            'ulcer': ulcer_day
        })

    # Build HTML table rows
    for stat in daily_stats:
        pnl_color = 'green' if stat['total_pnl'] >= 0 else 'red'
        row_class = 'profit' if stat['total_pnl'] >= 0 else 'loss'

        daily_summary_html += f"""
        <tr class="{row_class}">
            <td>{stat['date']}</td>
            <td>{stat['day_name']}</td>
            <td>{stat['total_trades']}</td>
            <td>{stat['profits']}/{stat['stops']}</td>
            <td>{stat['win_rate']:.1f}%</td>
            <td style="color: {pnl_color}; font-weight: bold;">${stat['total_pnl']:,.2f}</td>
            <td>${stat['avg_pnl']:,.2f}</td>
            <td>{stat['buy_trades']} (${stat['buy_pnl']:,.0f})</td>
            <td>{stat['sell_trades']} (${stat['sell_pnl']:,.0f})</td>
            <td>${stat['max_dd']:,.0f}</td>
            <td>{stat['sharpe']:.2f}</td>
            <td>{stat['sortino']:.2f}</td>
            <td>{stat['ulcer']:.1f}%</td>
        </tr>
        """
except Exception as e:
    daily_summary_html = f"<tr><td colspan='13'>Error generating daily summary: {e}</td></tr>"

# Build trades table HTML
trades_html = ""
for idx, row in df_all.iterrows():
    pnl_class = "profit" if row['exit_reason'] == 'profit' else "loss"

    trades_html += f"""
        <tr class="{pnl_class}">
            <td>{idx + 1}</td>
            <td>{row['trade_id']}</td>
            <td>{row['day_of_week']}</td>
            <td>{row['entry_time']}</td>
            <td>{row['exit_time']}</td>
            <td>{row['direction']}</td>
            <td>{row['entry_price']:.2f}</td>
            <td>{row['exit_price']:.2f}</td>
            <td>{row['entry_vwap']:.2f}</td>
            <td>{row['exit_vwap']:.2f}</td>
            <td>{row['tp_price']:.2f}</td>
            <td>{row['sl_price']:.2f}</td>
            <td>{row['exit_reason']}</td>
            <td>{row['pnl']:+.2f}</td>
            <td>${row['pnl_usd']:,.2f}</td>
            <td>{row['time_in_market']:.1f}</td>
            <td>{row['vwap_slope_entry']:.4f}</td>
            <td>{row['vwap_slope_exit']:.4f}</td>
        </tr>
    """

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>VWAP Momentum Strategy - Iteration Summary ({first_date} to {last_date})</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .summary-card .value {{
            font-size: 28px;
            font-weight: bold;
            margin: 0;
        }}
        .win-loss {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }}
        .win-loss p {{
            margin: 8px 0;
            color: #2c3e50;
        }}
        .win-loss .value {{
            font-weight: bold;
            color: #34495e;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .profit {{
            background-color: #d4edda;
        }}
        .loss {{
            background-color: #f8d7da;
        }}
        .stats {{
            margin-top: 30px;
            padding: 20px;
            background-color: #ecf0f1;
            border-radius: 8px;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #95a5a6;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>VWAP Momentum Strategy - Iteration Summary</h1>
        <p><strong>Date Range:</strong> {first_date} to {last_date}</p>
        <p><strong>Trading Hours:</strong> {VWAP_MOMENTUM_START_HOUR} to {VWAP_MOMENTUM_END_HOUR}</p>
        <p><strong>TP/SL:</strong> {VWAP_MOMENTUM_TP_POINTS:.0f} / {VWAP_MOMENTUM_SL_POINTS:.0f} points</p>
        <p><strong>Total Days Processed:</strong> {len(available_dates)}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

        <div class="summary">
            <div class="summary-card">
                <h3>Total Trades</h3>
                <p class="value">{total_trades}</p>
            </div>
            <div class="summary-card">
                <h3>Win Rate</h3>
                <p class="value">{win_rate:.1f}%</p>
            </div>
            <div class="summary-card">
                <h3>Total P&L</h3>
                <p class="value">${total_pnl_usd:,.0f}</p>
            </div>
            <div class="summary-card">
                <h3>Avg P&L per Trade</h3>
                <p class="value">${avg_pnl_usd:+,.2f}</p>
            </div>
        </div>

        <h2>Performance Breakdown</h2>
        <div class="win-loss">
            <p>Win Rate: <span class="value">{win_rate:.1f}%</span></p>
            <p>Winners / Losers: <span class="value">{profit_count} / {stop_count} (Ratio: {ratio_str})</span></p>
            <p>Gross Profit: <span class="value">${gross_profit:,.2f}</span></p>
            <p>Gross Loss: <span class="value">${gross_loss:,.2f}</span></p>
            <p>Avg Winner: <span class="value">${avg_winner:,.2f}</span></p>
            <p>Avg Loser: <span class="value">${avg_loser:,.2f}</span></p>
            <p>Avg Winner / Avg Loser: <span class="value">(Ratio: {avg_ratio_str})</span></p>
            <p>Largest Winner: <span class="value">${largest_winner:,.2f}</span></p>
            <p>Largest Loser: <span class="value">${largest_loser:,.2f}</span></p>
        </div>

        <h2>Trade Direction Analysis</h2>
        <div class="win-loss">
            <p>BUY Trades: <span class="value">{len(buy_trades)} (${buy_pnl_usd:,.2f})</span></p>
            <p>SELL Trades: <span class="value">{len(sell_trades)} (${sell_pnl_usd:,.2f})</span></p>
        </div>

        <h2>Risk Metrics</h2>
        <div class="win-loss">
            <p>Max Drawdown: <span class="value">${max_dd_global:,.2f}</span></p>
            <p>Sharpe Ratio: <span class="value">{sharpe_global:.2f}</span></p>
            <p>Sortino Ratio: <span class="value">{sortino_global:.2f}</span></p>
            <p>Ulcer Index: <span class="value">{ulcer_global:.1f}%</span></p>
        </div>

        <h2>Equity Curve</h2>
        <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            {equity_chart_div}
        </div>

        <h2>Daily Profit/Loss</h2>
        <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            {daily_histogram_div}
        </div>

        <h2>Daily Summary</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Day</th>
                    <th>Trades</th>
                    <th>W/L</th>
                    <th>Win Rate</th>
                    <th>Total P&L</th>
                    <th>Avg P&L</th>
                    <th>BUY (P&L)</th>
                    <th>SELL (P&L)</th>
                    <th>Max DD</th>
                    <th>Sharpe</th>
                    <th>Sortino</th>
                    <th>Ulcer</th>
                </tr>
            </thead>
            <tbody>
                {daily_summary_html}
            </tbody>
        </table>

        <h2>All Trades Detail</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Trade ID</th>
                    <th>Day</th>
                    <th>Entry Time</th>
                    <th>Exit Time</th>
                    <th>Direction</th>
                    <th>Entry Price</th>
                    <th>Exit Price</th>
                    <th>Entry VWAP</th>
                    <th>Exit VWAP</th>
                    <th>TP Price</th>
                    <th>SL Price</th>
                    <th>Exit Reason</th>
                    <th>P&L (pts)</th>
                    <th>P&L (USD)</th>
                    <th>Time (min)</th>
                    <th>VWAP Slope Entry</th>
                    <th>VWAP Slope Exit</th>
                </tr>
            </thead>
            <tbody>
                {trades_html}
            </tbody>
        </table>

        <div class="footer">
            <p>Generated by VWAP Momentum Strategy Iteration Script</p>
            <p>Date Range: {first_date} to {last_date} | Total Days: {len(available_dates)} | Total Trades: {total_trades}</p>
        </div>
    </div>
</body>
</html>
"""

# Save HTML summary
html_file = trading_dir / f"all_days_summary_{first_date}-{last_date}.html"
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"[OK] Consolidated HTML saved: {html_file}")

# Open consolidated summary in browser
print(f"[INFO] Opening consolidated summary in browser...")
try:
    import webbrowser
    uri = html_file.resolve().as_uri()
    webbrowser.open(uri)
    print(f"[INFO] Consolidated summary opened in browser: {uri}")
except Exception as e:
    print(f"[WARN] Could not open summary in browser: {e}")
    print(f"[INFO] Please open the summary manually at: {html_file.resolve()}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("ITERATION COMPLETE")
print("="*80)
print(f"\nProcessed {len(available_dates)} dates from {first_date} to {last_date}")
print(f"Total trades collected: {total_trades}")
print(f"Win rate: {win_rate:.1f}%")
print(f"Total P&L: ${total_pnl_usd:,.0f}")
print(f"\nOutput files:")
print(f"  - CSV: {consolidated_csv.name}")
print(f"  - HTML: {html_file.name}")
print("="*80 + "\n")

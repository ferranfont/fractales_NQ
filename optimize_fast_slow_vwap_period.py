"""
Optimize VWAP Fast and Slow Periods
Tests different combinations of VWAP periods to maximize:
- Total P&L
- Sortino Ratio
- Sharpe Ratio
- Win Rate

Generates comprehensive analysis and recommendations.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime
import json
from itertools import product

# Import configuration
from config import (
    DATA_DIR, OUTPUTS_DIR,
    VWAP_MOMENTUM_TP_POINTS, VWAP_MOMENTUM_SL_POINTS,
    ALL_DAYS_SEGMENT_START, ALL_DAYS_SEGMENT_END,
    VWAP_MOMENTUM_STRAT_START_HOUR, VWAP_MOMENTUM_STRAT_END_HOUR,
    PRICE_EJECTION_TRIGGER, POINT_VALUE
)

# Import data loading functions
from find_fractals import load_nq_tick_data, aggregate_ticks_to_ohlc

# ============================================================================
# CONFIGURATION
# ============================================================================
OPTIMIZATION_DIR = OUTPUTS_DIR / "optimization"
OPTIMIZATION_DIR.mkdir(parents=True, exist_ok=True)

# VWAP period ranges to test (simplified for faster execution)
VWAP_FAST_RANGE = [20, 30, 40, 50, 60, 80, 100, 120, 144]
VWAP_SLOW_RANGE = [100, 144, 180, 200, 240, 280]

# Filters for valid combinations
MIN_FAST_SLOW_DIFFERENCE = 40  # Fast must be at least 40 periods less than Slow

print("\n" + "="*80)
print("VWAP PERIOD OPTIMIZATION - Fast and Slow Periods")
print("="*80)
print(f"\nDate Range: {ALL_DAYS_SEGMENT_START} to {ALL_DAYS_SEGMENT_END}")
print(f"TP/SL: {VWAP_MOMENTUM_TP_POINTS}/{VWAP_MOMENTUM_SL_POINTS} points")
print(f"Price Ejection Trigger: {PRICE_EJECTION_TRIGGER*100:.2f}%")
print(f"\nTesting VWAP_FAST: {VWAP_FAST_RANGE}")
print(f"Testing VWAP_SLOW: {VWAP_SLOW_RANGE}")
print(f"Minimum Fast-Slow difference: {MIN_FAST_SLOW_DIFFERENCE} periods")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_vwap(df, period):
    """Calculate VWAP for given period"""
    df = df.copy()
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_volume'] = df['typical_price'] * df['volume']

    df['cum_tp_volume'] = df['tp_volume'].rolling(window=period, min_periods=1).sum()
    df['cum_volume'] = df['volume'].rolling(window=period, min_periods=1).sum()

    df['vwap'] = df['cum_tp_volume'] / df['cum_volume']
    return df['vwap']


def detect_price_ejection(price, vwap, threshold):
    """Detect if price is ejected from VWAP"""
    if pd.isna(price) or pd.isna(vwap) or vwap == 0:
        return False

    distance_pct = abs(price - vwap) / vwap
    return distance_pct >= threshold


def run_backtest(vwap_fast, vwap_slow, date_range):
    """
    Run backtest for given VWAP periods across all dates
    Returns performance metrics
    """
    all_trades = []

    # Get all CSV files in date range
    data_files = sorted(DATA_DIR.glob("time_and_sales_nq_*.csv"))

    for data_file in data_files:
        # Extract date from filename (time_and_sales_nq_20251001.csv -> 20251001)
        date_str = data_file.stem.split('_')[-1]

        # Check if date is in range
        if date_str < ALL_DAYS_SEGMENT_START or date_str > ALL_DAYS_SEGMENT_END:
            continue

        try:
            # Load tick data
            df_ticks = load_nq_tick_data(date_str)
            if df_ticks is None:
                continue

            # Aggregate to 1-minute OHLC bars
            df = aggregate_ticks_to_ohlc(df_ticks, timeframe='1min')
            if df is None or len(df) == 0:
                continue

            # Calculate VWAPs
            df['vwap_fast'] = calculate_vwap(df, vwap_fast)
            df['vwap_slow'] = calculate_vwap(df, vwap_slow)

            # Run simple strategy
            trades = simple_strategy(df, vwap_fast, vwap_slow, date_str)
            all_trades.extend(trades)

        except Exception as e:
            continue

    # Calculate metrics
    if len(all_trades) == 0:
        return None

    metrics = calculate_metrics(all_trades)
    return metrics


def simple_strategy(df, vwap_fast, vwap_slow, date_str):
    """
    Simple VWAP momentum strategy
    Entry: Price ejection from VWAP Fast
    Exit: TP/SL
    """
    trades = []
    open_position = None

    start_time = pd.to_datetime(VWAP_MOMENTUM_STRAT_START_HOUR).time()
    end_time = pd.to_datetime(VWAP_MOMENTUM_STRAT_END_HOUR).time()

    for idx, bar in df.iterrows():
        current_time = bar['timestamp'].time()

        # Skip if outside trading hours
        if current_time < start_time or current_time > end_time:
            continue

        # Check exit conditions first
        if open_position is not None:
            direction = open_position['direction']
            entry_price = open_position['entry_price']
            tp_price = open_position['tp_price']
            sl_price = open_position['sl_price']

            exit_reason = None
            exit_price = None

            if direction == 'BUY':
                # Check TP
                if bar['high'] >= tp_price:
                    exit_reason = 'tp_exit'
                    exit_price = tp_price
                # Check SL
                elif bar['low'] <= sl_price:
                    exit_reason = 'sl_exit'
                    exit_price = sl_price
            else:  # SELL
                # Check TP
                if bar['low'] <= tp_price:
                    exit_reason = 'tp_exit'
                    exit_price = tp_price
                # Check SL
                elif bar['high'] >= sl_price:
                    exit_reason = 'sl_exit'
                    exit_price = sl_price

            # Close position
            if exit_reason:
                if direction == 'BUY':
                    pnl_points = exit_price - entry_price
                else:
                    pnl_points = entry_price - exit_price

                pnl_usd = pnl_points * POINT_VALUE

                trades.append({
                    'date': date_str,
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl_points': pnl_points,
                    'pnl_usd': pnl_usd,
                    'exit_reason': exit_reason
                })

                open_position = None

        # Check entry conditions (only if no open position)
        if open_position is None:
            # BUY signal: Price ejection above VWAP Fast
            if detect_price_ejection(bar['close'], bar['vwap_fast'], PRICE_EJECTION_TRIGGER):
                if bar['close'] > bar['vwap_fast']:
                    entry_price = bar['close']
                    tp_price = entry_price + VWAP_MOMENTUM_TP_POINTS
                    sl_price = entry_price - VWAP_MOMENTUM_SL_POINTS

                    open_position = {
                        'direction': 'BUY',
                        'entry_price': entry_price,
                        'tp_price': tp_price,
                        'sl_price': sl_price
                    }

            # SELL signal: Price ejection below VWAP Fast
            elif detect_price_ejection(bar['close'], bar['vwap_fast'], PRICE_EJECTION_TRIGGER):
                if bar['close'] < bar['vwap_fast']:
                    entry_price = bar['close']
                    tp_price = entry_price - VWAP_MOMENTUM_TP_POINTS
                    sl_price = entry_price + VWAP_MOMENTUM_SL_POINTS

                    open_position = {
                        'direction': 'SELL',
                        'entry_price': entry_price,
                        'tp_price': tp_price,
                        'sl_price': sl_price
                    }

    # Close any remaining position at EOD
    if open_position is not None:
        direction = open_position['direction']
        entry_price = open_position['entry_price']
        exit_price = df.iloc[-1]['close']

        if direction == 'BUY':
            pnl_points = exit_price - entry_price
        else:
            pnl_points = entry_price - exit_price

        pnl_usd = pnl_points * POINT_VALUE

        trades.append({
            'date': date_str,
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_points': pnl_points,
            'pnl_usd': pnl_usd,
            'exit_reason': 'eod_exit'
        })

    return trades


def calculate_metrics(trades):
    """Calculate performance metrics from trades"""
    df = pd.DataFrame(trades)

    total_trades = len(df)
    winners = df[df['pnl_usd'] > 0]
    losers = df[df['pnl_usd'] <= 0]

    total_pnl = df['pnl_usd'].sum()
    win_rate = len(winners) / total_trades * 100 if total_trades > 0 else 0

    avg_winner = winners['pnl_usd'].mean() if len(winners) > 0 else 0
    avg_loser = losers['pnl_usd'].mean() if len(losers) > 0 else 0

    # Calculate Sharpe Ratio
    returns = df['pnl_usd']
    sharpe = returns.mean() / returns.std() if returns.std() > 0 else 0

    # Calculate Sortino Ratio (downside deviation)
    negative_returns = returns[returns < 0]
    downside_std = negative_returns.std() if len(negative_returns) > 0 else 0
    sortino = returns.mean() / downside_std if downside_std > 0 else 0

    # Max Drawdown
    cumulative = returns.cumsum()
    running_max = cumulative.cummax()
    drawdown = cumulative - running_max
    max_drawdown = drawdown.min()

    return {
        'total_trades': total_trades,
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'winners': len(winners),
        'losers': len(losers),
        'avg_winner': avg_winner,
        'avg_loser': avg_loser,
        'sharpe': sharpe,
        'sortino': sortino,
        'max_drawdown': max_drawdown,
        'avg_pnl_per_trade': total_pnl / total_trades if total_trades > 0 else 0
    }


# ============================================================================
# OPTIMIZATION
# ============================================================================

print("\n" + "="*80)
print("RUNNING OPTIMIZATION...")
print("="*80)

results = []
total_combinations = 0

# Generate valid combinations
valid_combinations = []
for fast in VWAP_FAST_RANGE:
    for slow in VWAP_SLOW_RANGE:
        if slow - fast >= MIN_FAST_SLOW_DIFFERENCE:
            valid_combinations.append((fast, slow))

total_combinations = len(valid_combinations)
print(f"\nTesting {total_combinations} valid VWAP period combinations...")

for idx, (fast, slow) in enumerate(valid_combinations, 1):
    print(f"\r[{idx}/{total_combinations}] Testing VWAP_FAST={fast}, VWAP_SLOW={slow}...", end='', flush=True)

    metrics = run_backtest(fast, slow, (ALL_DAYS_SEGMENT_START, ALL_DAYS_SEGMENT_END))

    if metrics:
        print(f" -> {metrics['total_trades']} trades, P&L=${metrics['total_pnl']:,.0f}")
        results.append({
            'vwap_fast': fast,
            'vwap_slow': slow,
            'fast_slow_diff': slow - fast,
            **metrics
        })
    else:
        print(f" -> No trades")

print("\n\nOptimization complete!")

# ============================================================================
# ANALYZE RESULTS
# ============================================================================

if len(results) == 0:
    print("\n[ERROR] No results generated. Check data files and date range.")
    sys.exit(1)

results_df = pd.DataFrame(results)

# Sort by different criteria
best_pnl = results_df.nlargest(10, 'total_pnl')
best_sortino = results_df.nlargest(10, 'sortino')
best_sharpe = results_df.nlargest(10, 'sharpe')
best_combined = results_df.assign(
    combined_score=lambda x: (
        x['total_pnl'] / x['total_pnl'].max() * 0.4 +
        x['sortino'] / x['sortino'].max() * 0.3 +
        x['sharpe'] / x['sharpe'].max() * 0.2 +
        x['win_rate'] / x['win_rate'].max() * 0.1
    )
).nlargest(10, 'combined_score')

# ============================================================================
# SAVE RESULTS
# ============================================================================

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Save full results to CSV
csv_file = OPTIMIZATION_DIR / f"vwap_period_optimization_{timestamp}.csv"
results_df.to_csv(csv_file, index=False)
print(f"\n✓ Full results saved to: {csv_file}")

# Save top performers to JSON
top_results = {
    'optimization_date': timestamp,
    'date_range': f"{ALL_DAYS_SEGMENT_START} to {ALL_DAYS_SEGMENT_END}",
    'total_combinations_tested': len(results),
    'best_by_pnl': best_pnl.to_dict('records')[:5],
    'best_by_sortino': best_sortino.to_dict('records')[:5],
    'best_by_sharpe': best_sharpe.to_dict('records')[:5],
    'best_combined': best_combined.to_dict('records')[:5],
    'recommended': best_combined.iloc[0].to_dict()
}

json_file = OPTIMIZATION_DIR / f"vwap_period_optimization_{timestamp}.json"
with open(json_file, 'w') as f:
    json.dump(top_results, f, indent=2)
print(f"✓ Top results saved to: {json_file}")

# ============================================================================
# GENERATE HTML REPORT
# ============================================================================

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>VWAP Period Optimization Results</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 10px; }}
        .summary {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .highlight {{ background: #e8f5e9; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 5px solid #4caf50; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th {{ background: #3498db; color: white; padding: 12px; text-align: left; font-weight: 600; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .positive {{ color: #27ae60; font-weight: bold; }}
        .negative {{ color: #e74c3c; font-weight: bold; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .metric-label {{ color: #7f8c8d; font-size: 0.9em; }}
        .metric-value {{ font-size: 1.3em; font-weight: bold; color: #2c3e50; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 VWAP Period Optimization Results</h1>

        <div class="summary">
            <strong>Optimization Date:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
            <strong>Date Range:</strong> {ALL_DAYS_SEGMENT_START} to {ALL_DAYS_SEGMENT_END}<br>
            <strong>TP/SL:</strong> {VWAP_MOMENTUM_TP_POINTS}/{VWAP_MOMENTUM_SL_POINTS} points<br>
            <strong>Price Ejection Trigger:</strong> {PRICE_EJECTION_TRIGGER*100:.2f}%<br>
            <strong>Combinations Tested:</strong> {len(results)}<br>
        </div>

        <div class="highlight">
            <h2>🏆 RECOMMENDED CONFIGURATION</h2>
            <div class="metric">
                <div class="metric-label">VWAP Fast</div>
                <div class="metric-value">{int(best_combined.iloc[0]['vwap_fast'])}</div>
            </div>
            <div class="metric">
                <div class="metric-label">VWAP Slow</div>
                <div class="metric-value">{int(best_combined.iloc[0]['vwap_slow'])}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total P&L</div>
                <div class="metric-value positive">${best_combined.iloc[0]['total_pnl']:,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Sortino Ratio</div>
                <div class="metric-value">{best_combined.iloc[0]['sortino']:.3f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Sharpe Ratio</div>
                <div class="metric-value">{best_combined.iloc[0]['sharpe']:.3f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Win Rate</div>
                <div class="metric-value">{best_combined.iloc[0]['win_rate']:.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Trades</div>
                <div class="metric-value">{int(best_combined.iloc[0]['total_trades'])}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Winner</div>
                <div class="metric-value positive">${best_combined.iloc[0]['avg_winner']:,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Loser</div>
                <div class="metric-value negative">${best_combined.iloc[0]['avg_loser']:,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Max Drawdown</div>
                <div class="metric-value negative">${best_combined.iloc[0]['max_drawdown']:,.2f}</div>
            </div>
        </div>

        <h2>📊 Top 10 by Total P&L</h2>
        <table>
            <tr>
                <th>Rank</th>
                <th>VWAP Fast</th>
                <th>VWAP Slow</th>
                <th>Diff</th>
                <th>Total P&L</th>
                <th>Trades</th>
                <th>Win Rate</th>
                <th>Sortino</th>
                <th>Sharpe</th>
                <th>Avg P&L/Trade</th>
            </tr>
"""

for idx, row in best_pnl.iterrows():
    pnl_class = 'positive' if row['total_pnl'] > 0 else 'negative'
    html_content += f"""
            <tr>
                <td>{best_pnl.index.get_loc(idx) + 1}</td>
                <td>{int(row['vwap_fast'])}</td>
                <td>{int(row['vwap_slow'])}</td>
                <td>{int(row['fast_slow_diff'])}</td>
                <td class="{pnl_class}">${row['total_pnl']:,.2f}</td>
                <td>{int(row['total_trades'])}</td>
                <td>{row['win_rate']:.1f}%</td>
                <td><strong>{row['sortino']:.3f}</strong></td>
                <td><strong>{row['sharpe']:.3f}</strong></td>
                <td class="{pnl_class}">${row['avg_pnl_per_trade']:,.2f}</td>
            </tr>
"""

html_content += """
        </table>

        <h2>📈 Top 10 by Sortino Ratio</h2>
        <table>
            <tr>
                <th>Rank</th>
                <th>VWAP Fast</th>
                <th>VWAP Slow</th>
                <th>Diff</th>
                <th>Sortino</th>
                <th>Sharpe</th>
                <th>Total P&L</th>
                <th>Win Rate</th>
                <th>Trades</th>
            </tr>
"""

for idx, row in best_sortino.iterrows():
    pnl_class = 'positive' if row['total_pnl'] > 0 else 'negative'
    html_content += f"""
            <tr>
                <td>{best_sortino.index.get_loc(idx) + 1}</td>
                <td>{int(row['vwap_fast'])}</td>
                <td>{int(row['vwap_slow'])}</td>
                <td>{int(row['fast_slow_diff'])}</td>
                <td><strong>{row['sortino']:.3f}</strong></td>
                <td><strong>{row['sharpe']:.3f}</strong></td>
                <td class="{pnl_class}">${row['total_pnl']:,.2f}</td>
                <td>{row['win_rate']:.1f}%</td>
                <td>{int(row['total_trades'])}</td>
            </tr>
"""

html_content += """
        </table>

        <h2>⚡ Top 10 by Combined Score</h2>
        <p style="color: #7f8c8d; font-style: italic;">
            Combined Score = 40% P&L + 30% Sortino + 20% Sharpe + 10% Win Rate
        </p>
        <table>
            <tr>
                <th>Rank</th>
                <th>VWAP Fast</th>
                <th>VWAP Slow</th>
                <th>Diff</th>
                <th>Score</th>
                <th>Total P&L</th>
                <th>Sortino</th>
                <th>Sharpe</th>
                <th>Win Rate</th>
                <th>Trades</th>
            </tr>
"""

for idx, row in best_combined.iterrows():
    pnl_class = 'positive' if row['total_pnl'] > 0 else 'negative'
    html_content += f"""
            <tr>
                <td>{best_combined.index.get_loc(idx) + 1}</td>
                <td>{int(row['vwap_fast'])}</td>
                <td>{int(row['vwap_slow'])}</td>
                <td>{int(row['fast_slow_diff'])}</td>
                <td><strong>{row['combined_score']:.3f}</strong></td>
                <td class="{pnl_class}">${row['total_pnl']:,.2f}</td>
                <td><strong>{row['sortino']:.3f}</strong></td>
                <td><strong>{row['sharpe']:.3f}</strong></td>
                <td>{row['win_rate']:.1f}%</td>
                <td>{int(row['total_trades'])}</td>
            </tr>
"""

html_content += """
        </table>
    </div>
</body>
</html>
"""

html_file = OPTIMIZATION_DIR / f"vwap_period_optimization_{timestamp}.html"
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html_content)
print(f"✓ HTML report saved to: {html_file}")

# ============================================================================
# PRINT CONCLUSIONS TO TERMINAL
# ============================================================================

print("\n" + "="*80)
print("OPTIMIZATION CONCLUSIONS")
print("="*80)

recommended = best_combined.iloc[0]

print(f"\n🏆 RECOMMENDED CONFIGURATION:")
print(f"   VWAP_FAST = {int(recommended['vwap_fast'])}")
print(f"   VWAP_SLOW = {int(recommended['vwap_slow'])}")
print(f"   Period Difference = {int(recommended['fast_slow_diff'])}")

print(f"\n📊 PERFORMANCE METRICS:")
print(f"   Total P&L: ${recommended['total_pnl']:,.2f}")
print(f"   Total Trades: {int(recommended['total_trades'])}")
print(f"   Win Rate: {recommended['win_rate']:.1f}%")
print(f"   Avg P&L per Trade: ${recommended['avg_pnl_per_trade']:,.2f}")
print(f"   Sortino Ratio: {recommended['sortino']:.2f}")
print(f"   Sharpe Ratio: {recommended['sharpe']:.2f}")
print(f"   Max Drawdown: ${recommended['max_drawdown']:,.2f}")

print(f"\n💡 KEY INSIGHTS:")

# Best for P&L
best_pnl_config = best_pnl.iloc[0]
print(f"   • Highest P&L: FAST={int(best_pnl_config['vwap_fast'])}, SLOW={int(best_pnl_config['vwap_slow'])} → ${best_pnl_config['total_pnl']:,.2f}")

# Best for Sortino
best_sortino_config = best_sortino.iloc[0]
print(f"   • Best Sortino: FAST={int(best_sortino_config['vwap_fast'])}, SLOW={int(best_sortino_config['vwap_slow'])} → {best_sortino_config['sortino']:.2f}")

# Best for Sharpe
best_sharpe_config = best_sharpe.iloc[0]
print(f"   • Best Sharpe: FAST={int(best_sharpe_config['vwap_fast'])}, SLOW={int(best_sharpe_config['vwap_slow'])} → {best_sharpe_config['sharpe']:.2f}")

# Analysis of period differences
avg_diff_top10 = best_combined.head(10)['fast_slow_diff'].mean()
print(f"   • Average period difference in top 10: {avg_diff_top10:.0f} periods")

# Trade count analysis
avg_trades_top10 = best_combined.head(10)['total_trades'].mean()
print(f"   • Average trade count in top 10: {avg_trades_top10:.0f} trades")

print(f"\n📈 COMPARATIVE ANALYSIS:")
current_fast = 50  # Default current setting
current_slow = 200  # Default current setting

current_result = results_df[(results_df['vwap_fast'] == current_fast) & (results_df['vwap_slow'] == current_slow)]
if len(current_result) > 0:
    current = current_result.iloc[0]
    pnl_improvement = ((recommended['total_pnl'] - current['total_pnl']) / abs(current['total_pnl']) * 100) if current['total_pnl'] != 0 else 0
    sortino_improvement = ((recommended['sortino'] - current['sortino']) / abs(current['sortino']) * 100) if current['sortino'] != 0 else 0

    print(f"   Current (FAST={current_fast}, SLOW={current_slow}):")
    print(f"      P&L: ${current['total_pnl']:,.2f}, Sortino: {current['sortino']:.2f}, Sharpe: {current['sharpe']:.2f}")
    print(f"   Recommended (FAST={int(recommended['vwap_fast'])}, SLOW={int(recommended['vwap_slow'])}):")
    print(f"      P&L: ${recommended['total_pnl']:,.2f} ({pnl_improvement:+.1f}%)")
    print(f"      Sortino: {recommended['sortino']:.2f} ({sortino_improvement:+.1f}%)")

print("\n" + "="*80)
print("✓ Optimization complete! Review the HTML report for detailed analysis.")
print("="*80)
print()

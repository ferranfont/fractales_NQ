"""
VWAP Momentum Strategy - Multi-Day Parameter Optimization
Finds the optimal TP (Take Profit) and SL (Stop Loss) combination across all available days
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime, time
import webbrowser
import re

# Import configuration
from config import (
    VWAP_MOMENTUM_MAX_POSITIONS,
    VWAP_MOMENTUM_START_HOUR, VWAP_MOMENTUM_END_HOUR,
    VWAP_FAST, PRICE_EJECTION_TRIGGER, VWAP_SLOPE_DEGREE_WINDOW,
    DATA_DIR, OUTPUTS_DIR
)
from calculate_vwap import calculate_vwap

POINT_VALUE = 20.0  # USD value per point for NQ futures


def get_available_dates():
    """Scan data directory for available NQ data files"""
    # Try both naming patterns: time_and_sales_nq_*.csv and nq_*.csv
    data_files_pattern1 = sorted(DATA_DIR.glob("time_and_sales_nq_*.csv"))
    data_files_pattern2 = sorted(DATA_DIR.glob("nq_*.csv"))

    data_files = data_files_pattern1 + data_files_pattern2

    dates = []
    for file in data_files:
        # Extract date from filename: time_and_sales_nq_20251021.csv -> 20251021
        # or nq_20251021.csv -> 20251021
        match = re.search(r'(?:time_and_sales_)?nq_(\d{8})\.csv', file.name)
        if match:
            dates.append(match.group(1))

    return sorted(set(dates))  # Remove duplicates and sort


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
    bar_position = df.index.get_loc(bar_idx)

    if bar_position < window - 1:
        return 0.0

    start_pos = bar_position - window + 1
    end_pos = bar_position + 1

    vwap_window = df.iloc[start_pos:end_pos]['vwap_fast'].values

    if pd.isna(vwap_window).any():
        return 0.0

    slope = (vwap_window[-1] - vwap_window[0]) / (window - 1)

    return slope


def backtest_single_day(
    date: str,
    tp_points: float,
    sl_points: float,
    max_positions: int = 1,
    start_hour: str = "00:00:00",
    end_hour: str = "22:00:00"
):
    """
    Run backtest for a single day with specified parameters

    Args:
        date: Date in YYYYMMDD format
        tp_points: Take profit in points
        sl_points: Stop loss in points
        max_positions: Maximum number of positions open simultaneously
        start_hour: Start trading hour
        end_hour: End trading hour

    Returns:
        DataFrame with trades, or None if no trades or error
    """
    try:
        # Load data using the same function as the working strategy
        # This will convert tick data to OHLC format automatically
        from find_fractals import load_date_range

        df = load_date_range(date, date)

        if df is None:
            return None

        # The load_date_range function returns OHLC data with 'timestamp' column already
        # No need to rename columns

        # Calculate VWAP
        df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)

        # Calculate price-VWAP distance
        df['price_vwap_distance'] = abs((df['close'] - df['vwap_fast']) / df['vwap_fast'])

        # Detect price ejection signals
        df['price_ejection'] = (df['price_vwap_distance'] > PRICE_EJECTION_TRIGGER) & (df['vwap_fast'].notna())

        # Detect price above/below VWAP
        df['price_above_vwap'] = (df['close'] > df['vwap_fast']).astype(bool)
        df['price_below_vwap'] = (df['close'] < df['vwap_fast']).astype(bool)

        # Entry signals
        df['long_signal'] = df['price_ejection'] & df['price_above_vwap']
        df['short_signal'] = df['price_ejection'] & df['price_below_vwap']

        # Parse trading time range
        start_time = datetime.strptime(start_hour, "%H:%M:%S").time()
        end_time = datetime.strptime(end_hour, "%H:%M:%S").time()

        # Calculate day of week
        date_obj = datetime.strptime(date, "%Y%m%d")
        day_of_week = date_obj.isoweekday()

        # Execute strategy
        trades = []
        open_position = None

        for idx, bar in df.iterrows():
            # Check trading hours
            current_time = bar['timestamp'].time()
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
                    if bar['high'] >= tp_price:
                        exit_reason = 'profit'
                        exit_price = tp_price
                    elif bar['low'] <= sl_price:
                        exit_reason = 'stop'
                        exit_price = sl_price
                else:  # SELL
                    if bar['low'] <= tp_price:
                        exit_reason = 'profit'
                        exit_price = tp_price
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

                    time_in_market = (bar['timestamp'] - open_position['entry_time']).total_seconds() / 60.0
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
                        'vwap_slope_exit': vwap_slope_exit,
                        'day_of_week': day_of_week
                    })

                    open_position = None
                    continue

            # Check for new entry signals (only if no position open)
            if open_position is None and max_positions > 0:
                # LONG signal
                if bar['long_signal']:
                    entry_price = bar['close']
                    tp_price = entry_price + tp_points
                    sl_price = entry_price - sl_points
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

                # SHORT signal
                elif bar['short_signal']:
                    entry_price = bar['close']
                    tp_price = entry_price - tp_points
                    sl_price = entry_price + sl_points
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

        # Close any remaining position at EOD
        if open_position is not None:
            last_bar = df.iloc[-1]
            direction = open_position['direction']
            entry_price = open_position['entry_price']
            exit_price = last_bar['close']

            if direction == 'BUY':
                pnl = exit_price - entry_price
            else:
                pnl = entry_price - exit_price

            pnl_usd = pnl * POINT_VALUE
            time_in_market = (last_bar['timestamp'] - open_position['entry_time']).total_seconds() / 60.0
            vwap_slope_exit = calculate_vwap_slope_at_bar(df, df.index[-1], VWAP_SLOPE_DEGREE_WINDOW)

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
                'pnl_usd': pnl_usd,
                'time_in_market': time_in_market,
                'vwap_slope_entry': open_position['vwap_slope_entry'],
                'vwap_slope_exit': vwap_slope_exit,
                'day_of_week': day_of_week
            })

        if len(trades) > 0:
            return pd.DataFrame(trades)
        else:
            return None

    except Exception as e:
        print(f"[ERROR] Failed to process {date}: {e}")
        return None


def optimize_parameters_multiday(
    dates: list,
    tp_range: list = None,
    sl_range: list = None
):
    """
    Optimize TP and SL parameters across multiple days

    Args:
        dates: List of dates in YYYYMMDD format
        tp_range: List of TP values to test
        sl_range: List of SL values to test

    Returns:
        DataFrame with optimization results
    """
    if tp_range is None:
        tp_range = [25.0, 50.0, 75.0, 100.0, 125.0, 150.0, 200.0]

    if sl_range is None:
        sl_range = [15.0, 25.0, 35.0, 50.0, 75.0, 100.0]

    print("=" * 80)
    print("VWAP MOMENTUM STRATEGY - MULTI-DAY PARAMETER OPTIMIZATION")
    print("=" * 80)
    print(f"Date Range: {dates[0]} -> {dates[-1]}")
    print(f"Total Days: {len(dates)}")
    print(f"TP Range: {tp_range}")
    print(f"SL Range: {sl_range}")
    print(f"Total combinations to test: {len(tp_range) * len(sl_range)}")
    print("=" * 80 + "\n")

    results = []
    total_combinations = len(tp_range) * len(sl_range)
    current_combination = 0

    for tp in tp_range:
        for sl in sl_range:
            current_combination += 1
            rr_ratio = tp / sl if sl > 0 else 0

            print(f"[{current_combination}/{total_combinations}] Testing TP={tp:.0f}, SL={sl:.0f} (R:R = {rr_ratio:.2f})")

            # Collect trades from all days
            all_trades = []
            days_processed = 0

            for date in dates:
                df_trades = backtest_single_day(
                    date,
                    tp_points=tp,
                    sl_points=sl,
                    max_positions=VWAP_MOMENTUM_MAX_POSITIONS,
                    start_hour=VWAP_MOMENTUM_START_HOUR,
                    end_hour=VWAP_MOMENTUM_END_HOUR
                )

                if df_trades is not None and len(df_trades) > 0:
                    df_trades['date'] = date
                    all_trades.append(df_trades)
                    days_processed += 1

            if len(all_trades) == 0:
                print(f"    No trades generated across any days")
                results.append({
                    'tp': tp,
                    'sl': sl,
                    'rr_ratio': rr_ratio,
                    'days_traded': 0,
                    'total_trades': 0,
                    'profit_trades': 0,
                    'stop_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'total_pnl_usd': 0.0,
                    'avg_pnl_usd': 0.0,
                    'max_drawdown': 0.0,
                    'sharpe_ratio': 0.0,
                    'sortino_ratio': 0.0,
                    'profit_factor': 0.0,
                    'avg_trades_per_day': 0.0
                })
                continue

            # Combine all trades
            df_all_trades = pd.concat(all_trades, ignore_index=True)

            # Calculate metrics
            total_trades = len(df_all_trades)
            profit_trades = df_all_trades[df_all_trades['exit_reason'] == 'profit']
            stop_trades = df_all_trades[df_all_trades['exit_reason'] == 'stop']

            profit_count = len(profit_trades)
            stop_count = len(stop_trades)

            total_pnl = df_all_trades['pnl'].sum()
            total_pnl_usd = df_all_trades['pnl_usd'].sum()
            avg_pnl_usd = total_pnl_usd / total_trades if total_trades > 0 else 0

            denom = profit_count + stop_count
            win_rate = (profit_count / denom * 100) if denom > 0 else 0.0

            # Sort by time for cumulative calculations
            df_sorted = df_all_trades.sort_values(['date', 'entry_time'])

            # Max Drawdown
            cum_pnl = df_sorted['pnl_usd'].cumsum()
            running_max = cum_pnl.cummax()
            drawdown = cum_pnl - running_max
            max_drawdown = drawdown.min()

            # Sharpe Ratio
            if len(df_all_trades) > 1:
                returns = df_all_trades['pnl_usd']
                sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
            else:
                sharpe_ratio = 0.0

            # Sortino Ratio
            downside = df_all_trades[df_all_trades['pnl_usd'] < 0]['pnl_usd']
            if len(downside) > 0:
                downside_std = downside.std()
                if downside_std > 0:
                    sortino_ratio = (df_all_trades['pnl_usd'].mean() / downside_std) * np.sqrt(252)
                else:
                    sortino_ratio = 0.0
            else:
                sortino_ratio = 0.0

            # Profit Factor
            gross_profit = profit_trades['pnl_usd'].sum() if len(profit_trades) > 0 else 0
            gross_loss = abs(stop_trades['pnl_usd'].sum()) if len(stop_trades) > 0 else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else (999.99 if gross_profit > 0 else 0)

            # Average trades per day
            avg_trades_per_day = total_trades / days_processed if days_processed > 0 else 0

            print(f"    Days: {days_processed}, Trades: {total_trades}, Win Rate: {win_rate:.1f}%, P&L: ${total_pnl_usd:,.0f}, Sharpe: {sharpe_ratio:.2f}")

            results.append({
                'tp': tp,
                'sl': sl,
                'rr_ratio': rr_ratio,
                'days_traded': days_processed,
                'total_trades': total_trades,
                'profit_trades': profit_count,
                'stop_trades': stop_count,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'total_pnl_usd': total_pnl_usd,
                'avg_pnl_usd': avg_pnl_usd,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'profit_factor': profit_factor if profit_factor < 999 else 999.99,
                'avg_trades_per_day': avg_trades_per_day
            })

    # Convert to DataFrame
    df_results = pd.DataFrame(results)

    # Sort by Sharpe Ratio (more reliable than total P&L)
    df_results = df_results.sort_values('sharpe_ratio', ascending=False).reset_index(drop=True)

    return df_results


def generate_optimization_report(df_results: pd.DataFrame, dates: list):
    """Generate HTML report with optimization results"""

    if df_results is None or len(df_results) == 0:
        print("[ERROR] No results to generate report")
        return None

    # Create output directory
    reports_dir = OUTPUTS_DIR / "optimization"
    reports_dir.mkdir(parents=True, exist_ok=True)

    first_date = dates[0]
    last_date = dates[-1]
    date_str = f"{first_date}_{last_date}"

    report_file = reports_dir / f"vwap_momentum_optimization_{date_str}.html"

    # Get top 10 results
    top_10 = df_results.head(10)

    # Find best by different criteria
    best_sharpe = df_results.loc[df_results['sharpe_ratio'].idxmax()] if df_results['sharpe_ratio'].max() > 0 else None
    best_pnl = df_results.loc[df_results['total_pnl_usd'].idxmax()]
    best_win_rate = df_results.loc[df_results['win_rate'].idxmax()] if df_results['win_rate'].max() > 0 else None
    best_profit_factor = df_results.loc[df_results['profit_factor'].idxmax()] if df_results['profit_factor'].max() > 0 else None

    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>VWAP Momentum - Multi-Day Optimization Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 20px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .header p {{
                margin: 5px 0 0 0;
                opacity: 0.9;
            }}
            .section {{
                background: white;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .section h2 {{
                margin-top: 0;
                color: #667eea;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }}
            .best-params {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }}
            .param-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
            }}
            .param-card h3 {{
                margin: 0 0 10px 0;
                font-size: 14px;
                opacity: 0.9;
            }}
            .param-card .value {{
                font-size: 24px;
                font-weight: bold;
            }}
            .param-card .details {{
                font-size: 12px;
                margin-top: 10px;
                opacity: 0.9;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                font-size: 13px;
            }}
            th, td {{
                padding: 10px;
                text-align: right;
                border-bottom: 1px solid #e0e0e0;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: 600;
                color: #333;
                position: sticky;
                top: 0;
            }}
            tr:hover {{
                background-color: #f8f9fa;
            }}
            .positive {{
                color: #22c55e;
                font-weight: 600;
            }}
            .negative {{
                color: #ef4444;
                font-weight: 600;
            }}
            .rank {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                color: #666;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
            }}
            .info-box {{
                background: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>VWAP Momentum Strategy - Multi-Day Parameter Optimization</h1>
            <p>Period: {first_date} → {last_date}</p>
            <p>Total Days Analyzed: {len(dates)}</p>
            <p>Total Combinations Tested: {len(df_results)}</p>
        </div>

        <div class="section">
            <h2>Recommendation</h2>
            <div class="info-box">
                <strong>Important:</strong> Results are ranked by <strong>Sharpe Ratio</strong>, which measures risk-adjusted returns.
                This is generally more reliable than raw P&L for long-term profitability.
                A higher Sharpe Ratio indicates more consistent returns relative to risk.
            </div>
        </div>
    """

    # Best Parameters Section
    html += """
        <div class="section">
            <h2>Recommended Parameters</h2>
            <div class="best-params">
    """

    if best_sharpe is not None:
        html += f"""
                <div class="param-card">
                    <h3>🏆 BEST SHARPE RATIO (RECOMMENDED)</h3>
                    <div class="value">TP: {best_sharpe['tp']:.0f} / SL: {best_sharpe['sl']:.0f}</div>
                    <div class="details">
                        R:R Ratio: {best_sharpe['rr_ratio']:.2f}<br>
                        Sharpe: {best_sharpe['sharpe_ratio']:.2f}<br>
                        Total P&L: ${best_sharpe['total_pnl_usd']:,.0f}<br>
                        Win Rate: {best_sharpe['win_rate']:.1f}%<br>
                        Trades: {best_sharpe['total_trades']:.0f} ({best_sharpe['avg_trades_per_day']:.1f}/day)
                    </div>
                </div>
        """

    if best_pnl is not None:
        html += f"""
                <div class="param-card">
                    <h3>💰 BEST TOTAL P&L</h3>
                    <div class="value">TP: {best_pnl['tp']:.0f} / SL: {best_pnl['sl']:.0f}</div>
                    <div class="details">
                        Total P&L: ${best_pnl['total_pnl_usd']:,.0f}<br>
                        R:R Ratio: {best_pnl['rr_ratio']:.2f}<br>
                        Win Rate: {best_pnl['win_rate']:.1f}%<br>
                        Sharpe: {best_pnl['sharpe_ratio']:.2f}<br>
                        Trades: {best_pnl['total_trades']:.0f}
                    </div>
                </div>
        """

    if best_win_rate is not None:
        html += f"""
                <div class="param-card">
                    <h3>🎯 BEST WIN RATE</h3>
                    <div class="value">TP: {best_win_rate['tp']:.0f} / SL: {best_win_rate['sl']:.0f}</div>
                    <div class="details">
                        Win Rate: {best_win_rate['win_rate']:.1f}%<br>
                        Total P&L: ${best_win_rate['total_pnl_usd']:,.0f}<br>
                        Sharpe: {best_win_rate['sharpe_ratio']:.2f}<br>
                        Trades: {best_win_rate['total_trades']:.0f}
                    </div>
                </div>
        """

    if best_profit_factor is not None and best_profit_factor['profit_factor'] < 999:
        html += f"""
                <div class="param-card">
                    <h3>📊 BEST PROFIT FACTOR</h3>
                    <div class="value">TP: {best_profit_factor['tp']:.0f} / SL: {best_profit_factor['sl']:.0f}</div>
                    <div class="details">
                        Profit Factor: {best_profit_factor['profit_factor']:.2f}<br>
                        Total P&L: ${best_profit_factor['total_pnl_usd']:,.0f}<br>
                        Win Rate: {best_profit_factor['win_rate']:.1f}%<br>
                        Sharpe: {best_profit_factor['sharpe_ratio']:.2f}
                    </div>
                </div>
        """

    html += """
            </div>
        </div>
    """

    # Top 10 Results Table
    html += """
        <div class="section">
            <h2>Top 10 Combinations (by Sharpe Ratio)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>TP</th>
                        <th>SL</th>
                        <th>R:R</th>
                        <th>Days</th>
                        <th>Trades</th>
                        <th>Avg/Day</th>
                        <th>Win%</th>
                        <th>Total P&L</th>
                        <th>Avg/Trade</th>
                        <th>Sharpe</th>
                        <th>Sortino</th>
                        <th>PF</th>
                        <th>Max DD</th>
                    </tr>
                </thead>
                <tbody>
    """

    for idx, row in top_10.iterrows():
        pnl_class = "positive" if row['total_pnl_usd'] > 0 else "negative"
        pf_display = f"{row['profit_factor']:.2f}" if row['profit_factor'] < 999 else '&infin;'
        html += f"""
                    <tr>
                        <td><span class="rank">#{idx + 1}</span></td>
                        <td>{row['tp']:.0f}</td>
                        <td>{row['sl']:.0f}</td>
                        <td>{row['rr_ratio']:.2f}</td>
                        <td>{row['days_traded']:.0f}</td>
                        <td>{row['total_trades']:.0f}</td>
                        <td>{row['avg_trades_per_day']:.1f}</td>
                        <td>{row['win_rate']:.1f}%</td>
                        <td class="{pnl_class}">${row['total_pnl_usd']:,.0f}</td>
                        <td class="{pnl_class}">${row['avg_pnl_usd']:,.2f}</td>
                        <td><strong>{row['sharpe_ratio']:.2f}</strong></td>
                        <td>{row['sortino_ratio']:.2f}</td>
                        <td>{pf_display}</td>
                        <td class="negative">${row['max_drawdown']:,.0f}</td>
                    </tr>
        """

    html += """
                </tbody>
            </table>
        </div>
    """

    # All Results Table
    html += """
        <div class="section">
            <h2>All Results (sorted by Sharpe Ratio)</h2>
            <div style="max-height: 600px; overflow-y: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>TP</th>
                            <th>SL</th>
                            <th>R:R</th>
                            <th>Days</th>
                            <th>Trades</th>
                            <th>Avg/Day</th>
                            <th>Win%</th>
                            <th>Total P&L</th>
                            <th>Avg/Trade</th>
                            <th>Sharpe</th>
                            <th>Sortino</th>
                            <th>PF</th>
                            <th>Max DD</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for idx, row in df_results.iterrows():
        pnl_class = "positive" if row['total_pnl_usd'] > 0 else "negative"
        pf_display = f"{row['profit_factor']:.2f}" if row['profit_factor'] < 999 else '&infin;'
        html += f"""
                        <tr>
                            <td>{idx + 1}</td>
                            <td>{row['tp']:.0f}</td>
                            <td>{row['sl']:.0f}</td>
                            <td>{row['rr_ratio']:.2f}</td>
                            <td>{row['days_traded']:.0f}</td>
                            <td>{row['total_trades']:.0f}</td>
                            <td>{row['avg_trades_per_day']:.1f}</td>
                            <td>{row['win_rate']:.1f}%</td>
                            <td class="{pnl_class}">${row['total_pnl_usd']:,.0f}</td>
                            <td class="{pnl_class}">${row['avg_pnl_usd']:,.2f}</td>
                            <td><strong>{row['sharpe_ratio']:.2f}</strong></td>
                            <td>{row['sortino_ratio']:.2f}</td>
                            <td>{pf_display}</td>
                            <td class="negative">${row['max_drawdown']:,.0f}</td>
                        </tr>
        """

    html += """
                    </tbody>
                </table>
            </div>
        </div>

        <div class="footer">
            <p>Generated on """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            <p><strong>Metric Definitions:</strong></p>
            <p style="font-size: 12px; margin: 5px 0;">
                <strong>Sharpe Ratio:</strong> Risk-adjusted return (higher is better, >1.0 is good, >2.0 is excellent)<br>
                <strong>Sortino Ratio:</strong> Like Sharpe but only penalizes downside volatility<br>
                <strong>Profit Factor:</strong> Gross profit / Gross loss (>1.5 is good)<br>
                <strong>Max DD:</strong> Maximum drawdown from peak equity
            </p>
        </div>
    </body>
    </html>
    """

    # Write HTML file
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[OK] Optimization report generated: {report_file}")

    # Save CSV
    csv_file = reports_dir / f"vwap_momentum_optimization_{date_str}.csv"
    df_results.to_csv(csv_file, index=False, sep=';', decimal=',')
    print(f"[OK] Results saved to CSV: {csv_file}")

    return report_file


if __name__ == "__main__":
    # Get all available dates
    available_dates = get_available_dates()

    if len(available_dates) == 0:
        print("[ERROR] No data files found in data directory")
        sys.exit(1)

    print(f"[INFO] Found {len(available_dates)} days of data")
    print(f"[INFO] Date range: {available_dates[0]} -> {available_dates[-1]}\n")

    # Run optimization
    df_results = optimize_parameters_multiday(available_dates)

    if df_results is not None and len(df_results) > 0:
        # Generate report
        report_file = generate_optimization_report(df_results, available_dates)

        if report_file and report_file.exists():
            # Open in browser
            try:
                webbrowser.open(report_file.resolve().as_uri())
                print(f"[OK] Opening report in browser...")
            except Exception as e:
                print(f"[WARN] Could not open browser: {e}")

        print("\n" + "=" * 80)
        print("OPTIMIZATION COMPLETE")
        print("=" * 80)

        # Print summary of best parameters
        best_sharpe = df_results.loc[df_results['sharpe_ratio'].idxmax()]
        print(f"\n🏆 RECOMMENDED PARAMETERS (Best Sharpe Ratio):")
        print(f"   TP: {best_sharpe['tp']:.0f} points")
        print(f"   SL: {best_sharpe['sl']:.0f} points")
        print(f"   R:R Ratio: {best_sharpe['rr_ratio']:.2f}")
        print(f"   Sharpe Ratio: {best_sharpe['sharpe_ratio']:.2f}")
        print(f"   Total P&L: ${best_sharpe['total_pnl_usd']:,.0f}")
        print(f"   Win Rate: {best_sharpe['win_rate']:.1f}%")
        print(f"   Total Trades: {best_sharpe['total_trades']:.0f}")
        print(f"   Avg Trades/Day: {best_sharpe['avg_trades_per_day']:.1f}")
        print()
    else:
        print("\n[ERROR] Optimization failed - no results generated")

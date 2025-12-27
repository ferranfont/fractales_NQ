"""
VWAP Momentum Strategy - Trading Hours Optimization
Analiza el rendimiento por hora del día para encontrar las mejores ventanas de trading
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, time
import webbrowser
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import configuration
from config import (
    VWAP_MOMENTUM_TP_POINTS, VWAP_MOMENTUM_SL_POINTS,
    VWAP_MOMENTUM_MAX_POSITIONS,
    VWAP_FAST, PRICE_EJECTION_TRIGGER, VWAP_SLOPE_DEGREE_WINDOW,
    DATA_DIR, OUTPUTS_DIR
)
from find_fractals import load_date_range
from calculate_vwap import calculate_vwap

POINT_VALUE = 20.0  # USD value per point for NQ futures


def get_available_dates():
    """Scan data directory for available NQ data files"""
    data_files_pattern1 = sorted(DATA_DIR.glob("time_and_sales_nq_*.csv"))
    data_files_pattern2 = sorted(DATA_DIR.glob("nq_*.csv"))

    data_files = data_files_pattern1 + data_files_pattern2

    dates = []
    import re
    for file in data_files:
        match = re.search(r'(?:time_and_sales_)?nq_(\d{8})\.csv', file.name)
        if match:
            dates.append(match.group(1))

    return sorted(set(dates))


def calculate_vwap_slope_at_bar(df, bar_idx, window=VWAP_SLOPE_DEGREE_WINDOW):
    """Calculate VWAP slope at a specific bar using linear regression"""
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


def backtest_all_days(dates: list):
    """
    Run backtest on all days and collect all trades with hourly information

    Returns:
        DataFrame with all trades including entry hour
    """
    print("=" * 80)
    print("COLLECTING ALL TRADES FROM ALL DAYS")
    print("=" * 80)
    print(f"Total days to process: {len(dates)}")
    print(f"TP: {VWAP_MOMENTUM_TP_POINTS} points")
    print(f"SL: {VWAP_MOMENTUM_SL_POINTS} points")
    print("=" * 80 + "\n")

    all_trades = []

    for idx, date in enumerate(dates, 1):
        print(f"[{idx}/{len(dates)}] Processing {date}...")

        try:
            # Load data
            df = load_date_range(date, date)

            if df is None:
                continue

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

            # Calculate day of week
            date_obj = datetime.strptime(date, "%Y%m%d")
            day_of_week = date_obj.isoweekday()

            # Execute strategy
            trades = []
            open_position = None

            for idx, bar in df.iterrows():
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

                        # Extract entry hour
                        entry_hour = open_position['entry_time'].hour

                        trades.append({
                            'date': date,
                            'entry_time': open_position['entry_time'],
                            'exit_time': bar['timestamp'],
                            'entry_hour': entry_hour,
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
                if open_position is None and VWAP_MOMENTUM_MAX_POSITIONS > 0:
                    # LONG signal
                    if bar['long_signal']:
                        entry_price = bar['close']
                        tp_price = entry_price + VWAP_MOMENTUM_TP_POINTS
                        sl_price = entry_price - VWAP_MOMENTUM_SL_POINTS
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
                        tp_price = entry_price - VWAP_MOMENTUM_TP_POINTS
                        sl_price = entry_price + VWAP_MOMENTUM_SL_POINTS
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

                entry_hour = open_position['entry_time'].hour

                trades.append({
                    'date': date,
                    'entry_time': open_position['entry_time'],
                    'exit_time': last_bar['timestamp'],
                    'entry_hour': entry_hour,
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
                all_trades.extend(trades)
                print(f"  {len(trades)} trades collected")

        except Exception as e:
            print(f"  [ERROR] Failed to process {date}: {e}")
            continue

    if len(all_trades) == 0:
        return None

    df_all_trades = pd.DataFrame(all_trades)
    print(f"\n[OK] Total trades collected: {len(df_all_trades)}")

    return df_all_trades


def analyze_by_hour(df_trades: pd.DataFrame):
    """
    Analyze trading performance by entry hour

    Returns:
        DataFrame with hourly statistics
    """
    hourly_stats = []

    for hour in range(24):
        hour_trades = df_trades[df_trades['entry_hour'] == hour]

        if len(hour_trades) == 0:
            continue

        total_trades = len(hour_trades)
        profit_trades = hour_trades[hour_trades['exit_reason'] == 'profit']
        stop_trades = hour_trades[hour_trades['exit_reason'] == 'stop']

        profit_count = len(profit_trades)
        stop_count = len(stop_trades)

        total_pnl_usd = hour_trades['pnl_usd'].sum()
        avg_pnl_usd = total_pnl_usd / total_trades

        win_rate = (profit_count / (profit_count + stop_count) * 100) if (profit_count + stop_count) > 0 else 0.0

        # Sharpe Ratio
        if len(hour_trades) > 1:
            returns = hour_trades['pnl_usd']
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0.0

        # Profit Factor
        gross_profit = profit_trades['pnl_usd'].sum() if len(profit_trades) > 0 else 0
        gross_loss = abs(stop_trades['pnl_usd'].sum()) if len(stop_trades) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (999.99 if gross_profit > 0 else 0)

        hourly_stats.append({
            'hour': hour,
            'hour_label': f"{hour:02d}:00",
            'total_trades': total_trades,
            'profit_trades': profit_count,
            'stop_trades': stop_count,
            'win_rate': win_rate,
            'total_pnl_usd': total_pnl_usd,
            'avg_pnl_usd': avg_pnl_usd,
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': profit_factor if profit_factor < 999 else 999.99
        })

    return pd.DataFrame(hourly_stats).sort_values('hour')


def generate_html_report(df_hourly: pd.DataFrame, df_trades: pd.DataFrame, dates: list):
    """Generate comprehensive HTML report with interactive charts"""

    reports_dir = OUTPUTS_DIR / "optimization"
    reports_dir.mkdir(parents=True, exist_ok=True)

    first_date = dates[0]
    last_date = dates[-1]
    date_str = f"{first_date}_{last_date}"

    report_file = reports_dir / f"trading_hours_analysis_{date_str}.html"

    # Find best hours
    best_pnl_hour = df_hourly.loc[df_hourly['total_pnl_usd'].idxmax()]
    best_sharpe_hour = df_hourly.loc[df_hourly['sharpe_ratio'].idxmax()]
    best_winrate_hour = df_hourly.loc[df_hourly['win_rate'].idxmax()]
    most_active_hour = df_hourly.loc[df_hourly['total_trades'].idxmax()]

    # Create sorted version for table (by Sharpe Ratio descending)
    df_hourly_sorted = df_hourly.sort_values('sharpe_ratio', ascending=False).reset_index(drop=True)

    # Create interactive Plotly charts
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'P&L por Hora',
            'Número de Trades por Hora',
            'Win Rate por Hora (%)',
            'Sharpe Ratio por Hora',
            'P&L Promedio por Trade',
            'Profit Factor por Hora'
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.12
    )

    # Chart 1: P&L by Hour
    colors_pnl = ['green' if x >= 0 else 'red' for x in df_hourly['total_pnl_usd']]
    fig.add_trace(
        go.Bar(x=df_hourly['hour_label'], y=df_hourly['total_pnl_usd'],
               marker_color=colors_pnl, name='Total P&L', showlegend=False),
        row=1, col=1
    )

    # Chart 2: Number of Trades
    fig.add_trace(
        go.Bar(x=df_hourly['hour_label'], y=df_hourly['total_trades'],
               marker_color='steelblue', name='Trades', showlegend=False),
        row=1, col=2
    )

    # Chart 3: Win Rate
    fig.add_trace(
        go.Bar(x=df_hourly['hour_label'], y=df_hourly['win_rate'],
               marker_color='purple', name='Win Rate', showlegend=False),
        row=2, col=1
    )

    # Chart 4: Sharpe Ratio
    colors_sharpe = ['green' if x >= 0 else 'red' for x in df_hourly['sharpe_ratio']]
    fig.add_trace(
        go.Bar(x=df_hourly['hour_label'], y=df_hourly['sharpe_ratio'],
               marker_color=colors_sharpe, name='Sharpe', showlegend=False),
        row=2, col=2
    )

    # Chart 5: Avg P&L per Trade
    colors_avg = ['green' if x >= 0 else 'red' for x in df_hourly['avg_pnl_usd']]
    fig.add_trace(
        go.Bar(x=df_hourly['hour_label'], y=df_hourly['avg_pnl_usd'],
               marker_color=colors_avg, name='Avg P&L', showlegend=False),
        row=3, col=1
    )

    # Chart 6: Profit Factor
    fig.add_trace(
        go.Bar(x=df_hourly['hour_label'], y=df_hourly['profit_factor'],
               marker_color='orange', name='PF', showlegend=False),
        row=3, col=2
    )

    # Update layout
    fig.update_xaxes(tickangle=45)
    fig.update_layout(height=1200, showlegend=False, title_text="Análisis de Performance por Hora de Trading")

    # Convert Plotly figure to HTML
    plotly_html = fig.to_html(include_plotlyjs='cdn', div_id='plotly_charts')

    # Generate full HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading Hours Analysis</title>
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
            .best-hours {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }}
            .hour-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
            }}
            .hour-card h3 {{
                margin: 0 0 10px 0;
                font-size: 14px;
                opacity: 0.9;
            }}
            .hour-card .value {{
                font-size: 24px;
                font-weight: bold;
            }}
            .hour-card .details {{
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
            <h1>VWAP Momentum - Análisis de Horas de Trading</h1>
            <p>Período: {first_date} → {last_date}</p>
            <p>Total Días: {len(dates)} | Total Trades: {len(df_trades):,}</p>
            <p>TP: {VWAP_MOMENTUM_TP_POINTS} pts | SL: {VWAP_MOMENTUM_SL_POINTS} pts</p>
        </div>

        <div class="section">
            <h2>Mejores Horas de Trading</h2>
            <div class="info-box">
                <strong>Recomendación:</strong> Analiza las horas con mejor Sharpe Ratio (riesgo-ajustado)
                y suficiente volumen de trades para resultados estadísticamente significativos.
            </div>
            <div class="best-hours">
                <div class="hour-card">
                    <h3>🏆 MEJOR SHARPE RATIO</h3>
                    <div class="value">{best_sharpe_hour['hour_label']}</div>
                    <div class="details">
                        Sharpe: {best_sharpe_hour['sharpe_ratio']:.2f}<br>
                        Total P&L: ${best_sharpe_hour['total_pnl_usd']:,.0f}<br>
                        Win Rate: {best_sharpe_hour['win_rate']:.1f}%<br>
                        Trades: {best_sharpe_hour['total_trades']:.0f}
                    </div>
                </div>

                <div class="hour-card">
                    <h3>💰 MAYOR P&L TOTAL</h3>
                    <div class="value">{best_pnl_hour['hour_label']}</div>
                    <div class="details">
                        Total P&L: ${best_pnl_hour['total_pnl_usd']:,.0f}<br>
                        Sharpe: {best_pnl_hour['sharpe_ratio']:.2f}<br>
                        Win Rate: {best_pnl_hour['win_rate']:.1f}%<br>
                        Trades: {best_pnl_hour['total_trades']:.0f}
                    </div>
                </div>

                <div class="hour-card">
                    <h3>🎯 MEJOR WIN RATE</h3>
                    <div class="value">{best_winrate_hour['hour_label']}</div>
                    <div class="details">
                        Win Rate: {best_winrate_hour['win_rate']:.1f}%<br>
                        Total P&L: ${best_winrate_hour['total_pnl_usd']:,.0f}<br>
                        Sharpe: {best_winrate_hour['sharpe_ratio']:.2f}<br>
                        Trades: {best_winrate_hour['total_trades']:.0f}
                    </div>
                </div>

                <div class="hour-card">
                    <h3>📊 MÁS ACTIVA</h3>
                    <div class="value">{most_active_hour['hour_label']}</div>
                    <div class="details">
                        Trades: {most_active_hour['total_trades']:.0f}<br>
                        Total P&L: ${most_active_hour['total_pnl_usd']:,.0f}<br>
                        Win Rate: {most_active_hour['win_rate']:.1f}%<br>
                        Sharpe: {most_active_hour['sharpe_ratio']:.2f}
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Gráficos Interactivos</h2>
            {plotly_html}
        </div>

        <div class="section">
            <h2>🏆 Ranking por Sharpe Ratio (Ordenado Descendente)</h2>
            <div style="max-height: 600px; overflow-y: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Hora</th>
                            <th>Trades</th>
                            <th>Win%</th>
                            <th>Total P&L</th>
                            <th>Avg P&L</th>
                            <th>Sharpe</th>
                            <th>PF</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for idx, row in df_hourly_sorted.iterrows():
        pnl_class = "positive" if row['total_pnl_usd'] > 0 else "negative"
        rank_class = "rank" if idx < 3 else ""
        html += f"""
                        <tr>
                            <td><span class="{rank_class}">#{idx + 1}</span></td>
                            <td><strong>{row['hour_label']}</strong></td>
                            <td>{row['total_trades']:.0f}</td>
                            <td>{row['win_rate']:.1f}%</td>
                            <td class="{pnl_class}">${row['total_pnl_usd']:,.0f}</td>
                            <td class="{pnl_class}">${row['avg_pnl_usd']:,.2f}</td>
                            <td><strong>{row['sharpe_ratio']:.2f}</strong></td>
                            <td>{row['profit_factor']:.2f}</td>
                        </tr>
        """

    html += """
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <h2>🕐 Tabla Completa por Hora (Orden Cronológico)</h2>
            <div style="max-height: 600px; overflow-y: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Hora</th>
                            <th>Trades</th>
                            <th>Win%</th>
                            <th>Total P&L</th>
                            <th>Avg P&L</th>
                            <th>Sharpe</th>
                            <th>PF</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    # Usar df_hourly original (ordenado por hora)
    for _, row in df_hourly.iterrows():
        pnl_class = "positive" if row['total_pnl_usd'] > 0 else "negative"
        html += f"""
                        <tr>
                            <td><strong>{row['hour_label']}</strong></td>
                            <td>{row['total_trades']:.0f}</td>
                            <td>{row['win_rate']:.1f}%</td>
                            <td class="{pnl_class}">${row['total_pnl_usd']:,.0f}</td>
                            <td class="{pnl_class}">${row['avg_pnl_usd']:,.2f}</td>
                            <td><strong>{row['sharpe_ratio']:.2f}</strong></td>
                            <td>{row['profit_factor']:.2f}</td>
                        </tr>
        """

    html += """
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <p style="text-align: center; color: #666;">
                Generado el """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
            </p>
        </div>
    </body>
    </html>
    """

    # Save HTML
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[OK] HTML report: {report_file}")

    # Save CSV
    csv_file = reports_dir / f"trading_hours_analysis_{date_str}.csv"
    df_hourly.to_csv(csv_file, index=False, sep=';', decimal=',')
    print(f"[OK] CSV report: {csv_file}")

    return report_file


if __name__ == "__main__":
    # Get all available dates
    available_dates = get_available_dates()

    if len(available_dates) == 0:
        print("[ERROR] No data files found")
        exit(1)

    print(f"[INFO] Found {len(available_dates)} days of data")
    print(f"[INFO] Date range: {available_dates[0]} -> {available_dates[-1]}\n")

    # Collect all trades
    df_all_trades = backtest_all_days(available_dates)

    if df_all_trades is None or len(df_all_trades) == 0:
        print("[ERROR] No trades collected")
        exit(1)

    # Analyze by hour
    print("\n" + "=" * 80)
    print("ANALYZING PERFORMANCE BY HOUR")
    print("=" * 80)

    df_hourly = analyze_by_hour(df_all_trades)

    print(f"\n[OK] Analyzed {len(df_hourly)} different hours")

    # Generate report
    report_file = generate_html_report(df_hourly, df_all_trades, available_dates)

    # Open in browser
    try:
        webbrowser.open(report_file.resolve().as_uri())
        print(f"[OK] Opening report in browser...")
    except Exception as e:
        print(f"[WARN] Could not open browser: {e}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    # Print summary
    print(f"\n📊 RESUMEN POR HORAS:")
    print(f"\nMejor Sharpe Ratio: {df_hourly.loc[df_hourly['sharpe_ratio'].idxmax()]['hour_label']} "
          f"(Sharpe: {df_hourly['sharpe_ratio'].max():.2f})")
    print(f"Mayor P&L: {df_hourly.loc[df_hourly['total_pnl_usd'].idxmax()]['hour_label']} "
          f"(${df_hourly['total_pnl_usd'].max():,.0f})")
    print(f"Mejor Win Rate: {df_hourly.loc[df_hourly['win_rate'].idxmax()]['hour_label']} "
          f"({df_hourly['win_rate'].max():.1f}%)")
    print(f"Hora más activa: {df_hourly.loc[df_hourly['total_trades'].idxmax()]['hour_label']} "
          f"({df_hourly['total_trades'].max():.0f} trades)")
    print()

"""
Analyze Trading Performance by Hour
Generates histogram showing trade distribution and P&L by hour of day
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime
import config

# Paths
OUTPUTS_DIR = Path(config.OUTPUTS_DIR)
TRADING_DIR = OUTPUTS_DIR / "trading"

def analyze_trades_by_hour(date_range_start=None, date_range_end=None):
    """
    Analyze all trades by hour and generate histogram

    Args:
        date_range_start: Start date (YYYYMMDD format) or None for all files
        date_range_end: End date (YYYYMMDD format) or None for all files
    """

    # Find all tracking record files
    tracking_files = list(TRADING_DIR.glob("tracking_record_vwap_momentum_*.csv"))

    if not tracking_files:
        print("[ERROR] No tracking record files found")
        return

    print(f"[INFO] Found {len(tracking_files)} tracking record files")

    # Load all trades
    all_trades = []
    for file in tracking_files:
        try:
            df = pd.read_csv(file, sep=';', decimal=',')

            # Convert timestamp strings to datetime
            df['entry_time'] = pd.to_datetime(df['entry_time'])
            df['exit_time'] = pd.to_datetime(df['exit_time'])

            all_trades.append(df)
        except Exception as e:
            print(f"[WARNING] Could not load {file.name}: {e}")
            continue

    if not all_trades:
        print("[ERROR] No valid trade data found")
        return

    # Combine all trades
    df_all = pd.concat(all_trades, ignore_index=True)

    # Extract entry hour (0-23)
    df_all['entry_hour'] = df_all['entry_time'].dt.hour

    # Group by hour
    hourly_stats = []

    for hour in range(24):
        hour_trades = df_all[df_all['entry_hour'] == hour]

        if len(hour_trades) == 0:
            hourly_stats.append({
                'hour': hour,
                'total_trades': 0,
                'winners': 0,
                'losers': 0,
                'win_rate': 0.0,
                'total_pnl_usd': 0.0,
                'avg_pnl_usd': 0.0,
                'best_trade': 0.0,
                'worst_trade': 0.0
            })
            continue

        winners = hour_trades[hour_trades['pnl_usd'] > 0]
        losers = hour_trades[hour_trades['pnl_usd'] <= 0]

        hourly_stats.append({
            'hour': hour,
            'total_trades': len(hour_trades),
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': (len(winners) / len(hour_trades)) * 100 if len(hour_trades) > 0 else 0.0,
            'total_pnl_usd': hour_trades['pnl_usd'].sum(),
            'avg_pnl_usd': hour_trades['pnl_usd'].mean(),
            'best_trade': hour_trades['pnl_usd'].max(),
            'worst_trade': hour_trades['pnl_usd'].min()
        })

    df_hourly = pd.DataFrame(hourly_stats)

    # Print summary
    print("\n" + "="*80)
    print("HOURLY TRADING ANALYSIS")
    print("="*80)
    print(f"Total Trades: {len(df_all)}")
    print(f"Date Range: {df_all['entry_time'].min().date()} to {df_all['entry_time'].max().date()}")
    print(f"Total Days: {df_all['entry_time'].dt.date.nunique()}")
    print("="*80)

    print(f"\n{'Hour':<6} {'Trades':<8} {'Win%':<8} {'Total P&L':<12} {'Avg P&L':<12} {'Best':<10} {'Worst':<10}")
    print("-" * 80)

    for _, row in df_hourly.iterrows():
        if row['total_trades'] > 0:
            print(f"{int(row['hour']):02d}:00  "
                  f"{int(row['total_trades']):<8} "
                  f"{row['win_rate']:<8.1f} "
                  f"${row['total_pnl_usd']:<11,.0f} "
                  f"${row['avg_pnl_usd']:<11,.2f} "
                  f"${row['best_trade']:<9,.0f} "
                  f"${row['worst_trade']:<9,.0f}")

    # Generate HTML report with interactive charts
    generate_hourly_report(df_hourly, df_all)

    print(f"\n[OK] Hourly analysis report saved to: {OUTPUTS_DIR / 'optimization' / 'hourly_trade_analysis.html'}")


def generate_hourly_report(df_hourly, df_all):
    """Generate HTML report with Plotly charts"""

    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            'Trade Count by Hour',
            'Total P&L by Hour',
            'Win Rate by Hour'
        ),
        vertical_spacing=0.12,
        row_heights=[0.33, 0.33, 0.34]
    )

    # Prepare data
    hours = df_hourly['hour'].tolist()
    hour_labels = [f"{h:02d}:00" for h in hours]

    # Chart 1: Trade Count
    colors_count = ['#2ecc71' if trades > 0 else '#95a5a6' for trades in df_hourly['total_trades']]

    fig.add_trace(
        go.Bar(
            x=hour_labels,
            y=df_hourly['total_trades'],
            name='Total Trades',
            marker_color=colors_count,
            text=df_hourly['total_trades'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Trades: %{y}<extra></extra>'
        ),
        row=1, col=1
    )

    # Chart 2: Total P&L
    colors_pnl = ['#2ecc71' if pnl > 0 else '#e74c3c' for pnl in df_hourly['total_pnl_usd']]

    fig.add_trace(
        go.Bar(
            x=hour_labels,
            y=df_hourly['total_pnl_usd'],
            name='Total P&L (USD)',
            marker_color=colors_pnl,
            text=[f"${pnl:,.0f}" if pnl != 0 else "" for pnl in df_hourly['total_pnl_usd']],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>P&L: $%{y:,.2f}<extra></extra>'
        ),
        row=2, col=1
    )

    # Chart 3: Win Rate
    colors_wr = ['#2ecc71' if wr >= 50 else '#e74c3c' if wr > 0 else '#95a5a6' for wr in df_hourly['win_rate']]

    fig.add_trace(
        go.Bar(
            x=hour_labels,
            y=df_hourly['win_rate'],
            name='Win Rate (%)',
            marker_color=colors_wr,
            text=[f"{wr:.1f}%" if wr > 0 else "" for wr in df_hourly['win_rate']],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1f}%<extra></extra>'
        ),
        row=3, col=1
    )

    # Add reference line at 50% win rate
    fig.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5, row=3, col=1)

    # Update axes
    fig.update_xaxes(title_text="Hour of Day", row=3, col=1)
    fig.update_yaxes(title_text="Number of Trades", row=1, col=1)
    fig.update_yaxes(title_text="Total P&L (USD)", row=2, col=1)
    fig.update_yaxes(title_text="Win Rate (%)", row=3, col=1)

    # Update layout
    fig.update_layout(
        height=1200,
        showlegend=False,
        title_text=f"Trading Performance by Hour of Day<br><sub>Total Trades: {len(df_all)} | Date Range: {df_all['entry_time'].min().date()} to {df_all['entry_time'].max().date()}</sub>",
        title_x=0.5,
        template='plotly_white',
        font=dict(size=12)
    )

    # Generate detailed HTML table
    table_html = generate_detailed_table(df_hourly)

    # Combine chart and table
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Hourly Trade Analysis</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            h1 {{
                text-align: center;
                color: #2c3e50;
            }}
            .summary {{
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #34495e;
                color: white;
                font-weight: bold;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .positive {{
                color: #27ae60;
                font-weight: bold;
            }}
            .negative {{
                color: #e74c3c;
                font-weight: bold;
            }}
            .neutral {{
                color: #95a5a6;
            }}
        </style>
    </head>
    <body>
        <h1>Hourly Trading Performance Analysis</h1>

        <div class="summary">
            <h3>Summary Statistics</h3>
            <p><strong>Total Trades:</strong> {len(df_all)}</p>
            <p><strong>Date Range:</strong> {df_all['entry_time'].min().date()} to {df_all['entry_time'].max().date()}</p>
            <p><strong>Total Days:</strong> {df_all['entry_time'].dt.date.nunique()}</p>
            <p><strong>Total P&L:</strong> ${df_all['pnl_usd'].sum():,.2f}</p>
            <p><strong>Overall Win Rate:</strong> {(len(df_all[df_all['pnl_usd'] > 0]) / len(df_all) * 100):.1f}%</p>
        </div>

        <div id="chart"></div>

        {table_html}

        <script>
            var plotData = {fig.to_json()};
            Plotly.newPlot('chart', plotData.data, plotData.layout);
        </script>
    </body>
    </html>
    """

    # Save HTML
    optimization_dir = OUTPUTS_DIR / "optimization"
    optimization_dir.mkdir(exist_ok=True)

    output_file = optimization_dir / "hourly_trade_analysis.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html)

    # Also save CSV
    csv_file = optimization_dir / "hourly_trade_analysis.csv"
    df_hourly.to_csv(csv_file, index=False)
    print(f"[OK] CSV data saved to: {csv_file}")


def generate_detailed_table(df_hourly):
    """Generate detailed HTML table"""

    rows = ""
    for _, row in df_hourly.iterrows():
        if row['total_trades'] == 0:
            pnl_class = "neutral"
            pnl_display = "$0.00"
        elif row['total_pnl_usd'] > 0:
            pnl_class = "positive"
            pnl_display = f"${row['total_pnl_usd']:,.2f}"
        else:
            pnl_class = "negative"
            pnl_display = f"${row['total_pnl_usd']:,.2f}"

        wr_class = "positive" if row['win_rate'] >= 50 else "negative" if row['win_rate'] > 0 else "neutral"

        rows += f"""
        <tr>
            <td><strong>{int(row['hour']):02d}:00</strong></td>
            <td>{int(row['total_trades'])}</td>
            <td>{int(row['winners'])}</td>
            <td>{int(row['losers'])}</td>
            <td class="{wr_class}">{row['win_rate']:.1f}%</td>
            <td class="{pnl_class}">{pnl_display}</td>
            <td>${row['avg_pnl_usd']:,.2f}</td>
            <td class="positive">${row['best_trade']:,.2f}</td>
            <td class="negative">${row['worst_trade']:,.2f}</td>
        </tr>
        """

    return f"""
    <div style="overflow-x: auto;">
        <table>
            <thead>
                <tr>
                    <th>Hour</th>
                    <th>Total Trades</th>
                    <th>Winners</th>
                    <th>Losers</th>
                    <th>Win Rate</th>
                    <th>Total P&L</th>
                    <th>Avg P&L</th>
                    <th>Best Trade</th>
                    <th>Worst Trade</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """


if __name__ == "__main__":
    analyze_trades_by_hour()

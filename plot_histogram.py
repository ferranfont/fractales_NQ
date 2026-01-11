import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

# Constants
OUTPUTS_DIR = Path("d:/PYTHON/ALGOS/factales_NQ/outputs/trading")

def plot_histogram():
    # Find latest all_days_tracking csv
    files = list(OUTPUTS_DIR.glob("all_days_tracking_*.csv"))
    if not files:
        print("[ERROR] No tracking CSV found.")
        return
    
    # Sort by modification time to get latest
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    print(f"[INFO] Processing file: {latest_file.name}")
    
    df = pd.read_csv(latest_file, sep=';', decimal=',')
    
    # Ensure entry_time is datetime
    if 'entry_time' not in df.columns:
        print("[ERROR] 'entry_time' column not found.")
        return

    # Check mapping
    try:
        df['entry_time'] = pd.to_datetime(df['entry_time'])
    except Exception as e:
         print(f"[ERROR] Date parsing failed: {e}")
         return

    df['hour'] = df['entry_time'].dt.hour
    
    # Group by Hour
    # Create complete index 0-23
    all_hours = pd.DataFrame({'hour': range(24)})
    
    grouped = df.groupby('hour').agg(
        trades=('entry_time', 'count'),
        pnl=('pnl_usd', 'sum'),
        win_rate=('pnl', lambda x: (x > 0).mean() * 100 if len(x) > 0 else 0)
    ).reset_index()
    
    # Merge with all hours ensures 0 for missing hours
    final_df = all_hours.merge(grouped, on='hour', how='left').fillna(0)
    
    # formatting
    final_df['label'] = final_df['hour'].apply(lambda h: f"{int(h):02d}:00")

    # Plot
    fig = go.Figure()
    
    # Add Trades Count Bar
    fig.add_trace(go.Bar(
        x=final_df['label'],
        y=final_df['trades'],
        name='Total Trades',
        marker_color='lightblue',
        opacity=0.7,
        yaxis='y'
    ))
    
    # Add P&L Line (secondary y)
    fig.add_trace(go.Scatter(
        x=final_df['label'],
        y=final_df['pnl'],
        name='Total P&L ($)',
        mode='lines+markers',
        line=dict(width=3, color='lightgreen'),
        marker=dict(size=8),
        yaxis='y2'
    ))

    fig.update_layout(
        title=f"Hourly Trade Analysis (Source: {latest_file.name})",
        xaxis=dict(
            title="Hour of Day",
            type='category'
        ),
        yaxis=dict(
            title="Number of Trades",
            side='left',
            showgrid=False
        ),
        yaxis2=dict(
            title="Total P&L ($)",
            side='right',
            overlaying='y',
            showgrid=True
        ),
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0.5)'),
        template='plotly_dark',
        height=600
    )
    
    output_path = OUTPUTS_DIR / "histogram_analysis.html"
    fig.write_html(output_path)
    print(f"[OK] Histogram saved to {output_path}")
    
    # Print summary table to console
    print("\nHourly Summary:")
    print(final_df[['label', 'trades', 'pnl', 'win_rate']].to_string(index=False))

if __name__ == "__main__":
    plot_histogram()

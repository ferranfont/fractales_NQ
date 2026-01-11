
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import os

# Specific file path
FILE_PATH = r'd:\PYTHON\ALGOS\factales_NQ\outputs\trading\all_days_tracking_20251001-20251219.csv'
OUTPUTS_DIR = Path(r'd:\PYTHON\ALGOS\factales_NQ\outputs')

def analyze_trades_by_hour():
    
    if not os.path.exists(FILE_PATH):
        print(f"[ERROR] File not found: {FILE_PATH}")
        return

    print(f"[INFO] Analyzing file: {FILE_PATH}")

    try:
        # Load the file
        # Using sep=';' as determined previously
        # Using decimal=',' assumption, or strictly treating strings
        # Based on previous robust reading:
        df = pd.read_csv(FILE_PATH, sep=';')
        
        # Clean currency columns like in previous steps
        for col in ['pnl_usd', 'pnl']:
            if df[col].dtype == object:
                 df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Convert timestamp strings to datetime
        df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce')
        df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')
        
        # Drop rows with invalid dates if any
        df = df.dropna(subset=['entry_time'])

    except Exception as e:
        print(f"[ERROR] Could not load file: {e}")
        return

    # Extract entry hour (0-23)
    df['entry_hour'] = df['entry_time'].dt.hour

    # Group by hour
    hourly_stats = []

    for hour in range(24):
        hour_trades = df[df['entry_hour'] == hour]

        if len(hour_trades) == 0:
            continue

        winners = hour_trades[hour_trades['pnl_usd'] > 0]
        losers = hour_trades[hour_trades['pnl_usd'] <= 0]

        hourly_stats.append({
            'hour': hour,
            'total_trades': len(hour_trades),
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': (len(winners) / len(hour_trades)) * 100,
            'total_pnl_usd': hour_trades['pnl_usd'].sum(),
            'avg_pnl_usd': hour_trades['pnl_usd'].mean(),
            'best_trade': hour_trades['pnl_usd'].max(),
            'worst_trade': hour_trades['pnl_usd'].min()
        })

    df_hourly = pd.DataFrame(hourly_stats)
    
    if df_hourly.empty:
         print("No hourly stats available.")
         return

    # Sort by hour
    df_hourly = df_hourly.sort_values('hour')

    # Print summary
    print("\n" + "="*90)
    print("HOURLY TRADING ANALYSIS (PRIORITY 1)")
    print("="*90)
    print(f"Total Trades: {len(df)}")
    print(f"Total P&L: ${df['pnl_usd'].sum():,.2f}")
    print("="*90)

    print(f"\n{'Hour':<6} {'Trades':<8} {'Win%':<8} {'Total P&L':<12} {'Avg P&L':<12} {'Best':<10} {'Worst':<10}")
    print("-" * 90)

    for _, row in df_hourly.iterrows():
        print(f"{int(row['hour']):02d}:00  "
              f"{int(row['total_trades']):<8} "
              f"{row['win_rate']:<8.1f} "
              f"${row['total_pnl_usd']:<11,.0f} "
              f"${row['avg_pnl_usd']:<11,.2f} "
              f"${row['best_trade']:<9,.0f} "
              f"${row['worst_trade']:<9,.0f}")
              
    print("\nRecommendations based on Win Rate < 40%:")
    bad_hours = df_hourly[df_hourly['win_rate'] < 40]
    for _, row in bad_hours.iterrows():
         print(f"❌ Hour {int(row['hour']):02d}:00 - Win Rate: {row['win_rate']:.1f}% - PnL: ${row['total_pnl_usd']:,.0f}")

if __name__ == "__main__":
    analyze_trades_by_hour()

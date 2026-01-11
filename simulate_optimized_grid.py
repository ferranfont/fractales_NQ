
import pandas as pd
import numpy as np
from pathlib import Path

FILE_PATH = r'd:\PYTHON\ALGOS\factales_NQ\outputs\trading\all_days_tracking_20251001-20251219.csv'

def calculate_metrics(df, name):
    if len(df) == 0:
        return None
        
    pnl = df['pnl_usd']
    wins = pnl[pnl > 0]
    losses = pnl[pnl <= 0]
    
    total_trades = len(df)
    win_rate = (len(wins) / total_trades) * 100
    total_pnl = pnl.sum()
    avg_trade = pnl.mean()
    
    avg_win = wins.mean() if len(wins) > 0 else 0
    avg_loss = losses.mean() if len(losses) > 0 else 0
    
    # Drawdown
    cumulative = pnl.cumsum()
    peak = cumulative.cummax()
    drawdown = cumulative - peak
    max_drawdown = drawdown.min()
    
    # Ratios (simplified/annualized approximations)
    # Assuming risk-free rate = 0 for simplicity
    std_dev = pnl.std()
    sharpe = (avg_trade / std_dev) if std_dev != 0 else 0
    
    downside_returns = pnl[pnl < 0]
    downside_std = downside_returns.std()
    sortino = (avg_trade / downside_std) if downside_std != 0 else 0
    
    # Recovery Index (Absolute Profit / Max Drawdown)
    recovery_factor = total_pnl / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # Wins needed to cover 1 loss
    recovery_index_trades = abs(avg_loss) / avg_win if avg_win != 0 else 0

    return {
        'Name': name,
        'Trades': total_trades,
        'Win Rate': win_rate,
        'Total PnL': total_pnl,
        'Max DD': max_drawdown,
        'Avg Win': avg_win,
        'Avg Loss': avg_loss,
        'Sharpe': sharpe,  # per trade
        'Sortino': sortino, # per trade
        'Recovery Factor (Net/DD)': recovery_factor,
        'Wins to Recover': recovery_index_trades
    }

def simulate():
    try:
        df = pd.read_csv(FILE_PATH, sep=';')
        
        # Clean data
        for col in ['pnl_usd']:
            if df[col].dtype == object:
                 df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce')
        df['hour'] = df['entry_time'].dt.hour
        
        # 1. Base Case (Option A - Current Grid)
        metrics_base = calculate_metrics(df, "Opción A (Base Grid)")
        
        # 2. Optimized Case (Grid + Hourly Filter)
        # Removing toxicity: Hours with toxic losses or very low win rates based on previous analysis
        # Bad list: 01, 02, 03, 09, 11, 14, 20
        # 20:00 had -7k loss
        hours_to_exclude = [1, 2, 3, 9, 11, 14, 20]
        
        df_opt = df[~df['hour'].isin(hours_to_exclude)]
        metrics_opt = calculate_metrics(df_opt, "Opción A+ (Grid Optimizado)")
        
        # Print Comparison
        results = pd.DataFrame([metrics_base, metrics_opt])
        
        # Transpose for readability
        print("\n=== SIMULACIÓN DE OPTIMIZACIÓN DE RIESGO ===")
        print("Estrategia: Eliminar horas tóxicas (01, 02, 03, 09, 11, 14, 20)")
        print("-" * 60)
        
        for col in results.columns:
            if col == 'Name': continue
            val_base = results.loc[0, col]
            val_opt = results.loc[1, col]
            
            diff = val_opt - val_base
            if col in ['Win Rate', 'Sharpe', 'Sortino', 'Recovery Factor (Net/DD)']:
                # Higher is better
                better = val_opt > val_base
            elif col in ['Max DD', 'Wins to Recover']:
                # Lower magnitude (closer to 0 or smaller) is better
                # Max DD is negative, so greater value (closer to 0) is better. e.g. -10k > -18k
                # Wins to Recover: smaller is better
                if col == 'Max DD': better = val_opt > val_base
                else: better = val_opt < val_base
            else:
                better = val_opt > val_base # PnL etc
            
            mark = "✅" if better else "🔻"
            
            # Format
            if 'PnL' in col or 'DD' in col or 'Avg' in col:
                fmt_base = f"${val_base:,.0f}"
                fmt_opt = f"${val_opt:,.0f}"
            elif 'Rate' in col:
                fmt_base = f"{val_base:.1f}%"
                fmt_opt = f"{val_opt:.1f}%"
            elif 'Wins' in col or 'Factor' in col or 'Sharpe' in col or 'Sortino' in col:
                fmt_base = f"{val_base:.2f}"
                fmt_opt = f"{val_opt:.2f}"
            else:
                fmt_base = val_base
                fmt_opt = val_opt
                
            print(f"{col:<25} | Base: {fmt_base:<10} | Opt: {fmt_opt:<10} | {mark}")

        print("-" * 60)
        print(f"Mejora de PnL: ${metrics_opt['Total PnL'] - metrics_base['Total PnL']:,.2f}")
        print(f"Reducción de Drawdown: ${abs(metrics_base['Max DD']) - abs(metrics_opt['Max DD']):,.2f}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    simulate()

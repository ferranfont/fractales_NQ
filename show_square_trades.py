"""Quick script to show Square trades"""
import pandas as pd

df = pd.read_csv('outputs/trading/tracking_record_vwap_square_20251104.csv', sep=';', decimal=',')

print('\n=== TRADES VWAP SQUARE - 20251104 ===\n')
print(df[['direction', 'entry_time', 'entry_price', 'exit_time', 'exit_price', 'pnl', 'pnl_usd', 'exit_reason']].to_string(index=True))

print(f'\n\nRESUMEN:')
print(f'Total Trades: {len(df)}')
print(f'TP Exits: {(df["exit_reason"] == "tp_exit").sum()}')
print(f'SL Exits: {(df["exit_reason"] == "sl_exit").sum()}')
print(f'EOD Exits: {(df["exit_reason"] == "eod_exit").sum()}')
print(f'BUY Trades: {(df["direction"] == "BUY").sum()}')
print(f'SELL Trades: {(df["direction"] == "SELL").sum()}')
print(f'Total PnL: {df["pnl"].sum():.2f} points (${df["pnl_usd"].sum():,.2f})')
print(f'Average PnL: {df["pnl"].mean():.2f} points (${df["pnl_usd"].mean():,.2f})')

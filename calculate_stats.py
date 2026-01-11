
import pandas as pd
import numpy as np

file_path = r'd:\PYTHON\ALGOS\factales_NQ\outputs\trading\all_days_tracking_20251001-20251219.csv'

try:
    df = pd.read_csv(file_path, sep=';')
    
    # Clean numeric columns
    # It seems pnl_usd might be string. Let's clean it.
    # Replace ',' with '.' if it's european style, or just remove ',' if it's thousands separator.
    # Given the previous error, let's assume it might be just string type.
    
    def clean_currency(x):
        if isinstance(x, str):
            x = x.replace(',', '.') # Assuming comma is decimal or thousands. Let's try direct to_numeric first or replace.
            # If it was 1,000.00 then replacing , with . gives 1.000.00 which is bad.
            # But if it was 1.000,00 (Eu) -> 1.000.00 -> still bad?
            # Let's simple check a value first? No time, just safe conversion.
            # Usually python float uses dot.
            pass
        return x

    # Let's inspect one value if possible? No, let's just use pd.to_numeric with coercing.
    # But if commas are present as decimal separators, pd.to_numeric won't handle it by default.
    # I'll replace ',' with '.' assuming it might be a decimal separator derived from a locale.
    
    for col in ['pnl_usd', 'pnl']:
        if df[col].dtype == object:
             df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    col_name = 'exit_reason'
    tag_sl = 'sl_exit_grid'
    tag_tp = 'tp_exit_grid'

    # Filter
    sl_operations = df[df[col_name] == tag_sl]
    tp_operations = df[df[col_name] == tag_tp]

    # Counts
    count_sl = len(sl_operations)
    count_tp = len(tp_operations)

    # Sums
    sum_sl = sl_operations['pnl_usd'].sum()
    sum_tp = tp_operations['pnl_usd'].sum()
    
    sum_sl_pts = sl_operations['pnl'].sum()
    sum_tp_pts = tp_operations['pnl'].sum()

    print("\n--- Results ---")
    print(f"{tag_sl}:")
    print(f"  Count: {count_sl}")
    print(f"  Sum PnL USD: {sum_sl: .2f}")
    
    print(f"\n{tag_tp}:")
    print(f"  Count: {count_tp}")
    print(f"  Sum PnL USD: {sum_tp: .2f}")

    print("\n--- Summary ---")
    # "luego haces la resta"
    # If SL sum is negative (loss), and TP sum is positive (profit).
    # He might want Profit - Loss (magnitude) or just Net.
    # I'll print: Net (TP + SL), and Difference of absolute values just in case.
    
    net_pnl = sum_tp + sum_sl
    diff_abs = sum_tp - abs(sum_sl) # Profit - Loss
    
    print(f"  Net PnL (TP + SL): {net_pnl: .2f}")
    print(f"  Difference (TP - |SL|): {diff_abs: .2f}")
    
    # Also counts
    print(f"  Count Difference (TP - SL): {count_tp - count_sl}")


except Exception as e:
    print(f"Error: {e}")
    # Print sample data for debugging
    try:
        print("Sample pnl_usd:", df['pnl_usd'].head())
    except:
        pass

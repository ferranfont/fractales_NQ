"""
Script to optimize VWAP Time Strategy by testing different entry times.
It iterates through a list of entry times, updates the configuration, runs the iteration over all days, and collects the results.
"""

import sys
import pandas as pd
from pathlib import Path
import subprocess
import re
import time

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    DATA_DIR, OUTPUTS_DIR,
    ENABLE_VWAP_TIME_STRATEGY,
    VWAP_TIME_EXIT, VWAP_TIME_TP_POINTS, VWAP_TIME_SL_POINTS
)

# Configuration for Optimization
ENTRY_TIMES_TO_TEST = [
    "13:00:00", "13:30:00", 
    "14:00:00", "14:30:00", 
    "15:00:00", "15:30:00", 
    "16:00:00", "16:30:00", 
    "17:00:00", "17:30:00", 
    "18:00:00", "18:30:00", 
    "19:00:00", "19:30:00",
    "20:00:00"
]

def update_config_entry_time(entry_time, config_path):
    """Updates the VWAP_TIME_ENTRY in config.py"""
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex to replace VWAP_TIME_ENTRY = "..."
    # We look for the variable definition and replace the value
    new_content = re.sub(
        r'VWAP_TIME_ENTRY\s*=\s*".*"', 
        f'VWAP_TIME_ENTRY = "{entry_time}"', 
        content
    )
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def run_optimization():
    project_root = Path(__file__).parent
    config_path = project_root / "config.py"
    iterate_script = project_root / "iterate" / "iterate_all_days.py"
    
    results = []
    
    print("="*80)
    print(f"STARTING VWAP TIME OPTIMIZATION")
    print(f"Times to test: {len(ENTRY_TIMES_TO_TEST)}")
    print("="*80 + "\n")

    # Backup original config to restore later
    with open(config_path, 'r', encoding='utf-8') as f:
        original_config = f.read()
        
    try:
        for i, entry_time in enumerate(ENTRY_TIMES_TO_TEST, 1):
            print(f"\n[{i}/{len(ENTRY_TIMES_TO_TEST)}] Testing Entry Time: {entry_time}")
            print("-" * 60)
            
            # 1. Update Config
            update_config_entry_time(entry_time, config_path)
            
            # 2. Run iterate_all_days.py
            # We run it and capture the output to verify completion, but we mainly care about the generated CSV
            # ensure iterate_all_days is configured to use ranges or we assume config is set for range
            # NOTE: The user's config currently has a single date set for 'main', but iterate_all_days uses USE_ALL_DAYS_AVAILABLE or segment.
            # We assume iterate_all_days is correctly set up to run the desired range.
            
            # We also need to make sure iterate_all_days is set to overwrite or we check the specific output file
            # iterate_all_days creates "all_days_tracking_{start}-{end}.csv"
            
            # To speed up, we might want to disable chart generation in config if possible, but we'll leave as is for now or modify on fly.
            # Let's just run it.
            
            process = subprocess.run(
                [sys.executable, str(iterate_script)],
                cwd=str(project_root),
                capture_output=False,
                text=True
            )
            
            if process.returncode != 0:
                print(f"[ERROR] Iteration script failed for {entry_time}")
                print(process.stderr[:500])
                continue
                
            # 3. Analyze Results
            # We need to find the result file. It is in outputs/trading/all_days_tracking_....csv
            # The filename depends on the date range in config. 
            # We can find the most recently modified file in that folder or search for the pattern.
            trading_dir = OUTPUTS_DIR / "trading"
            # Consolidated files usually start with "all_days_tracking_"
            
            # Find the consolidated csv
            consolidated_files = list(trading_dir.glob("all_days_tracking_*.csv"))
            if not consolidated_files:
                print("[WARN] No consolidated tracking file found.")
                continue
                
            # Get the most recent one to be sure
            latest_file = max(consolidated_files, key=lambda p: p.stat().st_mtime)
            
            try:
                df = pd.read_csv(latest_file, sep=';', decimal=',')
                
                # Filter for Time strategy if mixed (though likely only Time is running ideally)
                # If iterate_all_days runs all enabled strategies, we should filter.
                # Assuming 'Time' strategy has a distinguising feature or we check all.
                # In current iterate_all_days, it appends all enabled. 
                # Ideally, we should ensure only Time is enabled, but we can filter by logic if needed.
                # For now, we take the whole result assuming User only enabled Time or we analyze all.
                
                # Filter specifically for VWAP Time trades if possible. 
                # The 'strategy' column doesn't exist in the CSV by default in iterate_all_days unless added.
                # However, strat_vwap_time produces specific exit reasons or we can rely on total PnL.
                
                total_pnl = df['pnl'].sum()
                total_pnl_usd = df['pnl_usd'].sum()
                total_trades = len(df)
                win_rate = (len(df[df['pnl'] > 0]) / total_trades * 100) if total_trades > 0 else 0
                
                results.append({
                    'entry_time': entry_time,
                    'total_trades': total_trades,
                    'win_rate': win_rate,
                    'total_pnl_pts': total_pnl,
                    'total_pnl_usd': total_pnl_usd,
                    'avg_trade_usd': total_pnl_usd / total_trades if total_trades > 0 else 0
                })
                
                print(f"Result for {entry_time}: PnL=${total_pnl_usd:.2f} ({total_trades} trades)")
                
            except Exception as e:
                print(f"[ERROR] Could not read results: {e}")

    finally:
        # Restore Config
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(original_config)
            
    # 4. Save Optimization Report
    print("\n" + "="*80)
    print("OPTIMIZATION RESULTS")
    print("="*80)
    
    if results:
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('total_pnl_usd', ascending=False)
        
        print(df_results.to_string(index=False))
        
        timestamp = int(time.time())
        opt_filename = OUTPUTS_DIR / f"vwap_time_optimization_{timestamp}.csv"
        df_results.to_csv(opt_filename, index=False)
        print(f"\n[OK] Detailed optimization results saved to: {opt_filename}")
    else:
        print("No results collected.")

if __name__ == "__main__":
    run_optimization()

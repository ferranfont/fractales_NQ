"""
Script principal de análisis cuantitativo para Nasaq (NQ)
Orquesta la ejecución de:
1. Detección de fractales (find_fractals.py)
2. Generación de gráfico (plot_day.py)
"""
from pathlib import Path
from config import START_DATE, END_DATE, DATA_DIR, OUTPUTS_DIR, PROJECT_ROOT
from find_fractals import process_fractals_range
from find_reg_channel_scipy import calculate_channel
from find_choppiness import calculate_fractal_metrics, print_consolidation_table
from plot_day import plot_range_chart
from show_config_dashboard import update_dashboard

# Auto-update configuration dashboard
update_dashboard()


def generate_daily_summary_html(start_date: str, end_date: str):
    """
    Generate HTML summary report for a single day with all active strategies

    Args:
        start_date: Date in format YYYYMMDD
        end_date: Date in format YYYYMMDD (should be same as start_date for daily report)

    Returns:
        str: HTML content or None if no trades found
    """
    import pandas as pd
    from datetime import datetime
    from config import (
        ENABLE_VWAP_MOMENTUM_STRATEGY, ENABLE_VWAP_PULLBACK_STRATEGY, ENABLE_VWAP_CROSSOVER_STRATEGY, ENABLE_VWAP_SQUARE_STRATEGY,
        VWAP_MOMENTUM_TP_POINTS, VWAP_MOMENTUM_SL_POINTS,
        VWAP_PULLBACK_TP_POINTS, VWAP_PULLBACK_SL_POINTS,
        VWAP_CROSSOVER_TP_POINTS, VWAP_CROSSOVER_SL_POINTS,
        VWAP_SQUARE_TP_POINTS, VWAP_SQUARE_SL_POINTS,
        VWAP_SQUARE_TP_POINTS, VWAP_SQUARE_SL_POINTS,
        ENABLE_VWAP_TIME_STRATEGY, VWAP_TIME_TP_POINTS, VWAP_TIME_SL_POINTS,
        ENABLE_VWAP_WYCKOFF_STRATEGY, TP_ORANGE_DOT_WYCKOFF, SL_ORANGE_DOT_WYCKOFF
    )

    trading_dir = OUTPUTS_DIR / "trading"

    # Collect all trades from active strategies
    all_trades = []
    strategy_summaries = []

    # VWAP Momentum
    if ENABLE_VWAP_MOMENTUM_STRATEGY:
        csv_file = trading_dir / f"tracking_record_vwap_momentum_{start_date}.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file, sep=';', decimal=',')
            if len(df) > 0:
                df['strategy'] = 'Momentum'
                all_trades.append(df)

                # Calculate summary
                tp_count = (df['exit_reason'].isin(['profit', 'tp_exit'])).sum()
                sl_count = (df['exit_reason'].isin(['stop', 'sl_exit', 'protective_sl_exit', 'trail_stop', 'slope_exit', 'green_dot_timeout'])).sum()
                win_rate = (tp_count / (tp_count + sl_count) * 100) if (tp_count + sl_count) > 0 else 0

                strategy_summaries.append({
                    'name': 'VWAP Momentum',
                    'trades': len(df),
                    'win_rate': win_rate,
                    'pnl_usd': df['pnl_usd'].sum(),
                    'tp_sl': f"{VWAP_MOMENTUM_TP_POINTS:.0f} / {VWAP_MOMENTUM_SL_POINTS:.0f}"
                })

    # VWAP Pullback
    if ENABLE_VWAP_PULLBACK_STRATEGY:
        csv_file = trading_dir / f"tracking_record_vwap_pullback_{start_date}.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file, sep=';', decimal=',')
            if len(df) > 0:
                df['strategy'] = 'Pullback'
                all_trades.append(df)

                # Calculate summary
                tp_count = (df['exit_reason'] == 'tp_exit').sum()
                sl_count = (df['exit_reason'] == 'sl_exit').sum()
                win_rate = (tp_count / (tp_count + sl_count) * 100) if (tp_count + sl_count) > 0 else 0

                strategy_summaries.append({
                    'name': 'VWAP Pullback',
                    'trades': len(df),
                    'win_rate': win_rate,
                    'pnl_usd': df['pnl_usd'].sum(),
                    'tp_sl': f"{VWAP_PULLBACK_TP_POINTS:.0f} / {VWAP_PULLBACK_SL_POINTS:.0f}"
                })

    # VWAP Crossover
    if ENABLE_VWAP_CROSSOVER_STRATEGY:
        csv_file = trading_dir / f"tracking_record_vwap_crossover_{start_date}.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file, sep=';', decimal=',')
            if len(df) > 0:
                df['strategy'] = 'Crossover'
                all_trades.append(df)

                # Calculate summary
                tp_count = (df['exit_reason'] == 'profit').sum()
                sl_count = (df['exit_reason'] == 'stop').sum()
                win_rate = (tp_count / (tp_count + sl_count) * 100) if (tp_count + sl_count) > 0 else 0

                strategy_summaries.append({
                    'name': 'VWAP Crossover',
                    'trades': len(df),
                    'win_rate': win_rate,
                    'pnl_usd': df['pnl_usd'].sum(),
                    'tp_sl': f"{VWAP_CROSSOVER_TP_POINTS:.0f} / {VWAP_CROSSOVER_SL_POINTS:.0f}"
                })

    # VWAP Square
    if ENABLE_VWAP_SQUARE_STRATEGY:
        csv_file = trading_dir / f"tracking_record_vwap_square_{start_date}.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file, sep=';', decimal=',')
            if len(df) > 0:
                df['strategy'] = 'Square'
                all_trades.append(df)

                # Calculate summary
                tp_count = (df['exit_reason'] == 'tp_exit').sum()
                sl_count = (df['exit_reason'] == 'sl_exit').sum()
                win_rate = (tp_count / (tp_count + sl_count) * 100) if (tp_count + sl_count) > 0 else 0

                strategy_summaries.append({
                    'name': 'VWAP Square',
                    'trades': len(df),
                    'win_rate': win_rate,
                    'pnl_usd': df['pnl_usd'].sum(),
                    'tp_sl': f"{VWAP_SQUARE_TP_POINTS:.0f} / {VWAP_SQUARE_SL_POINTS:.0f}"
                })

    # VWAP Time
    if ENABLE_VWAP_TIME_STRATEGY:
        csv_file = trading_dir / f"tracking_record_vwap_time_{start_date}.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file, sep=';', decimal=',')
            if len(df) > 0:
                df['strategy'] = 'Time'
                all_trades.append(df)

                # Calculate summary
                tp_count = (df['exit_reason'] == 'tp_exit').sum()
                sl_count = (df['exit_reason'] == 'sl_exit').sum()
                win_rate = (tp_count / (tp_count + sl_count) * 100) if (tp_count + sl_count) > 0 else 0

                strategy_summaries.append({
                    'name': 'VWAP Time',
                    'trades': len(df),
                    'win_rate': win_rate,
                    'pnl_usd': df['pnl_usd'].sum(),
                    'tp_sl': f"{VWAP_TIME_TP_POINTS:.0f} / {VWAP_TIME_SL_POINTS:.0f}"
                })

    # VWAP Wyckoff
    if ENABLE_VWAP_WYCKOFF_STRATEGY:
        csv_file = trading_dir / f"tracking_record_vwap_wyckoff_{start_date}.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file, sep=';', decimal=',')
            if len(df) > 0:
                df['strategy'] = 'Wyckoff'
                all_trades.append(df)

                # Calculate summary
                tp_count = (df['exit_reason'].isin(['tp_exit', 'profit'])).sum()
                sl_count = (df['exit_reason'].isin(['sl_exit', 'stop'])).sum()
                win_rate = (tp_count / (tp_count + sl_count) * 100) if (tp_count + sl_count) > 0 else 0

                strategy_summaries.append({
                    'name': 'VWAP Wyckoff',
                    'trades': len(df),
                    'win_rate': win_rate,
                    'pnl_usd': df['pnl_usd'].sum(),
                    'tp_sl': f"{TP_ORANGE_DOT_WYCKOFF:.0f} / {SL_ORANGE_DOT_WYCKOFF:.0f}"
                })

    # If no trades found, return None
    if not all_trades:
        return None

    # Combine all trades
    df_all = pd.concat(all_trades, ignore_index=True)

    # Calculate overall statistics
    total_trades = len(df_all)
    total_pnl_usd = df_all['pnl_usd'].sum()
    avg_pnl_usd = total_pnl_usd / total_trades if total_trades > 0 else 0

    # Count exits by type
    tp_exits = df_all['exit_reason'].isin(['profit', 'tp_exit']).sum()
    sl_exits = df_all['exit_reason'].isin(['stop', 'sl_exit', 'protective_sl_exit', 'trail_stop', 'slope_exit', 'green_dot_timeout']).sum()
    eod_exits = df_all['exit_reason'].isin(['eod_exit', 'time_exit']).sum()

    win_rate = (tp_exits / (tp_exits + sl_exits) * 100) if (tp_exits + sl_exits) > 0 else 0

    # Parse date for display
    date_obj = datetime.strptime(start_date, "%Y%m%d")
    date_display = date_obj.strftime("%Y-%m-%d (%A)")

    # Build strategy summary table
    strategy_rows = ""
    for s in strategy_summaries:
        pnl_class = "positive" if s['pnl_usd'] >= 0 else "negative"
        strategy_rows += f"""
        <tr>
            <td>{s['name']}</td>
            <td>{s['trades']}</td>
            <td>{s['win_rate']:.1f}%</td>
            <td class="{pnl_class}">${s['pnl_usd']:,.0f}</td>
            <td>{s['tp_sl']}</td>
        </tr>
        """

    # Build trades table
    trades_rows = ""
    for idx, row in df_all.iterrows():
        pnl_class = "positive" if row['pnl_usd'] >= 0 else "negative"
        trades_rows += f"""
        <tr>
            <td>{idx + 1}</td>
            <td>{row['strategy']}</td>
            <td>{row['direction']}</td>
            <td>{row['entry_time']}</td>
            <td>{row['exit_time']}</td>
            <td>{row['entry_price']:.2f}</td>
            <td>{row['exit_price']:.2f}</td>
            <td>{row['exit_reason']}</td>
            <td class="{pnl_class}">${row['pnl_usd']:,.0f}</td>
        </tr>
        """

    # Generate HTML
    overall_pnl_class = "positive" if total_pnl_usd >= 0 else "negative"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Daily Summary - {start_date}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
        }}
        .date {{
            text-align: center;
            font-size: 18px;
            color: #666;
            margin-bottom: 30px;
        }}
        .summary-box {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px;
        }}
        .metric-label {{
            font-weight: bold;
            color: #666;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
        }}
        .positive {{
            color: #28a745;
        }}
        .negative {{
            color: #dc3545;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        h2 {{
            color: #667eea;
            margin-top: 40px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Daily Trading Summary</h1>
        <div class="date">{date_display}</div>

        <div class="summary-box">
            <div class="metric">
                <div class="metric-label">Total Trades</div>
                <div class="metric-value">{total_trades}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Win Rate</div>
                <div class="metric-value">{win_rate:.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total P&L</div>
                <div class="metric-value {overall_pnl_class}">${total_pnl_usd:,.0f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg per Trade</div>
                <div class="metric-value {overall_pnl_class}">${avg_pnl_usd:,.0f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">TP / SL / EOD</div>
                <div class="metric-value">{tp_exits} / {sl_exits} / {eod_exits}</div>
            </div>
        </div>

        <h2>Strategy Breakdown</h2>
        <table>
            <tr>
                <th>Strategy</th>
                <th>Trades</th>
                <th>Win Rate</th>
                <th>P&L (USD)</th>
                <th>TP / SL</th>
            </tr>
            {strategy_rows}
        </table>

        <h2>All Trades</h2>
        <table>
            <tr>
                <th>#</th>
                <th>Strategy</th>
                <th>Dir</th>
                <th>Entry Time</th>
                <th>Exit Time</th>
                <th>Entry</th>
                <th>Exit</th>
                <th>Reason</th>
                <th>P&L (USD)</th>
            </tr>
            {trades_rows}
        </table>

        <div style="margin-top: 40px; text-align: center; color: #999;">
            Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
</body>
</html>
"""

    return html_content


def main_quant_range(start_date: str, end_date: str):
    """
    Ejecuta el pipeline completo de análisis cuantitativo para un rango de fechas

    Args:
        start_date: Fecha inicial en formato YYYY-MM-DD
        end_date: Fecha final en formato YYYY-MM-DD
    """
    print("\n" + "="*70)
    print("ANÁLISIS CUANTITATIVO - Nasdaq (NQ)")
    print("="*70)
    if start_date == end_date:
        print(f"Fecha: {start_date}")
    else:
        print(f"Rango: {start_date} -> {end_date}")
    print("="*70 + "\n")
 
    # 1. Procesar fractales
    print("\n" + "-"*70)
    print("PASO 1: DETECCIÓN DE FRACTALES")
    print("-"*70)
    fractals_result = process_fractals_range(start_date, end_date)
    if fractals_result is None:
        print("[ERROR] Fallo en detección de fractales")
        return None

    # 1.4 Calcular Métricas de Consolidación
    print("\n" + "-"*70)
    print("PASO 1.4: CÁLCULO DE MÉTRICAS DE CONSOLIDACIÓN")
    print("-"*70)
    df_fractals_metrics = calculate_fractal_metrics(
        fractals_result['df_fractals_minor']
    )

    # Imprimir tabla de métricas
    print_consolidation_table(df_fractals_metrics, max_rows=30)

    # Guardar métricas en CSV
    from config import FRACTALS_DIR
    if start_date == end_date:
        date_range_str = start_date
    else:
        date_range_str = f"{start_date}_{end_date}"
    symbol = fractals_result.get('symbol', 'NQ')
    metrics_path = FRACTALS_DIR / f"{symbol}_consolidation_metrics_{date_range_str}.csv"
    df_fractals_metrics.to_csv(metrics_path, index=False)
    print(f"[INFO] Métricas guardadas en: {metrics_path}")

    # 1.5 Calcular Canal de Regresión
    print("\n" + "-"*70)
    print("PASO 1.5: CÁLCULO DE CANAL DE REGRESIÓN")
    print("-"*70)
    # Usamos los fractales MINOR para el canal (más puntos -> mejor reg?) O MAJOR?
    # El usuario dijo "unir los máximos", y Zigzag Minor da más detalle. Probaremos con Minor.
    channel_params = calculate_channel(
        fractals_result['df'],
        fractals_result['df_fractals_minor']
    )

    # 2. Execute VWAP Crossover Strategy if enabled
    print("\n" + "-"*70)
    print("PASO 2: EJECUCIÓN DE ESTRATEGIA VWAP CROSSOVER")
    print("-"*70)
    try:
        from config import ENABLE_VWAP_CROSSOVER_STRATEGY

        if ENABLE_VWAP_CROSSOVER_STRATEGY:
            print("[INFO] Strategy is enabled, executing...")
            import subprocess
            import sys

            # Execute the strategy as a subprocess
            strategy_script = PROJECT_ROOT / "strat_vwap_crossover.py"
            if strategy_script.exists():
                result = subprocess.run(
                    [sys.executable, str(strategy_script)],
                    capture_output=False,
                    text=True,
                    cwd=str(PROJECT_ROOT)
                )
                if result.returncode == 0:
                    print("[OK] Strategy executed successfully")
                else:
                    print(f"[WARN] Strategy execution returned code: {result.returncode}")
            else:
                print(f"[ERROR] Strategy file not found: {strategy_script}")
        else:
            print("[INFO] Strategy is disabled in config (ENABLE_VWAP_CROSSOVER_STRATEGY = False)")
    except Exception as e:
        print(f"[ERROR] Failed to execute strategy: {e}")

    # Note: Browser opening is handled by strat_vwap_crossover.py itself
    # to avoid duplicate browser windows

    # 2.5 Execute VWAP Momentum Strategy if enabled
    print("\n" + "-"*70)
    print("PASO 2.5: EJECUCIÓN DE ESTRATEGIA VWAP MOMENTUM")
    print("-"*70)
    try:
        from config import ENABLE_VWAP_MOMENTUM_STRATEGY

        if ENABLE_VWAP_MOMENTUM_STRATEGY:
            print("[INFO] Strategy is enabled, executing...")
            import subprocess
            import sys

            # Execute the strategy as a subprocess
            strategy_script = PROJECT_ROOT / "strat_vwap_momentum.py"
            if strategy_script.exists():
                result = subprocess.run(
                    [sys.executable, str(strategy_script)],
                    capture_output=False,
                    text=True,
                    cwd=str(PROJECT_ROOT)
                )
                if result.returncode == 0:
                    print("[OK] Strategy executed successfully")
                else:
                    print(f"[WARN] Strategy execution returned code: {result.returncode}")
            else:
                print(f"[ERROR] Strategy file not found: {strategy_script}")
        else:
            print("[INFO] Strategy is disabled in config (ENABLE_VWAP_MOMENTUM_STRATEGY = False)")
    except Exception as e:
        print(f"[ERROR] Failed to execute strategy: {e}")

    # Note: Browser opening is handled by strat_vwap_momentum.py itself
    # to avoid duplicate browser windows

    # 2.6 Execute VWAP Pullback Strategy if enabled
    print("\n" + "-"*70)
    print("PASO 2.6: EJECUCIÓN DE ESTRATEGIA VWAP PULLBACK")
    print("-"*70)
    try:
        from config import ENABLE_VWAP_PULLBACK_STRATEGY

        if ENABLE_VWAP_PULLBACK_STRATEGY:
            print("[INFO] Strategy is enabled, executing...")
            import subprocess
            import sys

            # Execute the strategy as a subprocess
            strategy_script = PROJECT_ROOT / "strat_vwap_pullback.py"
            if strategy_script.exists():
                result = subprocess.run(
                    [sys.executable, str(strategy_script)],
                    capture_output=False,
                    text=True,
                    cwd=str(PROJECT_ROOT)
                )
                if result.returncode == 0:
                    print("[OK] Strategy executed successfully")
                else:
                    print(f"[WARN] Strategy execution returned code: {result.returncode}")
            else:
                print(f"[ERROR] Strategy file not found: {strategy_script}")
        else:
            print("[INFO] Strategy is disabled in config (ENABLE_VWAP_PULLBACK_STRATEGY = False)")
    except Exception as e:
        print(f"[ERROR] Failed to execute strategy: {e}")

    # Note: Browser opening is handled by strat_vwap_pullback.py itself
    # to avoid duplicate browser windows

    # 2.7 Execute VWAP Square Strategy if enabled
    print("\n" + "-"*70)
    print("PASO 2.7: EJECUCIÓN DE ESTRATEGIA VWAP SQUARE")
    print("-"*70)
    try:
        from config import ENABLE_VWAP_SQUARE_STRATEGY

        if ENABLE_VWAP_SQUARE_STRATEGY:
            print("[INFO] Strategy is enabled, executing...")
            import subprocess
            import sys

            # Execute the strategy as a subprocess
            strategy_script = PROJECT_ROOT / "strat_vwap_square.py"
            if strategy_script.exists():
                result = subprocess.run(
                    [sys.executable, str(strategy_script)],
                    capture_output=False,
                    text=True,
                    cwd=str(PROJECT_ROOT)
                )
                if result.returncode == 0:
                    print("[OK] Strategy executed successfully")
                else:
                    print(f"[WARN] Strategy execution returned code: {result.returncode}")
            else:
                print(f"[ERROR] Strategy file not found: {strategy_script}")
        else:
            print("[INFO] Strategy is disabled in config (ENABLE_VWAP_SQUARE_STRATEGY = False)")
    except Exception as e:
        print(f"[ERROR] Failed to execute strategy: {e}")

    # Note: Browser opening is handled by strat_vwap_square.py itself
    # to avoid duplicate browser windows

    # 2.8 Execute VWAP Time Strategy if enabled
    print("\n" + "-"*70)
    print("PASO 2.8: EJECUCIÓN DE ESTRATEGIA VWAP TIME")
    print("-"*70)
    try:
        from config import ENABLE_VWAP_TIME_STRATEGY

        if ENABLE_VWAP_TIME_STRATEGY:
            print("[INFO] Strategy is enabled, executing...")
            import subprocess
            import sys

            # Execute the strategy as a subprocess
            strategy_script = PROJECT_ROOT / "strat_vwap_time.py"
            if strategy_script.exists():
                result = subprocess.run(
                    [sys.executable, str(strategy_script)],
                    capture_output=False,
                    text=True,
                    cwd=str(PROJECT_ROOT)
                )
                if result.returncode == 0:
                    print("[OK] Strategy executed successfully")
                else:
                    print(f"[WARN] Strategy execution returned code: {result.returncode}")
            else:
                print(f"[ERROR] Strategy file not found: {strategy_script}")
        else:
            print("[INFO] Strategy is disabled in config (ENABLE_VWAP_TIME_STRATEGY = False)")
    except Exception as e:
        print(f"[ERROR] Failed to execute strategy: {e}")

    # 2.9 Execute VWAP Wyckoff Strategy if enabled
    print("\n" + "-"*70)
    print("PASO 2.9: EJECUCIÓN DE ESTRATEGIA VWAP WYCKOFF")
    print("-"*70)
    try:
        from config import ENABLE_VWAP_WYCKOFF_STRATEGY

        if ENABLE_VWAP_WYCKOFF_STRATEGY:
            print("[INFO] Strategy is enabled, executing...")
            import subprocess
            import sys

            # Execute the strategy as a subprocess
            strategy_script = PROJECT_ROOT / "strat_vwap_wyckoff.py"
            if strategy_script.exists():
                result = subprocess.run(
                    [sys.executable, str(strategy_script)],
                    capture_output=False,
                    text=True,
                    cwd=str(PROJECT_ROOT)
                )
                if result.returncode == 0:
                    print("[OK] Strategy executed successfully")
                else:
                    print(f"[WARN] Strategy execution returned code: {result.returncode}")
            else:
                print(f"[ERROR] Strategy file not found: {strategy_script}")
        else:
            print("[INFO] Strategy is disabled in config (ENABLE_VWAP_WYCKOFF_STRATEGY = False)")
    except Exception as e:
        print(f"[ERROR] Failed to execute strategy: {e}")

    # 2.10 Execute VWAP Band Reversal Strategy if enabled
    print("\n" + "-"*70)
    print("PASO 2.10: EJECUCIÓN DE ESTRATEGIA VWAP BAND REVERSAL")
    print("-"*70)
    try:
        from config import ENABLE_VWAP_BAND_REVERSAL_STRATEGY

        if ENABLE_VWAP_BAND_REVERSAL_STRATEGY:
            print("[INFO] Strategy is enabled, executing...")
            import subprocess
            import sys

            # Execute the strategy as a subprocess
            strategy_script = PROJECT_ROOT / "strat_vwap_band_reversal.py"
            if strategy_script.exists():
                result = subprocess.run(
                    [sys.executable, str(strategy_script)],
                    capture_output=False,
                    text=True,
                    cwd=str(PROJECT_ROOT)
                )
                if result.returncode == 0:
                    print("[OK] Strategy executed successfully")
                else:
                    print(f"[WARN] Strategy execution returned code: {result.returncode}")
            else:
                print(f"[ERROR] Strategy file not found: {strategy_script}")
        else:
            print("[INFO] Strategy is disabled in config (ENABLE_VWAP_BAND_REVERSAL_STRATEGY = False)")
    except Exception as e:
        print(f"[ERROR] Failed to execute strategy: {e}")

    # 2.11 Execute VWAP Score Strategy (Clenow) if enabled
    print("\n" + "-"*70)
    print("PASO 2.11: EJECUCIÓN DE ESTRATEGIA VWAP SCORE (CLENOW)")
    print("-"*70)
    try:
        from config import ENABLE_STRAT_VWAP_SCORE

        if ENABLE_STRAT_VWAP_SCORE:
            print("[INFO] Strategy is enabled, executing...")
            import subprocess
            import sys

            # Execute the strategy as a subprocess
            strategy_script = PROJECT_ROOT / "strat_vwap_score.py"
            if strategy_script.exists():
                result = subprocess.run(
                    [sys.executable, str(strategy_script)],
                    capture_output=False,
                    text=True,
                    cwd=str(PROJECT_ROOT)
                )
                if result.returncode == 0:
                    print("[OK] Strategy executed successfully")
                else:
                    print(f"[WARN] Strategy execution returned code: {result.returncode}")
            else:
                print(f"[ERROR] Strategy file not found: {strategy_script}")
        else:
            print("[INFO] Strategy is disabled in config (ENABLE_STRAT_VWAP_SCORE = False)")
    except Exception as e:
        print(f"[ERROR] Failed to execute strategy: {e}")

    # 2.12 Execute VWAP Score Reversal Strategy if enabled
    print("\n" + "-"*70)
    print("PASO 2.12: EJECUCIÓN DE ESTRATEGIA VWAP SCORE REVERSAL")
    print("-"*70)
    try:
        from config import ENABLE_STRAT_VWAP_SCORE_REVERSAL

        if ENABLE_STRAT_VWAP_SCORE_REVERSAL:
            print("[INFO] Strategy is enabled, executing...")
            import subprocess
            import sys

            # Execute the strategy as a subprocess
            strategy_script = PROJECT_ROOT / "strat_vwap_score_reversal.py"
            if strategy_script.exists():
                result = subprocess.run(
                    [sys.executable, str(strategy_script)],
                    capture_output=False,
                    text=True,
                    cwd=str(PROJECT_ROOT)
                )
                if result.returncode == 0:
                    print("[OK] Strategy executed successfully")
                else:
                    print(f"[WARN] Strategy execution returned code: {result.returncode}")
            else:
                print(f"[ERROR] Strategy file not found: {strategy_script}")
        else:
            print("[INFO] Strategy is disabled in config (ENABLE_STRAT_VWAP_SCORE_REVERSAL = False)")
    except Exception as e:
        print(f"[ERROR] Failed to execute strategy: {e}")

    # 2.13 Execute VWAP Score Reversal Anticipate Strategy if enabled
    print("\n" + "-"*70)
    print("PASO 2.13: EJECUCIÓN DE ESTRATEGIA VWAP SCORE REVERSAL ANTICIPATE")
    print("-"*70)
    try:
        from config import ENABLE_STRAT_VWAP_SCORE_REVERSAL_ANTICIPATE

        if ENABLE_STRAT_VWAP_SCORE_REVERSAL_ANTICIPATE:
            print("[INFO] Strategy is enabled, executing...")
            import subprocess
            import sys

            # Execute the strategy as a subprocess
            strategy_script = PROJECT_ROOT / "strat_vwap_score_reversal_anticipate.py"
            if strategy_script.exists():
                result = subprocess.run(
                    [sys.executable, str(strategy_script)],
                    capture_output=False,
                    text=True,
                    cwd=str(PROJECT_ROOT)
                )
                if result.returncode == 0:
                    print("[OK] Strategy executed successfully")
                else:
                    print(f"[WARN] Strategy execution returned code: {result.returncode}")
            else:
                print(f"[ERROR] Strategy file not found: {strategy_script}")
        else:
            print("[INFO] Strategy is disabled in config (ENABLE_STRAT_VWAP_SCORE_REVERSAL_ANTICIPATE = False)")
    except Exception as e:
        print(f"[ERROR] Failed to execute strategy: {e}")

    # 3. Generar gráfico (AFTER strategies so CSV files are available)
    print("\n" + "-"*70)
    print("PASO 3: GENERACIÓN DE GRÁFICO")
    print("-"*70)

    # Load trades from all enabled strategies for plotting
    import pandas as pd
    from config import (
        ENABLE_VWAP_MOMENTUM_STRATEGY, ENABLE_VWAP_WYCKOFF_STRATEGY,
        ENABLE_VWAP_TIME_STRATEGY, ENABLE_VWAP_BAND_REVERSAL_STRATEGY,
        ENABLE_VWAP_PULLBACK_STRATEGY, ENABLE_VWAP_SQUARE_STRATEGY,
        ENABLE_VWAP_CROSSOVER_STRATEGY, ENABLE_STRAT_VWAP_SCORE,
        ENABLE_STRAT_VWAP_SCORE_REVERSAL, ENABLE_STRAT_VWAP_SCORE_REVERSAL_ANTICIPATE
    )

    all_trades_list = []

    # Use start_date for filename (assuming single day analysis or primary date)
    trade_date_str = start_date

    # Map strategies to their file names and enabled status
    strategy_map = [
        (ENABLE_VWAP_MOMENTUM_STRATEGY, f"tracking_record_vwap_momentum_{trade_date_str}.csv"),
        (ENABLE_VWAP_WYCKOFF_STRATEGY, f"tracking_record_vwap_wyckoff_{trade_date_str}.csv"),
        (ENABLE_VWAP_TIME_STRATEGY, f"tracking_record_vwap_time_{trade_date_str}.csv"),
        (ENABLE_VWAP_BAND_REVERSAL_STRATEGY, f"tracking_record_vwap_band_reversal_{trade_date_str}.csv"),
        (ENABLE_VWAP_PULLBACK_STRATEGY, f"tracking_record_vwap_pullback_{trade_date_str}.csv"),
        (ENABLE_VWAP_SQUARE_STRATEGY, f"tracking_record_vwap_square_{trade_date_str}.csv"),
        (ENABLE_VWAP_CROSSOVER_STRATEGY, f"tracking_record_vwap_crossover_{trade_date_str}.csv"),
        (ENABLE_STRAT_VWAP_SCORE, f"tracking_record_vwap_score_{trade_date_str}.csv"),
        (ENABLE_STRAT_VWAP_SCORE_REVERSAL, f"tracking_record_vwap_score_reversal_{trade_date_str}.csv"),
        (ENABLE_STRAT_VWAP_SCORE_REVERSAL_ANTICIPATE, f"tracking_record_vwap_score_reversal_anticipate_{trade_date_str}.csv")
    ]
    trading_dir = OUTPUTS_DIR / "trading"

    for is_enabled, t_file in strategy_map:
        if is_enabled:
            t_path = trading_dir / t_file
            if t_path.exists():
                try:
                    tdf = pd.read_csv(t_path, sep=';', decimal=',', parse_dates=['entry_time', 'exit_time'])
                    if len(tdf) > 0:
                        all_trades_list.append(tdf)
                        print(f"[INFO] Loaded trades from {t_file} (Strategy Enabled)")
                except Exception as e:
                    print(f"[WARN] Failed to load {t_file}: {e}")
        # else:
            # print(f"[INFO] Skipping {t_file} (Strategy Disabled)")


    df_combined_trades = pd.concat(all_trades_list, ignore_index=True) if all_trades_list else None


    plot_result = plot_range_chart(
        fractals_result['df'],
        fractals_result['df_fractals_minor'],
        fractals_result['df_fractals_major'],
        start_date,
        end_date,
        symbol=fractals_result.get('symbol', 'NQ'),
        df_trades=df_combined_trades,
        rsi_levels=None,
        fibo_levels=None,
        divergences=None,
        channel_params=channel_params,
        df_metrics=df_fractals_metrics
    )
    if plot_result is None:
        print("[ERROR] Fallo en generación de gráfico")
        return None

    # 4. Guardar Modelo (Parámetros del Canal)
    if channel_params:
        import json
        from config import MODELS_DIR

        # Crear directorio de modelos si no existe
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

        if start_date == end_date:
            date_range_str = start_date
        else:
            date_range_str = f"{start_date}_{end_date}"
        symbol = fractals_result.get('symbol', 'NQ')
        model_filename = MODELS_DIR / f"channel_model_{symbol.lower()}_{date_range_str}.json"

        # Añadir metadatos al modelo
        model_data = {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'parameters': channel_params
        }

        with open(model_filename, 'w') as f:
            json.dump(model_data, f, indent=4)

        print("\n" + "-"*70)
        print("PASO 4: GUARDADO DE MODELO")
        print("-"*70)
        print(f"Modelo guardado en: {model_filename}")

    # 5. Resumen final
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    if start_date == end_date:
        print(f"Fecha analizada: {start_date}")
    else:
        print(f"Rango analizado: {start_date} -> {end_date}")
    print(f"Registros procesados: {fractals_result['total_records']}")
    print(f"Fractales MINOR detectados: {fractals_result['minor_count']}")
    print(f"Fractales MAJOR detectados: {fractals_result['major_count']}")
    print(f"Gráfico generado: {plot_result['output_path']}")

    # Display trading strategy summaries if available
    try:
        import pandas as pd
        from config import ENABLE_VWAP_CROSSOVER_STRATEGY, ENABLE_VWAP_MOMENTUM_STRATEGY, DATE

        trading_dir = OUTPUTS_DIR / "trading"

        # --- VWAP Crossover Strategy Summary ---
        if ENABLE_VWAP_CROSSOVER_STRATEGY:
            csv_file = trading_dir / f"tracking_record_vwap_crossover_{DATE}.csv"

            if csv_file.exists():
                df_trades = pd.read_csv(csv_file, sep=';', decimal=',')

                if len(df_trades) > 0:
                    print("\n" + "-"*70)
                    print("STRATEGY SUMMARY - VWAP CROSSOVER")
                    print("-"*70)

                    # Calculate statistics
                    total_trades = len(df_trades)
                    profit_trades = df_trades[df_trades['exit_reason'] == 'profit']
                    stop_trades = df_trades[df_trades['exit_reason'] == 'stop']

                    total_pnl = df_trades['pnl'].sum()
                    total_pnl_usd = df_trades['pnl_usd'].sum()
                    avg_pnl_usd = total_pnl_usd / total_trades if total_trades > 0 else 0

                    profit_count = len(profit_trades)
                    stop_count = len(stop_trades)
                    denom = profit_count + stop_count
                    win_rate = (profit_count / denom * 100) if denom > 0 else 0.0

                    buy_trades = df_trades[df_trades['direction'] == 'BUY']
                    sell_trades = df_trades[df_trades['direction'] == 'SELL']
                    buy_pnl_usd = buy_trades['pnl_usd'].sum() if len(buy_trades) > 0 else 0.0
                    sell_pnl_usd = sell_trades['pnl_usd'].sum() if len(sell_trades) > 0 else 0.0

                    # Print formatted summary
                    print(f"Total trades: {total_trades}")
                    print(f"Win rate: {win_rate:.1f}% ({profit_count} profits / {stop_count} stops)")
                    print(f"Total P&L: {total_pnl:+.0f} points (${total_pnl_usd:,.0f})")
                    print(f"Average per trade: {avg_pnl_usd:+.2f} USD")
                    print(f"BUY trades: {len(buy_trades)} (${buy_pnl_usd:,.0f})")
                    print(f"SELL trades: {len(sell_trades)} (${sell_pnl_usd:,.0f})")
                    print(f"Trading record: {csv_file.name}")

                    summary_file = trading_dir / f"summary_vwap_crossover_{DATE}.html"
                    if summary_file.exists():
                        print(f"Summary HTML: {summary_file.name}")
                else:
                    print("\n[INFO] Crossover strategy executed but no trades were generated")
            else:
                print("\n[INFO] Crossover strategy not executed or no trading data available")

        # --- VWAP Momentum Strategy Summary ---
        if ENABLE_VWAP_MOMENTUM_STRATEGY:
            csv_file = trading_dir / f"tracking_record_vwap_momentum_{DATE}.csv"

            if csv_file.exists():
                df_trades = pd.read_csv(csv_file, sep=';', decimal=',')

                if len(df_trades) > 0:
                    print("\n" + "-"*70)
                    print("STRATEGY SUMMARY - VWAP MOMENTUM")
                    print("-"*70)

                    # Calculate statistics
                    total_trades = len(df_trades)
                    profit_trades = df_trades[df_trades['exit_reason'].isin(['profit', 'tp_exit'])]
                    stop_trades = df_trades[df_trades['exit_reason'].isin(['stop', 'sl_exit', 'protective_sl_exit', 'trail_stop', 'slope_exit', 'green_dot_timeout'])]

                    total_pnl = df_trades['pnl'].sum()
                    total_pnl_usd = df_trades['pnl_usd'].sum()
                    avg_pnl_usd = total_pnl_usd / total_trades if total_trades > 0 else 0

                    profit_count = len(profit_trades)
                    stop_count = len(stop_trades)
                    denom = profit_count + stop_count
                    win_rate = (profit_count / denom * 100) if denom > 0 else 0.0

                    # Momentum strategy trades both directions (BUY and SELL)
                    buy_trades = df_trades[df_trades['direction'] == 'BUY']
                    sell_trades = df_trades[df_trades['direction'] == 'SELL']
                    buy_pnl_usd = buy_trades['pnl_usd'].sum() if len(buy_trades) > 0 else 0.0
                    sell_pnl_usd = sell_trades['pnl_usd'].sum() if len(sell_trades) > 0 else 0.0

                    # Print formatted summary
                    print(f"Total trades: {total_trades}")
                    print(f"Win rate: {win_rate:.1f}% ({profit_count} profits / {stop_count} stops)")
                    print(f"Total P&L: {total_pnl:+.0f} points (${total_pnl_usd:,.0f})")
                    print(f"Average per trade: {avg_pnl_usd:+.2f} USD")
                    print(f"BUY trades: {len(buy_trades)} (${buy_pnl_usd:,.0f})")
                    print(f"SELL trades: {len(sell_trades)} (${sell_pnl_usd:,.0f})")
                    print(f"Trading record: {csv_file.name}")

                    summary_file = trading_dir / f"summary_vwap_momentum_{DATE}.html"
                    if summary_file.exists():
                        print(f"Summary HTML: {summary_file.name}")
                else:
                    print("\n[INFO] Momentum strategy executed but no trades were generated")
            else:
                print("\n[INFO] Momentum strategy not executed or no trading data available")

        # --- VWAP Pullback Strategy Summary ---
        from config import ENABLE_VWAP_PULLBACK_STRATEGY
        if ENABLE_VWAP_PULLBACK_STRATEGY:
            csv_file = trading_dir / f"tracking_record_vwap_pullback_{DATE}.csv"

            if csv_file.exists():
                df_trades = pd.read_csv(csv_file, sep=';', decimal=',')

                if len(df_trades) > 0:
                    print("\n" + "-"*70)
                    print("STRATEGY SUMMARY - VWAP PULLBACK")
                    print("-"*70)

                    # Calculate statistics
                    total_trades = len(df_trades)
                    profit_trades = df_trades[df_trades['exit_reason'] == 'tp_exit']
                    stop_trades = df_trades[df_trades['exit_reason'] == 'sl_exit']

                    total_pnl = df_trades['pnl'].sum()
                    total_pnl_usd = df_trades['pnl_usd'].sum()
                    avg_pnl_usd = total_pnl_usd / total_trades if total_trades > 0 else 0

                    profit_count = len(profit_trades)
                    stop_count = len(stop_trades)
                    denom = profit_count + stop_count
                    win_rate = (profit_count / denom * 100) if denom > 0 else 0.0

                    # Pullback strategy trades both directions (BUY and SELL)
                    buy_trades = df_trades[df_trades['direction'] == 'BUY']
                    sell_trades = df_trades[df_trades['direction'] == 'SELL']
                    buy_pnl_usd = buy_trades['pnl_usd'].sum() if len(buy_trades) > 0 else 0.0
                    sell_pnl_usd = sell_trades['pnl_usd'].sum() if len(sell_trades) > 0 else 0.0

                    # Print formatted summary
                    print(f"Total trades: {total_trades}")
                    print(f"Win rate: {win_rate:.1f}% ({profit_count} profits / {stop_count} stops)")
                    print(f"Total P&L: {total_pnl:+.0f} points (${total_pnl_usd:,.0f})")
                    print(f"Average per trade: {avg_pnl_usd:+.2f} USD")
                    print(f"BUY trades: {len(buy_trades)} (${buy_pnl_usd:,.0f})")
                    print(f"SELL trades: {len(sell_trades)} (${sell_pnl_usd:,.0f})")
                    print(f"Trading record: {csv_file.name}")
                else:
                    print("\n[INFO] Pullback strategy executed but no trades were generated")
            else:
                print("\n[INFO] Pullback strategy not executed or no trading data available")

        # --- VWAP Square Strategy Summary ---
        from config import ENABLE_VWAP_SQUARE_STRATEGY
        if ENABLE_VWAP_SQUARE_STRATEGY:
            csv_file = trading_dir / f"tracking_record_vwap_square_{DATE}.csv"

            if csv_file.exists():
                df_trades = pd.read_csv(csv_file, sep=';', decimal=',')

                if len(df_trades) > 0:
                    print("\n" + "-"*70)
                    print("STRATEGY SUMMARY - VWAP SQUARE")
                    print("-"*70)

                    # Calculate statistics
                    total_trades = len(df_trades)
                    profit_trades = df_trades[df_trades['exit_reason'] == 'tp_exit']
                    stop_trades = df_trades[df_trades['exit_reason'] == 'sl_exit']

                    total_pnl = df_trades['pnl'].sum()
                    total_pnl_usd = df_trades['pnl_usd'].sum()
                    avg_pnl_usd = total_pnl_usd / total_trades if total_trades > 0 else 0

                    profit_count = len(profit_trades)
                    stop_count = len(stop_trades)
                    denom = profit_count + stop_count
                    win_rate = (profit_count / denom * 100) if denom > 0 else 0.0

                    # Square strategy trades both directions (BUY and SELL)
                    buy_trades = df_trades[df_trades['direction'] == 'BUY']
                    sell_trades = df_trades[df_trades['direction'] == 'SELL']
                    buy_pnl_usd = buy_trades['pnl_usd'].sum() if len(buy_trades) > 0 else 0.0
                    sell_pnl_usd = sell_trades['pnl_usd'].sum() if len(sell_trades) > 0 else 0.0

                    # Print formatted summary
                    print(f"Total trades: {total_trades}")
                    print(f"Win rate: {win_rate:.1f}% ({profit_count} profits / {stop_count} stops)")
                    print(f"Total P&L: {total_pnl:+.0f} points (${total_pnl_usd:,.0f})")
                    print(f"Average per trade: {avg_pnl_usd:+.2f} USD")
                    print(f"BUY trades: {len(buy_trades)} (${buy_pnl_usd:,.0f})")
                    print(f"SELL trades: {len(sell_trades)} (${sell_pnl_usd:,.0f})")
                    print(f"Trading record: {csv_file.name}")
                else:
                    print("\n[INFO] Square strategy executed but no trades were generated")
            else:
                print("\n[INFO] Square strategy not executed or no trading data available")

        # --- VWAP Time Strategy Summary ---
        from config import ENABLE_VWAP_TIME_STRATEGY
        if ENABLE_VWAP_TIME_STRATEGY:
            csv_file = trading_dir / f"tracking_record_vwap_time_{DATE}.csv"

            if csv_file.exists():
                df_trades = pd.read_csv(csv_file, sep=';', decimal=',')

                if len(df_trades) > 0:
                    print("\n" + "-"*70)
                    print("STRATEGY SUMMARY - VWAP TIME")
                    print("-"*70)

                    # Calculate statistics
                    total_trades = len(df_trades)
                    profit_trades = df_trades[df_trades['exit_reason'].isin(['tp_exit', 'profit'])]
                    stop_trades = df_trades[df_trades['exit_reason'].isin(['sl_exit', 'stop', 'time_exit'])] # Count time exit as non-profit for win rate here or separate? Usually time exit is neutral, but effectively a stop to the trade.

                    total_pnl = df_trades['pnl'].sum()
                    total_pnl_usd = df_trades['pnl_usd'].sum()
                    avg_pnl_usd = total_pnl_usd / total_trades if total_trades > 0 else 0

                    profit_count = len(profit_trades)
                    stop_count = len(stop_trades)
                    denom = total_trades # Use total trades for simpler calc
                    wn_rate = (len(df_trades[df_trades['pnl'] > 0]) / total_trades * 100) if total_trades > 0 else 0.0

                    # Time strategy trades both directions (BUY and SELL)
                    buy_trades = df_trades[df_trades['direction'] == 'BUY']
                    sell_trades = df_trades[df_trades['direction'] == 'SELL']
                    buy_pnl_usd = buy_trades['pnl_usd'].sum() if len(buy_trades) > 0 else 0.0
                    sell_pnl_usd = sell_trades['pnl_usd'].sum() if len(sell_trades) > 0 else 0.0

                    # Print formatted summary
                    print(f"Total trades: {total_trades}")
                    print(f"Win rate: {win_rate:.1f}%")
                    print(f"Total P&L: {total_pnl:+.0f} points (${total_pnl_usd:,.0f})")
                    print(f"Average per trade: {avg_pnl_usd:+.2f} USD")
                    print(f"BUY trades: {len(buy_trades)} (${buy_pnl_usd:,.0f})")
                    print(f"SELL trades: {len(sell_trades)} (${sell_pnl_usd:,.0f})")
                    print(f"Trading record: {csv_file.name}")
                else:
                    print("\n[INFO] Time strategy executed but no trades were generated")
            else:
                print("\n[INFO] Time strategy not executed or no trading data available")

        # --- VWAP Wyckoff Strategy Summary ---
        from config import ENABLE_VWAP_WYCKOFF_STRATEGY
        if ENABLE_VWAP_WYCKOFF_STRATEGY:
            csv_file = trading_dir / f"tracking_record_vwap_wyckoff_{DATE}.csv"

            if csv_file.exists():
                df_trades = pd.read_csv(csv_file, sep=';', decimal=',')

                if len(df_trades) > 0:
                    print("\n" + "-"*70)
                    print("STRATEGY SUMMARY - VWAP WYCKOFF")
                    print("-"*70)

                    # Calculate statistics
                    total_trades = len(df_trades)
                    profit_trades = df_trades[df_trades['exit_reason'].isin(['tp_exit', 'profit'])]
                    stop_trades = df_trades[df_trades['exit_reason'].isin(['sl_exit', 'stop', 'time_exit'])]

                    total_pnl = df_trades['pnl'].sum()
                    total_pnl_usd = df_trades['pnl_usd'].sum()
                    avg_pnl_usd = total_pnl_usd / total_trades if total_trades > 0 else 0

                    profit_count = len(profit_trades)
                    stop_count = len(stop_trades)
                    denom = len(df_trades[df_trades['pnl'] != 0])
                    win_rate = (len(df_trades[df_trades['pnl'] > 0]) / denom * 100) if denom > 0 else 0.0

                    # Wyckoff strategy trades both directions
                    buy_trades = df_trades[df_trades['direction'] == 'BUY']
                    sell_trades = df_trades[df_trades['direction'] == 'SELL']
                    buy_pnl_usd = buy_trades['pnl_usd'].sum() if len(buy_trades) > 0 else 0.0
                    sell_pnl_usd = sell_trades['pnl_usd'].sum() if len(sell_trades) > 0 else 0.0

                    # Print formatted summary
                    print(f"Total trades: {total_trades}")
                    print(f"Win rate: {win_rate:.1f}%")
                    print(f"Total P&L: {total_pnl:+.0f} points (${total_pnl_usd:,.0f})")
                    print(f"Average per trade: {avg_pnl_usd:+.2f} USD")
                    print(f"BUY trades: {len(buy_trades)} (${buy_pnl_usd:,.0f})")
                    print(f"SELL trades: {len(sell_trades)} (${sell_pnl_usd:,.0f})")
                    print(f"Trading record: {csv_file.name}")
                else:
                    print("\n[INFO] Wyckoff strategy executed but no trades were generated")
            else:
                print("\n[INFO] Wyckoff strategy not executed or no trading data available")

        # --- VWAP Band Reversal Strategy Summary ---
        from config import ENABLE_VWAP_BAND_REVERSAL_STRATEGY
        if ENABLE_VWAP_BAND_REVERSAL_STRATEGY:
            csv_file = trading_dir / f"tracking_record_vwap_band_reversal_{DATE}.csv"

            if csv_file.exists():
                df_trades = pd.read_csv(csv_file, sep=';', decimal=',')

                if len(df_trades) > 0:
                    print("\n" + "-"*70)
                    print("STRATEGY SUMMARY - VWAP BAND REVERSAL")
                    print("-"*70)

                    # Calculate statistics
                    total_trades = len(df_trades)
                    # profit_trades = df_trades[df_trades['exit_reason'].isin(['tp_exit', 'profit'])]

                    total_pnl = df_trades['pnl'].sum()
                    total_pnl_usd = df_trades['pnl_usd'].sum()
                    avg_pnl_usd = total_pnl_usd / total_trades if total_trades > 0 else 0

                    denom = len(df_trades[df_trades['pnl'] != 0])
                    win_rate = (len(df_trades[df_trades['pnl'] > 0]) / denom * 100) if denom > 0 else 0.0

                    buy_trades = df_trades[df_trades['direction'] == 'BUY']
                    sell_trades = df_trades[df_trades['direction'] == 'SELL']
                    buy_pnl_usd = buy_trades['pnl_usd'].sum() if len(buy_trades) > 0 else 0.0
                    sell_pnl_usd = sell_trades['pnl_usd'].sum() if len(sell_trades) > 0 else 0.0

                    # Print formatted summary
                    print(f"Total trades: {total_trades}")
                    print(f"Win rate: {win_rate:.1f}%")
                    print(f"Total P&L: {total_pnl:+.0f} points (${total_pnl_usd:,.0f})")
                    print(f"Average per trade: {avg_pnl_usd:+.2f} USD")
                    print(f"BUY trades: {len(buy_trades)} (${buy_pnl_usd:,.0f})")
                    print(f"SELL trades: {len(sell_trades)} (${sell_pnl_usd:,.0f})")
                    print(f"Trading record: {csv_file.name}")
                else:
                    print("\n[INFO] Band Reversal strategy executed but no trades were generated")
                print("\n[INFO] Band Reversal strategy not executed or no trading data available")
        
        # --- VWAP Score Strategy Summary ---
        from config import ENABLE_STRAT_VWAP_SCORE
        if ENABLE_STRAT_VWAP_SCORE:
            csv_file = trading_dir / f"tracking_record_vwap_score_{DATE}.csv"

            if csv_file.exists():
                df_trades = pd.read_csv(csv_file, sep=';', decimal=',')

                if len(df_trades) > 0:
                    print("\n" + "-"*70)
                    print("STRATEGY SUMMARY - VWAP SCORE (CLENOW)")
                    print("-"*70)

                    # Calculate statistics
                    total_trades = len(df_trades)
                    
                    total_pnl = df_trades['pnl_points'].sum() # Note: strat_vwap_score uses pnl_points
                    total_pnl_usd = df_trades['pnl_usd'].sum()
                    avg_pnl_usd = total_pnl_usd / total_trades if total_trades > 0 else 0

                    if 'pnl_points' in df_trades.columns:
                        denom = len(df_trades[df_trades['pnl_points'] != 0])
                        win_rate = (len(df_trades[df_trades['pnl_points'] > 0]) / denom * 100) if denom > 0 else 0.0
                    else:
                        win_rate = 0.0

                    buy_trades = df_trades[df_trades['direction'] == 'BUY']
                    sell_trades = df_trades[df_trades['direction'] == 'SELL']
                    buy_pnl_usd = buy_trades['pnl_usd'].sum() if len(buy_trades) > 0 else 0.0
                    sell_pnl_usd = sell_trades['pnl_usd'].sum() if len(sell_trades) > 0 else 0.0

                    # Print formatted summary
                    print(f"Total trades: {total_trades}")
                    print(f"Win rate: {win_rate:.1f}%")
                    print(f"Total P&L: {total_pnl:+.0f} points (${total_pnl_usd:,.0f})")
                    print(f"Average per trade: {avg_pnl_usd:+.2f} USD")
                    print(f"BUY trades: {len(buy_trades)} (${buy_pnl_usd:,.0f})")
                    print(f"SELL trades: {len(sell_trades)} (${sell_pnl_usd:,.0f})")
                    print(f"Trading record: {csv_file.name}")
                else:
                    print("\n[INFO] VWAP Score strategy executed but no trades were generated")
            else:
                print("\n[INFO] VWAP Score strategy not executed or no trading data available")

    except Exception as e:
        print(f"\n[WARN] Could not load strategy summary: {e}")

    print("="*70 + "\n")

    # ============================================================================
    # GENERATE HTML SUMMARY REPORT
    # ============================================================================
    print("\n" + "-"*70)
    print("GENERATING HTML SUMMARY REPORT")
    print("-"*70)

    try:
        from datetime import datetime

        # Generate HTML summary with all active strategies
        html_summary = generate_daily_summary_html(start_date, end_date)

        if html_summary:
            summary_file = OUTPUTS_DIR / "trading" / f"daily_summary_{start_date}.html"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(html_summary)

            print(f"[OK] HTML summary saved: {summary_file}")

            # Open in browser
            import webbrowser
            webbrowser.open(str(summary_file.resolve()))
            print(f"[INFO] Opening summary in browser...")
        else:
            print("[WARN] No HTML summary generated (no trades found)")

    except Exception as e:
        print(f"[ERROR] Failed to generate HTML summary: {e}")
        import traceback
        traceback.print_exc()

    print("="*70 + "\n")

    return {
        'start_date': start_date,
        'end_date': end_date,
        'fractals': fractals_result,
        'plot': plot_result
    }


def main_quant(dia: str):
    """
    DEPRECATED: Ejecuta el pipeline completo de análisis cuantitativo para un día
    Esta función se mantiene por compatibilidad pero se recomienda usar main_quant_range()

    Args:
        dia: Fecha en formato YYYY-MM-DD
    """
    print("\n[WARNING] Esta función está deprecada. Use main_quant_range() en su lugar.")
    return None


if __name__ == "__main__":
    print("\nIniciando análisis cuantitativo...\n")
    result = main_quant_range(START_DATE, END_DATE)

    if result:
        print("[OK] Análisis completado exitosamente\n")

        # Open the summary HTML file in the browser
        import webbrowser
        from config import ENABLE_VWAP_MOMENTUM_STRATEGY, ENABLE_VWAP_CROSSOVER_STRATEGY, DATE

        trading_dir = OUTPUTS_DIR / "trading"

        # Priority: Open Momentum summary if enabled, otherwise Crossover
        if ENABLE_VWAP_MOMENTUM_STRATEGY:
            summary_file = trading_dir / f"summary_vwap_momentum_{DATE}.html"
            if summary_file.exists():
                print(f"[INFO] Opening summary dashboard: {summary_file}")
                webbrowser.open(str(summary_file))
        elif ENABLE_VWAP_CROSSOVER_STRATEGY:
            summary_file = trading_dir / f"summary_vwap_crossover_{DATE}.html"
            if summary_file.exists():
                print(f"[INFO] Opening summary dashboard: {summary_file}")
                webbrowser.open(str(summary_file))
    else:
        print("[ERROR] El análisis finalizó con errores\n")

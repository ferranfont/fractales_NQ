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

    # 3. Generar gráfico (AFTER strategies so CSV files are available)
    print("\n" + "-"*70)
    print("PASO 3: GENERACIÓN DE GRÁFICO")
    print("-"*70)
    plot_result = plot_range_chart(
        fractals_result['df'],
        fractals_result['df_fractals_minor'],
        fractals_result['df_fractals_major'],
        start_date,
        end_date,
        symbol=fractals_result.get('symbol', 'NQ'),
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
                    profit_trades = df_trades[df_trades['exit_reason'] == 'profit']
                    stop_trades = df_trades[df_trades['exit_reason'] == 'stop']

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

    except Exception as e:
        print(f"\n[WARN] Could not load strategy summary: {e}")

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

"""
Optimización de tiempo en mercado para estrategia VWAP Momentum
Prueba diferentes duraciones de holding time para todas las señales de entrada
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from config import DATA_DIR, OUTPUTS_DIR, PRICE_EJECTION_TRIGGER, VWAP_FAST, POINT_VALUE
from calculate_vwap import calculate_vwap

# ============================================================================
# FUNCIÓN DE CARGA DE DATOS
# ============================================================================
def load_nq_data(start_date, end_date):
    """
    Carga datos NQ y los agrega a barras de 1 minuto

    Args:
        start_date: Fecha inicio YYYYMMDD
        end_date: Fecha fin YYYYMMDD

    Returns:
        df: DataFrame con barras OHLC de 1 minuto
    """
    file_path = DATA_DIR / f"time_and_sales_nq_{start_date}.csv"

    if not file_path.exists():
        return None

    # Leer datos de tick (columnas ya normalizadas: timestamp, price, volume)
    df_ticks = pd.read_csv(file_path, sep=';', decimal=',')

    # Convertir timestamp a datetime
    df_ticks['timestamp'] = pd.to_datetime(df_ticks['timestamp'])

    # Agregar a barras de 1 minuto
    df_ticks.set_index('timestamp', inplace=True)

    df = df_ticks.resample('1min').agg({
        'price': ['first', 'max', 'min', 'last'],
        'volume': 'sum'
    })

    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df = df.dropna()
    df.reset_index(inplace=True)

    return df

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
# Tiempos a probar (en minutos)
TIME_EXITS = [
    1,      # 1 minuto
    5,      # 5 minutos
    15,     # 15 minutos
    60,     # 1 hora
    120,    # 2 horas
    180,    # 3 horas
    240,    # 4 horas
    300,    # 5 horas
    360,    # 6 horas
    480,    # 8 horas
    'EOD'   # End of Day
]

# Horas de entrada para análisis segmentado (formato 24h)
ENTRY_HOURS = list(range(0, 24))  # De 0 a 23 horas

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    """
    Calcula el Sharpe Ratio

    Args:
        returns: Series o array de retornos
        risk_free_rate: Tasa libre de riesgo (default 0.0)

    Returns:
        float: Sharpe Ratio
    """
    if len(returns) == 0:
        return 0.0

    mean_return = returns.mean()
    std_return = returns.std()

    if std_return == 0 or pd.isna(std_return):
        return 0.0

    sharpe = (mean_return - risk_free_rate) / std_return
    return sharpe

def format_duration_label(duration):
    """
    Formatea la duración con equivalente en horas

    Args:
        duration: Duración en minutos o 'EOD'

    Returns:
        str: Label formateado (ej: "120min (2h)" o "EOD")
    """
    if duration == 'EOD':
        return 'EOD'

    hours = duration / 60
    if hours >= 1:
        if hours == int(hours):
            return f"{duration}min ({int(hours)}h)"
        else:
            return f"{duration}min ({hours:.1f}h)"
    else:
        return f"{duration}min"

def get_exit_time(entry_time, duration_minutes, eod_time):
    """
    Calcula el tiempo de salida según la duración

    Args:
        entry_time: Timestamp de entrada
        duration_minutes: Duración en minutos (o 'EOD')
        eod_time: Timestamp del final del día

    Returns:
        exit_time: Timestamp de salida
    """
    if duration_minutes == 'EOD':
        return eod_time

    exit_time = entry_time + timedelta(minutes=duration_minutes)

    # Si la salida es después del EOD, usar EOD
    if exit_time > eod_time:
        return eod_time

    return exit_time

def calculate_pnl_at_exit(df, entry_idx, exit_time, direction, entry_price):
    """
    Calcula P&L, MAE y MFE a la salida según el tiempo

    Args:
        df: DataFrame con datos OHLC
        entry_idx: Index de entrada
        exit_time: Timestamp de salida
        direction: 'BUY' o 'SELL'
        entry_price: Precio de entrada

    Returns:
        pnl: P&L en puntos
        exit_price: Precio de salida
        actual_exit_time: Timestamp real de salida
        mae: Maximum Adverse Excursion en puntos
        mfe: Maximum Favorable Excursion en puntos
    """
    # Buscar la barra más cercana al exit_time
    exit_bars = df[df['timestamp'] >= exit_time]

    if exit_bars.empty:
        # No hay barra de salida disponible (fuera de horario)
        return None, None, None, None, None

    exit_bar = exit_bars.iloc[0]
    exit_price = exit_bar['close']
    actual_exit_time = exit_bar['timestamp']

    # Obtener todas las barras durante el trade
    entry_time = df.loc[entry_idx, 'timestamp']
    trade_bars = df[(df['timestamp'] >= entry_time) & (df['timestamp'] <= actual_exit_time)]

    # Calcular MAE y MFE
    if direction == 'BUY':
        # Para LONG: MFE = máxima ganancia no realizada, MAE = máxima pérdida no realizada
        mfe = (trade_bars['high'].max() - entry_price)  # Mejor momento
        mae = (trade_bars['low'].min() - entry_price)   # Peor momento (negativo)
        pnl = exit_price - entry_price
    else:  # SELL
        # Para SHORT: MFE = máxima ganancia no realizada, MAE = máxima pérdida no realizada
        mfe = (entry_price - trade_bars['low'].min())   # Mejor momento
        mae = (entry_price - trade_bars['high'].max())  # Peor momento (negativo)
        pnl = entry_price - exit_price

    return pnl, exit_price, actual_exit_time, mae, mfe

def detect_entry_signals(df):
    """
    Detecta señales de entrada por price ejection (puntos verdes)

    Args:
        df: DataFrame con datos OHLC y VWAP

    Returns:
        df_signals: DataFrame con señales de entrada
    """
    # Calcular distancia precio-VWAP
    df['price_vwap_distance'] = abs((df['close'] - df['vwap_fast']) / df['vwap_fast'])

    # Detectar price ejection
    df['is_ejection'] = df['price_vwap_distance'] >= PRICE_EJECTION_TRIGGER

    # Determinar dirección
    df['direction'] = np.where(df['close'] > df['vwap_fast'], 'BUY', 'SELL')

    # Filtrar solo señales de ejection
    df_signals = df[df['is_ejection']].copy()

    return df_signals

def optimize_single_day(date_str):
    """
    Optimiza tiempos de salida para un día específico

    Args:
        date_str: Fecha en formato YYYYMMDD

    Returns:
        results: Lista de resultados por cada combinación de tiempo
    """
    print(f"\n[INFO] Procesando {date_str}...")

    # Cargar datos
    df = load_nq_data(date_str, date_str)

    if df is None or df.empty:
        print(f"[WARN] No hay datos para {date_str}")
        return []

    # Calcular VWAP
    df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)

    # Detectar señales de entrada
    df_signals = detect_entry_signals(df)

    if df_signals.empty:
        print(f"[WARN] No hay señales de entrada para {date_str}")
        return []

    print(f"[INFO] Señales detectadas: {len(df_signals)}")

    # EOD time (última barra del día)
    eod_time = df['timestamp'].max()

    results = []

    # Probar cada duración de tiempo
    for duration in TIME_EXITS:
        duration_label = format_duration_label(duration)

        trades = []

        # Para cada señal de entrada
        for idx, signal in df_signals.iterrows():
            entry_time = signal['timestamp']
            entry_price = signal['close']
            direction = signal['direction']
            entry_hour = entry_time.hour

            # Calcular tiempo de salida
            if duration == 'EOD':
                exit_time = eod_time
                duration_minutes = (eod_time - entry_time).total_seconds() / 60
            else:
                exit_time = get_exit_time(entry_time, duration, eod_time)
                duration_minutes = duration

            # Calcular P&L, MAE y MFE
            pnl, exit_price, actual_exit_time, mae, mfe = calculate_pnl_at_exit(
                df, idx, exit_time, direction, entry_price
            )

            if pnl is None:
                continue

            pnl_usd = pnl * POINT_VALUE
            mae_usd = mae * POINT_VALUE
            mfe_usd = mfe * POINT_VALUE

            trades.append({
                'date': date_str,
                'entry_time': entry_time,
                'exit_time': actual_exit_time,
                'entry_hour': entry_hour,
                'direction': direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'pnl_usd': pnl_usd,
                'mae': mae,
                'mae_usd': mae_usd,
                'mfe': mfe,
                'mfe_usd': mfe_usd,
                'duration_minutes': duration_minutes,
                'duration_label': duration_label
            })

        if trades:
            df_trades = pd.DataFrame(trades)

            # Estadísticas globales para esta duración
            total_trades = len(df_trades)
            total_pnl = df_trades['pnl_usd'].sum()
            avg_pnl = df_trades['pnl_usd'].mean()
            win_rate = (df_trades['pnl'] > 0).sum() / total_trades * 100

            # Calcular avg_win y avg_loss
            winning_trades = df_trades[df_trades['pnl'] > 0]
            losing_trades = df_trades[df_trades['pnl'] <= 0]

            avg_win = winning_trades['pnl_usd'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['pnl_usd'].mean() if len(losing_trades) > 0 else 0

            max_win = df_trades['pnl_usd'].max()
            max_loss = df_trades['pnl_usd'].min()

            # Calcular estadísticas MAE/MFE
            avg_mae = df_trades['mae_usd'].mean()
            avg_mfe = df_trades['mfe_usd'].mean()
            max_mae = df_trades['mae_usd'].min()  # Más negativo = peor drawdown
            max_mfe = df_trades['mfe_usd'].max()  # Más positivo = mejor unrealized profit

            # Calcular Sharpe Ratio
            sharpe_ratio = calculate_sharpe_ratio(df_trades['pnl_usd'])

            results.append({
                'date': date_str,
                'duration_label': duration_label,
                'duration_minutes': duration if duration != 'EOD' else None,
                'total_trades': total_trades,
                'total_pnl_usd': total_pnl,
                'avg_pnl_usd': avg_pnl,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'max_win': max_win,
                'max_loss': max_loss,
                'avg_mae': avg_mae,
                'avg_mfe': avg_mfe,
                'max_mae': max_mae,
                'max_mfe': max_mfe,
                'sharpe_ratio': sharpe_ratio,
                'trades': df_trades
            })

            print(f"  [{duration_label:>6}] Trades: {total_trades:3d} | P&L: ${total_pnl:>8.0f} | Avg: ${avg_pnl:>6.0f} | WR: {win_rate:5.1f}%")

    return results

def optimize_by_entry_hour(date_str):
    """
    Optimiza tiempos de salida segmentado por hora de entrada

    Args:
        date_str: Fecha en formato YYYYMMDD

    Returns:
        results_by_hour: Resultados organizados por hora de entrada
    """
    print(f"\n[INFO] Analizando por hora de entrada: {date_str}...")

    # Cargar datos
    df = load_nq_data(date_str, date_str)

    if df is None or df.empty:
        return {}

    # Calcular VWAP
    df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)

    # Detectar señales
    df_signals = detect_entry_signals(df)

    if df_signals.empty:
        return {}

    # EOD time
    eod_time = df['timestamp'].max()

    results_by_hour = {}

    # Para cada hora de entrada
    for entry_hour in ENTRY_HOURS:
        # Filtrar señales de esa hora
        hour_signals = df_signals[df_signals['timestamp'].dt.hour == entry_hour]

        if hour_signals.empty:
            continue

        print(f"\n  Hora {entry_hour:02d}:00 - {len(hour_signals)} señales")

        hour_results = []

        # Probar cada duración
        for duration in TIME_EXITS:
            duration_label = format_duration_label(duration)

            trades = []

            for idx, signal in hour_signals.iterrows():
                entry_time = signal['timestamp']
                entry_price = signal['close']
                direction = signal['direction']

                # Calcular tiempo de salida
                if duration == 'EOD':
                    exit_time = eod_time
                else:
                    exit_time = get_exit_time(entry_time, duration, eod_time)
                    # Si la salida es después del EOD, skip
                    if exit_time > eod_time:
                        continue

                # Calcular P&L, MAE y MFE
                pnl, exit_price, actual_exit_time, mae, mfe = calculate_pnl_at_exit(
                    df, idx, exit_time, direction, entry_price
                )

                if pnl is None:
                    continue

                pnl_usd = pnl * POINT_VALUE
                mae_usd = mae * POINT_VALUE
                mfe_usd = mfe * POINT_VALUE

                trades.append({
                    'pnl_usd': pnl_usd,
                    'pnl': pnl,
                    'mae_usd': mae_usd,
                    'mfe_usd': mfe_usd
                })

            if trades:
                df_trades = pd.DataFrame(trades)

                total_trades = len(df_trades)
                total_pnl = df_trades['pnl_usd'].sum()
                avg_pnl = df_trades['pnl_usd'].mean()
                win_rate = (df_trades['pnl'] > 0).sum() / total_trades * 100

                # Calcular estadísticas adicionales
                winning_trades = df_trades[df_trades['pnl'] > 0]
                losing_trades = df_trades[df_trades['pnl'] <= 0]

                avg_win = winning_trades['pnl_usd'].mean() if len(winning_trades) > 0 else 0
                avg_loss = losing_trades['pnl_usd'].mean() if len(losing_trades) > 0 else 0
                avg_mae = df_trades['mae_usd'].mean()
                avg_mfe = df_trades['mfe_usd'].mean()
                sharpe_ratio = calculate_sharpe_ratio(df_trades['pnl_usd'])

                hour_results.append({
                    'entry_hour': entry_hour,
                    'duration_label': duration_label,
                    'total_trades': total_trades,
                    'total_pnl_usd': total_pnl,
                    'avg_pnl_usd': avg_pnl,
                    'win_rate': win_rate,
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    'avg_mae': avg_mae,
                    'avg_mfe': avg_mfe,
                    'sharpe_ratio': sharpe_ratio
                })

                print(f"    [{duration_label:>6}] Trades: {total_trades:2d} | Avg: ${avg_pnl:>6.0f} | WR: {win_rate:5.1f}%")

        if hour_results:
            results_by_hour[entry_hour] = hour_results

    return results_by_hour

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("OPTIMIZACIÓN DE TIEMPO EN MERCADO - VWAP MOMENTUM STRATEGY")
    print("=" * 80)

    # Obtener todos los archivos de datos disponibles
    data_files = sorted(DATA_DIR.glob("time_and_sales_nq_*.csv"))

    if not data_files:
        print("[ERROR] No se encontraron archivos de datos")
        exit(1)

    dates = [f.stem.replace("time_and_sales_nq_", "") for f in data_files]

    print(f"\n[INFO] Archivos encontrados: {len(dates)}")
    print(f"[INFO] Rango: {dates[0]} -> {dates[-1]}")

    # ========================================================================
    # PARTE 1: Optimización global por duración
    # ========================================================================
    print("\n" + "=" * 80)
    print("PARTE 1: OPTIMIZACIÓN GLOBAL POR DURACIÓN")
    print("=" * 80)

    all_results = []

    for date_str in dates:
        try:
            results = optimize_single_day(date_str)
            all_results.extend(results)
        except Exception as e:
            print(f"[ERROR] Error procesando {date_str}: {str(e)}")
            continue

    if all_results:
        # Consolidar resultados por duración
        df_all = pd.DataFrame(all_results)

        print("\n" + "=" * 80)
        print("RESUMEN GLOBAL POR DURACIÓN")
        print("=" * 80)

        summary_by_duration = df_all.groupby('duration_label').agg({
            'total_trades': 'sum',
            'total_pnl_usd': 'sum',
            'avg_pnl_usd': 'mean',
            'win_rate': 'mean',
            'avg_win': 'mean',
            'avg_loss': 'mean',
            'max_win': 'max',
            'max_loss': 'min',
            'avg_mae': 'mean',
            'avg_mfe': 'mean',
            'max_mae': 'min',
            'max_mfe': 'max',
            'sharpe_ratio': 'mean'
        }).round(2)

        # Calcular ratio recompensa/riesgo (avg_win / |avg_loss|)
        summary_by_duration['rr_ratio'] = (
            summary_by_duration['avg_win'] / abs(summary_by_duration['avg_loss'])
        ).round(1)

        # Formato 1:X.X
        summary_by_duration['rr_ratio_formatted'] = summary_by_duration['rr_ratio'].apply(
            lambda x: f"1:{x:.1f}" if not pd.isna(x) and x != float('inf') else "N/A"
        )

        # Ordenar por Total P&L descendente
        summary_by_duration = summary_by_duration.sort_values('total_pnl_usd', ascending=False)

        print(summary_by_duration)

        # Guardar resumen
        output_dir = OUTPUTS_DIR / "optimization"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Guardar CSV
        summary_path = output_dir / "time_in_market_optimization.csv"
        summary_by_duration.to_csv(summary_path, sep=';', decimal=',')
        print(f"\n[OK] Resumen CSV guardado en: {summary_path}")

        # Guardar HTML
        html_path = output_dir / "time_in_market_optimization.html"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Time Optimization Summary</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
        }}
        .summary-box {{
            background: white;
            padding: 20px;
            margin: 20px auto;
            max-width: 1200px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: right;
            font-weight: bold;
        }}
        th:first-child {{
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
            text-align: right;
        }}
        td:first-child {{
            text-align: left;
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
        .best-row {{
            background-color: #d5f4e6 !important;
            font-weight: bold;
        }}
        .metric-card {{
            display: inline-block;
            background: #ecf0f1;
            padding: 15px;
            margin: 10px;
            border-radius: 5px;
            min-width: 200px;
        }}
        .metric-label {{
            font-size: 12px;
            color: #7f8c8d;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
    </style>
</head>
<body>
    <h1>⏱️ TIME IN MARKET OPTIMIZATION SUMMARY</h1>

    <div class="summary-box">
        <h2>🎯 Best Duration</h2>
"""

        # Encontrar mejor duración
        best_duration = summary_by_duration['total_pnl_usd'].idxmax()
        best_pnl = summary_by_duration.loc[best_duration, 'total_pnl_usd']
        best_avg = summary_by_duration.loc[best_duration, 'avg_pnl_usd']
        best_wr = summary_by_duration.loc[best_duration, 'win_rate']
        best_trades = summary_by_duration.loc[best_duration, 'total_trades']
        best_avg_win = summary_by_duration.loc[best_duration, 'avg_win']
        best_avg_loss = summary_by_duration.loc[best_duration, 'avg_loss']
        best_rr = summary_by_duration.loc[best_duration, 'rr_ratio_formatted']
        best_sharpe = summary_by_duration.loc[best_duration, 'sharpe_ratio']

        # Contar días analizados
        total_days = len(dates)

        html_content += f"""
        <div class="metric-card">
            <div class="metric-label">Duration</div>
            <div class="metric-value">{best_duration}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total P&L</div>
            <div class="metric-value positive">${best_pnl:,.0f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg P&L</div>
            <div class="metric-value">${best_avg:,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Win Rate</div>
            <div class="metric-value">{best_wr:.1f}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Trades</div>
            <div class="metric-value">{int(best_trades):,}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Days Analyzed</div>
            <div class="metric-value">{total_days}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg Win</div>
            <div class="metric-value positive">${best_avg_win:,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg Loss</div>
            <div class="metric-value negative">${best_avg_loss:,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Risk/Reward</div>
            <div class="metric-value">{best_rr}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Sharpe Ratio</div>
            <div class="metric-value">{best_sharpe:.2f}</div>
        </div>
    </div>

    <div class="summary-box">
        <h2>📊 All Durations Summary</h2>
        <table>
            <thead>
                <tr>
                    <th>Duration</th>
                    <th>Total Trades</th>
                    <th>Total P&L (USD)</th>
                    <th>Avg P&L (USD)</th>
                    <th>Win Rate (%)</th>
                    <th>Avg Win (USD)</th>
                    <th>Avg Loss (USD)</th>
                    <th>Risk/Reward</th>
                    <th>Sharpe Ratio</th>
                    <th>Avg MAE (USD)</th>
                    <th>Avg MFE (USD)</th>
                    <th>Max Win (USD)</th>
                    <th>Max Loss (USD)</th>
                </tr>
            </thead>
            <tbody>
"""

        for idx, row in summary_by_duration.iterrows():
            row_class = 'best-row' if idx == best_duration else ''
            pnl_class = 'positive' if row['total_pnl_usd'] > 0 else 'negative'

            mae_class = 'negative' if row['avg_mae'] < 0 else ''
            mfe_class = 'positive' if row['avg_mfe'] > 0 else ''
            sharpe_class = 'positive' if row['sharpe_ratio'] > 0 else 'negative'

            html_content += f"""
                <tr class="{row_class}">
                    <td>{idx}</td>
                    <td>{int(row['total_trades']):,}</td>
                    <td class="{pnl_class}">${row['total_pnl_usd']:,.0f}</td>
                    <td>${row['avg_pnl_usd']:,.2f}</td>
                    <td>{row['win_rate']:.1f}%</td>
                    <td class="positive">${row['avg_win']:,.2f}</td>
                    <td class="negative">${row['avg_loss']:,.2f}</td>
                    <td>{row['rr_ratio_formatted']}</td>
                    <td class="{sharpe_class}">{row['sharpe_ratio']:.2f}</td>
                    <td class="{mae_class}">${row['avg_mae']:,.2f}</td>
                    <td class="{mfe_class}">${row['avg_mfe']:,.2f}</td>
                    <td class="positive">${row['max_win']:,.0f}</td>
                    <td class="negative">${row['max_loss']:,.0f}</td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>
    </div>

    <div class="summary-box">
        <h3>📝 Notes</h3>
        <ul>
            <li>Analysis based on all entry signals (green dots) generated by Price Ejection trigger</li>
            <li>No stop loss or take profit applied - pure time-based exits</li>
            <li>EOD = Exit at end of day (last bar)</li>
            <li>Risk/Reward = Avg Win / |Avg Loss|</li>
            <li>MAE = Maximum Adverse Excursion (worst unrealized drawdown during trade)</li>
            <li>MFE = Maximum Favorable Excursion (best unrealized profit during trade)</li>
            <li>Sharpe Ratio = Mean return / Standard deviation of returns</li>
            <li>Table sorted by Total P&L (descending) - best durations appear first</li>
        </ul>
    </div>
"""

        # Marcar donde insertar tablas por hora (se hará después)
        hourly_tables_placeholder = "<!-- HOURLY_TABLES_PLACEHOLDER -->"
        html_content += hourly_tables_placeholder

        html_content += """
</body>
</html>
"""

        # Guardar HTML temporal sin tablas por hora
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"[OK] Resumen HTML guardado en: {html_path}")

        print("\n" + "=" * 80)
        print(f"MEJOR DURACIÓN: {best_duration}")
        print(f"  Total P&L: ${best_pnl:,.0f}")
        print(f"  Avg P&L: ${best_avg:,.2f}")
        print(f"  Win Rate: {best_wr:.1f}%")
        print(f"  Avg Win: ${best_avg_win:,.2f}")
        print(f"  Avg Loss: ${best_avg_loss:,.2f}")
        print(f"  Risk/Reward: {best_rr}")
        print("=" * 80)

    # ========================================================================
    # PARTE 2: Optimización segmentada por hora de entrada
    # ========================================================================
    print("\n" + "=" * 80)
    print("PARTE 2: OPTIMIZACIÓN SEGMENTADA POR HORA DE ENTRADA")
    print("=" * 80)

    all_hour_results = []

    for date_str in dates:  # Procesar TODOS los días
        hour_results = optimize_by_entry_hour(date_str)

        for hour, results in hour_results.items():
            all_hour_results.extend(results)

    if all_hour_results:
        df_hours = pd.DataFrame(all_hour_results)

        # Consolidar por hora y duración
        summary_by_hour = df_hours.groupby(['entry_hour', 'duration_label']).agg({
            'total_trades': 'sum',
            'total_pnl_usd': 'sum',
            'avg_pnl_usd': 'mean',
            'win_rate': 'mean',
            'avg_win': 'mean',
            'avg_loss': 'mean',
            'avg_mae': 'mean',
            'avg_mfe': 'mean',
            'sharpe_ratio': 'mean'
        }).round(2)

        print("\n" + "=" * 80)
        print("RESUMEN POR HORA DE ENTRADA Y DURACIÓN")
        print("=" * 80)
        print(summary_by_hour.head(20))

        # Guardar CSV
        hour_summary_path = output_dir / "time_in_market_by_hour.csv"
        summary_by_hour.to_csv(hour_summary_path, sep=';', decimal=',')
        print(f"\n[OK] Resumen por hora guardado en: {hour_summary_path}")

        # ====================================================================
        # GENERAR TABLAS HTML POR HORA
        # ====================================================================

        # Crear tabla resumen de mejor duración por hora
        best_per_hour = []
        for hour in range(24):
            hour_data = summary_by_hour.loc[hour] if hour in summary_by_hour.index.get_level_values(0) else None
            if hour_data is not None and not hour_data.empty:
                best_idx = hour_data['total_pnl_usd'].idxmax()
                best_per_hour.append({
                    'entry_hour': hour,
                    'best_duration': best_idx,
                    'total_pnl_usd': hour_data.loc[best_idx, 'total_pnl_usd'],
                    'total_trades': hour_data.loc[best_idx, 'total_trades'],
                    'win_rate': hour_data.loc[best_idx, 'win_rate'],
                    'sharpe_ratio': hour_data.loc[best_idx, 'sharpe_ratio']
                })

        df_best_per_hour = pd.DataFrame(best_per_hour)

        # Generar HTML con tablas por hora
        hourly_html = """
    <div class="summary-box">
        <h2>⏰ BEST DURATION BY ENTRY HOUR</h2>
        <p>Summary of optimal holding duration for each hour of entry</p>
        <table>
            <thead>
                <tr>
                    <th>Entry Hour</th>
                    <th>Best Duration</th>
                    <th>Total Trades</th>
                    <th>Total P&L (USD)</th>
                    <th>Win Rate (%)</th>
                    <th>Sharpe Ratio</th>
                </tr>
            </thead>
            <tbody>
"""

        for _, row in df_best_per_hour.iterrows():
            pnl_class = 'positive' if row['total_pnl_usd'] > 0 else 'negative'
            sharpe_class = 'positive' if row['sharpe_ratio'] > 0 else 'negative'

            hourly_html += f"""
                <tr>
                    <td>{int(row['entry_hour']):02d}:00</td>
                    <td>{row['best_duration']}</td>
                    <td>{int(row['total_trades']):,}</td>
                    <td class="{pnl_class}">${row['total_pnl_usd']:,.0f}</td>
                    <td>{row['win_rate']:.1f}%</td>
                    <td class="{sharpe_class}">{row['sharpe_ratio']:.2f}</td>
                </tr>
"""

        hourly_html += """
            </tbody>
        </table>
    </div>
"""

        # Generar tablas detalladas por cada hora
        for hour in range(24):
            hour_data = summary_by_hour.loc[hour] if hour in summary_by_hour.index.get_level_values(0) else None

            if hour_data is not None and not hour_data.empty:
                # Ordenar por Total P&L
                hour_data_sorted = hour_data.sort_values('total_pnl_usd', ascending=False)

                hourly_html += f"""
    <div class="summary-box">
        <h3>🕐 Entry Hour: {hour:02d}:00</h3>
        <table>
            <thead>
                <tr>
                    <th>Duration</th>
                    <th>Total Trades</th>
                    <th>Total P&L (USD)</th>
                    <th>Avg P&L (USD)</th>
                    <th>Win Rate (%)</th>
                    <th>Avg Win (USD)</th>
                    <th>Avg Loss (USD)</th>
                    <th>Sharpe Ratio</th>
                    <th>Avg MAE (USD)</th>
                    <th>Avg MFE (USD)</th>
                </tr>
            </thead>
            <tbody>
"""

                for duration_label, row in hour_data_sorted.iterrows():
                    pnl_class = 'positive' if row['total_pnl_usd'] > 0 else 'negative'
                    sharpe_class = 'positive' if row['sharpe_ratio'] > 0 else 'negative'
                    mae_class = 'negative' if row['avg_mae'] < 0 else ''
                    mfe_class = 'positive' if row['avg_mfe'] > 0 else ''

                    hourly_html += f"""
                <tr>
                    <td>{duration_label}</td>
                    <td>{int(row['total_trades']):,}</td>
                    <td class="{pnl_class}">${row['total_pnl_usd']:,.0f}</td>
                    <td>${row['avg_pnl_usd']:,.2f}</td>
                    <td>{row['win_rate']:.1f}%</td>
                    <td class="positive">${row['avg_win']:,.2f}</td>
                    <td class="negative">${row['avg_loss']:,.2f}</td>
                    <td class="{sharpe_class}">{row['sharpe_ratio']:.2f}</td>
                    <td class="{mae_class}">${row['avg_mae']:,.2f}</td>
                    <td class="{mfe_class}">${row['avg_mfe']:,.2f}</td>
                </tr>
"""

                hourly_html += """
            </tbody>
        </table>
    </div>
"""

        # Actualizar HTML insertando las tablas por hora
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content_full = f.read()

        html_content_full = html_content_full.replace(hourly_tables_placeholder, hourly_html)

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content_full)

        print(f"[OK] HTML actualizado con tablas por hora: {html_path}")

    print("\n[SUCCESS] Optimización completada!")

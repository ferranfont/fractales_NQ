import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from pathlib import Path
from datetime import datetime
from config import (
    START_DATE, END_DATE, FRACTALS_DIR, CHARTS_DIR,
    PLOT_MINOR_FRACTALS, PLOT_MAJOR_FRACTALS, PLOT_MINOR_DOTS, PLOT_MAJOR_DOTS,
    SHOW_FREQUENCY_INDICATOR, PLOT_VWAP, SHOW_FAST_VWAP, SHOW_SLOW_VWAP,
    VWAP_FAST, VWAP_SLOW, SHOW_REGRESSION_CHANNEL,
    PRICE_EJECTION_TRIGGER, OVER_PRICE_EJECTION_TRIGGER, OUTPUTS_DIR,
    VWAP_SLOPE_DEGREE_WINDOW, SHOW_SUBPLOT_VWAP_SLOPE_INDICATOR,
    VWAP_SLOPE_INDICATOR_HIGH_VALUE, VWAP_SLOPE_INDICATOR_LOW_VALUE,
    SHOW_VWAP_INDICATOR_CROSSOVER,
    # Strategy parameters for title
    USE_TIME_IN_MARKET, TIME_IN_MARKET_MINUTES, USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE,
    USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET, MAX_SL_ALLOWED_IN_TIME_IN_MARKET,
    USE_TP_ALLOWED_IN_TIME_IN_MARKET, TP_IN_TIME_IN_MARKET,
    VWAP_MOMENTUM_TP_POINTS, VWAP_MOMENTUM_SL_POINTS,
    VWAP_MOMENTUM_LONG_ALLOWED, VWAP_MOMENTUM_SHORT_ALLOWED,
    USE_VWAP_SLOW_TREND_FILTER
)
from calculate_vwap import calculate_vwap
import numpy as np

# ============================================================================
# STRATEGY INFO STRING (for chart titles)
# ============================================================================
def get_strategy_info_compact():
    """Returns a compact string with current strategy configuration"""
    if USE_TIME_IN_MARKET:
        if USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE:
            exit_mode = "Time-Exit (JSON)"
        else:
            time_label = "EOD" if TIME_IN_MARKET_MINUTES >= 9999 else f"{TIME_IN_MARKET_MINUTES}min"
            exit_mode = f"Time-Exit ({time_label})"

        # TP info
        if USE_TP_ALLOWED_IN_TIME_IN_MARKET:
            tp_info = f"| TP:{TP_IN_TIME_IN_MARKET}pts"
        else:
            tp_info = ""

        # SL info
        if USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET:
            sl_info = f"| SL:{MAX_SL_ALLOWED_IN_TIME_IN_MARKET}pts"
        else:
            sl_info = ""
    else:
        exit_mode = f"TP/SL ({VWAP_MOMENTUM_TP_POINTS}/{VWAP_MOMENTUM_SL_POINTS}pts)"
        tp_info = ""
        sl_info = ""

    # Direction filter info
    if VWAP_MOMENTUM_LONG_ALLOWED and VWAP_MOMENTUM_SHORT_ALLOWED:
        direction_info = ""
    elif VWAP_MOMENTUM_SHORT_ALLOWED:
        direction_info = "| SHORT-ONLY"
    elif VWAP_MOMENTUM_LONG_ALLOWED:
        direction_info = "| LONG-ONLY"
    else:
        direction_info = "| NO TRADES"

    # Trend filter info
    if USE_VWAP_SLOW_TREND_FILTER:
        trend_info = f"| TREND-FILTER (VWAP{VWAP_SLOW})"
    else:
        trend_info = ""

    return f"VWAP Momentum | {exit_mode} {tp_info} {sl_info} {direction_info} {trend_info}"

def calculate_vwap_slope_at_bar(df, bar_idx, window=10):
    """
    Calculate VWAP slope at a specific bar using linear regression over window bars.

    Args:
        df: DataFrame with 'vwap_fast' column
        bar_idx: Index of the current bar
        window: Number of bars to look back for slope calculation

    Returns:
        slope: VWAP slope (points per bar), 0 if insufficient data
    """
    # Get the position in the dataframe
    bar_position = df.index.get_loc(bar_idx)

    # Need at least window bars
    if bar_position < window - 1:
        return 0.0

    # Get last 'window' bars including current bar
    start_pos = bar_position - window + 1
    end_pos = bar_position + 1

    vwap_window = df.iloc[start_pos:end_pos]['vwap_fast'].values

    # Check for NaN values
    if pd.isna(vwap_window).any():
        return 0.0

    # Simple linear regression: slope = (y2 - y1) / (x2 - x1)
    # Using first and last point for simplicity
    slope = (vwap_window[-1] - vwap_window[0]) / (window - 1)

    return slope

def plot_range_chart(df, df_fractals_minor, df_fractals_major, start_date, end_date, symbol='NQ', rsi_levels=None, fibo_levels=None, divergences=None, channel_params=None, df_metrics=None, df_trades=None):
    """
    Crea un gráfico con línea de precio y fractales ZigZag para un rango de fechas.

    Args:
        df: DataFrame con datos OHLC
        df_fractals_minor: DataFrame con fractales MINOR
        df_fractals_major: DataFrame con fractales MAJOR
        start_date: Fecha inicial en formato YYYY-MM-DD
        end_date: Fecha final en formato YYYY-MM-DD
        rsi_levels: No usado (compatibilidad)
        fibo_levels: No usado (compatibilidad)
        divergences: No usado (compatibilidad)
        channel_params: Parámetros del canal de regresión
        df_metrics: DataFrame con métricas de consolidación (opcional)

    Returns:
        dict con información del gráfico generado o None si hay error
    """
    if start_date == end_date:
        print(f"Generando gráfico para fecha: {start_date}")
    else:
        print(f"Generando gráfico para rango: {start_date} -> {end_date}")
    print(f"Datos cargados: {len(df)} registros")

    # Crear índice numérico para evitar huecos de fines de semana
    df = df.reset_index(drop=True)
    df['index'] = df.index
    # Asegurar que 'timestamp' sea tipo datetime (necesario para mapear fractales y trades)
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Configurar subplots según los indicadores habilitados
    has_metrics = df_metrics is not None and not df_metrics.empty
    show_frequency_subplot = has_metrics and SHOW_FREQUENCY_INDICATOR
    show_slope_subplot = SHOW_SUBPLOT_VWAP_SLOPE_INDICATOR

    if show_frequency_subplot and show_slope_subplot:
        # Crear figura con 3 subplots: Price, Slope, Frequency
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.6, 0.2, 0.2]
        )
        price_row = 1
        slope_row = 2
        metrics_row = 3
    elif show_slope_subplot:
        # Crear figura con 2 subplots: Price y Slope
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.75, 0.25]
        )
        price_row = 1
        slope_row = 2
        metrics_row = None
    elif show_frequency_subplot:
        # Crear figura con 2 subplots: Price y Frequency
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.75, 0.25]
        )
        price_row = 1
        slope_row = None
        metrics_row = 2
    else:
        # Crear figura con 1 solo subplot: Price
        fig = make_subplots(
            rows=1, cols=1,
            shared_xaxes=True
        )
        price_row = 1
        slope_row = None
        metrics_row = None

    # Añadir línea de precio original
    trace_price = go.Scatter(
        x=df['index'],
        y=df['close'],
        mode='lines',
        name='Price',
        line=dict(color='gray', width=0.5),
        opacity=0.5,
        hoverinfo='skip'
    )
    fig.add_trace(trace_price, row=price_row, col=1)

    # Añadir indicador VWAP
    if PLOT_VWAP:
        # VWAP Rápido (Fast - Magenta)
        df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)
        df_vwap_fast = df[df['vwap_fast'].notna()].copy()

        if SHOW_FAST_VWAP and not df_vwap_fast.empty:
            trace_vwap_fast = go.Scatter(
                x=df_vwap_fast['index'],
                y=df_vwap_fast['vwap_fast'],
                mode='lines',
                name=f'VWAP Fast({VWAP_FAST})',
                line=dict(color='magenta', width=1.5),
                opacity=0.8,
                hovertemplate='<b>VWAP Fast</b>: %{y:.2f}<extra></extra>'
            )
            fig.add_trace(trace_vwap_fast, row=price_row, col=1)

            print(f"[INFO] VWAP Fast({VWAP_FAST}) añadido al gráfico: {len(df_vwap_fast)} puntos válidos")

        # Calculate VWAP Slope for all bars (in absolute value) only if slope subplot is enabled
        # Note: For visualization, we apply a minimum value to avoid very small values in log scale
        if show_slope_subplot:
            # If vwap_slope already exists (from strategy), use it; otherwise calculate it
            if 'vwap_slope' not in df.columns:
                df['vwap_slope'] = [abs(calculate_vwap_slope_at_bar(df, idx, window=VWAP_SLOPE_DEGREE_WINDOW)) for idx in df.index]

            # Create a copy for plotting with minimum value for log scale visualization
            min_slope = 0.002
            df_vwap_slope = df[df['vwap_slope'].notna()].copy()
            df_vwap_slope['vwap_slope_plot'] = df_vwap_slope['vwap_slope'].apply(lambda x: max(x, min_slope))

            if not df_vwap_slope.empty:
                # Add horizontal solid line at low threshold
                trace_slope_threshold_low = go.Scatter(
                    x=[df['index'].min(), df['index'].max()],
                    y=[VWAP_SLOPE_INDICATOR_LOW_VALUE, VWAP_SLOPE_INDICATOR_LOW_VALUE],
                    mode='lines',
                    name=f'Threshold {VWAP_SLOPE_INDICATOR_LOW_VALUE}',
                    line=dict(color='orange', width=1),
                    opacity=0.5,
                    showlegend=False,
                    hoverinfo='skip'
                )
                fig.add_trace(trace_slope_threshold_low, row=slope_row, col=1)

                # Add VWAP Slope trace (sin fill) using the plot version with minimum
                trace_vwap_slope = go.Scatter(
                    x=df_vwap_slope['index'],
                    y=df_vwap_slope['vwap_slope_plot'],
                    mode='lines',
                    name=f'|VWAP Slope| (W={VWAP_SLOPE_DEGREE_WINDOW})',
                    line=dict(color='orange', width=1.5),
                    opacity=0.7,
                    hovertemplate='<b>|VWAP Slope|</b>: %{y:.4f}<extra></extra>'
                )
                fig.add_trace(trace_vwap_slope, row=slope_row, col=1)

                # Add horizontal solid line at high threshold (PRIMERO antes del fill)
                trace_slope_threshold_high = go.Scatter(
                    x=[df['index'].min(), df['index'].max()],
                    y=[VWAP_SLOPE_INDICATOR_HIGH_VALUE, VWAP_SLOPE_INDICATOR_HIGH_VALUE],
                    mode='lines',
                    name=f'Threshold {VWAP_SLOPE_INDICATOR_HIGH_VALUE}',
                    line=dict(color='orange', width=1),
                    opacity=0.5,
                    showlegend=False,
                    hoverinfo='skip'
                )
                fig.add_trace(trace_slope_threshold_high, row=slope_row, col=1)

                # Crear área de fill SOLO cuando vwap_slope > high threshold
                # Identificar segmentos continuos donde slope > 0.6
                above_threshold = df_vwap_slope['vwap_slope_plot'] > VWAP_SLOPE_INDICATOR_HIGH_VALUE

                # Encontrar los grupos de valores consecutivos que están por encima del threshold
                groups = (above_threshold != above_threshold.shift()).cumsum()

                # Iterar sobre cada grupo continuo que está por encima del threshold
                for group_id in groups[above_threshold].unique():
                    segment = df_vwap_slope[groups == group_id]

                    if len(segment) > 0:
                        # Crear x e y para este segmento
                        # Agregar puntos en los bordes exactos donde cruza el threshold
                        x_fill = segment['index'].tolist()
                        y_fill = segment['vwap_slope_plot'].tolist()

                        # Crear el polígono: threshold -> curva -> threshold
                        x_polygon = x_fill + x_fill[::-1]
                        y_polygon = [VWAP_SLOPE_INDICATOR_HIGH_VALUE] * len(x_fill) + y_fill[::-1]

                        trace_fill_segment = go.Scatter(
                            x=x_polygon,
                            y=y_polygon,
                            mode='lines',
                            line=dict(width=0),
                            fill='toself',
                            fillcolor='rgba(255, 165, 0, 0.3)',  # Naranja translúcido
                            showlegend=False,
                            hoverinfo='skip'
                        )
                        fig.add_trace(trace_fill_segment, row=slope_row, col=1)

                print(f"[INFO] VWAP Slope (Window={VWAP_SLOPE_DEGREE_WINDOW}) añadido al gráfico: {len(df_vwap_slope)} puntos válidos")

        # VWAP Lento (Slow - Verde)
        df['vwap_slow'] = calculate_vwap(df, period=VWAP_SLOW)
        df_vwap_slow = df[df['vwap_slow'].notna()].copy()

        if SHOW_SLOW_VWAP and not df_vwap_slow.empty:
            trace_vwap_slow = go.Scatter(
                x=df_vwap_slow['index'],
                y=df_vwap_slow['vwap_slow'],
                mode='lines',
                name=f'VWAP Slow({VWAP_SLOW})',
                line=dict(color='green', width=1),
                opacity=0.8,
                hovertemplate='<b>VWAP Slow</b>: %{y:.2f}<extra></extra>'
            )
            fig.add_trace(trace_vwap_slow, row=price_row, col=1)

            print(f"[INFO] VWAP Slow({VWAP_SLOW}) añadido al gráfico: {len(df_vwap_slow)} puntos válidos")

    # Añadir puntos naranjas cuando VWAP Slope cruza hacia arriba el nivel HIGH_VALUE (crossover)
    if SHOW_VWAP_INDICATOR_CROSSOVER and 'vwap_slope' in df.columns:
        # Detectar crossovers: cuando vwap_slope cruza de abajo hacia arriba el threshold HIGH_VALUE
        # Crossover ocurre cuando:
        # - Bar anterior: vwap_slope <= VWAP_SLOPE_INDICATOR_HIGH_VALUE
        # - Bar actual: vwap_slope > VWAP_SLOPE_INDICATOR_HIGH_VALUE

        df_crossover = df.copy()
        df_crossover['vwap_slope_prev'] = df_crossover['vwap_slope'].shift(1)

        # Condición de crossover
        crossover_condition = (
            (df_crossover['vwap_slope_prev'] <= VWAP_SLOPE_INDICATOR_HIGH_VALUE) &
            (df_crossover['vwap_slope'] > VWAP_SLOPE_INDICATOR_HIGH_VALUE) &
            (df_crossover['vwap_slope'].notna()) &
            (df_crossover['vwap_slope_prev'].notna())
        )

        df_crossover_points = df_crossover[crossover_condition].copy()

        if not df_crossover_points.empty:
            trace_crossover = go.Scatter(
                x=df_crossover_points['index'],
                y=df_crossover_points['close'],
                mode='markers',
                name=f'VWAP Slope Crossover (>{VWAP_SLOPE_INDICATOR_HIGH_VALUE})',
                marker=dict(
                    color='orange',
                    size=8,
                    symbol='circle',
                    line=dict(color='darkorange', width=1)
                ),
                hovertemplate='<b>VWAP Slope Crossover</b><br>Price: %{y:.2f}<br>Slope: %{customdata:.4f}<extra></extra>',
                customdata=df_crossover_points['vwap_slope']
            )
            fig.add_trace(trace_crossover, row=price_row, col=1)

            print(f"[INFO] VWAP Slope Crossover points detectados: {len(df_crossover_points)} (threshold: {VWAP_SLOPE_INDICATOR_HIGH_VALUE})")
        else:
            print(f"[INFO] No se detectaron VWAP Slope Crossovers (threshold: {VWAP_SLOPE_INDICATOR_HIGH_VALUE})")

    # Añadir puntos verdes cuando el precio se aleja del VWAP Fast (Price Ejection)
    if PLOT_VWAP and 'vwap_fast' in df.columns:
        # Calcular la distancia porcentual entre precio y VWAP fast
        df['price_vwap_distance'] = abs((df['close'] - df['vwap_fast']) / df['vwap_fast'])

        # Filtrar puntos donde la distancia supera el threshold
        df_ejection = df[df['price_vwap_distance'] >= PRICE_EJECTION_TRIGGER].copy()

        if not df_ejection.empty:
            trace_ejection = go.Scatter(
                x=df_ejection['index'],
                y=df_ejection['close'],
                mode='markers',
                name=f'Price Ejection (>{PRICE_EJECTION_TRIGGER*100:.1f}%)',
                marker=dict(
                    color='green',
                    size=4,
                    symbol='circle'
                ),
                hovertemplate='<b>Price Ejection</b><br>Price: %{y:.2f}<br>Distance: %{customdata:.2f}%<extra></extra>',
                customdata=df_ejection['price_vwap_distance'] * 100
            )
            fig.add_trace(trace_ejection, row=price_row, col=1)

            print(f"[INFO] Price Ejection points detectados: {len(df_ejection)} (threshold: {PRICE_EJECTION_TRIGGER*100:.1f}%)")
        else:
            # Debug: mostrar la distancia máxima detectada
            max_distance = df['price_vwap_distance'].max()
            print(f"[INFO] No hay Price Ejection points. Distancia máxima: {max_distance*100:.2f}% (threshold: {PRICE_EJECTION_TRIGGER*100:.1f}%)")

        # Añadir puntos rojos cuando el precio se aleja AÚN MÁS del VWAP Fast (Over Price Ejection)
        df_over_ejection = df[df['price_vwap_distance'] >= OVER_PRICE_EJECTION_TRIGGER].copy()

        if not df_over_ejection.empty:
            trace_over_ejection = go.Scatter(
                x=df_over_ejection['index'],
                y=df_over_ejection['close'],
                mode='markers',
                name=f'OVER Ejection (>{OVER_PRICE_EJECTION_TRIGGER*100:.1f}%)',
                marker=dict(
                    color='red',
                    size=4,
                    symbol='circle'
                ),
                hovertemplate='<b>OVER Price Ejection</b><br>Price: %{y:.2f}<br>Distance: %{customdata:.2f}%<extra></extra>',
                customdata=df_over_ejection['price_vwap_distance'] * 100
            )
            fig.add_trace(trace_over_ejection, row=price_row, col=1)

            print(f"[INFO] OVER Price Ejection points detectados: {len(df_over_ejection)} (threshold: {OVER_PRICE_EJECTION_TRIGGER*100:.1f}%)")
        else:
            print(f"[INFO] No hay OVER Price Ejection points (threshold: {OVER_PRICE_EJECTION_TRIGGER*100:.1f}%)")

    # Añadir líneas ZigZag y marcadores de fractales MINOR
    if PLOT_MINOR_FRACTALS and df_fractals_minor is not None and not df_fractals_minor.empty:
        # Mapear timestamps de fractales MINOR a índices
        df_fractals_minor = df_fractals_minor.copy()
        df_fractals_minor['index'] = df_fractals_minor['timestamp'].apply(
            lambda ts: df[df['timestamp'] == ts].index[0] if len(df[df['timestamp'] == ts]) > 0 else None
        )
        df_fractals_minor = df_fractals_minor.dropna(subset=['index'])

        trace_minor_line = go.Scatter(
            x=df_fractals_minor['index'],
            y=df_fractals_minor['price'],
            mode='lines',
            name='ZigZag Minor',
            line=dict(color='dodgerblue', width=1),
            opacity=0.7,
            hoverinfo='skip'
        )
        fig.add_trace(trace_minor_line, row=price_row, col=1)

        if PLOT_MINOR_DOTS:
            trace_minor_dots = go.Scatter(
                x=df_fractals_minor['index'],
                y=df_fractals_minor['price'],
                mode='markers',
                name='Fractales Minor',
                marker=dict(
                    color='cornflowerblue',
                    size=4,
                    symbol='circle'
                ),
                opacity=1,
                hoverinfo='skip'
            )
            fig.add_trace(trace_minor_dots, row=price_row, col=1)

    # Añadir líneas ZigZag y marcadores de fractales MAJOR
    if PLOT_MAJOR_FRACTALS and df_fractals_major is not None and not df_fractals_major.empty:
        # Mapear timestamps de fractales MAJOR a índices
        df_fractals_major_copy = df_fractals_major.copy()
        df_fractals_major_copy['index'] = df_fractals_major_copy['timestamp'].apply(
            lambda ts: df[df['timestamp'] == ts].index[0] if len(df[df['timestamp'] == ts]) > 0 else None
        )
        df_fractals_major_copy = df_fractals_major_copy.dropna(subset=['index'])

        trace_major_line = go.Scatter(
            x=df_fractals_major_copy['index'],
            y=df_fractals_major_copy['price'],
            mode='lines',
            name='ZigZag Major',
            line=dict(color='blue', width=1),
            hoverinfo='skip'
        )
        fig.add_trace(trace_major_line, row=price_row, col=1)

    # Añadir Canal de Regresión
    if channel_params and SHOW_REGRESSION_CHANNEL:
        slope = channel_params['slope']
        intercept_high = channel_params['intercept_high']
        intercept_low = channel_params['intercept_low']

        x_start = df['index'].iloc[0]
        x_end = df['index'].iloc[-1]
        x_vals = [x_start, x_end]
        y_high_vals = [slope * x + intercept_high for x in x_vals]
        y_low_vals = [slope * x + intercept_low for x in x_vals]

        # Canal Superior
        trace_upper = go.Scatter(
            x=x_vals, y=y_high_vals, mode='lines', name='Channel Upper',
            line=dict(color='red', width=1), opacity=0.6, hoverinfo='skip'
        )
        fig.add_trace(trace_upper, row=price_row, col=1)

        # Canal Inferior
        trace_lower = go.Scatter(
            x=x_vals, y=y_low_vals, mode='lines', name='Channel Lower',
            line=dict(color='red', width=1), opacity=0.6, hoverinfo='skip'
        )
        fig.add_trace(trace_lower, row=price_row, col=1)

        # Canal Clonado (Green)
        if channel_params.get('intercept_clone') is not None:
            intercept_clone = channel_params['intercept_clone']
            start_idx = channel_params.get('clone_start_idx', x_start)
            x_vals_clone = [start_idx, x_end]
            y_clone_vals = [slope * x + intercept_clone for x in x_vals_clone]

            trace_clone = go.Scatter(
                x=x_vals_clone, y=y_clone_vals, mode='lines', name='Channel Clone',
                line=dict(color='green', width=1), opacity=0.8,
                fill='tonexty', fillcolor='rgba(0, 255, 0, 0.1)', hoverinfo='skip'
            )
            fig.add_trace(trace_clone, row=price_row, col=1)

    # Añadir PUNTOS NARANJAS en el gráfico de precio cuando hay trigger de consolidación
    # MANTENER los puntos naranjas incluso si el subplot está oculto
    if has_metrics and df_metrics is not None and PLOT_MINOR_FRACTALS and df_fractals_minor is not None:
        # Filtrar fractales donde choppiness_trigger == 1
        df_triggers = df_metrics[df_metrics['choppiness_trigger'] == 1].copy()

        print(f"[DEBUG] Total fractales con trigger: {len(df_triggers)}")

        if not df_triggers.empty and 'index' in df_fractals_minor.columns:
            # Usar los índices ya mapeados de df_fractals_minor
            # Los índices de df_metrics y df_fractals_minor están en el mismo orden
            df_triggers['index'] = df_fractals_minor.loc[df_triggers.index, 'index'].values
            df_triggers = df_triggers.dropna(subset=['index'])

            print(f"[DEBUG] Fractales con índices válidos: {len(df_triggers)}")

            if not df_triggers.empty:
                # Añadir puntos naranjas en el gráfico de precio
                trace_triggers = go.Scatter(
                    x=df_triggers['index'],
                    y=df_triggers['price'],
                    mode='markers',
                    name='Consolidación detectada',
                    marker=dict(
                        color='orange',
                        size=5,
                        symbol='circle',
                        line=dict(color='darkorange', width=1)
                    ),
                    hovertemplate='<b>CONSOLIDACIÓN</b><br>Price: %{y:.2f}<extra></extra>'
                )
                if show_frequency_subplot:
                    fig.add_trace(trace_triggers, row=price_row, col=1)
                else:
                    fig.add_trace(trace_triggers)

                print(f"[DEBUG] Puntos de consolidación añadidos al gráfico: {len(df_triggers)}")

    # --- Trades plotting: Entradas / Salidas / Líneas conectando ---
    # df_trades puede pasarse como parámetro o ser cargado automáticamente desde outputs/trading
    # Load trades ONLY from ENABLED strategies
    if df_trades is None:
        from config import ENABLE_VWAP_CROSSOVER_STRATEGY, ENABLE_VWAP_MOMENTUM_STRATEGY

        date_range_str_local = start_date if start_date == end_date else f"{start_date}_{end_date}"
        trades_list = []

        # Try to load VWAP Crossover strategy trades (only if enabled)
        if ENABLE_VWAP_CROSSOVER_STRATEGY:
            crossover_path = OUTPUTS_DIR / "trading" / f"tracking_record_vwap_crossover_{date_range_str_local}.csv"
            if crossover_path.exists():
                try:
                    df_crossover = pd.read_csv(crossover_path, sep=';', decimal=',', parse_dates=['entry_time', 'exit_time'])
                    df_crossover['strategy'] = 'Crossover'  # Add strategy tag
                    trades_list.append(df_crossover)
                    print(f"[INFO] Crossover trades loaded: {len(df_crossover)} rows")
                except Exception as e:
                    print(f"[WARN] Could not load crossover trades: {e}")

        # Try to load VWAP Momentum strategy trades (only if enabled)
        if ENABLE_VWAP_MOMENTUM_STRATEGY:
            momentum_path = OUTPUTS_DIR / "trading" / f"tracking_record_vwap_momentum_{date_range_str_local}.csv"
            if momentum_path.exists():
                try:
                    df_momentum = pd.read_csv(momentum_path, sep=';', decimal=',', parse_dates=['entry_time', 'exit_time'])
                    df_momentum['strategy'] = 'Momentum'  # Add strategy tag
                    trades_list.append(df_momentum)
                    print(f"[INFO] Momentum trades loaded: {len(df_momentum)} rows")
                except Exception as e:
                    print(f"[WARN] Could not load momentum trades: {e}")

        # Combine all trades if any were loaded
        if trades_list:
            df_trades = pd.concat(trades_list, ignore_index=True)
            print(f"[INFO] Total trades combined: {len(df_trades)} rows")

    if df_trades is not None and not df_trades.empty:
        # Asegurar datetime en columnas de trades
        if 'entry_time' in df_trades.columns and not pd.api.types.is_datetime64_any_dtype(df_trades['entry_time']):
            df_trades['entry_time'] = pd.to_datetime(df_trades['entry_time'])
        if 'exit_time' in df_trades.columns and not pd.api.types.is_datetime64_any_dtype(df_trades['exit_time']):
            df_trades['exit_time'] = pd.to_datetime(df_trades['exit_time'])

        # Función para mapear timestamps de trades al índice del dataframe de precio
        def _map_ts_to_index(ts):
            if pd.isna(ts):
                return None
            match = df[df['timestamp'] == ts]
            if len(match) > 0:
                return int(match.index[0])
            # fallback: nearest within 1 minute
            delta = (df['timestamp'] - ts).abs()
            min_idx = int(delta.idxmin())
            if delta[min_idx] <= pd.Timedelta('1min'):
                return min_idx
            return None

        df_trades['entry_index'] = df_trades['entry_time'].apply(_map_ts_to_index)
        df_trades['exit_index'] = df_trades['exit_time'].apply(_map_ts_to_index)

        mapped_entries = df_trades.dropna(subset=['entry_index']).copy()
        mapped_exits = df_trades.dropna(subset=['exit_index']).copy()
        print(f"[INFO] Trades mapeados: entradas {len(mapped_entries)}, salidas {len(mapped_exits)}")

        # Entries markers (triangle up for BUY, triangle down for SELL)
        if not mapped_entries.empty:
            marker_symbols = ['triangle-up' if d == 'BUY' else 'triangle-down' for d in mapped_entries['direction']]
            marker_colors = ['green' if d == 'BUY' else 'red' for d in mapped_entries['direction']]
            trace_entries = go.Scatter(
                x=mapped_entries['entry_index'],
                y=mapped_entries['entry_price'],
                mode='markers',
                name='Entries',
                marker=dict(symbol=marker_symbols, color=marker_colors, size=10, line=dict(color='rgba(0, 0, 0, 0.3)', width=1)),
                customdata=mapped_entries[['direction','entry_time']].astype(str).values,
                hovertemplate='Entry: %{y:.2f}<br>Dir: %{customdata[0]}<br>%{customdata[1]}<extra></extra>'
            )
            fig.add_trace(trace_entries, row=price_row, col=1)

        # Exits markers (color by exit_reason: profit=green, stop=red)
        if not mapped_exits.empty:
            exit_colors = ['green' if r == 'profit' else ('red' if r == 'stop' else 'gray') for r in mapped_exits['exit_reason']]
            trace_exits = go.Scatter(
                x=mapped_exits['exit_index'],
                y=mapped_exits['exit_price'],
                mode='markers',
                name='Exits',
                marker=dict(
                    symbol='x',                # diagonal cross
                    color=exit_colors,
                    size=8,                   # slightly smaller for a thinner look
                    line=dict(width=0),       # remove black outline to avoid thickness
                    opacity=0.9
                ),
                customdata=mapped_exits[['exit_reason','exit_time']].astype(str).values,
                hovertemplate='Exit: %{y:.2f}<br>Reason: %{customdata[0]}<br>%{customdata[1]}<extra></extra>'
            )
            fig.add_trace(trace_exits, row=price_row, col=1)

        # Lines connecting entry and exit for trades with both indices mapped
        trades_with_both = df_trades.dropna(subset=['entry_index','exit_index']).copy()
        for _, t in trades_with_both.iterrows():
            xpair = [int(t['entry_index']), int(t['exit_index'])]
            ypair = [t['entry_price'], t['exit_price']]
            color = 'green' if t.get('exit_reason') == 'profit' else ('red' if t.get('exit_reason') == 'stop' else 'gray')
            trace_line = go.Scatter(
                x=xpair, y=ypair, mode='lines', line=dict(color=color, width=1), opacity=0.7,
                hoverinfo='skip', showlegend=False
            )
            fig.add_trace(trace_line, row=price_row, col=1)

    # --- END TRADES PLOTTING ---

    # Añadir subplot de métricas - SEGUNDOS entre fractales
    # Solo añadir si el subplot de frecuencia NO está oculto
    if show_frequency_subplot:
        # Usar directamente los índices de fractales que ya están mapeados
        df_metrics_plot = df_metrics.copy()

        # Buscar el DataFrame de fractales minor que ya tiene los índices mapeados
        if PLOT_MINOR_FRACTALS and df_fractals_minor is not None and 'index' in df_fractals_minor.columns:
            # Usar los índices ya mapeados de df_fractals_minor
            df_metrics_plot['index'] = df_fractals_minor['index'].values
        else:
            # Fallback: mapear timestamps manualmente
            df_metrics_plot['timestamp'] = pd.to_datetime(df_metrics_plot['timestamp'])
            df_metrics_plot['index'] = df_metrics_plot['timestamp'].apply(
                lambda ts: df[df['timestamp'] == ts].index[0] if len(df[df['timestamp'] == ts]) > 0 else None
            )

        df_metrics_plot = df_metrics_plot.dropna(subset=['index'])

        # Filtrar solo las filas con valores válidos (no NaN) en time_from_prev_seconds
        df_metrics_valid = df_metrics_plot.dropna(subset=['time_from_prev_seconds'])

        print(f"[DEBUG] Total métricas: {len(df_metrics_plot)}, Válidas: {len(df_metrics_valid)}")

        if not df_metrics_valid.empty:
            print(f"[DEBUG] Rango time_from_prev_seconds: {df_metrics_valid['time_from_prev_seconds'].min():.0f} - {df_metrics_valid['time_from_prev_seconds'].max():.0f} segundos")

            # Gráfico de SEGUNDOS INVERTIDOS entre fractales
            # INVERTIR: valores bajos (consolidación) -> arriba, valores altos (trending) -> abajo
            max_time = df_metrics_valid['time_from_prev_seconds'].max()
            inverted_time = max_time - df_metrics_valid['time_from_prev_seconds']

            trace_time = go.Scatter(
                x=df_metrics_valid['index'],
                y=inverted_time,
                mode='lines',
                name='Frecuencia de fractales (invertido)',
                line=dict(color='orange', width=2),
                hoverinfo='skip'
            )
            fig.add_trace(trace_time, row=metrics_row, col=1)
        else:
            print("[DEBUG] No hay métricas válidas para graficar")

    # Configurar eje X con etiquetas de fecha personalizadas
    num_ticks = 30
    tick_indices = [int(i) for i in range(0, len(df), max(1, len(df)//num_ticks))]
    tick_vals = df.iloc[tick_indices]['index']
    # Ensure 'timestamp' column is datetime for dt.strftime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    tick_text = df.iloc[tick_indices]['timestamp'].dt.strftime('%H:%M:%S')

    if show_frequency_subplot:
        # Eje X para precio (row 1) - sin grid vertical, con marco inferior gris
        fig.update_xaxes(
            tickmode='array', tickvals=tick_vals, ticktext=tick_text,
            tickangle=-45, showgrid=False,
            showline=True, linewidth=1, linecolor='#d3d3d3',
            row=price_row, col=1
        )
        # Eje X para métricas (row 2) - sin grid vertical, con marco inferior gris
        fig.update_xaxes(
            tickmode='array', tickvals=tick_vals, ticktext=tick_text,
            tickangle=-45, showgrid=False,
            showline=True, linewidth=1, linecolor='#d3d3d3',
            row=metrics_row, col=1
        )
    else:
        fig.update_xaxes(
            tickmode='array', tickvals=tick_vals, ticktext=tick_text,
            tickangle=-45, showgrid=False,
            showline=True, linewidth=1, linecolor='#d3d3d3'
        )

    # Añadir líneas verticales grises en horarios clave (9:00, 15:30, 22:00)
    key_times = ['09:00:00', '15:30:00', '22:00:00']
    for time_str in key_times:
        # Encontrar el índice más cercano a este horario
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Crear timestamp completo para buscar
        if start_date == end_date:
            target_time = pd.to_datetime(f"{start_date} {time_str}")
        else:
            # Para rangos, usar la fecha de inicio
            target_time = pd.to_datetime(f"{start_date} {time_str}")

        # Buscar el registro más cercano a este horario
        df_time = df[df['timestamp'].dt.time == pd.to_datetime(time_str).time()]

        if not df_time.empty:
            time_index = df_time.iloc[0]['index']

            # Añadir línea vertical gris con transparencia
            if show_frequency_subplot:
                # Añadir línea en ambos subplots
                fig.add_vline(x=time_index, line_width=1, line_dash="solid",
                             line_color="rgba(128, 128, 128, 0.3)", row=price_row, col=1)
                fig.add_vline(x=time_index, line_width=1, line_dash="solid",
                             line_color="rgba(128, 128, 128, 0.3)", row=metrics_row, col=1)
            else:
                fig.add_vline(x=time_index, line_width=1, line_dash="solid",
                             line_color="rgba(128, 128, 128, 0.3)")

    # Configurar layout
    # Título: mostrar solo una fecha si start_date == end_date
    strategy_info = get_strategy_info_compact()
    if start_date == end_date:
        # Calculate day of week for single date
        date_obj = datetime.strptime(start_date, "%Y%m%d")
        day_of_week = date_obj.isoweekday()  # 1=Monday, 2=Tuesday, ..., 7=Sunday
        day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
        day_name = day_names[day_of_week]
        title_text = f'{symbol.upper()} - {start_date} ({day_name}, DoW={day_of_week}) | {strategy_info}'
    else:
        title_text = f'{symbol.upper()} - {start_date} -> {end_date} | {strategy_info}'

    # Configurar layout general
    # Calcular altura según subplots activos
    if show_frequency_subplot and show_slope_subplot:
        height = 1200
    elif show_slope_subplot or show_frequency_subplot:
        height = 900
    else:
        height = 600

    fig.update_layout(
        title=title_text,
        template='plotly_white',
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial", size=12, color="#333333"),
        showlegend=True,
        height=height,
        xaxis_title="",
        yaxis_title=""
    )

    # Configurar ejes Y individuales
    # Eje Y para precio (row 1) - con grid horizontal gris
    fig.update_yaxes(
        title='Price',
        showgrid=True, gridcolor='#e0e0e0', gridwidth=0.5,
        showline=True, linewidth=1, linecolor='#d3d3d3',
        tickcolor='gray', tickfont=dict(color='gray'),
        tickformat=',',
        row=price_row, col=1
    )

    # Eje Y para VWAP Slope (row 2) - escala logarítmica SIN grid - solo si está habilitado
    if show_slope_subplot:
        fig.update_yaxes(
            title=f'|VWAP Slope| (W={VWAP_SLOPE_DEGREE_WINDOW}) [Log]',
            showgrid=False,
            showline=True, linewidth=1, linecolor='#d3d3d3',
            tickcolor='orange', tickfont=dict(color='orange'),
            type='log',
            row=slope_row, col=1
        )

    # Eje Y para métricas (row 3 o row 2 si no hay slope) - solo si existe
    if show_frequency_subplot:
        fig.update_yaxes(
            title='Frecuencia (↑ alta)',
            showgrid=True, gridcolor='#e0e0e0', gridwidth=0.5,
            showline=True, linewidth=1, linecolor='#d3d3d3',
            tickcolor='gray', tickfont=dict(color='gray'),
            row=metrics_row, col=1
        )

    # Crear carpeta de salida si no existe
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    # Guardar gráfico
    if start_date == end_date:
        date_range_str = start_date
    else:
        date_range_str = f"{start_date}_{end_date}"
    output_html = str(CHARTS_DIR / f'nq_{date_range_str}.html')
    print(f"Guardando gráfico en: {output_html}")
    fig.write_html(output_html)
    print(f"Gráfico guardado exitosamente")

    # Mostrar en navegador
    import webbrowser
    webbrowser.open(f'file://{os.path.abspath(output_html)}')
    print(f"Abriendo en navegador...")

    return {
        'start_date': start_date,
        'end_date': end_date,
        'output_path': output_html,
        'total_records': len(df)
    }


if __name__ == "__main__":
    from find_fractals import load_date_range
    from config import DATA_DIR

    print(f"Generando gráfico para: {START_DATE} -> {END_DATE}")

    # Cargar datos del rango
    df = load_date_range(START_DATE, END_DATE)
    if df is None:
        print("Error cargando datos")
        exit(1)

    # Symbol for NQ
    symbol = 'NQ'

    # Cargar fractales
    date_range_str = f"{START_DATE}_{END_DATE}"
    fractal_minor_path = FRACTALS_DIR / f"{symbol}_fractals_minor_{date_range_str}.csv"
    fractal_major_path = FRACTALS_DIR / f"{symbol}_fractals_major_{date_range_str}.csv"

    df_fractals_minor = None
    df_fractals_major = None

    if fractal_minor_path.exists():
        df_fractals_minor = pd.read_csv(fractal_minor_path)
    if fractal_major_path.exists():
        df_fractals_major = pd.read_csv(fractal_major_path)

    # Try to load trades file for this date range and pass it to the plotting function
    df_trades = None
    trades_path = OUTPUTS_DIR / "trading" / f"trading_vwap_momentum_{date_range_str}.csv"
    if trades_path.exists():
        try:
            df_trades = pd.read_csv(trades_path, sep=';', decimal=',', parse_dates=['entry_time', 'exit_time'])
            print(f"[INFO] Trades loaded from {trades_path} ({len(df_trades)} rows)")
        except Exception as e:
            print(f"[WARN] Could not load trades file {trades_path}: {e}")

    plot_range_chart(df, df_fractals_minor, df_fractals_major, START_DATE, END_DATE, symbol=symbol, df_trades=df_trades)

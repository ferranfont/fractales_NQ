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
    SHOW_ORANGE_DOT, SHOW_BLUE_SQUARE, SHOW_GREEN_DOT, SHOW_RED_DOT,
    # Strategy enable flags
    ENABLE_VWAP_MOMENTUM_STRATEGY, ENABLE_VWAP_SQUARE_STRATEGY,
    # VWAP Momentum parameters
    USE_TIME_IN_MARKET, TIME_IN_MARKET_MINUTES, USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE,
    USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET, MAX_SL_ALLOWED_IN_TIME_IN_MARKET,
    USE_TP_ALLOWED_IN_TIME_IN_MARKET, TP_IN_TIME_IN_MARKET,
    VWAP_MOMENTUM_TP_POINTS, VWAP_MOMENTUM_SL_POINTS,
    VWAP_MOMENTUM_LONG_ALLOWED, VWAP_MOMENTUM_SHORT_ALLOWED,
    USE_VWAP_SLOW_TREND_FILTER,
    # VWAP Square parameters
    VWAP_SQUARE_TP_POINTS, VWAP_SQUARE_SL_POINTS,
    VWAP_SQUARE_LISTENING_TIME, VWAP_SQUARE_MIN_SPIKE,
    USE_SQUARE_ATR_TRAILING_STOP, SQUARE_ATR_PERIOD, SQUARE_ATR_MULTIPLIER,
    USE_OPOSITE_SIDE_OF_SQUARE_AS_STOP,
    USE_VWAP_SQUARE_SHAKE_OUT, VWAP_SQUARE_SHAKE_OUT_RETRACEMENT_PCT,
    USE_SQUARE_VWAP_SLOW_TREND_FILTER,
    # VWAP Time Strategy
    ENABLE_VWAP_TIME_STRATEGY, VWAP_TIME_ENTRY,
    # VWAP Bands
    DRAW_VWAP_BANDS, VWAP_BANDS_START_TIME,
    # VWAP Wyckoff Strategy
    ENABLE_VWAP_WYCKOFF_STRATEGY, USE_WYCKOFF_ATR_TRAILING_STOP,
    ENABLE_OPENING_RANGE_PLOT, OPENING_RANGE_START, OPENING_RANGE_END
)
from calculate_vwap import calculate_vwap
import numpy as np

# ============================================================================
# STRATEGY INFO STRING (for chart titles)
# ============================================================================
def get_strategy_info_compact():
    """Returns a compact string with current strategy configuration"""

    # Determine which strategy is enabled
    if ENABLE_VWAP_SQUARE_STRATEGY:
        # VWAP SQUARE STRATEGY
        strategy_name = "VWAP Square"

        # TP/SL info
        if USE_SQUARE_ATR_TRAILING_STOP:
            sl_info = f"ATR-Trail({SQUARE_ATR_PERIOD}/{SQUARE_ATR_MULTIPLIER}x)"
        else:
            sl_info = f"SL:{VWAP_SQUARE_SL_POINTS}pts"

        tp_sl_info = f"TP/SL ({VWAP_SQUARE_TP_POINTS}/{sl_info})"

        # Listening time
        listen_info = f"Listen:{VWAP_SQUARE_LISTENING_TIME}min"

        # Shake out mode
        if USE_VWAP_SQUARE_SHAKE_OUT:
            mode_info = f"SHAKE-OUT({VWAP_SQUARE_SHAKE_OUT_RETRACEMENT_PCT}%)"
        else:
            mode_info = "BREAKOUT"

        # Additional filters
        filters = []
        if USE_OPOSITE_SIDE_OF_SQUARE_AS_STOP:
            filters.append("OppSide-SL")
        if USE_SQUARE_VWAP_SLOW_TREND_FILTER:
            filters.append(f"Trend(VWAP{VWAP_SLOW})")
        if VWAP_SQUARE_MIN_SPIKE > 0:
            filters.append(f"MinSpike:{VWAP_SQUARE_MIN_SPIKE}pts")

        filter_info = "| " + " | ".join(filters) if filters else ""

        return f"{strategy_name} | {tp_sl_info} | {listen_info} | {mode_info} {filter_info}"

    elif ENABLE_VWAP_MOMENTUM_STRATEGY:
        # VWAP MOMENTUM STRATEGY
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

    elif ENABLE_VWAP_TIME_STRATEGY:
        # VWAP TIME STRATEGY
        from config import VWAP_TIME_ENTRY, VWAP_TIME_EXIT, VWAP_TIME_TP_POINTS, VWAP_TIME_SL_POINTS

        # Calculate duration if possible roughly
        time_info = f"Entry:{VWAP_TIME_ENTRY} | Exit:{VWAP_TIME_EXIT}"
        tp_sl_info = f"TP/SL ({VWAP_TIME_TP_POINTS}/{VWAP_TIME_SL_POINTS}pts)"

        return f"VWAP Time | {time_info} | {tp_sl_info}"

    elif ENABLE_VWAP_WYCKOFF_STRATEGY:
        # VWAP WYCKOFF STRATEGY
        from config import (START_ORANGE_DOT_WYCKOFF_TIME, END_ORANGE_DOT_WYCKOFF_TIME, 
                           TP_ORANGE_DOT_WYCKOFF, SL_ORANGE_DOT_WYCKOFF)
        
        time_info = f"Window:{START_ORANGE_DOT_WYCKOFF_TIME}-{END_ORANGE_DOT_WYCKOFF_TIME}"
        tp_sl_info = f"TP/SL ({TP_ORANGE_DOT_WYCKOFF}/{SL_ORANGE_DOT_WYCKOFF}pts)"
        
        return f"VWAP Wyckoff (Orange Dot) | {time_info} | {tp_sl_info}"

    else:
        return "NO STRATEGY ENABLED"

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

    # Use polyfit with absolute value to match find_rectangles.py calculation
    # This ensures synchronization between chart and strategy
    import numpy as np
    slope = abs(np.polyfit(np.arange(len(vwap_window)), vwap_window, 1)[0])

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
    print("[DEBUG] Step 1: Data reset and timestamp check...")

    # Crear índice numérico para evitar huecos de fines de semana
    df = df.reset_index(drop=True)
    df['index'] = df.index
    # Asegurar que 'timestamp' sea tipo datetime (necesario para mapear fractales y trades)
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        print("[DEBUG] Converting timestamp column to datetime...")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print("[DEBUG] Step 2: Configuring subplots...")

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
        
    print("[DEBUG] Step 3: Adding price trace...")

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
    
    print("[DEBUG] Step 4: Adding VWAP indicators...")

    # Añadir indicador VWAP
    if PLOT_VWAP:
        print(f"[DEBUG] Calculating VWAP Fast ({VWAP_FAST})...")
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
            # IMPORTANT: Use exact same calculation method as find_rectangles.py for synchronization
            if 'vwap_slope' not in df.columns:
                import numpy as np
                df['vwap_slope'] = df['vwap_fast'].rolling(window=VWAP_SLOPE_DEGREE_WINDOW).apply(
                    lambda x: abs(np.polyfit(np.arange(len(x)), x, 1)[0]) if len(x) == VWAP_SLOPE_DEGREE_WINDOW else np.nan,
                    raw=False
                )

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
    # IMPORTANT: Detect crossovers directly from the vwap_slope indicator already calculated
    # Do NOT use find_vwap_slope_rectangles() - use the indicator itself
    if SHOW_VWAP_INDICATOR_CROSSOVER and 'vwap_slope' in df.columns:
        # Detect crossovers directly from vwap_slope indicator
        df_with_prev = df.copy()
        df_with_prev['vwap_slope_prev'] = df_with_prev['vwap_slope'].shift(1)

        # Crossover UP: previous <= threshold and current > threshold
        crossover_condition = (
            (df_with_prev['vwap_slope_prev'] <= VWAP_SLOPE_INDICATOR_HIGH_VALUE) &
            (df_with_prev['vwap_slope'] > VWAP_SLOPE_INDICATOR_HIGH_VALUE) &
            (df_with_prev['vwap_slope'].notna()) &
            (df_with_prev['vwap_slope_prev'].notna())
        )

        # Crossdown: previous > threshold and current <= threshold
        crossdown_condition = (
            (df_with_prev['vwap_slope_prev'] > VWAP_SLOPE_INDICATOR_HIGH_VALUE) &
            (df_with_prev['vwap_slope'] <= VWAP_SLOPE_INDICATOR_HIGH_VALUE) &
            (df_with_prev['vwap_slope'].notna()) &
            (df_with_prev['vwap_slope_prev'].notna())
        )

        df_crossover_points = df_with_prev[crossover_condition].copy()
        df_crossdown_points = df_with_prev[crossdown_condition].copy()

        # Show orange dots (crossover) if enabled
        if SHOW_ORANGE_DOT and not df_crossover_points.empty:
            trace_crossover = go.Scatter(
                x=df_crossover_points['index'],
                y=df_crossover_points['close'],
                mode='markers',
                name=f'VWAP Slope Crossover (>{VWAP_SLOPE_INDICATOR_HIGH_VALUE})',
                marker=dict(
                    color='orange',
                    size=5,
                    symbol='circle',
                    line=dict(color='darkorange', width=0.5)
                ),
                hovertemplate='<b>VWAP Slope Crossover</b><br>Price: %{y:.2f}<br>Slope: %{customdata:.4f}<extra></extra>',
                customdata=df_crossover_points['vwap_slope']
            )
            fig.add_trace(trace_crossover, row=price_row, col=1)
            print(f"[INFO] VWAP Slope Crossover points detectados: {len(df_crossover_points)} (threshold: {VWAP_SLOPE_INDICATOR_HIGH_VALUE})")
        elif not df_crossover_points.empty:
            print(f"[INFO] Found {len(df_crossover_points)} crossover points (orange dots hidden - SHOW_ORANGE_DOT=False)")

        # Show blue squares (crossdown) if enabled
        if SHOW_BLUE_SQUARE and not df_crossdown_points.empty:
            trace_crossdown = go.Scatter(
                x=df_crossdown_points['index'],
                y=df_crossdown_points['close'],
                mode='markers',
                name=f'VWAP Slope Crossdown (<{VWAP_SLOPE_INDICATOR_HIGH_VALUE})',
                marker=dict(
                    color='blue',
                    size=6,
                    symbol='square',
                    line=dict(color='darkblue', width=0.5)
                ),
                hovertemplate='<b>VWAP Slope Crossdown</b><br>Price: %{y:.2f}<br>Slope: %{customdata:.4f}<extra></extra>',
                customdata=df_crossdown_points['vwap_slope']
            )
            fig.add_trace(trace_crossdown, row=price_row, col=1)
            print(f"[INFO] VWAP Slope Crossdown points detectados: {len(df_crossdown_points)} (threshold: {VWAP_SLOPE_INDICATOR_HIGH_VALUE})")
        elif not df_crossdown_points.empty:
            print(f"[INFO] Found {len(df_crossdown_points)} crossdown points (blue squares hidden - SHOW_BLUE_SQUARE=False)")

    # Draw rectangles based on VWAP Slope crossover/crossdown pairs
    # Use REALTIME rectangle detection for faster, more aggressive patterns
    if SHOW_VWAP_INDICATOR_CROSSOVER and 'vwap_slope' in df.columns:
        if not df_crossover_points.empty and not df_crossdown_points.empty:
            # Import REALTIME classification function (closes rectangles early)
            from find_rectangles_realtime import find_vwap_slope_rectangles_realtime

            # Get rectangles with REALTIME classification
            rectangles_data = find_vwap_slope_rectangles_realtime(df)

            # Convert to plot format (map timestamps to index)
            rectangles = []
            for rect in rectangles_data:
                rectangles.append({
                    'x1_index': df.loc[rect['x1_index'], 'index'],
                    'x2_index': df.loc[rect['x2_index'], 'index'],
                    'y1': rect['y1'],
                    'y2': rect['y2'],
                    'type': rect['type'],
                    'price_per_bar': rect['price_per_bar']
                })

            print(f"[INFO] Created {len(rectangles)} rectangles from crossover/crossdown pairs")

            # Count rectangle types
            tall_narrow_up = [r for r in rectangles if r.get('type') == 'tall_narrow_up']
            tall_narrow_down = [r for r in rectangles if r.get('type') == 'tall_narrow_down']
            consolidation = [r for r in rectangles if r.get('type') == 'consolidation']
            print(f"[INFO] Drawing rectangles: {len(tall_narrow_up)} tall&narrow UP (chartreuse), {len(tall_narrow_down)} tall&narrow DOWN (red), {len(consolidation)} consolidation (orange)")

            for rect in rectangles:
                # Determine color based on aspect ratio AND trend direction
                rect_type = rect.get('type', 'consolidation')  # Default to orange if no type

                if rect_type == 'tall_narrow_up':
                    # Tall & Narrow UPTREND: high volatility, rising price (chartreuse green)
                    line_color = "green"  # Green outline
                    fill_color = "chartreuse"
                    opacity = 0.22  # More intense for green rectangles
                    line_width = 2  # Thicker outline for visibility
                elif rect_type == 'tall_narrow_down':
                    # Tall & Narrow DOWNTREND: high volatility, falling price (red)
                    line_color = "red"  # Red outline
                    fill_color = "red"
                    opacity = 0.22  # More intense for red rectangles
                    line_width = 2  # Thicker outline for visibility
                else:
                    # Consolidation: low volatility, sideways movement (orange)
                    line_color = "orange"
                    fill_color = "orange"
                    opacity = 0.03  # Very low opacity for orange consolidation squares (should NOT generate trades)
                    line_width = 1  # Standard width for orange

                # Add rectangle shape
                fig.add_shape(
                    type="rect",
                    x0=rect['x1_index'],
                    x1=rect['x2_index'],
                    y0=rect['y1'],
                    y1=rect['y2'],
                    line=dict(color=line_color, width=line_width),
                    fillcolor=fill_color,
                    opacity=opacity,
                    layer="below",
                    row=price_row,
                    col=1
                )

                # Add retracement level line for shake out mode
                if USE_VWAP_SQUARE_SHAKE_OUT and ENABLE_VWAP_SQUARE_STRATEGY:
                    # Only draw retracement lines for tall & narrow rectangles (not consolidation)
                    if rect_type in ['tall_narrow_up', 'tall_narrow_down']:
                        # Calculate retracement level
                        rectangle_height = rect['y2'] - rect['y1']
                        retracement_distance = rectangle_height * (VWAP_SQUARE_SHAKE_OUT_RETRACEMENT_PCT / 100.0)

                        if rect_type == 'tall_narrow_up':
                            # GREEN: retracement is DOWN from y2 (upper boundary)
                            retracement_level = rect['y2'] - retracement_distance
                            retrace_color = "green"  # Solid opaque green
                        else:  # tall_narrow_down
                            # RED: retracement is UP from y1 (lower boundary)
                            retracement_level = rect['y1'] + retracement_distance
                            retrace_color = "red"  # Match red rectangle color

                        # Common settings for all retracement lines
                        retrace_opacity = 0.5  # Semi-transparent
                        retrace_width = 1  # Standard width

                        # Calculate listening window end (x1 = x2 + LISTENING_TIME minutes)
                        # Get the timestamp at x2_index
                        x2_timestamp = df.loc[df['index'] == rect['x2_index'], 'timestamp'].iloc[0]
                        listening_end_timestamp = x2_timestamp + pd.Timedelta(minutes=VWAP_SQUARE_LISTENING_TIME)

                        # Find the index corresponding to listening_end_timestamp (or closest)
                        listening_end_index = df.loc[df['timestamp'] >= listening_end_timestamp, 'index'].min()
                        if pd.isna(listening_end_index):
                            # If listening window extends beyond data, use last available index
                            listening_end_index = df['index'].max()

                        # Draw horizontal line from rectangle end (x0) to listening window end (x1)
                        fig.add_shape(
                            type="line",
                            x0=rect['x2_index'],  # Start at rectangle close
                            x1=listening_end_index,  # End at listening window
                            y0=retracement_level,
                            y1=retracement_level,
                            line=dict(color=retrace_color, width=retrace_width, dash="dot"),
                            opacity=retrace_opacity,
                            layer="above",
                            row=price_row,
                            col=1
                        )

    # Añadir puntos verdes cuando el precio se aleja del VWAP Fast (Price Ejection)
    if PLOT_VWAP and 'vwap_fast' in df.columns:
        # Calcular la distancia porcentual entre precio y VWAP fast
        df['price_vwap_distance'] = abs((df['close'] - df['vwap_fast']) / df['vwap_fast'])

        # Filtrar puntos donde la distancia supera el threshold
        df_ejection = df[df['price_vwap_distance'] >= PRICE_EJECTION_TRIGGER].copy()

        # Show green dots (Price Ejection) if enabled
        if SHOW_GREEN_DOT and not df_ejection.empty:
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
        elif not df_ejection.empty:
            print(f"[INFO] Found {len(df_ejection)} price ejection points (green dots hidden - SHOW_GREEN_DOT=False)")
        else:
            # Debug: mostrar la distancia máxima detectada
            max_distance = df['price_vwap_distance'].max()
            print(f"[INFO] No hay Price Ejection points. Distancia máxima: {max_distance*100:.2f}% (threshold: {PRICE_EJECTION_TRIGGER*100:.1f}%)")

        # Añadir puntos rojos cuando el precio se aleja AÚN MÁS del VWAP Fast (Over Price Ejection)
        df_over_ejection = df[df['price_vwap_distance'] >= OVER_PRICE_EJECTION_TRIGGER].copy()

        # Show red dots (OVER Price Ejection) if enabled
        if SHOW_RED_DOT and not df_over_ejection.empty:
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
        elif not df_over_ejection.empty:
            print(f"[INFO] Found {len(df_over_ejection)} OVER ejection points (red dots hidden - SHOW_RED_DOT=False)")
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

            fig.add_trace(trace_clone, row=price_row, col=1)

    # -------------------------------------------------------------------------
    # OPENING RANGE CHANNEL (User Request)
    # -------------------------------------------------------------------------
    if ENABLE_OPENING_RANGE_PLOT:
        try:
            # Parse times
            or_start_time = datetime.strptime(OPENING_RANGE_START, "%H:%M:%S").time()
            or_end_time = datetime.strptime(OPENING_RANGE_END, "%H:%M:%S").time()

            # Filter data within the opening range
            # Note: df['timestamp'] is datetime64
            df_or = df.set_index('timestamp').between_time(or_start_time, or_end_time).reset_index()

            if not df_or.empty:
                # Find Max High and Min Low in this range
                or_high = df_or['high'].max()
                or_low = df_or['low'].min()

                # We want to plot this channel from or_start_time (or earlier?) to end of data
                # Typically plot starts at 'end' of range, but user said "create a channel... from x0"
                # Let's plot from start of opening range to end of chart.
                
                # We need x-coordinates.
                # If we use df['index'], we need to find the index corresponding to start time and end of df.
                
                # Get index of start time of opening range
                # We want to LIMIT the plot to the range [or_start_time, or_end_time] only, not extend it.
                
                mask_range = (df['timestamp'].dt.time >= or_start_time) & (df['timestamp'].dt.time <= or_end_time)
                df_range_filtered = df.loc[mask_range]
                
                if not df_range_filtered.empty:
                    start_idx = df_range_filtered['index'].iloc[0]
                    end_idx = df_range_filtered['index'].iloc[-1]
                    
                    # Trace 1: Upper Line
                    trace_or_high = go.Scatter(
                        x=[start_idx, end_idx],
                        y=[or_high, or_high],
                        mode='lines',
                        name='Opening Range High',
                        line=dict(color='lightblue', width=1),
                        showlegend=False
                    )
                    
                    # Trace 2: Lower Line (fill to upper)
                    trace_or_low = go.Scatter(
                        x=[start_idx, end_idx],
                        y=[or_low, or_low],
                        mode='lines',
                        name='Opening Range Channel', # Show this one in legend
                        line=dict(color='lightblue', width=1),
                        fill='tonexty', # Fill to the previous trace (trace_or_high)
                        fillcolor='rgba(173, 216, 230, 0.3)' # Light Blue with 0.3 alpha (more visible)
                    )
                    
                    # Add trace_or_high FIRST, then trace_or_low (order matters for 'tonexty')
                    fig.add_trace(trace_or_high, row=price_row, col=1)
                    fig.add_trace(trace_or_low, row=price_row, col=1)
                    
                    print(f"[INFO] Opening Range Channel ({OPENING_RANGE_START}-{OPENING_RANGE_END}) added: High={or_high}, Low={or_low}")
            else:
                print(f"[WARN] No data found in Opening Range {OPENING_RANGE_START}-{OPENING_RANGE_END}")

        except Exception as e:
            print(f"[ERROR] Failed to plot Opening Range: {e}")
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

    # --- Trend Divergence Indicator (Orange Dots) ---
    # Plot an orange dot at the first Green Dot (Price Ejection) after a Price/VWAP crossover
    if PLOT_VWAP and 'vwap_fast' in df.columns:
        from find_trend_divergence import find_trend_divergence_dots
        
        df_divergence_dots = find_trend_divergence_dots(df)
        
        if not df_divergence_dots.empty:
            trace_divergence = go.Scatter(
                x=df_divergence_dots['index'],
                y=df_divergence_dots['close'],
                mode='markers',
                name='Trend Divergence (First Green Dot)',
                marker=dict(
                    color='orange',
                    size=8,              # Larger size to distinguish from other dots
                    symbol='circle-open', # Distinct symbol (open circle) or just circle
                    line=dict(color='orange', width=2)
                ),
                hovertemplate='<b>Trend Divergence</b><br>Price: %{y:.2f}<extra></extra>'
            )
            fig.add_trace(trace_divergence, row=price_row, col=1)
            print(f"[INFO] Trend Divergence points (Blue/Orange logic) added: {len(df_divergence_dots)}")

    # --- Trades plotting: Entradas / Salidas / Líneas conectando ---
    # df_trades puede pasarse como parámetro o ser cargado automáticamente desde outputs/trading
    # Load trades ONLY from ENABLED strategies
    if df_trades is None:
        from config import ENABLE_VWAP_CROSSOVER_STRATEGY, ENABLE_VWAP_PULLBACK_STRATEGY
        # ENABLE_VWAP_MOMENTUM_STRATEGY and ENABLE_VWAP_SQUARE_STRATEGY already imported at module level

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

        # Try to load VWAP Pullback strategy trades (only if enabled)
        if ENABLE_VWAP_PULLBACK_STRATEGY:
            pullback_path = OUTPUTS_DIR / "trading" / f"tracking_record_vwap_pullback_{date_range_str_local}.csv"
            if pullback_path.exists():
                try:
                    df_pullback = pd.read_csv(pullback_path, sep=';', decimal=',', parse_dates=['entry_time', 'exit_time'])
                    df_pullback['strategy'] = 'Pullback'  # Add strategy tag
                    trades_list.append(df_pullback)
                    print(f"[INFO] Pullback trades loaded: {len(df_pullback)} rows")
                except Exception as e:
                    print(f"[WARN] Could not load pullback trades: {e}")

        # Try to load VWAP Wyckoff strategy trades (only if enabled)
        if ENABLE_VWAP_WYCKOFF_STRATEGY:
            wyckoff_path = OUTPUTS_DIR / "trading" / f"tracking_record_vwap_wyckoff_{date_range_str_local}.csv"
            if wyckoff_path.exists():
                try:
                    df_wyckoff = pd.read_csv(wyckoff_path, sep=';', decimal=',', parse_dates=['entry_time', 'exit_time'])
                    df_wyckoff['strategy'] = 'Wyckoff'  # Add strategy tag
                    trades_list.append(df_wyckoff)
                    print(f"[INFO] Wyckoff trades loaded: {len(df_wyckoff)} rows")
                except Exception as e:
                    print(f"[WARN] Could not load wyckoff trades: {e}")

        # Try to load VWAP Square strategy trades (only if enabled)
        if ENABLE_VWAP_SQUARE_STRATEGY:
            square_path = OUTPUTS_DIR / "trading" / f"tracking_record_vwap_square_{date_range_str_local}.csv"
            if square_path.exists():
                try:
                    df_square = pd.read_csv(square_path, sep=';', decimal=',', parse_dates=['entry_time', 'exit_time'])
                    df_square['strategy'] = 'Square'  # Add strategy tag
                    trades_list.append(df_square)
                    print(f"[INFO] Square trades loaded: {len(df_square)} rows")
                except Exception as e:
                    print(f"[WARN] Could not load square trades: {e}")

        # Try to load VWAP Time strategy trades (only if enabled)
        from config import ENABLE_VWAP_TIME_STRATEGY
        if ENABLE_VWAP_TIME_STRATEGY:
            time_path = OUTPUTS_DIR / "trading" / f"tracking_record_vwap_time_{date_range_str_local}.csv"
            if time_path.exists():
                try:
                    df_time = pd.read_csv(time_path, sep=';', decimal=',', parse_dates=['entry_time', 'exit_time'])
                    df_time['strategy'] = 'Time'  # Add strategy tag
                    trades_list.append(df_time)
                    print(f"[INFO] Time trades loaded: {len(df_time)} rows")
                except Exception as e:
                    print(f"[WARN] Could not load time trades: {e}")

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

            # Green for BUY, Bright Red for SELL (all strategies)
            marker_colors = ['green' if d == 'BUY' else '#FF0000' for d in mapped_entries['direction']]

            trace_entries = go.Scatter(
                x=mapped_entries['entry_index'],
                y=mapped_entries['entry_price'],
                mode='markers',
                name='Entries',
                marker=dict(symbol=marker_symbols, color=marker_colors, size=10, line=dict(width=0), opacity=1.0),
                customdata=mapped_entries[['direction','entry_time']].astype(str).values,
                hovertemplate='Entry: %{y:.2f}<br>Dir: %{customdata[0]}<br>%{customdata[1]}<extra></extra>'
            )
            fig.add_trace(trace_entries, row=price_row, col=1)

        # Exits markers (all gray crosses, matching Momentum strategy style)
        if not mapped_exits.empty:
            trace_exits = go.Scatter(
                x=mapped_exits['exit_index'],
                y=mapped_exits['exit_price'],
                mode='markers',
                name='Exits',
                marker=dict(
                    symbol='x',                # diagonal cross
                    color='gray',              # all exits in gray
                    size=8,                   # slightly smaller for a thinner look
                    line=dict(width=0),       # remove black outline to avoid thickness
                    opacity=0.9
                ),
                customdata=mapped_exits[['exit_reason','exit_time']].astype(str).values,
                hovertemplate='Exit: %{y:.2f}<br>Reason: %{customdata[0]}<br>%{customdata[1]}<extra></extra>'
            )
            fig.add_trace(trace_exits, row=price_row, col=1)

        # Lines connecting entry and exit for trades with both indices mapped (all gray, matching Momentum strategy style)
        trades_with_both = df_trades.dropna(subset=['entry_index','exit_index']).copy()
        for _, t in trades_with_both.iterrows():
            xpair = [int(t['entry_index']), int(t['exit_index'])]
            ypair = [t['entry_price'], t['exit_price']]
            trace_line = go.Scatter(
                x=xpair, y=ypair, mode='lines', line=dict(color='gray', width=1), opacity=0.7,
                hoverinfo='skip', showlegend=False
            )
            fig.add_trace(trace_line, row=price_row, col=1)

    # --- END TRADES PLOTTING ---

    # --- TRAILING STOP EVOLUTION PLOTTING (SL History) ---
    # Load SL history from CSV if available (only for Square strategy - shown as violet line)
    # Only display trailing stop during active positions (from entry to exit)

    # Square strategy SL history (violet dashed line, only during active positions)
    # Only plot if Square strategy is enabled
    if ENABLE_VWAP_SQUARE_STRATEGY:
        sl_history_path_square = OUTPUTS_DIR / "trading" / f"sl_history_vwap_square_{date_range_str_local}.csv"
        trades_path_square = OUTPUTS_DIR / "trading" / f"tracking_record_vwap_square_{date_range_str_local}.csv"

        if sl_history_path_square.exists() and trades_path_square.exists():
            try:
                print(f"[INFO] Loading Square SL history from {sl_history_path_square.name}")
                df_sl_history_sq = pd.read_csv(sl_history_path_square, sep=';', decimal=',', parse_dates=['timestamp'])
                df_trades_sq = pd.read_csv(trades_path_square, sep=';', decimal=',', parse_dates=['entry_time', 'exit_time'])

                # Map timestamps to index
                if not pd.api.types.is_datetime64_any_dtype(df_sl_history_sq['timestamp']):
                    df_sl_history_sq['timestamp'] = pd.to_datetime(df_sl_history_sq['timestamp'])

                # Use same mapping function as for trades
                if 'df' in locals() or 'df' in globals():
                    df_sl_history_sq['index'] = df_sl_history_sq['timestamp'].apply(_map_ts_to_index)
                    df_sl_valid_sq = df_sl_history_sq.dropna(subset=['index']).copy()

                    if not df_sl_valid_sq.empty:
                        # Filter SL history to only show during active positions
                        # For each trade, only show SL points between entry_time and exit_time
                        active_sl_segments = []

                        for _, trade in df_trades_sq.iterrows():
                            entry_time = trade['entry_time']
                            exit_time = trade['exit_time']

                            # Filter SL history for this trade's active period
                            trade_sl = df_sl_valid_sq[
                                (df_sl_valid_sq['timestamp'] >= entry_time) &
                                (df_sl_valid_sq['timestamp'] <= exit_time)
                            ].copy()

                            if not trade_sl.empty:
                                active_sl_segments.append(trade_sl)

                        # Draw each segment separately (one per trade)
                        total_points = 0
                        for segment in active_sl_segments:
                            segment = segment.sort_values('index')

                            trace_sl_line_sq = go.Scatter(
                                x=segment['index'],
                                y=segment['sl_price'],
                                mode='lines',
                                name='Trailing Stop (Square)',
                                line=dict(
                                    color='violet',  # Violet dashed line for trailing stop
                                    width=1,
                                    dash='dash'  # Dashed line style
                                ),
                                showlegend=(total_points == 0),  # Only show legend for first segment
                                hovertemplate='SL (Square): %{y:.2f}<br>%{x}<extra></extra>'
                            )
                            fig.add_trace(trace_sl_line_sq, row=price_row, col=1)
                            total_points += len(segment)

                        print(f"[INFO] Square Trailing Stop line added: {total_points} points across {len(active_sl_segments)} trades")
            except Exception as e:
                print(f"[WARN] Failed to load/plot Square SL history: {e}")

    # Wyckoff strategy SL history (red dashed line, only during active positions)
    if ENABLE_VWAP_WYCKOFF_STRATEGY and USE_WYCKOFF_ATR_TRAILING_STOP:
        sl_history_path_wyckoff = OUTPUTS_DIR / "trading" / f"sl_history_vwap_wyckoff_{date_range_str_local}.csv"
        trades_path_wyckoff = OUTPUTS_DIR / "trading" / f"tracking_record_vwap_wyckoff_{date_range_str_local}.csv"

        if sl_history_path_wyckoff.exists() and trades_path_wyckoff.exists():
            try:
                print(f"[INFO] Loading Wyckoff SL history from {sl_history_path_wyckoff.name}")
                df_sl_history_wy = pd.read_csv(sl_history_path_wyckoff, sep=';', decimal=',', parse_dates=['timestamp'])
                df_trades_wy = pd.read_csv(trades_path_wyckoff, sep=';', decimal=',', parse_dates=['entry_time', 'exit_time'])

                # Map timestamps to index
                if not pd.api.types.is_datetime64_any_dtype(df_sl_history_wy['timestamp']):
                    df_sl_history_wy['timestamp'] = pd.to_datetime(df_sl_history_wy['timestamp'])

                if 'df' in locals():
                    df_sl_history_wy['index'] = df_sl_history_wy['timestamp'].apply(_map_ts_to_index)
                    df_sl_valid_wy = df_sl_history_wy.dropna(subset=['index']).copy()

                    if not df_sl_valid_wy.empty:
                        # Filter active segments
                        active_sl_segments_wy = []
                        for _, trade in df_trades_wy.iterrows():
                            entry_time = trade['entry_time']
                            exit_time = trade['exit_time']
                            seg = df_sl_valid_wy[
                                (df_sl_valid_wy['timestamp'] >= entry_time) & 
                                (df_sl_valid_wy['timestamp'] <= exit_time)
                            ].copy()
                            if not seg.empty:
                                active_sl_segments_wy.append(seg)
                        
                        total_points_wy = 0
                        for segment in active_sl_segments_wy:
                            segment = segment.sort_values('index')
                            trace_sl_wy = go.Scatter(
                                x=segment['index'],
                                y=segment['sl_price'],
                                mode='lines',
                                name='Trailing Stop (Wyckoff)',
                                line=dict(color='red', width=1, dash='dash'),
                                showlegend=(total_points_wy == 0),
                                hovertemplate='SL (Wyckoff): %{y:.2f}<br>%{x}<extra></extra>'
                            )
                            fig.add_trace(trace_sl_wy, row=price_row, col=1)
                            total_points_wy += len(segment)
                        print(f"[INFO] Wyckoff Trailing Stop line added: {total_points_wy} points")

            except Exception as e:
                print(f"[WARN] Failed to load/plot Wyckoff SL history: {e}")

    # Momentum strategy SL history (violet solid line, only during active positions)
    sl_history_path_momentum = OUTPUTS_DIR / "trading" / f"sl_history_vwap_momentum_{date_range_str_local}.csv"
    trades_path_momentum = OUTPUTS_DIR / "trading" / f"tracking_record_vwap_momentum_{date_range_str_local}.csv"

    if ENABLE_VWAP_MOMENTUM_STRATEGY and sl_history_path_momentum.exists() and trades_path_momentum.exists():
        try:
            print(f"[INFO] Loading Momentum SL history from {sl_history_path_momentum.name}")
            df_sl_history_mom = pd.read_csv(sl_history_path_momentum, sep=';', decimal=',', parse_dates=['timestamp'])
            df_trades_mom = pd.read_csv(trades_path_momentum, sep=';', decimal=',', parse_dates=['entry_time', 'exit_time'])

            # Map timestamps to index
            if not pd.api.types.is_datetime64_any_dtype(df_sl_history_mom['timestamp']):
                df_sl_history_mom['timestamp'] = pd.to_datetime(df_sl_history_mom['timestamp'])

            # Use same mapping function as for trades
            if 'df' in locals() or 'df' in globals():
                df_sl_history_mom['index'] = df_sl_history_mom['timestamp'].apply(_map_ts_to_index)
                df_sl_valid_mom = df_sl_history_mom.dropna(subset=['index']).copy()

                if not df_sl_valid_mom.empty:
                    # Filter SL history to only show during active positions
                    # For each trade, only show SL points between entry_time and exit_time
                    active_sl_segments = []

                    for _, trade in df_trades_mom.iterrows():
                        entry_time = trade['entry_time']
                        exit_time = trade['exit_time']

                        # Filter SL history for this trade's active period
                        trade_sl = df_sl_valid_mom[
                            (df_sl_valid_mom['timestamp'] >= entry_time) &
                            (df_sl_valid_mom['timestamp'] <= exit_time)
                        ].copy()

                        if not trade_sl.empty:
                            active_sl_segments.append(trade_sl)

                    # Draw each segment separately (one per trade)
                    total_points = 0
                    for segment in active_sl_segments:
                        segment = segment.sort_values('index')

                        trace_sl_line_mom = go.Scatter(
                            x=segment['index'],
                            y=segment['sl_price'],
                            mode='lines',
                            name='Trailing Stop (Momentum)',
                            line=dict(
                                color='violet',  # Violet dashed line for trailing stop
                                width=1,
                                dash='dash'  # Dashed line style
                            ),
                            showlegend=(total_points == 0),  # Only show legend for first segment
                            hovertemplate='SL (Momentum): %{y:.2f}<br>%{x}<extra></extra>'
                        )
                        fig.add_trace(trace_sl_line_mom, row=price_row, col=1)
                        total_points += len(segment)

                    print(f"[INFO] Momentum Trailing Stop line added: {total_points} points across {len(active_sl_segments)} trades")
        except Exception as e:
            print(f"[WARN] Failed to load/plot Momentum SL history: {e}")
    # --- END TRAILING STOP PLOTTING ---

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

    # ========================================================================
    # VWAP BANDS & ENTRY TIME ANALYSIS
    # ========================================================================
    if ENABLE_VWAP_TIME_STRATEGY:
        # Encontrar el índice más cercano a la hora de entrada
        if start_date == end_date:
            target_entry_time = pd.to_datetime(f"{start_date} {VWAP_TIME_ENTRY}")
        else:
            target_entry_time = pd.to_datetime(f"{start_date} {VWAP_TIME_ENTRY}")

        # Buscar el registro más cercano a la hora de entrada de la estrategia
        df_entry_time = df[df['timestamp'].dt.time == pd.to_datetime(VWAP_TIME_ENTRY).time()]

        if not df_entry_time.empty:
            entry_time_index = df_entry_time.iloc[0]['index']

            # Calcular máximo y mínimo desde 15:30 hasta VWAP_TIME_ENTRY
            bands_start_time = pd.to_datetime(VWAP_BANDS_START_TIME).time()
            entry_time = pd.to_datetime(VWAP_TIME_ENTRY).time()

            df_range = df[(df['timestamp'].dt.time >= bands_start_time) &
                         (df['timestamp'].dt.time <= entry_time)]

            if not df_range.empty:
                day_high = df_range['high'].max()
                day_low = df_range['low'].min()
                day_range = day_high - day_low

                # Obtener precio en el momento de entrada
                entry_price = df_entry_time.iloc[0]['close']
                vwap_fast_at_entry = df_entry_time.iloc[0]['vwap_fast']

                # Calcular porcentajes en relación al rango del día
                if day_range > 0:
                    pct_from_low = ((entry_price - day_low) / day_range) * 100
                    pct_from_high = ((day_high - entry_price) / day_range) * 100
                    annotation_text = f"Entry Time {pct_from_high:.1f}%/{pct_from_low:.1f}%"
                else:
                    annotation_text = "Entry Time"

                print(f"[INFO] Day range ({bands_start_time}-{entry_time}): High={day_high:.2f}, Low={day_low:.2f}, Range={day_range:.2f}")
                print(f"[INFO] Entry price: {entry_price:.2f}, Distance from high: {pct_from_high:.1f}%, Distance from low: {pct_from_low:.1f}%")
            else:
                annotation_text = "Entry Time"

            # Añadir línea vertical AZUL
            fig.add_vline(x=entry_time_index, line_width=1, line_dash="dot",
                         line_color="blue", row=price_row, col=1,
                         annotation_text=annotation_text,
                         annotation_position="top right",
                         annotation_font_color="blue")
            print(f"[INFO] Entry Time line added at {VWAP_TIME_ENTRY}")

    # ========================================================================
    # VWAP BANDS (Standard Deviation)
    # ========================================================================
    if DRAW_VWAP_BANDS and 'vwap_fast' in df.columns:
        # Filtrar datos desde VWAP_BANDS_START_TIME
        bands_start_time = pd.to_datetime(VWAP_BANDS_START_TIME).time()
        df_bands = df[df['timestamp'].dt.time >= bands_start_time].copy()

        if not df_bands.empty:
            # Calcular desviación estándar del precio respecto al VWAP Fast
            df_bands['price_deviation'] = df_bands['close'] - df_bands['vwap_fast']
            std_dev = df_bands['price_deviation'].expanding().std()

            # Bandas 2 sigma
            upper_band_2sigma = df_bands['vwap_fast'] + 2 * std_dev
            lower_band_2sigma = df_bands['vwap_fast'] - 2 * std_dev

            # Bandas 3 sigma
            upper_band_3sigma = df_bands['vwap_fast'] + 3 * std_dev
            lower_band_3sigma = df_bands['vwap_fast'] - 3 * std_dev

            # Dibujar bandas 2 sigma
            fig.add_trace(go.Scatter(
                x=df_bands['index'],
                y=upper_band_2sigma,
                mode='lines',
                name='VWAP +2σ',
                line=dict(color='rgba(255, 165, 0, 0.4)', width=1, dash='dash'),
                showlegend=True
            ), row=price_row, col=1)

            fig.add_trace(go.Scatter(
                x=df_bands['index'],
                y=lower_band_2sigma,
                mode='lines',
                name='VWAP -2σ',
                line=dict(color='rgba(255, 165, 0, 0.4)', width=1, dash='dash'),
                showlegend=True
            ), row=price_row, col=1)

            # Dibujar bandas 3 sigma
            fig.add_trace(go.Scatter(
                x=df_bands['index'],
                y=upper_band_3sigma,
                mode='lines',
                name='VWAP +3σ',
                line=dict(color='rgba(255, 0, 0, 0.3)', width=1, dash='dot'),
                showlegend=True
            ), row=price_row, col=1)

            fig.add_trace(go.Scatter(
                x=df_bands['index'],
                y=lower_band_3sigma,
                mode='lines',
                name='VWAP -3σ',
                line=dict(color='rgba(255, 0, 0, 0.3)', width=1, dash='dot'),
                showlegend=True
            ), row=price_row, col=1)

            print(f"[INFO] VWAP bands (2σ and 3σ) added from {VWAP_BANDS_START_TIME}")

    # Configurar layout
    # Título: mostrar solo una fecha si start_date == end_date
    strategy_info = get_strategy_info_compact()

    # Calculate day profit from trades
    day_profit_usd = 0
    if df_trades is not None and not df_trades.empty and 'pnl_usd' in df_trades.columns:
        day_profit_usd = df_trades['pnl_usd'].sum()

    # Format profit with sign
    profit_str = f"Day_profit: ${day_profit_usd:,.0f}"

    if start_date == end_date:
        # Calculate day of week for single date
        date_obj = datetime.strptime(start_date, "%Y%m%d")
        day_of_week = date_obj.isoweekday()  # 1=Monday, 2=Tuesday, ..., 7=Sunday
        day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
        day_name = day_names[day_of_week]
        title_text = f'{symbol.upper()} - {start_date} ({day_name}, DoW={day_of_week}) | {strategy_info} | {profit_str}'
    else:
        title_text = f'{symbol.upper()} - {start_date} -> {end_date} | {strategy_info} | {profit_str}'

    # Configurar layout general
    # Calcular altura según subplots activos
    if show_frequency_subplot and show_slope_subplot:
        height = 1200
    elif show_slope_subplot or show_frequency_subplot:
        height = 900
    else:
        height = 800  # Increased from 600 to 800 for better visibility when no subplots

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
        # title='Price',
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

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from pathlib import Path
from config import START_DATE, END_DATE, FRACTALS_DIR, PLOT_MINOR_FRACTALS, PLOT_MAJOR_FRACTALS, PLOT_MINOR_DOTS, PLOT_MAJOR_DOTS, HIDE_FREQUENCY_INDICATOR, PLOT_VWAP, VWAP_FAST, VWAP_SLOW, SHOW_REGRESSION_CHANNEL, PRICE_EJECTION_TRIGGER, OVER_PRICE_EJECTION_TRIGGER
from calculate_vwap import calculate_vwap

def plot_range_chart(df, df_fractals_minor, df_fractals_major, start_date, end_date, symbol='NQ', rsi_levels=None, fibo_levels=None, divergences=None, channel_params=None, df_metrics=None):
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

    # Determinar si se necesita subplot para métricas
    # Solo crear subplot si hay métricas Y no está oculto el indicador
    has_metrics = df_metrics is not None and not df_metrics.empty
    show_frequency_subplot = has_metrics and not HIDE_FREQUENCY_INDICATOR

    if show_frequency_subplot:
        # Crear figura con 2 subplots
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{symbol.upper()} - Price & Fractals', 'Frecuencia de Fractales (invertido: ↑ = consolidación)')
        )
        price_row = 1
        metrics_row = 2
    else:
        # Crear figura simple
        fig = go.Figure()
        price_row = None

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
    if show_frequency_subplot:
        fig.add_trace(trace_price, row=price_row, col=1)
    else:
        fig.add_trace(trace_price)

    # Añadir indicador VWAP
    if PLOT_VWAP:
        # VWAP Rápido (Fast - Magenta)
        df['vwap_fast'] = calculate_vwap(df, period=VWAP_FAST)
        df_vwap_fast = df[df['vwap_fast'].notna()].copy()

        if not df_vwap_fast.empty:
            trace_vwap_fast = go.Scatter(
                x=df_vwap_fast['index'],
                y=df_vwap_fast['vwap_fast'],
                mode='lines',
                name=f'VWAP Fast({VWAP_FAST})',
                line=dict(color='magenta', width=1.5),
                opacity=0.8,
                hovertemplate='<b>VWAP Fast</b>: %{y:.2f}<extra></extra>'
            )
            if show_frequency_subplot:
                fig.add_trace(trace_vwap_fast, row=price_row, col=1)
            else:
                fig.add_trace(trace_vwap_fast)

            print(f"[INFO] VWAP Fast({VWAP_FAST}) añadido al gráfico: {len(df_vwap_fast)} puntos válidos")

        # VWAP Lento (Slow - Verde)
        df['vwap_slow'] = calculate_vwap(df, period=VWAP_SLOW)
        df_vwap_slow = df[df['vwap_slow'].notna()].copy()

        if not df_vwap_slow.empty:
            trace_vwap_slow = go.Scatter(
                x=df_vwap_slow['index'],
                y=df_vwap_slow['vwap_slow'],
                mode='lines',
                name=f'VWAP Slow({VWAP_SLOW})',
                line=dict(color='green', width=1),
                opacity=0.8,
                hovertemplate='<b>VWAP Slow</b>: %{y:.2f}<extra></extra>'
            )
            if show_frequency_subplot:
                fig.add_trace(trace_vwap_slow, row=price_row, col=1)
            else:
                fig.add_trace(trace_vwap_slow)

            print(f"[INFO] VWAP Slow({VWAP_SLOW}) añadido al gráfico: {len(df_vwap_slow)} puntos válidos")

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
            if show_frequency_subplot:
                fig.add_trace(trace_ejection, row=price_row, col=1)
            else:
                fig.add_trace(trace_ejection)

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
            if show_frequency_subplot:
                fig.add_trace(trace_over_ejection, row=price_row, col=1)
            else:
                fig.add_trace(trace_over_ejection)

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
        if show_frequency_subplot:
            fig.add_trace(trace_minor_line, row=price_row, col=1)
        else:
            fig.add_trace(trace_minor_line)

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
            if show_frequency_subplot:
                fig.add_trace(trace_minor_dots, row=price_row, col=1)
            else:
                fig.add_trace(trace_minor_dots)

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
        if show_frequency_subplot:
            fig.add_trace(trace_major_line, row=price_row, col=1)
        else:
            fig.add_trace(trace_major_line)

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
        if show_frequency_subplot:
            fig.add_trace(trace_upper, row=price_row, col=1)
        else:
            fig.add_trace(trace_upper)

        # Canal Inferior
        trace_lower = go.Scatter(
            x=x_vals, y=y_low_vals, mode='lines', name='Channel Lower',
            line=dict(color='red', width=1), opacity=0.6, hoverinfo='skip'
        )
        if show_frequency_subplot:
            fig.add_trace(trace_lower, row=price_row, col=1)
        else:
            fig.add_trace(trace_lower)

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
            if show_frequency_subplot:
                fig.add_trace(trace_clone, row=price_row, col=1)
            else:
                fig.add_trace(trace_clone)

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
    if start_date == end_date:
        title_text = f'{symbol.upper()} - {start_date}'
    else:
        title_text = f'{symbol.upper()} - {start_date} -> {end_date}'

    if show_frequency_subplot:
        fig.update_layout(
            title=title_text,
            template='plotly_white',
            hovermode='closest',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial", size=12, color="#333333"),
            showlegend=True,
            height=1000,
            xaxis_title="",
            yaxis_title=""
        )
    else:
        fig.update_layout(
            title=title_text,
            template='plotly_white',
            hovermode='closest',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial", size=12, color="#333333"),
            showlegend=True,
            height=900,
            xaxis_title="",
            yaxis_title=""
        )

    # Configurar eje Y - horizontal grid enabled, marco izquierdo gris suave
    if show_frequency_subplot:
        # Eje Y para precio (row 1) - con marco lateral izquierdo gris
        fig.update_yaxes(
            showgrid=True, gridcolor='#e0e0e0', gridwidth=0.5,
            showline=True, linewidth=1, linecolor='#d3d3d3',
            tickcolor='gray', tickfont=dict(color='gray'),
            tickformat=',',
            row=price_row, col=1
        )
        # Eje Y para métricas (row 2) - Frecuencia invertida con marco lateral izquierdo gris
        fig.update_yaxes(
            title='Frecuencia (↑ alta)',
            showgrid=True, gridcolor='#e0e0e0', gridwidth=0.5,
            showline=True, linewidth=1, linecolor='#d3d3d3',
            tickcolor='gray', tickfont=dict(color='gray'),
            row=metrics_row, col=1
        )
    else:
        fig.update_yaxes(
            showgrid=True, gridcolor='#e0e0e0', gridwidth=0.5,
            showline=True, linewidth=1, linecolor='#d3d3d3',
            tickformat=',',
            tickcolor='gray', tickfont=dict(color='gray')
        )

    # Crear carpeta de salida si no existe
    output_dir = 'outputs'
    os.makedirs(output_dir, exist_ok=True)

    # Guardar gráfico
    if start_date == end_date:
        date_range_str = start_date
    else:
        date_range_str = f"{start_date}_{end_date}"
    output_html = os.path.join(output_dir, f'nq_{date_range_str}.html')
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

    plot_range_chart(df, df_fractals_minor, df_fractals_major, START_DATE, END_DATE, symbol=symbol)

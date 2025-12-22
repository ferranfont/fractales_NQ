import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from pathlib import Path
from config import START_DATE, END_DATE, FRACTALS_DIR, PLOT_MINOR_FRACTALS, PLOT_MAJOR_FRACTALS, PLOT_MINOR_DOTS, PLOT_MAJOR_DOTS

def plot_range_chart(df, df_fractals_minor, df_fractals_major, start_date, end_date, symbol='GC', rsi_levels=None, fibo_levels=None, divergences=None, channel_params=None, df_metrics=None):
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
    print(f"Generando gráfico para rango: {start_date} -> {end_date}")
    print(f"Datos cargados: {len(df)} registros")

    # Crear índice numérico para evitar huecos de fines de semana
    df = df.reset_index(drop=True)
    df['index'] = df.index

    # Determinar si se necesita subplot para métricas
    has_metrics = df_metrics is not None and not df_metrics.empty

    if has_metrics:
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
    if has_metrics:
        fig.add_trace(trace_price, row=price_row, col=1)
    else:
        fig.add_trace(trace_price)

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
        if has_metrics:
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
            if has_metrics:
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
            line=dict(color='blue', width=2),
            hoverinfo='skip'
        )
        if has_metrics:
            fig.add_trace(trace_major_line, row=price_row, col=1)
        else:
            fig.add_trace(trace_major_line)

    # Añadir Canal de Regresión
    if channel_params:
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
        if has_metrics:
            fig.add_trace(trace_upper, row=price_row, col=1)
        else:
            fig.add_trace(trace_upper)

        # Canal Inferior
        trace_lower = go.Scatter(
            x=x_vals, y=y_low_vals, mode='lines', name='Channel Lower',
            line=dict(color='red', width=1), opacity=0.6, hoverinfo='skip'
        )
        if has_metrics:
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
            if has_metrics:
                fig.add_trace(trace_clone, row=price_row, col=1)
            else:
                fig.add_trace(trace_clone)

    # Añadir PUNTOS NARANJAS en el gráfico de precio cuando hay trigger de consolidación
    if has_metrics and df_metrics is not None:
        # Filtrar fractales donde choppiness_trigger == 1
        df_triggers = df_metrics[df_metrics['choppiness_trigger'] == 1].copy()

        if not df_triggers.empty:
            # Mapear timestamps a índices
            df_triggers['index'] = df_triggers['timestamp'].apply(
                lambda ts: df[df['timestamp'] == ts].index[0] if len(df[df['timestamp'] == ts]) > 0 else None
            )
            df_triggers = df_triggers.dropna(subset=['index'])

            if not df_triggers.empty:
                # Añadir puntos naranjas en el gráfico de precio
                trace_triggers = go.Scatter(
                    x=df_triggers['index'],
                    y=df_triggers['price'],
                    mode='markers',
                    name='Consolidación detectada',
                    marker=dict(
                        color='orange',
                        size=8,
                        symbol='circle',
                        line=dict(color='darkorange', width=1)
                    ),
                    hovertemplate='<b>CONSOLIDACIÓN</b><br>Price: %{y:.2f}<extra></extra>'
                )
                if has_metrics:
                    fig.add_trace(trace_triggers, row=price_row, col=1)
                else:
                    fig.add_trace(trace_triggers)

                print(f"[DEBUG] Puntos de consolidación detectados: {len(df_triggers)}")

    # Añadir subplot de métricas - SEGUNDOS entre fractales
    if has_metrics:
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
    num_ticks = 10
    tick_indices = [int(i) for i in range(0, len(df), max(1, len(df)//num_ticks))]
    tick_vals = df.iloc[tick_indices]['index']
    # Ensure 'timestamp' column is datetime for dt.strftime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    tick_text = df.iloc[tick_indices]['timestamp'].dt.strftime('%Y-%m-%d | %H:%M:%S')

    if has_metrics:
        fig.update_xaxes(
            tickmode='array', tickvals=tick_vals, ticktext=tick_text,
            tickangle=-45, showgrid=False, gridcolor='#f0f0f0',
            row=metrics_row, col=1
        )
    else:
        fig.update_xaxes(
            tickmode='array', tickvals=tick_vals, ticktext=tick_text,
            tickangle=-45, showgrid=False, gridcolor='#f0f0f0'
        )

    # Configurar layout
    if has_metrics:
        fig.update_layout(
            title=f'{symbol.upper()} - {start_date} -> {end_date}',
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
            title=f'{symbol.upper()} - {start_date} -> {end_date}',
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

    # Configurar eje Y - horizontal grid enabled, vertical grid disabled
    if has_metrics:
        # Eje Y para precio (row 1)
        fig.update_yaxes(
            showgrid=True, gridcolor='#e0e0e0', gridwidth=0.5,
            showline=True, linewidth=1, linecolor='gray',
            tickcolor='gray', tickfont=dict(color='gray'),
            row=price_row, col=1
        )
        # Eje Y para métricas (row 2) - Frecuencia invertida
        fig.update_yaxes(
            title='Frecuencia (↑ alta)',
            showgrid=True, gridcolor='#e0e0e0', gridwidth=0.5,
            showline=True, linewidth=1, linecolor='gray',
            tickcolor='gray', tickfont=dict(color='gray'),
            row=metrics_row, col=1
        )
    else:
        fig.update_yaxes(
            showgrid=True, gridcolor='#e0e0e0', gridwidth=0.5,
            showline=True, linewidth=1, linecolor='gray',
            tickcolor='gray', tickfont=dict(color='gray')
        )

    # Crear carpeta de salida si no existe
    output_dir = 'outputs'
    os.makedirs(output_dir, exist_ok=True)

    # Guardar gráfico
    date_range_str = f"{start_date}_{end_date}"
    output_html = os.path.join(output_dir, f'gc_{date_range_str}.html')
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

    # Extraer símbolo del primer archivo
    first_file = DATA_DIR / f"gc_{START_DATE}.csv"
    symbol = 'GC'  # default
    if first_file.exists():
        symbol = first_file.stem.split('_')[0]

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

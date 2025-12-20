import pandas as pd
import plotly.graph_objects as go
import os
from pathlib import Path
from config import START_DATE, END_DATE, FRACTALS_DIR, PLOT_MINOR_FRACTALS, PLOT_MAJOR_FRACTALS

def plot_range_chart(df, df_fractals_minor, df_fractals_major, start_date, end_date, rsi_levels=None, fibo_levels=None, divergences=None):
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

    Returns:
        dict con información del gráfico generado o None si hay error
    """
    print(f"Generando gráfico para rango: {start_date} -> {end_date}")
    print(f"Datos cargados: {len(df)} registros")

    # Crear figura simple
    fig = go.Figure()

    # Crear índice numérico para evitar huecos de fines de semana
    df = df.reset_index(drop=True)
    df['index'] = df.index

    # Línea de precio (close) - gris con transparencia
    fig.add_trace(go.Scatter(
        x=df['index'],
        y=df['close'],
        mode='lines',
        name='Price',
        line=dict(color='gray', width=1),
        opacity=0.5,
        text=df['timestamp'],
        hovertemplate='<b>Price</b><br>Time: %{text}<br>Price: %{y:.2f}<extra></extra>'
    ))

    # Añadir líneas ZigZag y marcadores de fractales MINOR
    if PLOT_MINOR_FRACTALS and df_fractals_minor is not None and not df_fractals_minor.empty:
        # Mapear timestamps de fractales MINOR a índices
        df_fractals_minor = df_fractals_minor.copy()
        df_fractals_minor['index'] = df_fractals_minor['timestamp'].apply(
            lambda ts: df[df['timestamp'] == ts].index[0] if len(df[df['timestamp'] == ts]) > 0 else None
        )
        df_fractals_minor = df_fractals_minor.dropna(subset=['index'])

        # Línea ZigZag MINOR - dodgerblue
        fig.add_trace(go.Scatter(
            x=df_fractals_minor['index'],
            y=df_fractals_minor['price'],
            mode='lines',
            name='ZigZag Minor',
            line=dict(color='dodgerblue', width=1),
            opacity=0.7,
            text=df_fractals_minor['timestamp'],
            hovertemplate='<b>Minor</b><br>Time: %{text}<br>Price: %{y:.2f}<extra></extra>'
        ))

        # Puntos MINOR - dodgerblue pequeños
        fig.add_trace(go.Scatter(
            x=df_fractals_minor['index'],
            y=df_fractals_minor['price'],
            mode='markers',
            name='Fractales Minor',
            marker=dict(
                color='cornflowerblue',
                size=3,
                symbol='circle'
            ),
            opacity=1,
            text=df_fractals_minor['timestamp'],
            hovertemplate='<b>Minor</b><br>Time: %{text}<br>Price: %{y:.2f}<extra></extra>'
        ))

    # Añadir líneas ZigZag y marcadores de fractales MAJOR
    if PLOT_MAJOR_FRACTALS and df_fractals_major is not None and not df_fractals_major.empty:
        # Mapear timestamps de fractales MAJOR a índices
        df_fractals_major = df_fractals_major.copy()
        df_fractals_major['index'] = df_fractals_major['timestamp'].apply(
            lambda ts: df[df['timestamp'] == ts].index[0] if len(df[df['timestamp'] == ts]) > 0 else None
        )
        df_fractals_major = df_fractals_major.dropna(subset=['index'])

        # Línea ZigZag MAJOR - AZUL
        fig.add_trace(go.Scatter(
            x=df_fractals_major['index'],
            y=df_fractals_major['price'],
            mode='lines',
            name='ZigZag Major',
            line=dict(color='blue', width=2),
            text=df_fractals_major['timestamp'],
            hovertemplate='<b>Major</b><br>Time: %{text}<br>Price: %{y:.2f}<extra></extra>'
        ))

        # Separar picos y valles MAJOR para los marcadores
        df_picos_major = df_fractals_major[df_fractals_major['type'] == 'PICO'].copy()
        df_valles_major = df_fractals_major[df_fractals_major['type'] == 'VALLE'].copy()

        # PICOS - círculos verdes rellenos
        if not df_picos_major.empty:
            fig.add_trace(go.Scatter(
                x=df_picos_major['index'],
                y=df_picos_major['price'],
                mode='markers',
                name='PICO Major',
                marker=dict(
                    color='green',
                    size=8,
                    symbol='circle'
                ),
                text=df_picos_major['timestamp'],
                hovertemplate='<b>PICO Major</b><br>Time: %{text}<br>Price: %{y:.2f}<extra></extra>'
            ))

        # VALLES - círculos rojos rellenos
        if not df_valles_major.empty:
            fig.add_trace(go.Scatter(
                x=df_valles_major['index'],
                y=df_valles_major['price'],
                mode='markers',
                name='VALLE Major',
                marker=dict(
                    color='red',
                    size=8,
                    symbol='circle'
                ),
                text=df_valles_major['timestamp'],
                hovertemplate='<b>VALLE Major</b><br>Time: %{text}<br>Price: %{y:.2f}<extra></extra>'
            ))

    # Configurar eje X con etiquetas de fecha personalizadas
    # Seleccionar ~20 puntos distribuidos uniformemente para las etiquetas
    step = max(1, len(df) // 20)
    tickvals = list(range(0, len(df), step))
    ticktext = [df.loc[i, 'timestamp'] for i in tickvals]

    # Configurar layout
    fig.update_layout(
        title=f'Gold (GC) - {start_date} -> {end_date}',
        template='plotly_white',
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(
            family='Arial',
            size=12,
            color='#333333'
        ),
        height=800,
        showlegend=True,
        xaxis_title="Tiempo",
        yaxis_title="Precio"
    )

    # Configurar eje X con etiquetas de fecha
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor='gray',
        tickcolor='gray',
        tickfont=dict(color='gray'),
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext,
        tickangle=-45
    )

    # Configurar eje Y
    fig.update_yaxes(
        showgrid=True,
        gridcolor='#f0f0f0',
        showline=True,
        linewidth=1,
        linecolor='gray',
        tickcolor='gray',
        tickfont=dict(color='gray'),
        side='left'
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

    print(f"Generando gráfico para: {START_DATE} -> {END_DATE}")

    # Cargar datos del rango
    df = load_date_range(START_DATE, END_DATE)
    if df is None:
        print("Error cargando datos")
        exit(1)

    # Cargar fractales
    date_range_str = f"{START_DATE}_{END_DATE}"
    fractal_minor_path = FRACTALS_DIR / f"gc_fractals_minor_{date_range_str}.csv"
    fractal_major_path = FRACTALS_DIR / f"gc_fractals_major_{date_range_str}.csv"

    df_fractals_minor = None
    df_fractals_major = None

    if fractal_minor_path.exists():
        df_fractals_minor = pd.read_csv(fractal_minor_path)
    if fractal_major_path.exists():
        df_fractals_major = pd.read_csv(fractal_major_path)

    plot_range_chart(df, df_fractals_minor, df_fractals_major, START_DATE, END_DATE)

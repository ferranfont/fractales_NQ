import pandas as pd
import plotly.graph_objects as go
import os
from pathlib import Path
from config import DIA, FRACTALS_DIR

def plot_day_chart(dia):
    """
    Crea un gráfico con línea de precio y fractales ZigZag para el día especificado.

    Args:
        dia: Fecha en formato YYYY-MM-DD
    """
    # Ruta al archivo CSV
    csv_path = f"data/gc_{dia}.csv"

    if not os.path.exists(csv_path):
        print(f"Error: No se encuentra el archivo {csv_path}")
        return

    # Leer datos de precio
    print(f"Cargando datos de: {csv_path}")
    df = pd.read_csv(csv_path)

    # Verificar columnas requeridas
    required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"Error: Faltan columnas: {missing_cols}")
        return

    print(f"Datos cargados: {len(df)} registros")

    # Cargar fractales si existen
    fractal_minor_path = FRACTALS_DIR / f"gc_fractals_minor_{dia}.csv"
    fractal_major_path = FRACTALS_DIR / f"gc_fractals_major_{dia}.csv"

    df_fractals_minor = None
    df_fractals_major = None

    if fractal_minor_path.exists():
        df_fractals_minor = pd.read_csv(fractal_minor_path)
        print(f"Fractales MINOR cargados: {len(df_fractals_minor)}")
    else:
        print(f"No se encontraron fractales MINOR para {dia}")

    if fractal_major_path.exists():
        df_fractals_major = pd.read_csv(fractal_major_path)
        print(f"Fractales MAJOR cargados: {len(df_fractals_major)}")
    else:
        print(f"No se encontraron fractales MAJOR para {dia}")

    # Crear figura
    fig = go.Figure()

    # Línea de precio (close) - gris con transparencia
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['close'],
        mode='lines',
        name='Price',
        line=dict(color='gray', width=1),
        opacity=0.5
    ))

    # Añadir líneas ZigZag y marcadores de fractales
    if df_fractals_minor is not None and not df_fractals_minor.empty:
        # Línea ZigZag MINOR - gris más opaco
        fig.add_trace(go.Scatter(
            x=df_fractals_minor['timestamp'],
            y=df_fractals_minor['price'],
            mode='lines',
            name='ZigZag Minor',
            line=dict(color='gray', width=1),
            opacity=0.85,
            hovertemplate='<b>Minor</b><br>Time: %{x}<br>Price: %{y:.2f}<extra></extra>'
        ))

        # Puntos MINOR - grises pequeños
        fig.add_trace(go.Scatter(
            x=df_fractals_minor['timestamp'],
            y=df_fractals_minor['price'],
            mode='markers',
            name='Fractales Minor',
            marker=dict(
                color='gray',
                size=3,
                symbol='circle'
            ),
            opacity=0.85,
            hovertemplate='<b>Minor</b><br>Time: %{x}<br>Price: %{y:.2f}<extra></extra>'
        ))

    if df_fractals_major is not None and not df_fractals_major.empty:
        # Línea ZigZag MAJOR - AZUL
        fig.add_trace(go.Scatter(
            x=df_fractals_major['timestamp'],
            y=df_fractals_major['price'],
            mode='lines',
            name='ZigZag Major',
            line=dict(color='blue', width=2),
            hovertemplate='<b>Major</b><br>Time: %{x}<br>Price: %{y:.2f}<extra></extra>'
        ))

        # Separar picos y valles MAJOR para los marcadores
        df_picos_major = df_fractals_major[df_fractals_major['type'] == 'PICO'].copy()
        df_valles_major = df_fractals_major[df_fractals_major['type'] == 'VALLE'].copy()

        # PICOS - círculos verdes rellenos
        if not df_picos_major.empty:
            fig.add_trace(go.Scatter(
                x=df_picos_major['timestamp'],
                y=df_picos_major['price'],
                mode='markers',
                name='PICO Major',
                marker=dict(
                    color='green',
                    size=5,
                    symbol='circle'
                ),
                hovertemplate='<b>PICO Major</b><br>Time: %{x}<br>Price: %{y:.2f}<extra></extra>'
            ))

        # VALLES - círculos rojos rellenos
        if not df_valles_major.empty:
            fig.add_trace(go.Scatter(
                x=df_valles_major['timestamp'],
                y=df_valles_major['price'],
                mode='markers',
                name='VALLE Major',
                marker=dict(
                    color='red',
                    size=5,
                    symbol='circle'
                ),
                hovertemplate='<b>VALLE Major</b><br>Time: %{x}<br>Price: %{y:.2f}<extra></extra>'
            ))

    # Configurar layout
    fig.update_layout(
        title=f'GL {dia}',
        xaxis_title='',
        yaxis_title='',
        template='plotly_white',
        hovermode=False,
        xaxis=dict(
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='gray',
            tickcolor='gray',
            tickfont=dict(color='gray'),
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            showline=True,
            linewidth=1,
            linecolor='gray',
            tickcolor='gray',
            tickfont=dict(color='gray'),
            side='left'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(
            family='Arial',
            size=12,
            color='#333333'
        )
    )

    # Crear carpeta de salida si no existe
    output_dir = 'outputs'
    os.makedirs(output_dir, exist_ok=True)

    # Guardar gráfico
    output_html = os.path.join(output_dir, f'gc_{dia}.html')
    print(f"Guardando gráfico en: {output_html}")
    fig.write_html(output_html)
    print(f"Gráfico guardado exitosamente")

    # Mostrar en navegador
    import webbrowser
    webbrowser.open(f'file://{os.path.abspath(output_html)}')
    print(f"Abriendo en navegador...")

if __name__ == "__main__":
    from config import DIA
    print(f"Generando gráfico para: {DIA}")
    plot_day_chart(DIA)

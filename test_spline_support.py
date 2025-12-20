"""
Script de prueba para líneas de soporte/resistencia usando interpolación
Compara PCHIP vs Cubic Spline para unir fractales VALLE y PICO
"""
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import PchipInterpolator, CubicSpline
from pathlib import Path
from config import START_DATE, END_DATE, FRACTALS_DIR
from find_fractals import load_date_range


def create_support_resistance_lines(df_fractals, df_price, method='pchip'):
    """
    Crea líneas de soporte (VALLES) y resistencia (PICOS) usando interpolación

    Args:
        df_fractals: DataFrame con fractales (debe tener columnas 'index', 'price', 'type')
        df_price: DataFrame de precios (para obtener el rango x completo)
        method: 'pchip' o 'spline' (cubic spline)

    Returns:
        dict con arrays de soporte y resistencia
    """
    # Separar PICOS y VALLES
    df_picos = df_fractals[df_fractals['type'] == 'PICO'].copy()
    df_valles = df_fractals[df_fractals['type'] == 'VALLE'].copy()

    result = {}

    # Crear línea de SOPORTE (VALLES)
    if not df_valles.empty and len(df_valles) >= 2:
        x_valles = df_valles['index'].values
        y_valles = df_valles['price'].values

        # Ordenar por índice
        sorted_indices = np.argsort(x_valles)
        x_valles = x_valles[sorted_indices]
        y_valles = y_valles[sorted_indices]

        # Crear interpolador
        if method == 'pchip':
            interpolator = PchipInterpolator(x_valles, y_valles)
        else:  # cubic spline
            interpolator = CubicSpline(x_valles, y_valles)

        # Generar puntos suaves entre el primer y último valle
        x_smooth = np.linspace(x_valles[0], x_valles[-1], num=500)
        y_smooth = interpolator(x_smooth)

        result['support'] = {
            'x': x_smooth,
            'y': y_smooth,
            'original_x': x_valles,
            'original_y': y_valles
        }

    # Crear línea de RESISTENCIA (PICOS)
    if not df_picos.empty and len(df_picos) >= 2:
        x_picos = df_picos['index'].values
        y_picos = df_picos['price'].values

        # Ordenar por índice
        sorted_indices = np.argsort(x_picos)
        x_picos = x_picos[sorted_indices]
        y_picos = y_picos[sorted_indices]

        # Crear interpolador
        if method == 'pchip':
            interpolator = PchipInterpolator(x_picos, y_picos)
        else:  # cubic spline
            interpolator = CubicSpline(x_picos, y_picos)

        # Generar puntos suaves entre el primer y último pico
        x_smooth = np.linspace(x_picos[0], x_picos[-1], num=500)
        y_smooth = interpolator(x_smooth)

        result['resistance'] = {
            'x': x_smooth,
            'y': y_smooth,
            'original_x': x_picos,
            'original_y': y_picos
        }

    return result


def plot_comparison():
    """
    Genera gráfico de comparación entre PCHIP y Cubic Spline
    """
    print("Cargando datos...")

    # Cargar datos de precio
    df = load_date_range(START_DATE, END_DATE)
    if df is None:
        print("Error cargando datos de precio")
        return

    df = df.reset_index(drop=True)
    df['index'] = df.index

    # Cargar fractales MAJOR
    date_range_str = f"{START_DATE}_{END_DATE}"
    fractal_major_path = FRACTALS_DIR / f"gc_fractals_major_{date_range_str}.csv"

    if not fractal_major_path.exists():
        print(f"Error: No se encontró {fractal_major_path}")
        print("Ejecuta primero: python main_quant.py")
        return

    df_fractals_major = pd.read_csv(fractal_major_path)

    # Mapear timestamps a índices
    df_fractals_major['index'] = df_fractals_major['timestamp'].apply(
        lambda ts: df[df['timestamp'] == ts].index[0] if len(df[df['timestamp'] == ts]) > 0 else None
    )
    df_fractals_major = df_fractals_major.dropna(subset=['index'])

    print(f"Fractales cargados: {len(df_fractals_major)}")

    # Generar líneas con ambos métodos
    print("\nGenerando líneas PCHIP...")
    lines_pchip = create_support_resistance_lines(df_fractals_major, df, method='pchip')

    print("Generando líneas Cubic Spline...")
    lines_spline = create_support_resistance_lines(df_fractals_major, df, method='spline')

    # Crear figura con 2 subplots para comparar
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('PCHIP Interpolation', 'Cubic Spline Interpolation'),
        vertical_spacing=0.1
    )

    # --- SUBPLOT 1: PCHIP ---
    # Precio
    fig.add_trace(go.Scatter(
        x=df['index'],
        y=df['close'],
        mode='lines',
        name='Price',
        line=dict(color='gray', width=0.5),
        opacity=0.3,
        showlegend=False
    ), row=1, col=1)

    # Línea de soporte PCHIP
    if 'support' in lines_pchip:
        fig.add_trace(go.Scatter(
            x=lines_pchip['support']['x'],
            y=lines_pchip['support']['y'],
            mode='lines',
            name='Support (PCHIP)',
            line=dict(color='red', width=2, dash='solid'),
            showlegend=True
        ), row=1, col=1)

        # Puntos originales VALLES
        fig.add_trace(go.Scatter(
            x=lines_pchip['support']['original_x'],
            y=lines_pchip['support']['original_y'],
            mode='markers',
            name='VALLES',
            marker=dict(color='darkred', size=8, symbol='circle'),
            showlegend=False
        ), row=1, col=1)

    # Línea de resistencia PCHIP
    if 'resistance' in lines_pchip:
        fig.add_trace(go.Scatter(
            x=lines_pchip['resistance']['x'],
            y=lines_pchip['resistance']['y'],
            mode='lines',
            name='Resistance (PCHIP)',
            line=dict(color='green', width=2, dash='solid'),
            showlegend=True
        ), row=1, col=1)

        # Puntos originales PICOS
        fig.add_trace(go.Scatter(
            x=lines_pchip['resistance']['original_x'],
            y=lines_pchip['resistance']['original_y'],
            mode='markers',
            name='PICOS',
            marker=dict(color='darkgreen', size=8, symbol='circle'),
            showlegend=False
        ), row=1, col=1)

    # --- SUBPLOT 2: Cubic Spline ---
    # Precio
    fig.add_trace(go.Scatter(
        x=df['index'],
        y=df['close'],
        mode='lines',
        name='Price',
        line=dict(color='gray', width=0.5),
        opacity=0.3,
        showlegend=False
    ), row=2, col=1)

    # Línea de soporte Spline
    if 'support' in lines_spline:
        fig.add_trace(go.Scatter(
            x=lines_spline['support']['x'],
            y=lines_spline['support']['y'],
            mode='lines',
            name='Support (Spline)',
            line=dict(color='red', width=2, dash='solid'),
            showlegend=True
        ), row=2, col=1)

        # Puntos originales VALLES
        fig.add_trace(go.Scatter(
            x=lines_spline['support']['original_x'],
            y=lines_spline['support']['original_y'],
            mode='markers',
            name='VALLES',
            marker=dict(color='darkred', size=8, symbol='circle'),
            showlegend=False
        ), row=2, col=1)

    # Línea de resistencia Spline
    if 'resistance' in lines_spline:
        fig.add_trace(go.Scatter(
            x=lines_spline['resistance']['x'],
            y=lines_spline['resistance']['y'],
            mode='lines',
            name='Resistance (Spline)',
            line=dict(color='green', width=2, dash='solid'),
            showlegend=True
        ), row=2, col=1)

        # Puntos originales PICOS
        fig.add_trace(go.Scatter(
            x=lines_spline['resistance']['original_x'],
            y=lines_spline['resistance']['original_y'],
            mode='markers',
            name='PICOS',
            marker=dict(color='darkgreen', size=8, symbol='circle'),
            showlegend=False
        ), row=2, col=1)

    # Layout
    fig.update_layout(
        title=f'Comparación: PCHIP vs Cubic Spline - {START_DATE} -> {END_DATE}',
        template='plotly_white',
        height=1200,
        showlegend=True
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')

    # Guardar
    output_path = Path('outputs') / 'test_spline_comparison.html'
    output_path.parent.mkdir(exist_ok=True)

    print(f"\nGuardando gráfico en: {output_path}")
    fig.write_html(str(output_path))

    # Abrir en navegador
    import webbrowser
    webbrowser.open(f'file://{output_path.absolute()}')

    print("[OK] Grafico generado exitosamente")
    print("\nComparación:")
    print("- PCHIP: Más conservador, evita oscilaciones artificiales")
    print("- Cubic Spline: Más suave, puede tener pequeñas oscilaciones")


if __name__ == "__main__":
    print("="*70)
    print("TEST: Líneas de Soporte/Resistencia con Interpolación")
    print("="*70)
    plot_comparison()

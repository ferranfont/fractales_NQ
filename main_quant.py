"""
Script principal de análisis cuantitativo para Nasaq (NQ)
Orquesta la ejecución de:
1. Detección de fractales (find_fractals.py)
2. Generación de gráfico (plot_day.py)
"""
from pathlib import Path
from config import START_DATE, END_DATE, DATA_DIR
from find_fractals import process_fractals_range
from find_reg_channel_scipy import calculate_channel
from find_choppiness import calculate_fractal_metrics, print_consolidation_table
from plot_day import plot_range_chart


def main_quant_range(start_date: str, end_date: str):
    """
    Ejecuta el pipeline completo de análisis cuantitativo para un rango de fechas

    Args:
        start_date: Fecha inicial en formato YYYY-MM-DD
        end_date: Fecha final en formato YYYY-MM-DD
    """
    print("\n" + "="*70)
    print("ANÁLISIS CUANTITATIVO - Nasdaq (NQ")
    print("="*70)
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
    date_range_str = f"{start_date}_{end_date}"
    symbol = fractals_result.get('symbol', 'GC')
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

    # 2. Generar gráfico
    print("\n" + "-"*70)
    print("PASO 2: GENERACIÓN DE GRÁFICO")
    print("-"*70)
    plot_result = plot_range_chart(
        fractals_result['df'],
        fractals_result['df_fractals_minor'],
        fractals_result['df_fractals_major'],
        start_date,
        end_date,
        symbol=fractals_result.get('symbol', 'GC'),
        rsi_levels=None,
        fibo_levels=None,
        divergences=None,
        channel_params=channel_params,
        df_metrics=df_fractals_metrics
    )
    if plot_result is None:
        print("[ERROR] Fallo en generación de gráfico")
        return None

    # 3. Guardar Modelo (Parámetros del Canal)
    if channel_params:
        import json
        from config import OUTPUTS_DIR
        
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        date_range_str = f"{start_date}_{end_date}"
        model_filename = OUTPUTS_DIR / f"channel_model_gc_{date_range_str}.json"
        
        # Añadir metadatos al modelo
        model_data = {
            'symbol': fractals_result.get('symbol', 'GC'),
            'start_date': start_date, 
            'end_date': end_date,
            'parameters': channel_params
        }
        
        with open(model_filename, 'w') as f:
            json.dump(model_data, f, indent=4)
            
        print("\n" + "-"*70)
        print("PASO 3: GUARDADO DE MODELO")
        print("-"*70)
        print(f"Modelo guardado en: {model_filename}")

    # 4. Resumen final
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    print(f"Rango analizado: {start_date} -> {end_date}")
    print(f"Registros procesados: {fractals_result['total_records']}")
    print(f"Fractales MINOR detectados: {fractals_result['minor_count']}")
    print(f"Fractales MAJOR detectados: {fractals_result['major_count']}")
    print(f"Gráfico generado: {plot_result['output_path']}")
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
    else:
        print("[ERROR] El análisis finalizó con errores\n")

"""
Script principal de análisis cuantitativo para Gold (GC)
Orquesta la ejecución de:
1. Detección de fractales (find_fractals.py)
2. Generación de gráfico (plot_day.py)
"""
from pathlib import Path
from config import START_DATE, END_DATE, DATA_DIR
from find_fractals import process_fractals_range
from plot_day import plot_range_chart


def main_quant_range(start_date: str, end_date: str):
    """
    Ejecuta el pipeline completo de análisis cuantitativo para un rango de fechas

    Args:
        start_date: Fecha inicial en formato YYYY-MM-DD
        end_date: Fecha final en formato YYYY-MM-DD
    """
    print("\n" + "="*70)
    print("ANÁLISIS CUANTITATIVO - Gold (GC)")
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
        rsi_levels=None,
        fibo_levels=None,
        divergences=None
    )
    if plot_result is None:
        print("[ERROR] Fallo en generación de gráfico")
        return None

    # 3. Resumen final
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

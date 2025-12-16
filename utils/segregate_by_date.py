import pandas as pd
import os
from pathlib import Path

def segregate_csv_by_date(input_file='data/export_GC_2015_formatted.csv'):
    """
    Segrega un archivo CSV por fecha, creando un archivo CSV por cada día único.

    Args:
        input_file: Ruta al archivo CSV de entrada
    """
    # Leer el archivo CSV
    print(f"Leyendo archivo: {input_file}")
    df = pd.read_csv(input_file)

    # Renombrar columnas a minúsculas
    df.columns = df.columns.str.lower()
    if 'volumen' in df.columns:
        df.rename(columns={'volumen': 'volume'}, inplace=True)

    # Renombrar Date a timestamp
    df.rename(columns={'date': 'timestamp'}, inplace=True)

    # Extraer solo la fecha (sin hora) usando split de string para evitar problemas con timezone
    df['date_only'] = df['timestamp'].str.split(' ').str[0]

    # Obtener el nombre base del archivo y su carpeta
    input_path = Path(input_file)
    output_dir = input_path.parent

    # Agrupar por fecha
    grouped = df.groupby('date_only')

    print(f"Se encontraron {len(grouped)} días únicos")

    # Crear un archivo por cada fecha
    for date, group in grouped:
        # Eliminar la columna auxiliar date_only
        group = group.drop('date_only', axis=1)

        # Crear el nombre del archivo de salida
        output_file = output_dir / f"gc_{date}.csv"

        # Guardar el archivo
        group.to_csv(output_file, index=False)
        print(f"Creado: {output_file} ({len(group)} registros)")

    print(f"\nProceso completado. Se crearon {len(grouped)} archivos en {output_dir}")

if __name__ == "__main__":
    segregate_csv_by_date()

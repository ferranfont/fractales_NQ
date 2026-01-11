import pandas as pd
import os
from pathlib import Path
from normaliza_columns_csv import normalize_columns

def segregate_csv_by_date(input_file='data/time_and_sales_20251225_090830.csv'):
    """
    Segrega un archivo CSV por fecha, creando un archivo CSV por cada día único.
    Normaliza automáticamente los nombres de columnas usando normaliza_columns_csv.py

    Args:
        input_file: Ruta al archivo CSV de entrada
    """
    # Leer el archivo CSV (formato europeo: separador ; y decimal ,)
    print(f"Leyendo archivo: {input_file}")
    df = pd.read_csv(input_file, sep=';', decimal=',')

    print(f"[INFO] Columnas originales: {list(df.columns)}")

    # Normalizar columnas usando la función compartida
    df = normalize_columns(df)

    print(f"[INFO] Columnas normalizadas: {list(df.columns)}")

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

        # Crear el nombre del archivo de salida (formato NQ)
        # Convertir fecha YYYY-MM-DD a YYYYMMDD
        date_formatted = date.replace('-', '')
        output_file = output_dir / f"time_and_sales_nq_{date_formatted}.csv"

        # Guardar el archivo (mantener formato europeo)
        group.to_csv(output_file, index=False, sep=';', decimal=',')
        print(f"Creado: {output_file} ({len(group)} registros)")

    print(f"\nProceso completado. Se crearon {len(grouped)} archivos en {output_dir}")

if __name__ == "__main__":
    segregate_csv_by_date()

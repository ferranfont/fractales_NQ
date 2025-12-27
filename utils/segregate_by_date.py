import pandas as pd
import os
from pathlib import Path

def segregate_csv_by_date(input_file='data/time_and_sales_20251224_080632.csv'):
    """
    Segrega un archivo CSV por fecha, creando un archivo CSV por cada día único.
    Normaliza automáticamente los nombres de columnas (mayúsculas/minúsculas).

    Args:
        input_file: Ruta al archivo CSV de entrada
    """
    # Leer el archivo CSV (formato europeo: separador ; y decimal ,)
    print(f"Leyendo archivo: {input_file}")
    df = pd.read_csv(input_file, sep=';', decimal=',')

    # Normalizar nombres de columnas (soportar mayúsculas y minúsculas)
    # Siempre convertir a minúsculas para el formato de salida
    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in ('timestamp', 'date'):
            column_mapping[col] = 'timestamp'
        elif col_lower == 'precio':
            column_mapping[col] = 'precio'
        elif col_lower in ('volumen', 'volume'):
            column_mapping[col] = 'volume'
        elif col_lower == 'lado':
            column_mapping[col] = 'lado'
        elif col_lower == 'bid':
            column_mapping[col] = 'bid'
        elif col_lower == 'ask':
            column_mapping[col] = 'ask'

    df.rename(columns=column_mapping, inplace=True)

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

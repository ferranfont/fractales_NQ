"""
Script para normalizar columnas de archivos CSV a formato estándar (minúsculas).
Convierte archivos con formato antiguo (Timestamp, Precio, Volumen) al nuevo formato.
"""
import pandas as pd
from pathlib import Path
import sys

def normalize_csv_columns(file_path, dry_run=True):
    """
    Normaliza las columnas de un archivo CSV al formato estándar (minúsculas).

    Args:
        file_path: Ruta al archivo CSV
        dry_run: Si True, solo muestra qué cambios se harían sin modificar el archivo

    Returns:
        True si se normalizó (o se normalizaría), False si ya estaba normalizado
    """
    try:
        # Leer archivo
        df = pd.read_csv(file_path, sep=';', decimal=',', nrows=1)

        # Crear mapeo de normalización
        column_mapping = {}
        needs_normalization = False

        for col in df.columns:
            col_lower = col.lower()

            # Determinar nombre normalizado (minúsculas + inglés)
            normalized_name = None

            if col_lower == 'timestamp':
                normalized_name = 'timestamp'
            elif col_lower in ('precio', 'price'):
                normalized_name = 'price'  # Siempre a inglés
            elif col_lower in ('volumen', 'volume'):
                normalized_name = 'volume'
            elif col_lower == 'lado':
                normalized_name = 'lado'
            elif col_lower == 'bid':
                normalized_name = 'bid'
            elif col_lower == 'ask':
                normalized_name = 'ask'

            # Si la columna ya está normalizada, no necesita cambio
            if col == normalized_name:
                continue

            # Si llegamos aquí, necesita normalización
            if normalized_name:
                needs_normalization = True
                column_mapping[col] = normalized_name

        if not needs_normalization:
            return False

        if dry_run:
            print(f"  [DRY-RUN] {file_path.name}")
            print(f"    Cambios: {column_mapping}")
            return True

        # Leer archivo completo
        df_full = pd.read_csv(file_path, sep=';', decimal=',')

        # Aplicar normalización
        df_full.rename(columns=column_mapping, inplace=True)

        # Guardar archivo con formato normalizado
        df_full.to_csv(file_path, index=False, sep=';', decimal=',')

        print(f"  [OK] Normalizado: {file_path.name}")
        print(f"    Cambios: {column_mapping}")

        return True

    except Exception as e:
        print(f"  ✗ Error en {file_path.name}: {e}")
        return False


def normalize_all_csv_in_directory(directory='data', pattern='time_and_sales_nq_*.csv', dry_run=True):
    """
    Normaliza todos los archivos CSV que coincidan con el patrón en el directorio.

    Args:
        directory: Directorio donde buscar archivos
        pattern: Patrón glob para filtrar archivos
        dry_run: Si True, solo muestra qué cambios se harían sin modificar archivos
    """
    data_dir = Path(directory)

    if not data_dir.exists():
        print(f"[ERROR] Directorio no encontrado: {data_dir}")
        return

    # Buscar archivos
    csv_files = sorted(data_dir.glob(pattern))

    if len(csv_files) == 0:
        print(f"[INFO] No se encontraron archivos que coincidan con '{pattern}' en {data_dir}")
        return

    print(f"{'='*70}")
    print(f"NORMALIZACIÓN DE COLUMNAS CSV")
    print(f"{'='*70}")
    print(f"Directorio: {data_dir}")
    print(f"Patrón: {pattern}")
    print(f"Archivos encontrados: {len(csv_files)}")
    print(f"Modo: {'DRY-RUN (simulación)' if dry_run else 'APLICAR CAMBIOS'}")
    print(f"{'='*70}\n")

    normalized_count = 0
    already_normalized_count = 0
    error_count = 0

    for csv_file in csv_files:
        result = normalize_csv_columns(csv_file, dry_run=dry_run)

        if result is True:
            normalized_count += 1
        elif result is False:
            already_normalized_count += 1
        else:
            error_count += 1

    print(f"\n{'='*70}")
    print(f"RESUMEN")
    print(f"{'='*70}")
    print(f"Total archivos procesados: {len(csv_files)}")
    print(f"  [OK] Normalizados: {normalized_count}")
    print(f"  [-] Ya normalizados: {already_normalized_count}")
    print(f"  [X] Errores: {error_count}")

    if dry_run and normalized_count > 0:
        print(f"\n[!] MODO DRY-RUN ACTIVO")
        print(f"    No se modificaron archivos. Para aplicar cambios ejecuta:")
        print(f"    python utils/normalize_csv_columns.py --apply")


if __name__ == "__main__":
    # Verificar argumentos
    dry_run = True

    if len(sys.argv) > 1:
        if sys.argv[1] in ('--apply', '-a'):
            dry_run = False
            print("[!] MODO APLICAR CAMBIOS - Los archivos seran modificados\n")
        elif sys.argv[1] in ('--help', '-h'):
            print("Uso:")
            print("  python utils/normalize_csv_columns.py           # Modo dry-run (solo muestra cambios)")
            print("  python utils/normalize_csv_columns.py --apply   # Aplica cambios a los archivos")
            print("  python utils/normalize_csv_columns.py --help    # Muestra esta ayuda")
            sys.exit(0)

    # Ejecutar normalización
    normalize_all_csv_in_directory(
        directory='data',
        pattern='time_and_sales_nq_*.csv',
        dry_run=dry_run
    )

"""
Column Normalization Utility for NQ Time & Sales Data

This module provides consistent column name normalization across all CSV processing tools.
Handles various column name formats (uppercase/lowercase, different languages, etc.)
and standardizes them to a common format.
"""

import pandas as pd


def normalize_columns(df):
    """
    Normalize column names to standard format.

    Supports multiple column name variations:
    - Timestamp/Date/timestamp/date -> timestamp
    - Precio/precio/Price/price -> precio
    - Volumen/volumen/Volume/volume -> volume
    - Lado/lado/Side/side -> lado
    - Bid/bid -> bid
    - Ask/ask -> ask

    Args:
        df: pandas DataFrame with columns to normalize

    Returns:
        pandas DataFrame with normalized column names
    """
    column_mapping = {}

    for col in df.columns:
        col_lower = col.lower()

        # Timestamp/Date column
        if col_lower in ('timestamp', 'date'):
            column_mapping[col] = 'timestamp'

        # Price column
        elif col_lower in ('precio', 'price'):
            column_mapping[col] = 'precio'

        # Volume column
        elif col_lower in ('volumen', 'volume'):
            column_mapping[col] = 'volume'

        # Side column
        elif col_lower in ('lado', 'side'):
            column_mapping[col] = 'lado'

        # Bid column
        elif col_lower == 'bid':
            column_mapping[col] = 'bid'

        # Ask column
        elif col_lower == 'ask':
            column_mapping[col] = 'ask'

    # Apply the mapping
    df_normalized = df.rename(columns=column_mapping)

    return df_normalized


def normalize_csv_file(input_file, output_file=None):
    """
    Normalize columns in a CSV file.

    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (optional, defaults to overwriting input)

    Returns:
        pandas DataFrame with normalized columns
    """
    # Read CSV (European format: ; separator, , decimal)
    df = pd.read_csv(input_file, sep=';', decimal=',')

    print(f"[INFO] Original columns: {list(df.columns)}")

    # Normalize columns
    df_normalized = normalize_columns(df)

    print(f"[INFO] Normalized columns: {list(df_normalized.columns)}")

    # Save if output file specified
    if output_file:
        df_normalized.to_csv(output_file, index=False, sep=';', decimal=',')
        print(f"[OK] Normalized file saved to: {output_file}")

    return df_normalized


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python normaliza_columns_csv.py <input_file> [output_file]")
        print("If output_file is not specified, input file will be overwritten")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file

    normalize_csv_file(input_file, output_file)

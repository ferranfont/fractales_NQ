"""
Muestra la configuración óptima de time-in-market por hora de entrada
"""

from optimize_time_in_market import load_optimal_duration
import json
from pathlib import Path
from config import OUTPUTS_DIR

# Cargar archivo JSON completo
json_path = OUTPUTS_DIR / "optimization" / "optimal_time_in_market_config.json"

if not json_path.exists():
    print(f"[ERROR] No se encontró el archivo de configuración: {json_path}")
    exit(1)

with open(json_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

print("=" * 100)
print("CONFIGURACION OPTIMA DE TIME-IN-MARKET POR HORA DE ENTRADA")
print("=" * 100)
print(f"\nArchivo: {json_path}")
print(f"Generado: {config['metadata']['generated_at']}")
print(f"Criterio: {config['metadata']['optimization_criteria']}")
print(f"\n{config['metadata']['description']}")

print("\n" + "=" * 100)
print(f"{'Hour':^6} | {'Duration':^12} | {'Sharpe':^8} | {'Trades':^7} | {'Win%':^6} | {'Avg P&L':^10} | {'Total P&L':^12}")
print("=" * 100)

for hour in range(24):
    hour_key = f"{hour:02d}"
    if hour_key in config['optimal_durations']:
        data = config['optimal_durations'][hour_key]

        # Color coding based on Sharpe Ratio
        sharpe = data['sharpe_ratio']
        if sharpe > 5:
            marker = "+++"
        elif sharpe > 2:
            marker = "++"
        elif sharpe > 0:
            marker = "+"
        else:
            marker = "-"

        print(f"{hour:02d}:00  | {data['duration_label']:>12} | {sharpe:>7.2f} | "
              f"{data['total_trades']:>7} | {data['win_rate']:>5.1f}% | "
              f"${data['avg_pnl_usd']:>9.2f} | ${data['total_pnl_usd']:>11,.0f} {marker}")
    else:
        print(f"{hour:02d}:00  | {'N/A':>12} | {'N/A':>8} | {'N/A':>7} | {'N/A':>6} | {'N/A':>10} | {'N/A':>12}")

print("=" * 100)
print("\nLeyenda:")
print("  +++ = Sharpe Ratio > 5  (Excelente)")
print("  ++  = Sharpe Ratio > 2  (Bueno)")
print("  +   = Sharpe Ratio > 0  (Positivo)")
print("  -   = Sharpe Ratio <= 0 (Negativo)")
print("=" * 100)

# Mostrar las mejores horas
print("\nMEJORES HORAS POR SHARPE RATIO:")
best_hours = []
for hour in range(24):
    hour_key = f"{hour:02d}"
    if hour_key in config['optimal_durations']:
        data = config['optimal_durations'][hour_key]
        best_hours.append((hour, data['sharpe_ratio'], data['duration_label']))

# Ordenar por Sharpe Ratio descendente
best_hours.sort(key=lambda x: x[1], reverse=True)

print(f"\n{'Rank':^6} | {'Hour':^6} | {'Sharpe':^8} | {'Duration':^12}")
print("-" * 40)
for i, (hour, sharpe, duration) in enumerate(best_hours[:10], 1):
    print(f"{i:^6} | {hour:02d}:00  | {sharpe:>7.2f} | {duration:>12}")

print("\n" + "=" * 100)

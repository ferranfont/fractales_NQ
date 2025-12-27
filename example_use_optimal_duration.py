"""
Ejemplo de uso del archivo JSON de configuración óptima de time-in-market

Este archivo demuestra cómo integrar la configuración óptima de duración
por hora de entrada en tu sistema de trading.
"""

from optimize_time_in_market import load_optimal_duration
from datetime import datetime
from config import USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE, TIME_IN_MARKET_MINUTES

def get_optimal_duration_for_trade(entry_time):
    """
    Obtiene la duración óptima de time-in-market para un trade basado en la hora de entrada

    Args:
        entry_time: datetime object con la hora de entrada del trade

    Returns:
        int or str: Duración en minutos o 'EOD'
    """
    if USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE:
        # Cargar configuración óptima desde JSON
        entry_hour = entry_time.hour
        config = load_optimal_duration(entry_hour)

        if config:
            duration = config['duration_minutes']
            print(f"[INFO] Hora entrada: {entry_hour:02d}:00")
            print(f"[INFO] Duración óptima cargada desde JSON: {config['duration_label']}")
            print(f"[INFO] Sharpe Ratio: {config['sharpe_ratio']:.3f}")
            print(f"[INFO] Win Rate: {config['win_rate']:.1f}%")
            print(f"[INFO] Avg P&L: ${config['avg_pnl_usd']:.2f}")
            return duration
        else:
            print(f"[WARN] No se encontró configuración para hora {entry_hour}, usando valor por defecto")
            return TIME_IN_MARKET_MINUTES
    else:
        # Usar duración fija desde config.py
        print(f"[INFO] Usando duración fija desde config: {TIME_IN_MARKET_MINUTES} minutos")
        return TIME_IN_MARKET_MINUTES

# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("EJEMPLO DE USO - OPTIMAL TIME IN MARKET DURATION")
    print("=" * 80)

    # Simular diferentes horas de entrada
    test_hours = [9, 10, 11, 14, 15, 16, 20]

    for hour in test_hours:
        # Crear timestamp de ejemplo
        entry_time = datetime(2024, 11, 4, hour, 30, 0)

        print(f"\n{'='*80}")
        print(f"ENTRADA A LAS {hour:02d}:30:00")
        print(f"{'='*80}")

        # Obtener duración óptima
        duration = get_optimal_duration_for_trade(entry_time)

        if duration == 'EOD':
            print(f">>> SALIDA: End of Day (EOD)")
        else:
            print(f">>> SALIDA: {duration} minutos ({duration/60:.1f} horas)")

    print("\n" + "=" * 80)
    print("EJEMPLO COMPLETO DE INTEGRACIÓN")
    print("=" * 80)

    # Ejemplo más completo mostrando toda la información
    entry_time = datetime(2024, 11, 4, 14, 0, 0)
    entry_hour = entry_time.hour

    print(f"\nTrade Entry Time: {entry_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Cargar configuración
    config = load_optimal_duration(entry_hour)

    if config:
        print("\n[CONFIG] CONFIGURACION OPTIMA PARA ESTA HORA:")
        print(f"  Entry Hour:        {config['entry_hour']:02d}:00")
        print(f"  Duration:          {config['duration_label']}")
        print(f"  Duration (min):    {config['duration_minutes']}")
        print(f"  Sharpe Ratio:      {config['sharpe_ratio']:.3f}")
        print(f"  Total P&L:         ${config['total_pnl_usd']:,.0f}")
        print(f"  Avg P&L:           ${config['avg_pnl_usd']:,.2f}")
        print(f"  Total Trades:      {config['total_trades']}")
        print(f"  Win Rate:          {config['win_rate']:.1f}%")
        print(f"  Avg Win:           ${config['avg_win_usd']:,.2f}")
        print(f"  Avg Loss:          ${config['avg_loss_usd']:,.2f}")
        print(f"  Avg MAE:           ${config['avg_mae_usd']:,.2f}")
        print(f"  Avg MFE:           ${config['avg_mfe_usd']:,.2f}")

        # Calcular exit time
        if config['duration_minutes'] == 'EOD':
            print(f"\n[OK] EXIT TIME: End of Day")
        else:
            from datetime import timedelta
            exit_time = entry_time + timedelta(minutes=config['duration_minutes'])
            print(f"\n[OK] EXIT TIME: {exit_time.strftime('%Y-%m-%d %H:%M:%S')}")

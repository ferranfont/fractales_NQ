"""
Generador automático de dashboard de configuración
Lee config.py y genera config_dashboard.html con valores actualizados
"""

import importlib.util
from pathlib import Path
from datetime import datetime

def load_config_module():
    """Carga el módulo config.py dinámicamente"""
    config_path = Path(__file__).parent / "config.py"
    spec = importlib.util.spec_from_file_location("config", config_path)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config

def get_config_value(config, name, default="N/A"):
    """Obtiene valor de configuración con fallback"""
    return getattr(config, name, default)

def generate_dashboard_html(config):
    """Genera el HTML del dashboard con valores actuales"""

    # ===== EXTRACT ALL CONFIG VALUES =====

    # GENERAL
    point_value = get_config_value(config, 'POINT_VALUE', 20.0)
    vwap_fast = get_config_value(config, 'VWAP_FAST', 100)
    vwap_slow = get_config_value(config, 'VWAP_SLOW', 200)

    # VWAP MOMENTUM STRATEGY
    enable_vwap_momentum = get_config_value(config, 'ENABLE_VWAP_MOMENTUM_STRATEGY', False)
    use_time_in_market = get_config_value(config, 'USE_TIME_IN_MARKET', False)
    use_json_optimization = get_config_value(config, 'USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE', False)
    use_max_sl = get_config_value(config, 'USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET', False)

    # VWAP CROSSOVER STRATEGY
    enable_vwap_crossover = get_config_value(config, 'ENABLE_VWAP_CROSSOVER_STRATEGY', False)
    crossover_tp = get_config_value(config, 'VWAP_CROSSOVER_TP_POINTS', 5.0)
    crossover_sl = get_config_value(config, 'VWAP_CROSSOVER_SL_POINTS', 9.0)
    crossover_start = get_config_value(config, 'VWAP_CROSSOVER_START_HOUR', '16:30:00')
    crossover_end = get_config_value(config, 'VWAP_CROSSOVER_END_HOUR', '22:00:00')

    # VWAP PULLBACK STRATEGY
    enable_vwap_pullback = get_config_value(config, 'ENABLE_VWAP_PULLBACK_STRATEGY', False)
    pullback_tp = get_config_value(config, 'VWAP_PULLBACK_TP_POINTS', 125.0)
    pullback_sl = get_config_value(config, 'VWAP_PULLBACK_SL_POINTS', 40.0)
    pullback_start = get_config_value(config, 'VWAP_PULLBACK_START_HOUR', '00:01:00')
    pullback_end = get_config_value(config, 'VWAP_PULLBACK_END_HOUR', '22:00:00')

    # VWAP SQUARE STRATEGY
    enable_vwap_square = get_config_value(config, 'ENABLE_VWAP_SQUARE_STRATEGY', False)
    square_tp = get_config_value(config, 'VWAP_SQUARE_TP_POINTS', 100.0)
    square_sl = get_config_value(config, 'VWAP_SQUARE_SL_POINTS', 60.0)
    square_start = get_config_value(config, 'VWAP_SQUARE_START_HOUR', '00:01:00')
    square_end = get_config_value(config, 'VWAP_SQUARE_END_HOUR', '22:00:00')
    square_listening_time = get_config_value(config, 'VWAP_SQUARE_LISTENING_TIME', 60)
    square_min_spike = get_config_value(config, 'VWAP_SQUARE_MIN_SPIKE', 50)
    use_square_trend_filter = get_config_value(config, 'USE_SQUARE_VWAP_SLOW_TREND_FILTER', False)
    use_square_atr_trailing = get_config_value(config, 'USE_SQUARE_ATR_TRAILING_STOP', False)
    square_atr_period = get_config_value(config, 'SQUARE_ATR_PERIOD', 21)
    square_atr_mult = get_config_value(config, 'SQUARE_ATR_MULTIPLIER', 7)
    use_opposite_side_stop = get_config_value(config, 'USE_OPOSITE_SIDE_OF_SQUARE_AS_STOP', False)
    use_shake_out = get_config_value(config, 'USE_VWAP_SQUARE_SHAKE_OUT', False)
    shake_out_retrace_pct = get_config_value(config, 'VWAP_SQUARE_SHAKE_OUT_RETRACEMENT_PCT', 100)

    time_in_market_minutes = get_config_value(config, 'TIME_IN_MARKET_MINUTES', 180)
    use_tp_in_time = get_config_value(config, 'USE_TP_ALLOWED_IN_TIME_IN_MARKET', True)
    tp_in_time_points = get_config_value(config, 'TP_IN_TIME_IN_MARKET', 125)
    max_sl_points = get_config_value(config, 'MAX_SL_ALLOWED_IN_TIME_IN_MARKET', 120)

    tp_points = get_config_value(config, 'VWAP_MOMENTUM_TP_POINTS', 125.0)
    sl_points = get_config_value(config, 'VWAP_MOMENTUM_SL_POINTS', 75.0)
    max_positions = get_config_value(config, 'VWAP_MOMENTUM_MAX_POSITIONS', 1)
    start_hour = get_config_value(config, 'VWAP_MOMENTUM_STRAT_START_HOUR', '00:00:00')
    end_hour = get_config_value(config, 'VWAP_MOMENTUM_STRAT_END_HOUR', '22:59:59')

    # Entry filters
    use_selected_allowed_hours = get_config_value(config, 'USE_SELECTED_ALLOWED_HOURS', False)
    allowed_hours = get_config_value(config, 'VWAP_MOMENTUM_ALLOWED_HOURS', [])
    long_allowed = get_config_value(config, 'VWAP_MOMENTUM_LONG_ALLOWED', True)
    short_allowed = get_config_value(config, 'VWAP_MOMENTUM_SHORT_ALLOWED', True)
    use_vwap_slow_trend_filter = get_config_value(config, 'USE_VWAP_SLOW_TREND_FILTER', False)
    vwap_slow = get_config_value(config, 'VWAP_SLOW', 200)

    # Grid Entry System
    use_entry_grid = get_config_value(config, 'USE_ENTRY_GRID', False)
    grid_step = get_config_value(config, 'GRID_STEP', 30)
    number_of_grid_steps = get_config_value(config, 'NUMBER_OF_GRID_STEPS', 2)

    use_vwap_slope_sl = get_config_value(config, 'USE_VWAP_SLOPE_INDICATOR_STOP_LOSS', False)
    use_trail_cash = get_config_value(config, 'USE_TRAIL_CASH', False)
    trail_cash_trigger = get_config_value(config, 'TRAIL_CASH_TRIGGER_POINTS', 100)
    trail_cash_profit = get_config_value(config, 'TRAIL_CASH_BREAK_EVEN_POINTS_PROFIT', 0)

    vwap_fast = get_config_value(config, 'VWAP_FAST', 50)
    vwap_slope_window = get_config_value(config, 'VWAP_SLOPE_DEGREE_WINDOW', 10)
    show_vwap_slope_subplot = get_config_value(config, 'SHOW_SUBPLOT_VWAP_SLOPE_INDICATOR', True)
    vwap_slope_high = get_config_value(config, 'VWAP_SLOPE_INDICATOR_HIGH_VALUE', 0.6)
    vwap_slope_low = get_config_value(config, 'VWAP_SLOPE_INDICATOR_LOW_VALUE', 0.01)
    price_ejection = get_config_value(config, 'PRICE_EJECTION_TRIGGER', 0.001)
    point_value = get_config_value(config, 'POINT_VALUE', 20.0)

    # Determinar estados
    strategy_name = "VWAP Momentum" if enable_vwap_momentum else "Deshabilitada"
    exit_mode = "Time-in-Market" if use_time_in_market else "TP/SL Tradicional"
    duration_source = "JSON Optimizado" if use_json_optimization else "Duración Fija"
    sl_protector_status = "Habilitado" if use_max_sl else "Deshabilitado"

    # CSS para estados
    strategy_class = "active" if enable_vwap_momentum else "inactive"
    exit_mode_class = "active" if use_time_in_market else "inactive"
    json_class = "active" if use_json_optimization else "inactive"
    sl_protector_class = "active" if use_max_sl else "inactive"

    # Generar timestamp
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_content = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NQ Trading Strategy - Configuration Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f2f5;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .header h1 {{
            font-size: 2.2em;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.95;
        }}

        .timestamp {{
            text-align: right;
            color: #64748b;
            font-size: 0.9em;
            margin-bottom: 20px;
            font-style: italic;
        }}

        /* TARJETAS DE ESTADO */
        .status-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .status-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            border-left: 5px solid #667eea;
        }}

        .status-card.active {{
            border-left-color: #10b981;
            background: linear-gradient(135deg, #d1fae5 0%, #ffffff 100%);
        }}

        .status-card.inactive {{
            border-left-color: #ef4444;
            background: linear-gradient(135deg, #fee2e2 0%, #ffffff 100%);
        }}

        .status-card h3 {{
            font-size: 0.9em;
            color: #64748b;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .status-card .value {{
            font-size: 1.8em;
            font-weight: 700;
            color: #1e293b;
        }}

        .status-card .description {{
            font-size: 0.85em;
            color: #64748b;
            margin-top: 8px;
        }}

        /* SECCIONES PRINCIPALES */
        .section {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
        }}

        .section-header h2 {{
            font-size: 1.5em;
            color: #1e293b;
            font-weight: 600;
        }}

        .section-icon {{
            font-size: 1.8em;
        }}

        /* FLUJO DE DECISIÓN */
        .decision-flow {{
            background: #f8fafc;
            padding: 25px;
            border-radius: 12px;
            margin: 20px 0;
        }}

        .flow-step {{
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .flow-step.active {{
            border-left-color: #10b981;
            background: #ecfdf5;
        }}

        .flow-step.inactive {{
            border-left-color: #94a3b8;
            background: #f1f5f9;
            opacity: 0.7;
        }}

        .flow-step-title {{
            font-size: 1.1em;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 8px;
        }}

        .flow-step-value {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.95em;
        }}

        .flow-step.active .flow-step-value {{
            background: #10b981;
        }}

        .flow-step.inactive .flow-step-value {{
            background: #94a3b8;
        }}

        .flow-arrow {{
            text-align: center;
            color: #cbd5e1;
            font-size: 2em;
            margin: 5px 0;
        }}

        /* TABLA DE PARÁMETROS */
        .params-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 8px;
        }}

        .params-table tr {{
            background: white;
        }}

        .params-table td {{
            padding: 15px;
            border-top: 1px solid #e2e8f0;
            border-bottom: 1px solid #e2e8f0;
        }}

        .params-table td:first-child {{
            border-left: 1px solid #e2e8f0;
            border-radius: 8px 0 0 8px;
            font-weight: 600;
            color: #334155;
            width: 40%;
        }}

        .params-table td:last-child {{
            border-right: 1px solid #e2e8f0;
            border-radius: 0 8px 8px 0;
        }}

        .param-value {{
            display: inline-block;
            background: #ddd6fe;
            color: #5b21b6;
            padding: 5px 12px;
            border-radius: 6px;
            font-weight: 600;
        }}

        .param-value.true {{
            background: #d1fae5;
            color: #065f46;
        }}

        .param-value.inactive {{
            background: #f1f5f9;
            color: #94a3b8;
            border: 1px dashed #cbd5e1;
        }}

        .param-value.false {{
            background: #fee2e2;
            color: #991b1b;
        }}

        /* ALERTAS */
        .alert {{
            padding: 18px;
            border-radius: 10px;
            margin: 20px 0;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }}

        .alert-icon {{
            font-size: 1.5em;
            flex-shrink: 0;
        }}

        .alert.info {{
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
            color: #1e40af;
        }}

        .alert.warning {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            color: #92400e;
        }}

        .alert.success {{
            background: #d1fae5;
            border-left: 4px solid #10b981;
            color: #065f46;
        }}

        .alert-title {{
            font-weight: 700;
            margin-bottom: 5px;
            font-size: 1.05em;
        }}

        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}

        @media (max-width: 768px) {{
            .grid-2 {{
                grid-template-columns: 1fr;
            }}
        }}

        code {{
            background: #f1f5f9;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            color: #7c3aed;
            font-size: 0.9em;
        }}

        .feature-list {{
            list-style: none;
            padding: 0;
        }}

        .feature-list li {{
            padding: 10px 0;
            padding-left: 30px;
            position: relative;
        }}

        .feature-list li:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #10b981;
            font-weight: bold;
            font-size: 1.2em;
        }}

        .summary-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin: 30px 0;
        }}

        .summary-box h3 {{
            margin-bottom: 15px;
            font-size: 1.4em;
        }}

        .summary-box .summary-item {{
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }}

        .summary-box .summary-item:last-child {{
            border-bottom: none;
        }}

        .summary-box strong {{
            color: #fde68a;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <h1>📊 NQ Trading Strategy Configuration</h1>
            <p>Panel de Control de Parámetros y Dependencias</p>
        </div>

        <div class="timestamp">
            🕒 Última actualización: {generated_at}
        </div>

        <!-- STATUS CARDS -->
        <div class="status-cards">
            <div class="status-card {strategy_class}">
                <h3>Estrategia Activa</h3>
                <div class="value">{strategy_name}</div>
                <div class="description">Price Ejection Strategy</div>
            </div>

            <div class="status-card {exit_mode_class if use_time_in_market else 'inactive'}">
                <h3>Modo de Salida</h3>
                <div class="value">{exit_mode}</div>
                <div class="description">{"Basado en tiempo" if use_time_in_market else "Basado en TP/SL"}</div>
            </div>

            <div class="status-card {json_class if use_json_optimization else 'inactive'}">
                <h3>Fuente de Duración</h3>
                <div class="value">{duration_source}</div>
                <div class="description">{"Por hora de entrada" if use_json_optimization else f"{time_in_market_minutes} minutos fijos"}</div>
            </div>

            <div class="status-card {sl_protector_class if use_max_sl else 'inactive'}">
                <h3>Stop Loss Protector</h3>
                <div class="value">{sl_protector_status}</div>
                <div class="description">{"Protección activa" if use_max_sl else "Sin protección SL"}</div>
            </div>
        </div>

        <!-- SECCIÓN 1: CONFIGURACIÓN PRINCIPAL -->
        <div class="section">
            <div class="section-header">
                <span class="section-icon">⚙️</span>
                <h2>Configuración Principal del Sistema</h2>
            </div>

            <div class="decision-flow">
                <div class="flow-step {'active' if use_time_in_market else 'inactive'}">
                    <div class="flow-step-title">USE_TIME_IN_MARKET</div>
                    <div class="flow-step-value">{str(use_time_in_market)}</div>
                    <p style="margin-top: 10px; color: #64748b;">
                        {"✅ Modo time-in-market ACTIVO - Las salidas son por tiempo o EOD" if use_time_in_market else "❌ Modo TP/SL tradicional activo → Parámetros de abajo NO SE USAN"}
                    </p>
                </div>

                <div class="flow-arrow" style="{'opacity: 1;' if use_time_in_market else 'opacity: 0.3;'}">↓</div>

                <div class="flow-step {'inactive' if not use_time_in_market else ('active' if use_json_optimization else 'inactive')}" style="{'opacity: 0.5; background: #f8fafc;' if not use_time_in_market else ''}">
                    <div class="flow-step-title">USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE</div>
                    <div class="flow-step-value">{str(use_json_optimization)}</div>
                    <p style="margin-top: 10px; color: {'#94a3b8' if not use_time_in_market else '#64748b'};">
                        {("⚠️ NO SE USA (filtro superior deshabilitado)" if not use_time_in_market else ("✅ Duración dinámica cargada desde JSON según hora de entrada" if use_json_optimization else f"✗ Usando duración fija de {time_in_market_minutes} minutos"))}
                    </p>
                </div>

                <div class="flow-arrow" style="{'opacity: 1;' if use_time_in_market else 'opacity: 0.3;'}">↓</div>

                <div class="flow-step {'inactive' if not use_time_in_market else ('active' if use_max_sl else 'inactive')}" style="{'opacity: 0.5; background: #f8fafc;' if not use_time_in_market else ''}">
                    <div class="flow-step-title">USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET</div>
                    <div class="flow-step-value">{str(use_max_sl)}</div>
                    <p style="margin-top: 10px; color: {'#94a3b8' if not use_time_in_market else '#64748b'};">
                        {("⚠️ NO SE USA (filtro superior deshabilitado)" if not use_time_in_market else ("✅ Stop loss protector de " + str(max_sl_points) + " puntos activo" if use_max_sl else "✗ Stop loss protector deshabilitado"))}
                    </p>
                </div>
            </div>

            {f'''<div class="alert warning">
                <span class="alert-icon">⚠️</span>
                <div>
                    <div class="alert-title">Importante: Configuraciones Deshabilitadas</div>
                    Cuando <code>USE_TIME_IN_MARKET = True</code>, las siguientes funciones están <strong>DESHABILITADAS</strong>:
                    <ul style="margin-top: 8px; margin-left: 20px;">
                        <li>Take Profit (TP)</li>
                        <li>Stop Loss (SL) - excepto protective SL si está habilitado</li>
                        <li>VWAP Slope Indicator Stop Loss</li>
                        <li>Trailing Stop (Break-Even)</li>
                    </ul>
                </div>
            </div>''' if use_time_in_market else ''}
        </div>

        <!-- SECCIÓN 2: PARÁMETROS COMPLETOS -->
        <div class="section">
            <div class="section-header">
                <span class="section-icon">📝</span>
                <h2>Parámetros Completos del Sistema</h2>
            </div>

            <!-- 1. MAIN TRADING PARAMETERS -->
            <h3 style="margin: 20px 0 15px 0; color: #1e293b;">⚙️ MAIN TRADING PARAMETERS VWAP MOMENTUM STRATEGY</h3>
            <table class="params-table">
                <tr>
                    <td>VWAP_MOMENTUM_TP_POINTS</td>
                    <td><span class="param-value">{tp_points} puntos</span> - {"No se usa (USE_TIME_IN_MARKET=True)" if use_time_in_market else "Take Profit ACTIVO"} (${tp_points * point_value:,.0f})</td>
                </tr>
                <tr>
                    <td>VWAP_MOMENTUM_SL_POINTS</td>
                    <td><span class="param-value">{sl_points} puntos</span> - {"No se usa (USE_TIME_IN_MARKET=True)" if use_time_in_market else "Stop Loss ACTIVO"} (${sl_points * point_value:,.0f})</td>
                </tr>
                <tr>
                    <td>VWAP_MOMENTUM_MAX_POSITIONS</td>
                    <td><span class="param-value">{max_positions}</span> - Máximo de posiciones simultáneas</td>
                </tr>
            </table>

            <!-- 2. CONFIGURACIÓN DE HORARIO DE TRADING -->
            <h3 style="margin: 30px 0 15px 0; color: #1e293b;">🕒 CONFIGURACIÓN DE HORARIO DE TRADING</h3>
            <table class="params-table">
                <tr>
                    <td>VWAP_MOMENTUM_STRAT_START_HOUR</td>
                    <td><span class="param-value">{start_hour}</span> - Hora de inicio de trading (filtro genérico)</td>
                </tr>
                <tr>
                    <td>VWAP_MOMENTUM_STRAT_END_HOUR</td>
                    <td><span class="param-value">{end_hour}</span> - Hora de fin de trading (filtro genérico)</td>
                </tr>
                <tr>
                    <td>USE_SELECTED_ALLOWED_HOURS</td>
                    <td><span class="param-value {'true' if use_selected_allowed_hours else 'false'}">{str(use_selected_allowed_hours)}</span> - {"Filtro de horas específicas ACTIVO" if use_selected_allowed_hours else "Solo usa rango genérico (START_HOUR a END_HOUR)"}</td>
                </tr>
                <tr style="{'opacity: 1;' if use_selected_allowed_hours else 'opacity: 0.6;'}">
                    <td>VWAP_MOMENTUM_ALLOWED_HOURS</td>
                    <td><span class="param-value {'inactive' if not use_selected_allowed_hours else ''}">{allowed_hours}</span> - {("Solo opera en estas horas óptimas (Sortino 0.11→0.95)" if use_selected_allowed_hours else "⚠️ NO SE USA (USE_SELECTED_ALLOWED_HOURS=False)")}</td>
                </tr>
            </table>

            <!-- 3. FILTROS DE ENTRADA A FAVOR TENDENCIA -->
            <h3 style="margin: 30px 0 15px 0; color: #1e293b;">🎯 FILTROS DE ENTRADA A FAVOR TENDENCIA VWAP MOMENTUM STRATEGY</h3>
            <table class="params-table">
                <tr>
                    <td>USE_VWAP_SLOW_TREND_FILTER</td>
                    <td><span class="param-value {'true' if use_vwap_slow_trend_filter else 'false'}">{str(use_vwap_slow_trend_filter)}</span> - {"Filtro de tendencia ACTIVO (VWAP_SLOW=" + str(vwap_slow) + "): LONG si VWAP_FAST>VWAP_SLOW, SHORT si VWAP_FAST<VWAP_SLOW" if use_vwap_slow_trend_filter else "Filtro de tendencia DESACTIVADO (opera con/contra tendencia)"}</td>
                </tr>
                <tr>
                    <td>VWAP_MOMENTUM_LONG_ALLOWED</td>
                    <td><span class="param-value {'true' if long_allowed else 'false'}">{str(long_allowed)}</span> - {"Trades BUY habilitadas" if long_allowed else "Trades BUY DESHABILITADAS"}</td>
                </tr>
                <tr>
                    <td>VWAP_MOMENTUM_SHORT_ALLOWED</td>
                    <td><span class="param-value {'true' if short_allowed else 'false'}">{str(short_allowed)}</span> - {"Trades SELL habilitadas" if short_allowed else "Trades SELL DESHABILITADAS"}</td>
                </tr>
            </table>

            <!-- 3.5. GRID ENTRY SYSTEM -->
            <h3 style="margin: 30px 0 15px 0; color: #1e293b;">🔢 GRID ENTRY SYSTEM (Multiple entries at different price levels)</h3>
            <table class="params-table" style="{'opacity: 1; background: #fff3cd;' if use_entry_grid else 'opacity: 0.5; background: #f8fafc;'}">
                <tr>
                    <td>USE_ENTRY_GRID</td>
                    <td><span class="param-value {'true' if use_entry_grid else 'false'}">{str(use_entry_grid)}</span> - {"Grid Entry System ENABLED" if use_entry_grid else "Grid Entry System DISABLED"}</td>
                </tr>
                <tr style="{'opacity: 1;' if use_entry_grid else 'opacity: 0.6;'}">
                    <td>GRID_STEP</td>
                    <td><span class="param-value {'inactive' if not use_entry_grid else ''}">{grid_step} pts</span> - {("Distance between grid levels (${grid_step * point_value:,.0f})" if use_entry_grid else "Not used (grid disabled)")}</td>
                </tr>
                <tr style="{'opacity: 1;' if use_entry_grid else 'opacity: 0.6;'}">
                    <td>NUMBER_OF_GRID_STEPS</td>
                    <td><span class="param-value {'inactive' if not use_entry_grid else ''}">{number_of_grid_steps}</span> - {("Number of additional limit orders to place" if use_entry_grid else "Not used (grid disabled)")}</td>
                </tr>
                <tr style="{'opacity: 1;' if use_entry_grid else 'opacity: 0.6;'}">
                    <td colspan="2" style="background: #fef3c7; padding: 10px; font-size: 0.85rem; line-height: 1.5;">
                        <strong>Grid Logic:</strong><br>
                        • <strong>BUY:</strong> Places {number_of_grid_steps} limit orders BELOW entry price at -{grid_step}pts, -{grid_step*2}pts, etc.<br>
                        • <strong>SELL:</strong> Places {number_of_grid_steps} limit orders ABOVE entry price at +{grid_step}pts, +{grid_step*2}pts, etc.<br>
                        • <strong>Stop Loss:</strong> All grid positions share the SAME SL level as main position<br>
                        • <strong>Take Profit:</strong> Each grid position has its own TP calculated from fill price<br>
                        • <strong>Max Positions:</strong> Grid orders do NOT count toward VWAP_MOMENTUM_MAX_POSITIONS<br>
                        <br>
                        <strong>Example (BUY @ 25000, TP={tp_points}, SL={sl_points}):</strong><br>
                        - Main entry 25000 → SL {25000-sl_points} → TP {25000+tp_points}<br>
                        - Grid 1 fills @ {25000-grid_step} → SL {25000-sl_points} (SAME) → TP {25000-grid_step+tp_points}<br>
                        - Grid 2 fills @ {25000-grid_step*2} → SL {25000-sl_points} (SAME) → TP {25000-grid_step*2+tp_points}
                    </td>
                </tr>
            </table>

            <!-- 4. FILTROS DE SALIDA -->
            <h3 style="margin: 30px 0 15px 0; color: #1e293b;">🚪 FILTROS DE SALIDA VWAP MOMENTUM STRATEGY</h3>
            <table class="params-table">
                <tr>
                    <td>USE_VWAP_SLOPE_INDICATOR_STOP_LOSS</td>
                    <td><span class="param-value {'false' if use_time_in_market or not use_vwap_slope_sl else 'true'}">{str(use_vwap_slope_sl)}</span> - {"Deshabilitado (USE_TIME_IN_MARKET=True)" if use_time_in_market else ("VWAP Slope Stop Loss ACTIVO" if use_vwap_slope_sl else "VWAP Slope Stop Loss deshabilitado")}</td>
                </tr>
            </table>

            <!-- 5. FILTRO DE SALIDA POR TIEMPO -->
            <h3 style="margin: 30px 0 15px 0; color: #1e293b;">{"✅ FILTRO DE SALIDA POR TIEMPO VWAP MOMENTUM STRATEGY (ACTIVO)" if use_time_in_market else "❌ FILTRO DE SALIDA POR TIEMPO (DESHABILITADO - parámetros no se usan)"}</h3>
            <table class="params-table" style="{'opacity: 1;' if use_time_in_market else 'opacity: 0.5; background: #f8fafc;'}">
                <tr>
                    <td>USE_TIME_IN_MARKET</td>
                    <td><span class="param-value {'true' if use_time_in_market else 'false'}">{str(use_time_in_market)}</span> - <strong>{"✅ Modo time-in-market ACTIVO" if use_time_in_market else "❌ Modo INACTIVO → Todos los parámetros de abajo NO SE USAN"}</strong></td>
                </tr>
                <tr style="{'opacity: 1;' if use_time_in_market else 'opacity: 0.6;'}">
                    <td>USE_TIME_IN_MARKET_JSON_OPTIMIZATION_FILE</td>
                    <td><span class="param-value {'inactive' if not use_time_in_market else ('true' if use_json_optimization else 'false')}">{str(use_json_optimization)}</span> - {("⚠️ NO SE USA (USE_TIME_IN_MARKET=False)" if not use_time_in_market else ("Carga duración óptima desde JSON por hora de entrada" if use_json_optimization else "Usa duración fija"))}</td>
                </tr>
                <tr style="{'opacity: 1;' if use_time_in_market else 'opacity: 0.6;'}">
                    <td>TIME_IN_MARKET_MINUTES</td>
                    <td><span class="param-value {'inactive' if not use_time_in_market else ''}">{time_in_market_minutes} min</span> - {("⚠️ NO SE USA (USE_TIME_IN_MARKET=False)" if not use_time_in_market else ("Fallback (solo si JSON falla)" if use_json_optimization else "Duración fija de salida"))}</td>
                </tr>
                <tr style="{'opacity: 1;' if use_time_in_market else 'opacity: 0.6;'}">
                    <td>USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET</td>
                    <td><span class="param-value {'inactive' if not use_time_in_market else ('true' if use_max_sl else 'false')}">{str(use_max_sl)}</span> - {("⚠️ NO SE USA (USE_TIME_IN_MARKET=False)" if not use_time_in_market else ("Stop loss protector ACTIVO" if use_max_sl else "Stop loss protector deshabilitado"))}</td>
                </tr>
                <tr style="{'opacity: 1;' if use_time_in_market else 'opacity: 0.6;'}">
                    <td>MAX_SL_ALLOWED_IN_TIME_IN_MARKET</td>
                    <td><span class="param-value {'inactive' if not use_time_in_market else ''}">{max_sl_points} puntos</span> - {("⚠️ NO SE USA (USE_TIME_IN_MARKET=False)" if not use_time_in_market else ("Se aplica (${} USD)".format(int(max_sl_points * point_value)) if use_max_sl else "No se aplica (USE_MAX_SL_ALLOWED_IN_TIME_IN_MARKET=False)"))}</td>
                </tr>
                <tr style="{'opacity: 1;' if use_time_in_market else 'opacity: 0.6;'}">
                    <td>USE_TP_ALLOWED_IN_TIME_IN_MARKET</td>
                    <td><span class="param-value {'inactive' if not use_time_in_market else ('true' if use_tp_in_time else 'false')}">{str(use_tp_in_time)}</span> - {("⚠️ NO SE USA (USE_TIME_IN_MARKET=False)" if not use_time_in_market else ("TP opcional habilitado (cierra si alcanza antes del tiempo)" if use_tp_in_time else "TP deshabilitado"))}</td>
                </tr>
                <tr style="{'opacity: 1;' if use_time_in_market else 'opacity: 0.6;'}">
                    <td>TP_IN_TIME_IN_MARKET</td>
                    <td><span class="param-value {'inactive' if not use_time_in_market else ''}">{tp_in_time_points} puntos</span> - {("⚠️ NO SE USA (USE_TIME_IN_MARKET=False)" if not use_time_in_market else ("Se aplica si alcanza (${} USD)".format(int(tp_in_time_points * point_value)) if use_tp_in_time else "No se aplica (USE_TP_ALLOWED_IN_TIME_IN_MARKET=False)"))}</td>
                </tr>
            </table>

            <!-- 6. TRAILING STOP LOSS PARAMETERS -->
            <h3 style="margin: 30px 0 15px 0; color: #1e293b;">📈 TRAILING STOP LOSS PARAMETERS VWAP MOMENTUM STRATEGY</h3>
            <table class="params-table">
                <tr>
                    <td>USE_TRAIL_CASH</td>
                    <td><span class="param-value {'false' if use_time_in_market or not use_trail_cash else 'true'}">{str(use_trail_cash)}</span> - {"Deshabilitado (USE_TIME_IN_MARKET=True)" if use_time_in_market else ("Trailing a Break-Even ACTIVO" if use_trail_cash else "Trailing a Break-Even deshabilitado")}</td>
                </tr>
                <tr style="{'opacity: 1;' if use_trail_cash and not use_time_in_market else 'opacity: 0.6;'}">
                    <td>TRAIL_CASH_TRIGGER_POINTS</td>
                    <td><span class="param-value {'inactive' if not use_trail_cash or use_time_in_market else ''}">{trail_cash_trigger} pts</span> - {("⚠️ NO SE USA" if (not use_trail_cash or use_time_in_market) else "Trigger para mover SL a break-even (${} USD)".format(int(trail_cash_trigger * point_value)))}</td>
                </tr>
                <tr style="{'opacity: 1;' if use_trail_cash and not use_time_in_market else 'opacity: 0.6;'}">
                    <td>TRAIL_CASH_BREAK_EVEN_POINTS_PROFIT</td>
                    <td><span class="param-value {'inactive' if not use_trail_cash or use_time_in_market else ''}">{trail_cash_profit} pts</span> - {("⚠️ NO SE USA" if (not use_trail_cash or use_time_in_market) else "Puntos de ganancia a proteger (${} USD)".format(int(trail_cash_profit * point_value)))}</td>
                </tr>
            </table>

            <!-- 7. INDICADORES TÉCNICOS (Parámetros Generales) -->
            <h3 style="margin: 30px 0 15px 0; color: #1e293b;">📊 PARÁMETROS DE INDICADORES TÉCNICOS</h3>
            <table class="params-table">
                <tr>
                    <td>VWAP_FAST</td>
                    <td><span class="param-value">{vwap_fast} períodos</span> - VWAP Fast (magenta) para señales de entrada</td>
                </tr>
                <tr>
                    <td>VWAP_SLOW</td>
                    <td><span class="param-value">{vwap_slow} períodos</span> - VWAP Slow (verde) para filtro de tendencia</td>
                </tr>
                <tr>
                    <td>PRICE_EJECTION_TRIGGER</td>
                    <td><span class="param-value">{price_ejection*100:.1f}%</span> - Umbral de distancia precio-VWAP para green dots</td>
                </tr>
                <tr>
                    <td>VWAP_SLOPE_DEGREE_WINDOW</td>
                    <td><span class="param-value">{vwap_slope_window} barras</span> - Ventana para cálculo de pendiente VWAP</td>
                </tr>
                <tr>
                    <td>SHOW_SUBPLOT_VWAP_SLOPE_INDICATOR</td>
                    <td><span class="param-value {'true' if show_vwap_slope_subplot else 'false'}">{str(show_vwap_slope_subplot)}</span> - {"Subplot VWAP Slope visible" if show_vwap_slope_subplot else "Subplot VWAP Slope oculto"}</td>
                </tr>
                <tr>
                    <td>VWAP_SLOPE_INDICATOR_HIGH_VALUE</td>
                    <td><span class="param-value">{vwap_slope_high}</span> - Umbral alto para indicador de pendiente</td>
                </tr>
                <tr>
                    <td>VWAP_SLOPE_INDICATOR_LOW_VALUE</td>
                    <td><span class="param-value">{vwap_slope_low}</span> - Umbral bajo para indicador de pendiente</td>
                </tr>
                <tr>
                    <td>POINT_VALUE</td>
                    <td><span class="param-value">${point_value:.0f} por punto</span> - Valor contractual NQ Futures</td>
                </tr>
            </table>
        </div>

        <!-- VWAP CROSSOVER STRATEGY -->
        <div class="section">
            <div class="section-header">
                <span class="section-icon">🔄</span>
                <h2>VWAP Crossover Strategy</h2>
            </div>
            <table class="params-table">
                <tr>
                    <td>ENABLE_VWAP_CROSSOVER_STRATEGY</td>
                    <td><span class="param-value {'true' if enable_vwap_crossover else 'false'}">{str(enable_vwap_crossover)}</span> - {"Estrategia ACTIVA" if enable_vwap_crossover else "Estrategia DESHABILITADA"}</td>
                </tr>
                <tr>
                    <td>TP / SL</td>
                    <td><span class="param-value">{crossover_tp} / {crossover_sl} pts</span> - (${crossover_tp * point_value:,.0f} / ${crossover_sl * point_value:,.0f})</td>
                </tr>
                <tr>
                    <td>Trading Hours</td>
                    <td><span class="param-value">{crossover_start} - {crossover_end}</span></td>
                </tr>
            </table>
        </div>

        <!-- VWAP PULLBACK STRATEGY -->
        <div class="section">
            <div class="section-header">
                <span class="section-icon">↩️</span>
                <h2>VWAP Pullback Strategy</h2>
            </div>
            <table class="params-table">
                <tr>
                    <td>ENABLE_VWAP_PULLBACK_STRATEGY</td>
                    <td><span class="param-value {'true' if enable_vwap_pullback else 'false'}">{str(enable_vwap_pullback)}</span> - {"Estrategia ACTIVA" if enable_vwap_pullback else "Estrategia DESHABILITADA"}</td>
                </tr>
                <tr>
                    <td>TP / SL</td>
                    <td><span class="param-value">{pullback_tp} / {pullback_sl} pts</span> - (${pullback_tp * point_value:,.0f} / ${pullback_sl * point_value:,.0f})</td>
                </tr>
                <tr>
                    <td>Trading Hours</td>
                    <td><span class="param-value">{pullback_start} - {pullback_end}</span></td>
                </tr>
            </table>
        </div>

        <!-- VWAP SQUARE STRATEGY -->
        <div class="section">
            <div class="section-header">
                <span class="section-icon">🟥</span>
                <h2>VWAP Square Strategy (Rectangle Breakout)</h2>
            </div>
            <table class="params-table">
                <tr>
                    <td>ENABLE_VWAP_SQUARE_STRATEGY</td>
                    <td><span class="param-value {'true' if enable_vwap_square else 'false'}">{str(enable_vwap_square)}</span> - {"Estrategia ACTIVA" if enable_vwap_square else "Estrategia DESHABILITADA"}</td>
                </tr>
                <tr>
                    <td>TP / SL</td>
                    <td><span class="param-value">{square_tp} / {square_sl} pts</span> - (${square_tp * point_value:,.0f} / ${square_sl * point_value:,.0f})</td>
                </tr>
                <tr>
                    <td>Trading Hours</td>
                    <td><span class="param-value">{square_start} - {square_end}</span></td>
                </tr>
                <tr>
                    <td>VWAP_SQUARE_LISTENING_TIME</td>
                    <td><span class="param-value">{square_listening_time} min</span> - Ventana de escucha después del cierre del rectángulo</td>
                </tr>
                <tr>
                    <td>VWAP_SQUARE_MIN_SPIKE</td>
                    <td><span class="param-value">{square_min_spike} pts</span> - Altura mínima del rectángulo (filtra ruido pequeño)</td>
                </tr>
                <tr>
                    <td>USE_SQUARE_VWAP_SLOW_TREND_FILTER</td>
                    <td><span class="param-value {'true' if use_square_trend_filter else 'false'}">{str(use_square_trend_filter)}</span> - {"Opera solo a favor de tendencia VWAP" if use_square_trend_filter else "Opera en ambas direcciones"}</td>
                </tr>
                <tr>
                    <td>USE_SQUARE_ATR_TRAILING_STOP</td>
                    <td><span class="param-value {'true' if use_square_atr_trailing else 'false'}">{str(use_square_atr_trailing)}</span> - {"ATR Trailing activo (Period={square_atr_period}, Mult={square_atr_mult}x)" if use_square_atr_trailing else "SL fijo"}</td>
                </tr>
                <tr>
                    <td>USE_OPOSITE_SIDE_OF_SQUARE_AS_STOP</td>
                    <td><span class="param-value {'true' if use_opposite_side_stop else 'false'}">{str(use_opposite_side_stop)}</span> - {"SL en lado opuesto del rectángulo" if use_opposite_side_stop else "SL fijo en puntos"}</td>
                </tr>
                <tr>
                    <td>USE_VWAP_SQUARE_SHAKE_OUT</td>
                    <td><span class="param-value {'true' if use_shake_out else 'false'}">{str(use_shake_out)}</span> - {"Shake Out mode: trade failed breakouts" if use_shake_out else "Normal breakout mode"}</td>
                </tr>
                <tr style="{'opacity: 1;' if use_shake_out else 'opacity: 0.6;'}">
                    <td>VWAP_SQUARE_SHAKE_OUT_RETRACEMENT_PCT</td>
                    <td><span class="param-value {'inactive' if not use_shake_out else ''}">{shake_out_retrace_pct}%</span> - {("Requiere retroceso del " + str(shake_out_retrace_pct) + "% para confirmar shake out" if use_shake_out else "No se usa (shake out deshabilitado)")}</td>
                </tr>
            </table>
        </div>

        <!-- RESUMEN EJECUTIVO -->
        <div class="summary-box">
            <h3>📋 Resumen de Configuración Actual</h3>

            <div class="summary-item">
                <strong>Estrategia:</strong> {strategy_name}
            </div>
            <div class="summary-item">
                <strong>Modo Salida:</strong> {exit_mode}{"con JSON Optimizado" if use_json_optimization and use_time_in_market else ""}
            </div>
            <div class="summary-item">
                <strong>Duración:</strong> {"Variable según hora de entrada (JSON)" if use_json_optimization and use_time_in_market else f"{time_in_market_minutes} minutos fijos" if use_time_in_market else f"TP: {tp_points} pts / SL: {sl_points} pts"}
            </div>
            <div class="summary-item">
                <strong>Stop Loss Protector:</strong> {f"{max_sl_points} puntos" if use_max_sl else "Deshabilitado"}
            </div>
            <div class="summary-item">
                <strong>Máx Posiciones:</strong> {max_positions} posición{"es" if max_positions > 1 else ""} simultánea{"s" if max_positions > 1 else ""}
            </div>
            <div class="summary-item">
                <strong>Horario:</strong> {start_hour} - {end_hour}
            </div>
        </div>

    </div>
</body>
</html>
'''

    return html_content

def update_dashboard():
    """Actualiza el dashboard con los valores actuales del config"""
    try:
        # Cargar config
        config = load_config_module()

        # Generar HTML
        html_content = generate_dashboard_html(config)

        # Guardar archivo en outputs/charts
        from config import OUTPUTS_DIR
        charts_dir = OUTPUTS_DIR / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)

        dashboard_path = charts_dir / "config_dashboard.html"
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"[OK] Dashboard actualizado: {dashboard_path}")
        return True

    except Exception as e:
        print(f"[ERROR] No se pudo actualizar dashboard: {str(e)}")
        return False

if __name__ == "__main__":
    success = update_dashboard()

    if success:
        # Automatically open the dashboard in the web browser
        import webbrowser
        from config import OUTPUTS_DIR

        charts_dir = OUTPUTS_DIR / "charts"
        dashboard_path = charts_dir / "config_dashboard.html"

        if dashboard_path.exists():
            print(f"[INFO] Opening configuration dashboard in browser...")
            webbrowser.open(str(dashboard_path))
        else:
            print(f"[ERROR] Dashboard file not found: {dashboard_path}")

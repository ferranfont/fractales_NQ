import pandas as pd
import numpy as np
from typing import Dict, Optional

def calculate_channel(df_price: pd.DataFrame, df_fractals: pd.DataFrame) -> Optional[Dict]:
    """
    Calcula los parámetros del canal basado en la heurística de los PRIMEROS 3 FRACTALES.
    
    Lógica:
    1. Se obtienen los primeros 3 fractales en orden cronológico.
    2. Si los fractales 1 y 3 son del mismo tipo (ej: VALLE), se calcula la pendiente entre ellos.
    3. El canal opuesto se proyecta usando la misma pendiente pasando por el fractal 2 (ej: PICO).
    
    Args:
        df_price: DataFrame principal con datos OHLC y timestamp
        df_fractals: DataFrame con fractales detectados (debe contener 'type', 'price', 'timestamp')
        
    Returns:
        Dict con parámetros del canal: slope, intercept_high, intercept_low, r_value (ficticio aquí)
    """
    if df_fractals is None or df_fractals.empty or df_price is None:
        print("[WARNING] No hay datos suficientes para calcular el canal")
        return None
        
    # Crear un mapa de timestamp -> index para ubicación precisa
    ts_to_idx = {ts: idx for idx, ts in enumerate(df_price['timestamp'])}
    
    # Preparar fractales con índice
    df = df_fractals.copy()
    df['idx'] = df['timestamp'].map(ts_to_idx)
    df = df.dropna(subset=['idx'])
    
    # Ordenar cronológicamente y tomar los primeros 3
    df = df.sort_values('idx').head(3)
    
    if len(df) < 3:
        print(f"[WARNING] Se necesitan al menos 3 fractales para esta lógica. Encontrados: {len(df)}")
        return None
        
    f1 = df.iloc[0]
    f2 = df.iloc[1]
    f3 = df.iloc[2]
    
    print(f"\n[INFO] Usando los primeros 3 fractales para el canal:")
    print(f"  1. {f1['type']} @ {f1['timestamp']} (idx={f1['idx']}, price={f1['price']})")
    print(f"  2. {f2['type']} @ {f2['timestamp']} (idx={f2['idx']}, price={f2['price']})")
    print(f"  3. {f3['type']} @ {f3['timestamp']} (idx={f3['idx']}, price={f3['price']})")
    
    slope = 0.0
    intercept_high = 0.0
    intercept_low = 0.0
    
    # Verificar patrón: F1 y F3 deben ser del mismo tipo
    if f1['type'] == f3['type']:
        # Calcular pendiente entre F1 y F3
        delta_y = f3['price'] - f1['price']
        delta_x = f3['idx'] - f1['idx']
        
        if delta_x == 0:
            print("[ERROR] Fractales 1 y 3 están en el mismo índice")
            return None
            
        slope = delta_y / delta_x
        
        # Calcular intercepto de la línea principal (y = mx + b -> b = y - mx)
        # Usamos F1 como ancla
        b_main = f1['price'] - (slope * f1['idx'])
        
        # Calcular intercepto de la línea paralela (que pasa por F2)
        b_parallel = f2['price'] - (slope * f2['idx'])
        
        # Asignar High/Low dependiendo del tipo
        if f1['type'] == 'VALLE':
            # F1 y F3 son VALLES (Suelo) -> b_main es intercept_low
            # F2 es PICO (Techo) -> b_parallel es intercept_high
            intercept_low = b_main
            intercept_high = b_parallel
            print("[INFO] Patrón detectado: VALLE -> PICO -> VALLE")
            
        elif f1['type'] == 'PICO':
            # F1 y F3 son PICOS (Techo) -> b_main es intercept_high
            # F2 es VALLE (Suelo) -> b_parallel es intercept_low
            intercept_high = b_main
            intercept_low = b_parallel
            print("[INFO] Patrón detectado: PICO -> VALLE -> PICO")
            
    else:
        print("[WARNING] Los fractales 1 y 3 no son del mismo tipo. No se puede aplicar la lógica 1-3.")
        # Podríamos intentar buscar el siguiente fractal del mismo tipo que F1, pero por ahora estricto a primeros 3.
        return None

    print(f"\n[INFO] Canal Calculado (3-Puntos):")
    print(f"  Pendiente (Slope): {slope:.5f}")
    print(f"  Intercepto Superior: {intercept_high:.2f}")
    print(f"  Intercepto Inferior: {intercept_low:.2f}")
    
    # Lógica para FRACTAL CLONE (Dynamic Outlier)
    intercept_clone = None
    clone_start_idx = None
    
    # Re-mapear índices para todo el dataframe de fractales
    df_all = df_fractals.copy()
    df_all['idx'] = df_all['timestamp'].map(ts_to_idx)
    df_all = df_all.dropna(subset=['idx'])
    df_all = df_all.sort_values('idx')
    
    # Iterar sobre los fractales que NO son los primeros 3 (que definen el canal)
    if len(df_all) > 3:
        # Los primeros 3 definen el canal, buscamos outliers a partir del 4to (índice 3)
        potential_outliers = df_all.iloc[3:]
        
        for idx in range(len(potential_outliers)):
            f = potential_outliers.iloc[idx]
            x = f['idx']
            y = f['price']
            
            # Calcular límites teóricos
            y_high = (slope * x) + intercept_high
            y_low = (slope * x) + intercept_low
            
            # Tolerancia pequeña para errores de flotante? No, estricto.
            # Verificar si está fuera (por encima de High o por debajo de Low)
            # Aunque la petición específica fue "fractal low outside... intercept it".
            # Asumiremos rotura por abajo para start (Low) o arriba (High)
            
            is_outlier_low = y < y_low
            # is_outlier_high = y > y_high # (Opcional si queremos clonar por arriba también)
            
            if is_outlier_low:
                print(f"[INFO] Primer Outlier detectado: {f['type']} @ {f['timestamp']} (idx={x}, price={y})")
                print(f"       Límite Low era: {y_low:.2f}, Precio: {y:.2f}")
                
                # Calcular nuevo intercepto
                intercept_clone = y - (slope * x)
                clone_start_idx = int(x)
                print(f"       Intercepto Clonado: {intercept_clone:.2f}")
                break
                
    return {
        'slope': slope,
        'intercept_high': intercept_high,
        'intercept_low': intercept_low,
        'intercept_clone': intercept_clone,
        'clone_start_idx': clone_start_idx,
        'r_value': 1.0, 
        'std_err': 0.0
    }

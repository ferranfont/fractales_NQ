"""
Detección de fractales ZigZag para Gold (GC)
Detecta picos y valles usando algoritmo Zigzag sin look-ahead bias
"""

import pandas as pd
from pathlib import Path
from enum import Enum
from typing import List, Optional

from config import (
    DATA_DIR, FRACTALS_DIR, DIA,
    MIN_CHANGE_PCT_MINOR, MIN_CHANGE_PCT_MAJOR
)


# =============================================================================
# CLASSES
# =============================================================================

class ZigzagDirection(Enum):
    UP = "up"      # Pico (máximo)
    DOWN = "down"  # Valle (mínimo)


class ZigzagPoint:
    def __init__(self, index: int, price: float, direction: ZigzagDirection, timestamp: Optional[str] = None):
        self.index = index
        self.price = price
        self.direction = direction
        self.timestamp = timestamp
        self.confirmed = False

    def __repr__(self):
        tipo = "PICO" if self.direction == ZigzagDirection.UP else "VALLE"
        return f"{tipo} @ idx={self.index}, price={self.price:.2f}, ts={self.timestamp}"


class UnifiedZigzagDetector:
    def __init__(self, min_change_pct: float = 0.15):
        """
        Detector Zigzag unificado que procesa High/Low y garantiza alternancia

        Args:
            min_change_pct: Cambio mínimo en porcentaje (ej: 0.15 = 0.15%)
        """
        self.min_change_pct = min_change_pct / 100.0  # Convertir a decimal

        # Estado del detector
        self.candles = []  # Lista de velas (dict con High, Low, index)
        self.current_trend = None  # None, UP (buscando pico), DOWN (buscando valle)
        self.last_pivot = None  # Último punto de giro confirmado

        # Buffer para tracking
        self.current_high = None  # Máximo actual desde último valle
        self.current_high_index = None
        self.current_high_timestamp = None
        self.current_low = None   # Mínimo actual desde último pico
        self.current_low_index = None
        self.current_low_timestamp = None

        # Puntos de giro detectados
        self.zigzag_points = []

    def add_candle(self, high: float, low: float, index: int, timestamp: str = None) -> Optional[ZigzagPoint]:
        """
        Añade una nueva vela y retorna un punto zigzag si se detecta

        Args:
            high: Precio máximo de la vela
            low: Precio mínimo de la vela
            index: Índice de la vela
            timestamp: Timestamp de la vela (opcional)

        Returns:
            ZigzagPoint si se confirma un punto de giro, None en caso contrario
        """
        candle = {'high': high, 'low': low, 'index': index, 'timestamp': timestamp}
        self.candles.append(candle)

        # Primera vela - inicializar
        if len(self.candles) == 1:
            self.current_high = high
            self.current_high_index = index
            self.current_high_timestamp = timestamp
            self.current_low = low
            self.current_low_index = index
            self.current_low_timestamp = timestamp
            return None

        # Segunda vela - determinar tendencia inicial
        if len(self.candles) == 2:
            if high > self.current_high:
                self.current_high = high
                self.current_high_index = index
                self.current_high_timestamp = timestamp
            if low < self.current_low:
                self.current_low = low
                self.current_low_index = index
                self.current_low_timestamp = timestamp

            # Establecer tendencia inicial basada en qué se movió más
            high_change = (self.current_high - self.candles[0]['high']) / self.candles[0]['high']
            low_change = (self.candles[0]['low'] - self.current_low) / self.candles[0]['low']

            if high_change > low_change:
                self.current_trend = ZigzagDirection.UP
                self.last_pivot = ZigzagPoint(
                    self.current_low_index,
                    self.current_low,
                    ZigzagDirection.DOWN,
                    self.current_low_timestamp
                )
            else:
                self.current_trend = ZigzagDirection.DOWN
                self.last_pivot = ZigzagPoint(
                    self.current_high_index,
                    self.current_high,
                    ZigzagDirection.UP,
                    self.current_high_timestamp
                )
            return None

        return self._check_for_pivot(candle)

    def _check_for_pivot(self, candle: dict) -> Optional[ZigzagPoint]:
        """
        Verifica si la vela actual constituye un punto de giro
        """
        high = candle['high']
        low = candle['low']
        index = candle['index']
        timestamp = candle.get('timestamp')

        # Actualizar extremos actuales
        if high > self.current_high:
            self.current_high = high
            self.current_high_index = index
            self.current_high_timestamp = timestamp
        if low < self.current_low:
            self.current_low = low
            self.current_low_index = index
            self.current_low_timestamp = timestamp

        if not self.last_pivot:
            return None

        # Si estamos buscando un pico (tendencia alcista)
        if self.current_trend == ZigzagDirection.UP:
            if self.current_high > self.last_pivot.price:
                change_from_high = (self.current_high - low) / self.current_high
                if change_from_high >= self.min_change_pct:
                    pivot = ZigzagPoint(
                        self.current_high_index,
                        self.current_high,
                        ZigzagDirection.UP,
                        self.current_high_timestamp
                    )
                    pivot.confirmed = True
                    self.zigzag_points.append(pivot)
                    self.last_pivot = pivot
                    self.current_trend = ZigzagDirection.DOWN

                    self.current_low = low
                    self.current_low_index = index
                    self.current_low_timestamp = timestamp

                    return pivot

        # Si estamos buscando un valle (tendencia bajista)
        elif self.current_trend == ZigzagDirection.DOWN:
            if self.current_low < self.last_pivot.price:
                change_from_low = (high - self.current_low) / self.current_low
                if change_from_low >= self.min_change_pct:
                    pivot = ZigzagPoint(
                        self.current_low_index,
                        self.current_low,
                        ZigzagDirection.DOWN,
                        self.current_low_timestamp
                    )
                    pivot.confirmed = True
                    self.zigzag_points.append(pivot)
                    self.last_pivot = pivot
                    self.current_trend = ZigzagDirection.UP

                    self.current_high = high
                    self.current_high_index = index
                    self.current_high_timestamp = timestamp

                    return pivot

        return None

    def get_zigzag_points(self) -> List[ZigzagPoint]:
        """
        Retorna todos los puntos zigzag detectados
        """
        return self.zigzag_points.copy()


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def detect_fractals(df: pd.DataFrame, min_change_pct: float, tag: str) -> pd.DataFrame:
    """
    Detecta fractales en los datos OHLC

    Args:
        df: DataFrame con columnas timestamp, open, high, low, close
        min_change_pct: Cambio mínimo en porcentaje
        tag: 'major' o 'minor'

    Returns:
        DataFrame con fractales detectados
    """
    print(f"\n[INFO] Detectando fractales {tag.upper()} (min_change={min_change_pct:.3f}%)...")

    detector = UnifiedZigzagDetector(min_change_pct=min_change_pct)

    # Procesar cada vela
    for idx, row in df.iterrows():
        detector.add_candle(
            high=row['high'],
            low=row['low'],
            index=idx,
            timestamp=row['timestamp']
        )

    # Obtener fractales detectados
    fractals = detector.get_zigzag_points()

    print(f"[OK] Detectados {len(fractals)} fractales {tag}")

    # Contar picos y valles
    picos = [f for f in fractals if f.direction == ZigzagDirection.UP]
    valles = [f for f in fractals if f.direction == ZigzagDirection.DOWN]
    print(f"    Picos: {len(picos)}")
    print(f"    Valles: {len(valles)}")

    # Verificar alternancia
    alternancia_correcta = True
    for i in range(1, len(fractals)):
        if fractals[i].direction == fractals[i-1].direction:
            alternancia_correcta = False
            print(f"[WARNING] Alternancia incorrecta en índices {fractals[i-1].index} y {fractals[i].index}")

    if alternancia_correcta and len(fractals) > 1:
        print(f"[OK] Alternancia correcta verificada")

    # Convertir a DataFrame
    data = []
    for f in fractals:
        tipo = "PICO" if f.direction == ZigzagDirection.UP else "VALLE"
        data.append({
            'timestamp': f.timestamp,
            'price': f.price,
            'type': tipo,
            'direction': f.direction.value,
            'tag': tag
        })

    return pd.DataFrame(data)


def main():
    """
    Función principal de ejecución
    """
    print("="*70)
    print("DETECCIÓN DE FRACTALES - Gold (GC)")
    print("="*70)
    print(f"\nDía a procesar: {DIA}")
    print(f"Minor threshold: {MIN_CHANGE_PCT_MINOR}%")
    print(f"Major threshold: {MIN_CHANGE_PCT_MAJOR}%")
    print("-"*70)

    # Leer archivo del día
    csv_path = DATA_DIR / f"gc_{DIA}.csv"
    if not csv_path.exists():
        print(f"\n[ERROR] Archivo no encontrado: {csv_path}")
        return

    print(f"\n[INFO] Cargando datos de: {csv_path.name}")
    df = pd.read_csv(csv_path)
    print(f"[OK] Cargados {len(df)} registros")

    # Verificar columnas
    required_cols = ['timestamp', 'open', 'high', 'low', 'close']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"[ERROR] Faltan columnas: {missing}")
        return

    # Detectar fractales MINOR
    df_fractals_minor = detect_fractals(df, MIN_CHANGE_PCT_MINOR, 'minor')

    # Detectar fractales MAJOR
    df_fractals_major = detect_fractals(df, MIN_CHANGE_PCT_MAJOR, 'major')

    # Crear directorio de salida
    FRACTALS_DIR.mkdir(parents=True, exist_ok=True)

    # Guardar fractales
    output_minor = FRACTALS_DIR / f"gc_fractals_minor_{DIA}.csv"
    output_major = FRACTALS_DIR / f"gc_fractals_major_{DIA}.csv"

    df_fractals_minor.to_csv(output_minor, index=False)
    df_fractals_major.to_csv(output_major, index=False)

    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"Registros procesados: {len(df)}")
    print(f"Fractales MINOR: {len(df_fractals_minor)}")
    print(f"  - Guardado en: {output_minor}")
    print(f"Fractales MAJOR: {len(df_fractals_major)}")
    print(f"  - Guardado en: {output_major}")
    print("="*70)


if __name__ == "__main__":
    main()

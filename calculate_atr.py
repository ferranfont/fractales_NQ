import pandas as pd
import numpy as np

def calculate_atr(df, period=14):
    """
    Calculate Average True Range (ATR) for a DataFrame.
    
    Args:
        df: DataFrame containing 'high', 'low', 'close' columns
        period: ATR period (default 14)
        
    Returns:
        pd.Series: ATR values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate True Range (TR)
    # TR = Max(H-L, |H-Cp|, |L-Cp|)
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate ATR (Wilder's Smoothing usually, or SMA for simplicity)
    # Here using SMA as per the VIX example which uses rolling mean
    # "atr = tr.rolling(window=atr_period).mean()"
    atr = tr.rolling(window=period).mean()
    
    return atr

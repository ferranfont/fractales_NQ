import pandas as pd
import numpy as np
from config import PRICE_EJECTION_TRIGGER

def find_trend_divergence_dots(df):
    """
    Identifies the first 'Green Dot' (Price Ejection) after a Price/VWAP Fast Crossover/Crossdown.
    These specific Green Dots are to be plotted as Orange Dots.
    
    Args:
        df: DataFrame with 'close' and 'vwap_fast' columns.
        
    Returns:
        DataFrame containing only the rows where the Orange Dot should be plotted.
    """
    if 'vwap_fast' not in df.columns:
        return pd.DataFrame()
    
    # Working on a copy to avoid SettingWithCopy warnings on the original df
    work_df = df.copy()
    
    # 1. Identify Price Ejection (Green Dots) based on config logic
    # Logic from plot_day.py: abs((df['close'] - df['vwap_fast']) / df['vwap_fast']) >= PRICE_EJECTION_TRIGGER
    work_df['price_vwap_dist'] = abs((work_df['close'] - work_df['vwap_fast']) / work_df['vwap_fast'])
    work_df['is_green_dot'] = work_df['price_vwap_dist'] >= PRICE_EJECTION_TRIGGER
    
    # 2. Identify Crossovers/Crossdowns
    work_df['prev_close'] = work_df['close'].shift(1)
    work_df['prev_vwap'] = work_df['vwap_fast'].shift(1)
    
    # Crossover: Close crosses ABOVE VWAP
    # (Prev Close <= Prev VWAP) AND (Curr Close > Curr VWAP) - using <= to catch exact touches
    crossover = (work_df['prev_close'] <= work_df['prev_vwap']) & (work_df['close'] > work_df['vwap_fast'])
    
    # Crossdown: Close crosses BELOW VWAP
    # (Prev Close >= Prev VWAP) AND (Curr Close < Curr VWAP)
    crossdown = (work_df['prev_close'] >= work_df['prev_vwap']) & (work_df['close'] < work_df['vwap_fast'])
    
    work_df['is_cross'] = crossover | crossdown
    
    # 3. Find First Green Dot after Cross
    orange_dots_indices = []
    waiting_for_dot = False
    
    # Iterate to find the sequence: Cross -> ... -> Green Dot
    # Using itertuples for speed
    for row in work_df.itertuples():
        if row.is_cross:
            waiting_for_dot = True
            # If a cross happens on a green dot (unlikely but possible), 
            # we count it? "after" usually implies subsequent. 
            # If strict "after", we continue. If inclusive, check here.
            # Assuming "after" means strictly subsequent time steps or same step is fine?
            # User said "first green dot after...". 
            # Let's assume if it happens SAME bar, it counts (immediate divergence).
            
        if waiting_for_dot and row.is_green_dot:
            # Found the target dot
            orange_dots_indices.append(row.Index)
            waiting_for_dot = False # Reset, wait for next cross
            
    # Return the subset of the original dataframe
    return df.loc[orange_dots_indices].copy()

import numpy as np
import pandas as pd
from scipy.stats import linregress

def calculate_clenow_momentum(df, window=125, projection_factor=1440):
    """
    Calculates Clenow Systematic Momentum Score for Intraday Data.
    
    Formula:
        Score = (Projected Exponential Slope) * (R^2)
        
    Args:
        df: DataFrame with 'close' column.
        window: Rolling window size (number of bars).
        projection_factor: Factor to project slope to a larger timeframe 
                           (e.g., 1440 for Daily projection of 1-min data).
                           
    Returns:
        df: DataFrame with added columns: 'clenow_score', 'clenow_slope', 'clenow_r2'.
    """
    if 'close' not in df.columns:
        return df
        
    # 1. Natural Log of Price
    log_prices = np.log(df['close'])
    
    # 2. Helper for Rolling R^2 (Correlation^2)
    # We correlate Log-Price vs Time (0..N)
    # Since Time is a perfect line, correlation of (Y, Time) = Correlation of Trend
    
    # Construct a static time array 0..N-1 for correlation reference
    # Note: Rolling correlation with a fixed 'other' requires a trick or loop.
    # But R^2 in regression is just square of correlation coefficient.
    
    # Fast approach for Rolling Correlation against Index (0..N):
    # We can use pandas rolling .corr() if we construct a time series?
    # Actually, simpler: 
    # Slope = Cov(X,Y) / Var(X)
    # R^2 = (Cov(X,Y) / (Std(X)*Std(Y)))^2
    
    # Constants for window X = [0, 1, ..., window-1]
    x = np.arange(window)
    var_x = x.var()
    mean_x = x.mean()
    std_x = x.std()
    
    # We need rolling Covariance(LogPrice, Time) and rolling Variance(LogPrice)
    
    # A) Rolling Covariance(Y, X) = Mean(XY) - Mean(X)*Mean(Y)
    # To compute Rolling Mean(XY) efficiently where X resets every window (0..N-1):
    # This is equivalent to Weighted Moving Average with weights 0..N-1
    # We can use a convolution.
    
    # 3. Vectorized Convolution for "Sum of (Y * Index)"
    weights = np.arange(window)
    # Ensure no NaN in convolution (fill with 0 or handle) - validation done by pandas rolling mostly
    # We use numpy convolve
    
    # Valid convolution mode returns only fully overlapping parts
    # But pandas rolling aligns to right.
    
    try:
        y_values = log_prices.values
        
        # Convolve `y` with `weights` reversed (because convolve flips the kernel)
        # We want at index i: sum(y[i-w+1+k] * k) for k in 0..w-1
        sum_xy = np.convolve(y_values, weights[::-1], mode='full')[:len(y_values)]
        # Shift sum_xy because 'full' convolution starts early.
        # Actually, 'full' output index i corresponds to end of overlap? 
        # Easier to check: convolve([1,1], [0,1]) -> 
        # index 0: 1*0
        # index 1: 1*1 + 1*0
        # We need to be careful with alignment.
        # Let's use `valid` and pad?
        
        # Proper alignment:
        # sum_xy should start having values at index `window-1`.
        sum_xy = np.full(len(y_values), np.nan)
        conv_valid = np.convolve(y_values, weights[::-1], mode='valid')
        sum_xy[window-1:] = conv_valid
        
    except Exception as e:
        print(f"[WARN] Vectorized Clenow Calculation failed: {e}. Falling back to slow method.")
        # Fallback (slow but safe)
        return calculate_clenow_momentum_slow(df, window, projection_factor)

    # Rolling Mean(Y)
    mean_y = log_prices.rolling(window=window).mean()
    
    # Rolling Covariance (XY)
    # Cov(X,Y) = E[XY] - E[X]E[Y]
    # mean_xy = sum_xy / window
    mean_xy = sum_xy / window
    
    cov_xy = mean_xy - (mean_x * mean_y)
    
    # Slope = Cov(X, Y) / Var(X)
    slope = cov_xy / var_x
    
    # R^2 calculation
    # R = Cov(X,Y) / (Std(X) * Std(Y))
    std_y = log_prices.rolling(window=window).std(ddof=0) # Match numpy std default ddof=0 for consistency with var_x?
    # std_x is from numpy (ddof=0 by default)
    
    r_value = cov_xy / (std_x * std_y)
    r2 = r_value ** 2
    
    # 4. Projected Slope and Score
    # The book annualizes: (exp(slope)^252 - 1)
    # We project to daily minutes: (exp(slope)^1440 - 1) * 100
    
    # Avoid overflow if slope is crazy high (e.g. data error)
    # slope is log-return per minute. 0.0001 is common.
    
    projected_return = (np.power(np.exp(slope), projection_factor) - 1) * 100
    
    # 5. Final Score
    # Score = Projected_Return * R^2
    score = projected_return * r2
    
    # Assign columns
    df['clenow_slope'] = projected_return
    df['clenow_r2'] = r2
    df['clenow_score'] = score
    
    return df

def calculate_clenow_momentum_slow(df, window, projection_factor):
    """Fallback slow implementation using apply."""
    x = np.arange(window)
    log_prices = np.log(df['close'])
    
    def get_score_row(y_window):
        if len(y_window) < window: return np.nan
        slope, intercept, r_val, p_val, std_err = linregress(x, y_window)
        
        # Project
        proj_ret = (np.power(np.exp(slope), projection_factor) - 1) * 100
        score = proj_ret * (r_val ** 2)
        return pd.Series({'score': score, 'slope': proj_ret, 'r2': r_val**2})

    results = log_prices.rolling(window=window).apply(
        lambda y: get_score_row(y)['score'], raw=True # Only returning score to keep it simple for apply
    )
    # This slow method is incomplete/complex to return multiple cols with apply.
    # Just returning score for safety if vectorization breaks.
    df['clenow_score'] = results
    return df

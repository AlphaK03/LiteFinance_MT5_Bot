import pandas as pd

def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calculate_dema(series, period):
    ema = calculate_ema(series, period)
    dema = 2 * ema - calculate_ema(ema, period)
    return dema

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_stochastic(df, k_period=5, d_period=3, smooth_k=3):
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()
    k_fast = 100 * ((df['close'] - low_min) / (high_max - low_min))
    k_slow = k_fast.rolling(window=smooth_k).mean()
    d_slow = k_slow.rolling(window=d_period).mean()
    return k_slow, d_slow

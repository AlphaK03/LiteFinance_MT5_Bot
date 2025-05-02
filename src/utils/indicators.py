import pandas as pd

def calculate_ema(prices: pd.Series, period=10):
    return prices.ewm(span=period, adjust=False).mean()

def calculate_rsi(prices: pd.Series, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

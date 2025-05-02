import MetaTrader5 as mt5
import pandas as pd
from utils.indicators import calculate_ema, calculate_rsi

def get_data(symbol, timeframe, candles):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, candles)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def analyze_trend(df, slope_threshold=0.05, min_range=0.2):
    df['EMA'] = calculate_ema(df['close'], period=10)

    last_close = df['close'].iloc[-1]
    last_ema = df['EMA'].iloc[-1]
    prev_ema = df['EMA'].iloc[-4]
    ema_slope = last_ema - prev_ema

    # Velas alcistas y bajistas en las últimas 5
    bullish_count = sum(df['close'].iloc[-5:] > df['open'].iloc[-5:])
    bearish_count = sum(df['close'].iloc[-5:] < df['open'].iloc[-5:])

    # Rango reciente
    recent_range = df['close'].iloc[-10:].max() - df['close'].iloc[-10:].min()

    if recent_range < min_range or abs(ema_slope) < slope_threshold:
        return "HOLD"

    if bullish_count >= 4 and last_close > last_ema and ema_slope > 0:
        return "BUY"
    elif bearish_count >= 4 and last_close < last_ema and ema_slope < 0:
        return "SELL"
    else:
        return "HOLD"

def predict_multi_tf(symbol):
    df_m1 = get_data(symbol, mt5.TIMEFRAME_M1, 100)
    df_m5 = get_data(symbol, mt5.TIMEFRAME_M5, 100)

    signal_m1 = analyze_trend(df_m1)
    signal_m5 = analyze_trend(df_m5)

    print(f"🧠 Señales → M1: {signal_m1}, M5: {signal_m5}")

    # Lógica permisiva si uno es fuerte y otro no se opone
    if signal_m1 == signal_m5 and signal_m1 != "HOLD":
        return signal_m1
    elif signal_m1 != "HOLD" and signal_m5 == "HOLD":
        return signal_m1
    elif signal_m5 != "HOLD" and signal_m1 == "HOLD":
        return signal_m5
    else:
        return "HOLD"

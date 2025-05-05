import MetaTrader5 as mt5
import pandas as pd
from src.utils.indicators import calculate_ema, calculate_rsi

def get_data(symbol, timeframe, candles):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, candles)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def analyze_trend(df):
    df['EMA'] = calculate_ema(df['close'], period=10)
    df['EMA_fast'] = calculate_ema(df['close'], period=3)   # más sensible
    df['EMA_slow'] = calculate_ema(df['close'], period=12)

    bullish_count = sum(df['close'].iloc[-5:] > df['open'].iloc[-5:])
    bearish_count = sum(df['close'].iloc[-5:] < df['open'].iloc[-5:])

    last_close = df['close'].iloc[-1]
    ema = df['EMA'].iloc[-1]
    ema_fast = df['EMA_fast'].iloc[-1]
    ema_slow = df['EMA_slow'].iloc[-1]

    # BUY agresivo: 2 velas verdes, cruce positivo y precio > EMA
    if bullish_count >= 2 and ema_fast > ema_slow and last_close > ema:
        return "BUY"
    # SELL agresivo: 2 velas rojas, cruce negativo y precio < EMA
    elif bearish_count >= 2 and ema_fast < ema_slow and last_close < ema:
        return "SELL"

    return "HOLD"

def predict_multi_tf(symbol):
    df_m1 = get_data(symbol, mt5.TIMEFRAME_M1, 30)
    df_m5 = get_data(symbol, mt5.TIMEFRAME_M5, 30)

    signal_m1 = analyze_trend(df_m1)
    signal_m5 = analyze_trend(df_m5)

    print(f"⚡ Señales rápidas → M1: {signal_m1}, M5: {signal_m5}")

    if signal_m1 == signal_m5 and signal_m1 != "HOLD":
        return signal_m1
    elif signal_m1 != "HOLD":
        return signal_m1
    elif signal_m5 != "HOLD":
        return signal_m5
    else:
        return "HOLD"

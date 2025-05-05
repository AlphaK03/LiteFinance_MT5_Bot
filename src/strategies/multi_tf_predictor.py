
import MetaTrader5 as mt5
import pandas as pd
from src.utils.indicators import calculate_ema, calculate_rsi

def get_data(symbol, timeframe, candles):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, candles)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def analyze_trend(df, slope_threshold=0.05, min_range=0.2):
    df['EMA'] = calculate_ema(df['close'], period=10)
    df['EMA_fast'] = calculate_ema(df['close'], period=5)
    df['EMA_slow'] = calculate_ema(df['close'], period=20)
    df['RSI'] = calculate_rsi(df['close'], period=14)

    bullish_count = sum(df['close'].iloc[-5:] > df['open'].iloc[-5:])
    bearish_count = sum(df['close'].iloc[-5:] < df['open'].iloc[-5:])

    df['body'] = abs(df['close'] - df['open'])
    df['upper_wick'] = df['high'] - df[['close', 'open']].max(axis=1)
    df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
    mecha_larga = (
        df['upper_wick'].iloc[-1] > df['body'].iloc[-1] * 1.5 or
        df['lower_wick'].iloc[-1] > df['body'].iloc[-1] * 1.5
    )

    last_close = df['close'].iloc[-1]
    last_ema = df['EMA'].iloc[-1]
    prev_ema = df['EMA'].iloc[-4]
    ema_slope = last_ema - prev_ema
    recent_range = df['close'].iloc[-10:].max() - df['close'].iloc[-10:].min()
    rsi = df['RSI'].iloc[-1]

    if recent_range < min_range or abs(ema_slope) < slope_threshold:
        return "HOLD"
    if rsi > 75 or rsi < 25:
        return "HOLD"
    if mecha_larga:
        return "HOLD"

    # Señal de compra
    if bullish_count >= 4 and last_close > last_ema and ema_slope > 0:
        if df['EMA_fast'].iloc[-1] > df['EMA_slow'].iloc[-1]:
            distancia_ema = abs(last_close - last_ema)
            relativa_ema = distancia_ema / last_ema
            if relativa_ema < 0.0015:  # evitar comprar en la cima
                return "BUY"
    # Señal de venta
    elif bearish_count >= 4 and last_close < last_ema and ema_slope < 0:
        if df['EMA_fast'].iloc[-1] < df['EMA_slow'].iloc[-1]:
            distancia_ema = abs(last_close - last_ema)
            relativa_ema = distancia_ema / last_ema
            if relativa_ema < 0.0015:  # evitar vender en el fondo
                return "SELL"

    return "HOLD"

def predict_multi_tf(symbol):
    df_m1 = get_data(symbol, mt5.TIMEFRAME_M1, 100)
    df_m5 = get_data(symbol, mt5.TIMEFRAME_M5, 100)

    signal_m1 = analyze_trend(df_m1)
    signal_m5 = analyze_trend(df_m5)

    print(f"🧠 Señales → M1: {signal_m1}, M5: {signal_m5}")

    if signal_m1 == signal_m5 and signal_m1 != "HOLD":
        return signal_m1
    elif signal_m1 != "HOLD" and signal_m5 == "HOLD":
        return signal_m1
    elif signal_m5 != "HOLD" and signal_m1 == "HOLD":
        return signal_m5
    else:
        return "HOLD"

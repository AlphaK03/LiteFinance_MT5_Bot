from src.utils.indicators import calculate_ema, calculate_rsi

def predict_signal(df):
    df['EMA'] = calculate_ema(df['close'], period=10)
    df['RSI'] = calculate_rsi(df['close'], period=14)

    last_close = df['close'].iloc[-1]
    last_ema = df['EMA'].iloc[-1]
    prev_ema = df['EMA'].iloc[-4]  # más atrás para evaluar pendiente
    rsi = df['RSI'].iloc[-1]

    ema_slope = last_ema - prev_ema
    ema_trending_up = ema_slope > 0
    ema_trending_down = ema_slope < 0

    # Señal de COMPRA
    if (
        rsi < 40 and
        last_close > last_ema and
        ema_trending_up
    ):
        return "BUY"

    # Señal de VENTA
    elif (
        rsi > 60 and
        last_close < last_ema and
        ema_trending_down
    ):
        return "SELL"

    else:
        return "HOLD"

import MetaTrader5 as mt5
import pandas as pd
from src.utils.indicators import calculate_dema, calculate_rsi, calculate_stochastic

def get_data(symbol, timeframe=mt5.TIMEFRAME_M1, candles=40):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, candles)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def predict_dema_rsi_stoch(symbol, threshold=0.01):
    df = get_data(symbol)
    if len(df) < 20:
        return "HOLD"

    # Indicadores
    df['DEMA'] = calculate_dema(df['close'], 10)
    df['RSI'] = calculate_rsi(df['close'], 14)
    df['STOCH_K'], df['STOCH_D'] = calculate_stochastic(df)

    # Últimos valores
    last_price = df['close'].iloc[-1]
    last_dema = df['DEMA'].iloc[-1]
    last_rsi = df['RSI'].iloc[-1]
    last_k = df['STOCH_K'].iloc[-1]
    last_d = df['STOCH_D'].iloc[-1]

    # Pendiente DEMA
    slope_dema = df['DEMA'].iloc[-1] - df['DEMA'].iloc[-4]

    # Racha de velas
    green_count = 0
    red_count = 0
    for i in range(1, 6):
        if df['close'].iloc[-i] > df['open'].iloc[-i]:
            green_count += 1
            red_count = 0
        elif df['close'].iloc[-i] < df['open'].iloc[-i]:
            red_count += 1
            green_count = 0

    # Mostrar contexto
    print(f"💡 DEMA slope: {slope_dema:.5f}, RSI: {last_rsi:.2f}, Stoch: K={last_k:.2f} D={last_d:.2f}, Green: {green_count}, Red: {red_count}")

    # === FILTROS ===
    if green_count >= 4:
        print("⚠️ Demasiadas velas verdes, posible agotamiento.")
        return "HOLD"
    if red_count >= 4:
        print("⚠️ Demasiadas velas rojas, posible rebote.")
        return "HOLD"

    if last_rsi > 70:
        print("⚠️ RSI en sobrecompra, evitando BUY.")
        return "HOLD"
    if last_rsi < 30:
        print("⚠️ RSI en sobreventa, evitando SELL.")
        return "HOLD"

    if slope_dema < 0.01 and last_price > last_dema:
        print("⚠️ DEMA sin fuerza suficiente para BUY.")
        return "HOLD"
    if slope_dema > -0.01 and last_price < last_dema:
        print("⚠️ DEMA sin fuerza suficiente para SELL.")
        return "HOLD"

    # === SEÑALES ===
    if (
        last_price > last_dema and
        last_rsi > 50 and last_rsi < 68 and
        last_k > last_d and last_k < 80
    ):
        print("✅ BUY confirmado")
        return "BUY"

    if (
        last_price < last_dema and
        last_rsi < 50 and last_rsi > 32 and
        last_k < last_d and last_k > 20
    ):
        print("✅ SELL confirmado")
        return "SELL"

    print("⏸ HOLD por condiciones no alineadas.")
    return "HOLD"

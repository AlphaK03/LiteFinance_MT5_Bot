import MetaTrader5 as mt5
from datetime import datetime
from colorama import Fore
import time

# Modo de llenado global (caché)
FILLING_MODE = None

def detectar_filling_mode_valido(symbol):
    info = mt5.symbol_info(symbol)
    if info is None:
        print(Fore.RED + f"❌ No se pudo obtener información del símbolo {symbol}")
        return mt5.ORDER_FILLING_FOK  # valor por defecto

    for modo in [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN]:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": 0.01,
            "type": mt5.ORDER_TYPE_BUY,
            "price": mt5.symbol_info_tick(symbol).ask,
            "deviation": 10,
            "magic": 42,
            "comment": "FILL_TEST",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": modo,
        }

        result = mt5.order_check(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(Fore.GREEN + f"✅ Modo de llenado aceptado: {modo}")
            return modo

    print(Fore.YELLOW + f"⚠️ No se encontró un modo válido. Usando FOK por defecto.")
    return mt5.ORDER_FILLING_FOK

def hay_operacion_abierta(symbol):
    posiciones = mt5.positions_get(symbol=symbol)
    return posiciones and len(posiciones) > 0

def esperar_nueva_vela(symbol, timeframe=mt5.TIMEFRAME_M1, timeout=30):
    print(Fore.CYAN + "⏳ Esperando nueva vela M1...")
    start_time = time.time()

    ultima_vela = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
    if not ultima_vela or len(ultima_vela) == 0:
        print(Fore.RED + "❌ No se pudo obtener la vela actual.")
        return False

    ultimo_ts = ultima_vela[0]['time']

    while time.time() - start_time < timeout:
        nueva_vela = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
        if nueva_vela and nueva_vela[0]['time'] != ultimo_ts:
            ts = datetime.fromtimestamp(nueva_vela[0]['time']).strftime('%H:%M:%S')
            print(Fore.GREEN + f"🟢 Nueva vela detectada: {ts}")
            return True
        time.sleep(0.2)

    print(Fore.RED + "⏰ Timeout esperando nueva vela.")
    return False

def open_trade(symbol, direction, volume):
    global FILLING_MODE

    if hay_operacion_abierta(symbol):
        print(Fore.YELLOW + f"⚠️ Ya hay una operación activa para {symbol}. No se abrirá otra.")
        return None

    print(Fore.CYAN + "🚀 Ejecutando orden inmediatamente tras sincronización.")

    if FILLING_MODE is None:
        FILLING_MODE = detectar_filling_mode_valido(symbol)

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(Fore.RED + "❌ No se pudo obtener el precio actual del símbolo.")
        return None

    price = tick.ask if direction == "BUY" else tick.bid
    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": 10,
        "magic": 42,
        "comment": "Trade AUTO",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": FILLING_MODE,
    }

    result = mt5.order_send(request)

    if result is None:
        print(Fore.RED + "❌ mt5.order_send() retornó None.")
        return None

    print(Fore.CYAN + f"🔁 Resultado: retcode={result.retcode}, comentario='{result.comment}'")

    if result.retcode in [mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED, mt5.TRADE_RETCODE_DONE_PARTIAL]:
        print(Fore.GREEN + f"✅ Operación enviada correctamente (retcode {result.retcode})")
        return result
    else:
        print(Fore.RED + f"❌ Falló con retcode {result.retcode}: {result.comment}")
        return result

import MetaTrader5 as mt5
from datetime import datetime
from colorama import Fore
import time

def esperar_antes_de_apertura(symbol, anticipacion_segundos=2):
    print(f"⏳ Esperando hasta {anticipacion_segundos}s antes de la próxima vela M1...")
    while True:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            time.sleep(0.1)
            continue
        broker_time = datetime.fromtimestamp(tick.time)
        segundos_restantes = 60 - broker_time.second
        if segundos_restantes == anticipacion_segundos:
            print(f"🟢 Ejecutando operación a las {broker_time.strftime('%H:%M:%S')} (anticipado)")
            break
        time.sleep(0.05)

def hay_operacion_abierta(symbol):
    posiciones = mt5.positions_get(symbol=symbol)
    return posiciones and len(posiciones) > 0

def open_trade(symbol, direction, volume):
    if hay_operacion_abierta(symbol):
        print(Fore.YELLOW + f"⚠️ Ya hay una operación activa para {symbol}. No se abrirá otra.")
        return None

    esperar_antes_de_apertura(symbol, anticipacion_segundos=2)

    price = mt5.symbol_info_tick(symbol).ask if direction == "BUY" else mt5.symbol_info_tick(symbol).bid
    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL

    for filling_mode in [1, 0]:  # IOC y luego FOK
        print(Fore.YELLOW + f"🧪 Probando modo de llenado: {filling_mode}")
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 10,
            "magic": 42,
            "comment": "Test Order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(Fore.GREEN + f"✅ Operación ejecutada correctamente con modo: {filling_mode}")
            return result
        elif result:
            print(Fore.RED + f"❌ Retcode {result.retcode} - {result.comment}")

    print(Fore.RED + "❌ No se pudo abrir la operación.")
    return None

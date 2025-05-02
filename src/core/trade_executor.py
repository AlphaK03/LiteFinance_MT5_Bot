import MetaTrader5 as mt5
from colorama import Fore

def open_trade(symbol, direction, volume):
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

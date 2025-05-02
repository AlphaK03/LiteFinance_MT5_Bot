import MetaTrader5 as mt5
import time
from colorama import init, Fore
from datetime import datetime
import os

init(autoreset=True)

SYMBOL = "XAUUSD"
VOLUME = 0.01

def connect():
    print(Fore.CYAN + "🔌 Conectando a MetaTrader 5...")
    if not mt5.initialize():
        print(Fore.RED + f"❌ Error al conectar: {mt5.last_error()}")
        exit()
    print(Fore.GREEN + "✅ Conexión establecida con MetaTrader 5")

def disconnect():
    mt5.shutdown()
    print(Fore.CYAN + "🔌 Desconectado de MetaTrader 5.")

def open_trade(symbol, volume):
    price = mt5.symbol_info_tick(symbol).ask
    order_type = mt5.ORDER_TYPE_BUY

    for mode in [1, 0]:  # Intenta IOC, luego FOK
        print(Fore.YELLOW + f"🧪 Probando modo de llenado: {mode}")
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 10,
            "magic": 42,
            "comment": "Test Open",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mode,
        }
        result = mt5.order_send(request)

        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(Fore.GREEN + f"✅ Operación ejecutada correctamente con modo: {mode}")
            return result
        else:
            print(Fore.RED + f"❌ Retcode {result.retcode if result else 'None'} - {result.comment if result else 'Sin respuesta'}")

    return None

def close_trade(pos, symbol):
    existing_positions = mt5.positions_get(ticket=pos.ticket)
    if not existing_positions:
        print(Fore.YELLOW + f"⚠️ La posición {pos.ticket} ya no está activa.")
        return None

    close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print(Fore.RED + f"❌ No se pudo obtener el precio actual de {symbol}.")
        return None

    close_price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": pos.ticket,
        "symbol": symbol,
        "volume": pos.volume,
        "type": close_type,
        "price": close_price,
        "deviation": 10,
        "magic": 42,
        "comment": "Test Close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": 0,
    }

    print(Fore.YELLOW + f"📤 Enviando cierre: vol={pos.volume}, tipo={close_type}, precio={close_price:.2f}")
    result = mt5.order_send(request)

    if result is None:
        print(Fore.RED + "❌ mt5.order_send() retornó None. Reintentando tras reconexión...")
        mt5.shutdown()
        if not mt5.initialize():
            print(Fore.RED + "❌ Reintento fallido: no se pudo reconectar.")
            return None
        result = mt5.order_send(request)
        if result is None:
            print(Fore.RED + "❌ Segundo intento fallido. No se pudo cerrar la operación.")
            return None

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(Fore.GREEN + f"✅ Operación cerrada con éxito (retcode {result.retcode})")
    else:
        print(Fore.RED + f"❌ Cierre fallido: retcode {result.retcode} - {result.comment}")

    return result

def main():
    connect()
    print(Fore.YELLOW + f"📈 Abriendo operación BUY en {SYMBOL} con volumen {VOLUME}")
    result = open_trade(SYMBOL, VOLUME)

    if not result or result.retcode != mt5.TRADE_RETCODE_DONE:
        print(Fore.RED + "❌ No se pudo abrir la operación.")
        disconnect()
        return

    print(Fore.CYAN + "⏳ Esperando 10 segundos antes de cerrar...")

    print(Fore.YELLOW + "📉 Cerrando operación manualmente...")
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions:
        close_trade(positions[0], SYMBOL)
    else:
        print(Fore.RED + "❌ No hay posiciones abiertas para cerrar.")

    disconnect()

if __name__ == "__main__":
    main()

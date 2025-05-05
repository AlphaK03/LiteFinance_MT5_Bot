import MetaTrader5 as mt5
import time
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)

SYMBOL = "ALIUSD"
CHECK_INTERVAL = 1  # segundos entre chequeos

def connect():
    if not mt5.initialize():
        print(Fore.RED + "❌ No se pudo conectar a MetaTrader 5")
        quit()
    print(Fore.CYAN + "✅ Conectado a MetaTrader 5")

def cerrar_operacion(pos):
    tipo_cierre = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(SYMBOL)
    if not tick:
        print(Fore.RED + "❌ No se pudo obtener el precio actual para cerrar.")
        return

    precio_cierre = tick.bid if tipo_cierre == mt5.ORDER_TYPE_SELL else tick.ask

    for filling in [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN]:
        print(Fore.YELLOW + f"🔁 Probando cierre con type_filling: {filling}")
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": pos.ticket,
            "symbol": SYMBOL,
            "volume": pos.volume,
            "type": tipo_cierre,
            "price": precio_cierre,
            "deviation": 10,
            "magic": 42,
            "comment": "AutoClose",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling,
        }

        result = mt5.order_send(request)
        if result is None:
            print(Fore.RED + "❌ mt5.order_send() retornó None.")
            continue

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(Fore.GREEN + f"✅ Operación cerrada correctamente con modo {filling}. Ticket: {pos.ticket}")
            return
        else:
            print(Fore.RED + f"❌ Falló con retcode {result.retcode}: {result.comment}")

    print(Fore.RED + "❌ No se pudo cerrar la operación con ninguno de los modos.")

def monitor_y_cerrar(symbol):
    print(Fore.YELLOW + f"🔍 Buscando operación activa para {symbol}...\n")
    while True:
        positions = mt5.positions_get(symbol=symbol)
        if positions and len(positions) > 0:
            pos = positions[0]
            now = datetime.now().strftime('%H:%M:%S')
            print(Fore.CYAN + f"🕒 {now} | 🎫 Ticket: {pos.ticket} detectado. Cerrando operación...")
            cerrar_operacion(pos)
            break
        else:
            print(Fore.LIGHTBLACK_EX + "📭 No hay operaciones abiertas.")
            break

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    connect()
    monitor_y_cerrar(SYMBOL)
    mt5.shutdown()

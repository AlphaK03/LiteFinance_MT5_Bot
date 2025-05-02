
import sys
import os

from src.telegram.alerts import send_telegram_alert, send_trade_summary

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import csv
import sys

import MetaTrader5 as mt5
import time
import os
from datetime import datetime
from colorama import Fore

MINIMUM_NET_PROFIT_USD = 0.15  # Ganancia neta deseada
COMMISSION_ESTIMATE_USD = 0.10  # Comisión típica

MINIMUM_RAW_PROFIT_USD = MINIMUM_NET_PROFIT_USD + COMMISSION_ESTIMATE_USD



def monitor_and_close(symbol, target_profit_pct=0.05, timeout_sec=120, check_interval=0.2, session_stats=None, shared_flags=None):
    if session_stats is None:
        session_stats = {'total': 0, 'ganadas': 0, 'profit_total': 0.0}
    if shared_flags is None:
        shared_flags = {"pause": False, "extend": False, "force_close": False, "status": ""}

    start_time = time.time()
    fallback_mode = False
    last_alert_step = -1  # Para evitar alertas duplicadas

    while True:
        clear_console()

        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            print(Fore.YELLOW + f"📭 No hay operaciones abiertas para {symbol}")
            break

        pos = positions[0]
        entry_price = pos.price_open
        tick = mt5.symbol_info_tick(symbol)
        current_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

        profit_pct = ((current_price - entry_price) / entry_price) * 100
        if pos.type == mt5.ORDER_TYPE_SELL:
            profit_pct *= -1

        profit_usd = pos.profit
        elapsed = int(time.time() - start_time)
        direction = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
        now = datetime.now().strftime('%H:%M:%S')

        # Actualizar estado
        shared_flags["status"] = f"{direction} | {profit_pct:.2f}% | {profit_usd:.2f} USD | {elapsed}s"

        print(Fore.CYAN + f"🕒 {now}")
        print(Fore.CYAN + "╔════════════════════════════════════════════╗")
        print(Fore.CYAN + f"║   🪙 {symbol} | 📈 {direction} | ⏱️ {elapsed} seg")
        print(Fore.CYAN + f"║   Entrada: {entry_price:.2f} | Actual: {current_price:.2f}")
        print(Fore.CYAN + f"║   Ticket ID: {pos.ticket}")
        if profit_pct >= 0:
            print(Fore.GREEN + f"║   Profit:  {profit_pct:.2f}% | {profit_usd:.2f} USD")
        else:
            print(Fore.RED + f"║   Profit:  {profit_pct:.2f}% | {profit_usd:.2f} USD")
        print(Fore.CYAN + "╚════════════════════════════════════════════╝", flush=True)

        # Alerta por pérdida progresiva
        alert_step = int(abs(profit_usd)) if profit_usd < 0 else None
        if alert_step and alert_step > last_alert_step:
            last_alert_step = alert_step
            send_telegram_alert(f"📉 Pérdida alcanzada: `{profit_usd:.2f} USD` en `{symbol}` (ID: {pos.ticket})")

        # ⚙️ Control remoto: forzar cierre
        if shared_flags.get("force_close"):
            shared_flags["force_close"] = False
            if safe_close("🛑 Cierre forzado por comando.") is True:
                break

        def safe_close(reason):
            print(Fore.GREEN + f"\n{reason} Cerrando operación...")
            updated_positions = mt5.positions_get(symbol=symbol)
            if updated_positions:
                updated_pos = updated_positions[0]
                result = close_trade(updated_pos, symbol)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    session_stats['total'] += 1
                    session_stats['ganadas'] += 1
                    session_stats['profit_total'] += updated_pos.profit
                    print(Fore.LIGHTMAGENTA_EX + f"🎫 ID operación cerrada: {result.order}")

                    log_trade({
                        'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'symbol': symbol,
                        'ticket': updated_pos.ticket,
                        'direction': direction,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'profit_pct': round(profit_pct, 4),
                        'profit_usd': round(updated_pos.profit, 2),
                        'balance_after': mt5.account_info().balance,
                        'elapsed_sec': elapsed,
                        'status': reason.strip("💡🎯🛑 ").upper()
                    })

                    send_trade_summary(
                        trade_id=str(updated_pos.ticket),
                        direction=direction,
                        profit_pct=profit_pct / 100,
                        elapsed=elapsed,
                        balance_actual=mt5.account_info().balance,
                        cambio=round(updated_pos.profit, 2)
                    )

                    return True
            return False

        if profit_pct >= target_profit_pct and profit_usd >= MINIMUM_RAW_PROFIT_USD:
            if safe_close("🎯 Objetivo alcanzado."):
                break

        if not fallback_mode and elapsed >= timeout_sec:
            print(Fore.MAGENTA + "\n⏳ Tiempo agotado. Esperando primer profit positivo...")
            fallback_mode = True

        if fallback_mode and profit_usd > 0:
            if safe_close("💡 Profit positivo detectado."):
                break

        time.sleep(check_interval)

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

def log_trade(data):
    file_path = 'trade_log.csv'
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)




def clear_console():
    sys.stdout.write('\033[2J\033[H')
    sys.stdout.flush()

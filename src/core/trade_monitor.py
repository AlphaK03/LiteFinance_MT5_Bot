import sys
import os
import csv
import time
from datetime import datetime
from colorama import Fore
import MetaTrader5 as mt5
from src.telegram.alerts import send_telegram_alert, send_trade_summary

MINIMUM_NET_PROFIT_USD = 0.30
COMMISSION_ESTIMATE_USD = 0.05
MINIMUM_RAW_PROFIT_USD = MINIMUM_NET_PROFIT_USD + COMMISSION_ESTIMATE_USD

def monitor_and_close(symbol, target_profit_pct=0.05, timeout_sec=120, check_interval=0.2, session_stats=None, shared_flags=None):
    if session_stats is None:
        session_stats = {'total': 0, 'ganadas': 0, 'profit_total': 0.0}
    if shared_flags is None:
        shared_flags = {
            "pause": False,
            "extend": False,
            "force_close": False,
            "status": "",
            "bloqueado": False
        }

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
                    'direction': "BUY" if updated_pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                    'entry_price': updated_pos.price_open,
                    'exit_price': mt5.symbol_info_tick(symbol).bid if updated_pos.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).ask,
                    'profit_pct': round(updated_pos.profit / updated_pos.price_open * 100, 4),
                    'profit_usd': round(updated_pos.profit, 2),
                    'balance_after': mt5.account_info().balance,
                    'elapsed_sec': int(time.time() - start_time),
                    'status': reason.strip("💡🎯🛑📉 ").upper()
                })

                send_trade_summary(
                    trade_id=str(updated_pos.ticket),
                    direction="BUY" if updated_pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                    profit_pct=updated_pos.profit / updated_pos.price_open,
                    elapsed=int(time.time() - start_time),
                    balance_actual=mt5.account_info().balance,
                    cambio=round(updated_pos.profit, 2)
                )
                return True
        return False

    start_time = time.time()
    hold_start = None
    max_profit = float('-inf')
    profit_window_ready = False

    while True:
        clear_console()
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            print(Fore.RED + f"❌ No hay operación activa para {symbol}.")
            return

        pos = positions[0]
        entry_price = pos.price_open
        tick = mt5.symbol_info_tick(symbol)
        current_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
        profit_usd = pos.profit
        elapsed = int(time.time() - start_time)

        if profit_usd > max_profit:
            max_profit = profit_usd

        if profit_usd >= COMMISSION_ESTIMATE_USD:
            if hold_start is None:
                hold_start = time.time()
            elif time.time() - hold_start >= 2:
                profit_window_ready = True
        else:
            hold_start = None
            profit_window_ready = False

        if profit_window_ready and profit_usd < max_profit:
            if safe_close("📉 Retroceso tras 2s de profit aceptable."):
                break

        if shared_flags.get("force_close"):
            shared_flags["force_close"] = False
            if safe_close("🛑 Cierre forzado por comando."):
                break

        time.sleep(check_interval)

FILLING_MODES_CACHE = {}

def close_trade(pos, symbol):
    if symbol not in FILLING_MODES_CACHE:
        for modo in [mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN]:
            test_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_BUY,
                "price": mt5.symbol_info_tick(symbol).ask,
                "deviation": 10,
                "magic": 42,
                "comment": "FILL_TEST",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": modo,
            }
            test_result = mt5.order_check(test_request)
            if test_result and test_result.retcode == mt5.TRADE_RETCODE_DONE:
                FILLING_MODES_CACHE[symbol] = modo
                break
        else:
            FILLING_MODES_CACHE[symbol] = mt5.ORDER_FILLING_FOK

    close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(symbol)
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
        "comment": "Auto Close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": FILLING_MODES_CACHE[symbol],
    }

    result = mt5.order_send(request)
    return result

def log_trade(data):
    file_path = 'trade_log.csv'
    file_exists = os.path.isfile(file_path)
    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

def clear_console():
    sys.stdout.write('\033[2J\033[H')
    sys.stdout.flush()

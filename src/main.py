import os
import time
from datetime import datetime
from colorama import init, Fore
import MetaTrader5 as mt5

from src.core.mt5_connection import connect, disconnect
from src.core.trade_executor import open_trade
from src.core.trade_monitor import monitor_and_close
from src.strategies.multi_tf_predictor import predict_multi_tf
from threading import Thread
from src.telegram.commands import listen_for_commands

init(autoreset=True)

# Configuración
SYMBOL = "XAUUSD"
VOLUME = 0.01
TARGET_PROFIT_PCT = 0.02
INTERVAL_SECONDS = 2  # Frecuencia de análisis (no de operación)
DELAY_AFTER_TRADE = 5

# Estado global
session_stats = {
    'total': 0,
    'ganadas': 0,
    'profit_total': 0.0
}
shared_flags = {"pause": False, "extend": False, "status": "", "force_close": False}

# Hilo para escuchar comandos por Telegram
Thread(target=listen_for_commands, args=(shared_flags,), daemon=True).start()

def sincronizar_con_vela():
    """Espera al inicio exacto de una nueva vela M1"""
    print(Fore.CYAN + "⏳ Sincronizando con inicio de nueva vela M1...")
    while True:
        ahora = datetime.now()
        if ahora.second == 0:
            print(Fore.GREEN + f"🟢 Nueva vela detectada: {ahora.strftime('%H:%M:%S')}")
            return
        time.sleep(0.2)

def procesar_resultado(result, direction):
    if result:
        print(Fore.BLUE + f"🧾 Resultado {direction}: retcode={result.retcode}, comentario={result.comment}")
        if result.retcode in [mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED, mt5.TRADE_RETCODE_DONE_PARTIAL]:
            monitor_and_close(SYMBOL, TARGET_PROFIT_PCT, timeout_sec=60,
                              session_stats=session_stats, shared_flags=shared_flags)
            print(Fore.CYAN + f"\n🕓 Esperando {DELAY_AFTER_TRADE} segundos antes de buscar nueva señal...\n")
            time.sleep(DELAY_AFTER_TRADE)
        else:
            print(Fore.RED + "⚠️ Operación no aceptada.")
    else:
        print(Fore.RED + f"❌ open_trade() retornó None para {direction}.")

def run_bot_loop():
    print(Fore.CYAN + "\n🤖 Iniciando bot en modo automático (multiframe)")
    connect(SYMBOL)

    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')

            if shared_flags.get("pause"):
                print(Fore.MAGENTA + "⏸️ Pausado por comando. Esperando...")
                time.sleep(3)
                continue
            if shared_flags.get("bloqueado"):
                print("❌ El bot está bloqueado por pérdida crítica. Esperando desbloqueo manual.")
                return

            print(Fore.YELLOW + f"🔄 Analizando mercado para {SYMBOL}...")
            signal = predict_multi_tf(SYMBOL)

            if signal in ["BUY", "SELL"]:
                print(Fore.GREEN if signal == "BUY" else Fore.RED + f"📉 Señal: {signal} detectada. Esperando nueva vela...")
                sincronizar_con_vela()
                result = open_trade(SYMBOL, signal, VOLUME)
                procesar_resultado(result, signal)
            else:
                print(Fore.BLUE + "🚫 No hay consenso para operar.")

            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print(Fore.LIGHTRED_EX + "\n🛑 Bot detenido por el usuario (Ctrl + C).")
    finally:
        disconnect()
        print(Fore.CYAN + "\n🔌 Sesión finalizada con MetaTrader 5.")
        print(Fore.LIGHTCYAN_EX + f"\n📊 RESUMEN FINAL DE LA SESIÓN")
        print(Fore.LIGHTCYAN_EX + f"➡️  Operaciones: {session_stats['total']}")
        print(Fore.LIGHTCYAN_EX + f"✅ Ganadas:     {session_stats['ganadas']}")
        print(Fore.LIGHTCYAN_EX + f"💰 Profit total: {session_stats['profit_total']:.2f} USD")

def invert_signal(signal):
    return "SELL" if signal == "BUY" else "BUY" if signal == "SELL" else "HOLD"

if __name__ == "__main__":
    run_bot_loop()

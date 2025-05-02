import os
import time
from colorama import init, Fore

from src.core.mt5_connection import connect, disconnect
from src.core.trade_executor import open_trade
from src.core.trade_monitor import monitor_and_close
from src.strategies.multi_tf_predictor import predict_multi_tf
from threading import Thread
from src.telegram.commands import listen_for_commands
# Inicializa colorama
init(autoreset=True)

# Configuración
SYMBOL = "XAUUSD"
VOLUME = 0.01
TARGET_PROFIT_PCT = 0.02
INTERVAL_SECONDS = 5  # Evaluar cada 30 segundos
DELAY_AFTER_TRADE = 5  # Esperar 5s tras cerrar operación

# Resumen de sesión
session_stats = {
    'total': 0,
    'ganadas': 0,
    'profit_total': 0.0
}
shared_flags = {"pause": False, "extend": False, "status": "", "force_close": False}

Thread(target=listen_for_commands, args=(shared_flags,), daemon=True).start()

def run_bot_loop():
    print(Fore.CYAN + "\n🤖 Iniciando bot en modo automático (multiframe)")
    connect()

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
            #Esta función solo es experimental:
            # signal = invert_signal(signal)

            if signal == "BUY":
                print(Fore.GREEN + "📈 Señal: BUY detectada. Ejecutando operación...")
                result = open_trade(SYMBOL, "BUY", VOLUME)
                if result and result.retcode == 10009:
                    monitor_and_close(SYMBOL, TARGET_PROFIT_PCT, timeout_sec=60, session_stats=session_stats, shared_flags=shared_flags)
                    print(Fore.CYAN + f"\n🕓 Esperando {DELAY_AFTER_TRADE} segundos antes de buscar nueva señal...\n")
                    time.sleep(DELAY_AFTER_TRADE)

            elif signal == "SELL":
                print(Fore.RED + "📉 Señal: SELL detectada. Ejecutando operación...")
                result = open_trade(SYMBOL, "SELL", VOLUME)
                if result and result.retcode == 10009:
                    monitor_and_close(SYMBOL, TARGET_PROFIT_PCT, timeout_sec=60, session_stats=session_stats, shared_flags=shared_flags)
                    print(Fore.CYAN + f"\n🕓 Esperando {DELAY_AFTER_TRADE} segundos antes de buscar nueva señal...\n")
                    time.sleep(DELAY_AFTER_TRADE)

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
    if signal == "BUY":
        return "SELL"
    elif signal == "SELL":
        return "BUY"
    return "HOLD"

if __name__ == "__main__":
    run_bot_loop()

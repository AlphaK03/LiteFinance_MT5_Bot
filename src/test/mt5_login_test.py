import MetaTrader5 as mt5
from datetime import datetime
from colorama import Fore

def verificar_info_cuenta():
    if not mt5.initialize():
        print(Fore.RED + "❌ No se pudo inicializar MetaTrader 5.")
        return

    cuenta = mt5.account_info()
    if cuenta is None:
        print(Fore.RED + "❌ No se pudo obtener información de la cuenta.")
        mt5.shutdown()
        return

    print(Fore.CYAN + "\n📋 Información de la cuenta conectada:")
    print(Fore.CYAN + "═════════════════════════════════════")
    print(Fore.YELLOW + f"🧾 Login:       {cuenta.login}")
    print(Fore.YELLOW + f"👤 Nombre:      {cuenta.name}")
    print(Fore.YELLOW + f"🌐 Servidor:    {cuenta.server}")
    print(Fore.YELLOW + f"💼 Tipo:        {'DEMO' if 'demo' in cuenta.server.lower() else 'REAL'}")
    print(Fore.GREEN + f"💰 Balance:     {cuenta.balance:.2f} USD")
    print(Fore.GREEN + f"💵 Equity:      {cuenta.equity:.2f} USD")
    print(Fore.GREEN + f"📉 Margen libre:{cuenta.margin_free:.2f} USD")
    print(Fore.CYAN + "═════════════════════════════════════")

    mt5.shutdown()

if __name__ == "__main__":
    verificar_info_cuenta()

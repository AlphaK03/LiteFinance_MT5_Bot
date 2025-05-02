import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.telegram.commands import listen_for_commands
from threading import Thread
import time

flags = {
    "pause": False,
    "extend": False,
    "status": "Bot en espera...",
    "force_close": False
}

print("🤖 Iniciando prueba de comandos de Telegram...")
Thread(target=listen_for_commands, args=(flags,), daemon=True).start()

try:
    while True:
        print(f"📡 Estado actual del bot: {flags}")
        time.sleep(5)
except KeyboardInterrupt:
    print("\n🛑 Prueba finalizada manualmente.")

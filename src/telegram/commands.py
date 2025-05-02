import requests
import time
from src.config.settings import TELEGRAM_TOKEN, CHAT_ID

BOT_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def get_updates(offset=None):
    url = f"{BOT_URL}/getUpdates"
    params = {"timeout": 10, "offset": offset}
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"⚠️ Error leyendo comandos: {e}")
        return {}

def send_reply(text: str):
    try:
        requests.post(f"{BOT_URL}/sendMessage", data={
            "chat_id": CHAT_ID,
            "text": text
        })
    except Exception as e:
        print(f"⚠️ Error enviando respuesta: {e}")

def listen_for_commands(shared_flags):
    offset = None
    while True:
        updates = get_updates(offset)
        for result in updates.get("result", []):
            offset = result["update_id"] + 1
            msg = result.get("message", {}).get("text", "").strip().lower()
            print(f"\n📥 Comando recibido: {msg}")

            if msg == "/detener":
                shared_flags["pause"] = True
                send_reply("⏸ Bot detenido.")
            elif msg == "/reanudar":
                shared_flags["pause"] = False
                shared_flags["bloqueado"] = False

                send_reply("▶️ Bot reanudado.")
            elif msg == "/extender":
                shared_flags["extend"] = True
                send_reply("🕒 Tiempo extendido.")
            elif msg == "/estado":
                estado = shared_flags.get("status", "Sin datos")
                send_reply(f"📊 Estado actual:\n{estado}")
            elif msg == "/cerrar":
                shared_flags["force_close"] = True
                send_reply("⚠️ Solicitud de cierre forzado enviada.")

        time.sleep(1)

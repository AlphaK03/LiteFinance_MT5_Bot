"""
alerts.py
---------
Comunicación con Telegram.
"""
import requests, textwrap
from src.config import settings

_TELEGRAM_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage"

def _send(msg: str) -> None:
    payload = {"chat_id": settings.CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(_TELEGRAM_URL, data=payload, timeout=5)
    except Exception as exc:
        print(f"⚠️  No se pudo enviar mensaje Telegram: {exc}")

def send_telegram_message(msg: str) -> None:
    _send(msg)

def send_telegram_alert(message: str) -> None:
    _send(f"⚠️ *ALERTA*\n{message}")

def send_trade_summary(trade_id: str, direction: str, profit_pct: float,
                       elapsed: int, balance_actual: float, cambio: float) -> None:
    resumen = textwrap.dedent(f"""
        📈 *Resumen de operación completada*
        • ID: `{trade_id}`
        • Dirección: *{direction}*
        • Duración: `{elapsed}s`
        • Resultado: `{profit_pct:.2%}`
        • Balance actual: `${balance_actual:.2f}`
        • Cambio neto: `{cambio:+.2f}`
    """)
    _send(resumen.strip())

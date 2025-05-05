
TOKEN = '7976923210:AAGcUOZghLNdgH3ZrJcaI1GTaiqFh7R_jqc'
CHAT_ID_AUTORIZADO = 1035317624  # Asegúrate de que solo tú puedas usarlo
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import subprocess
import pyautogui
import time
import psutil

# ✔ Utilidad para validar autorización
def autorizado(update: Update) -> bool:
    return update.effective_chat.id == CHAT_ID_AUTORIZADO

# Abrir AnyDesk
async def abrir_anydesk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        await update.message.reply_text("❌ No autorizado.")
        return

    subprocess.Popen(["C:\\Program Files (x86)\\AnyDesk\\AnyDesk.exe"])
    await update.message.reply_text("🟢 AnyDesk abierto.")

# Cerrar AnyDesk
async def cerrar_anydesk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        await update.message.reply_text("❌ No autorizado.")
        return

    subprocess.run(["taskkill", "/f", "/im", "AnyDesk.exe"])
    await update.message.reply_text("🔴 AnyDesk cerrado.")

async def bloquear_pc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        await update.message.reply_text("❌ No autorizado.")
        return

    subprocess.run("rundll32.exe user32.dll,LockWorkStation")
    await update.message.reply_text("🔒 PC bloqueada.")

async def estado_anydesk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        await update.message.reply_text("❌ No autorizado.")
        return

    running = any(proc.name().lower() == "anydesk.exe" for proc in psutil.process_iter())
    estado = "🟢 AnyDesk está en ejecución." if running else "🔴 AnyDesk no está ejecutándose."
    await update.message.reply_text(estado)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("abrir", abrir_anydesk))
    app.add_handler(CommandHandler("cerrar", cerrar_anydesk))
    app.add_handler(CommandHandler("bloquear", bloquear_pc))
    app.add_handler(CommandHandler("estado", estado_anydesk))

    app.run_polling()

if __name__ == "__main__":
    main()


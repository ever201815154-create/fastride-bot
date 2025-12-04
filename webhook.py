from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, Dispatcher, MessageHandler, filters
import asyncio

TOKEN = "8214450317:AAHprh0zHTuPYSBJ0xnOFDPeeyySIm57kmo"

app = Flask(__name__)

bot = Bot(token=TOKEN)

application = Application.builder().token(TOKEN).build()
dispatcher = application.dispatcher


# --- Handler básico (responde cualquier mensaje) ---
async def mensaje(update: Update, context):
    await update.message.reply_text("Hola! El webhook funciona correctamente 😊")


dispatcher.add_handler(MessageHandler(filters.ALL, mensaje))


# --- Ruta del Webhook ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    # Recibe el JSON que envía Telegram
    json_update = request.get_json()

    # Lo convierte a objeto Update
    update = Update.de_json(json_update, bot)

    # Procesa el mensaje con Dispatcher
    asyncio.run(dispatcher.process_update(update))

    return "OK", 200


# --- Para verificar que el servidor corre ---
@app.route("/")
def index():
    return "Webhook activo!", 200


if __name__ == "__main__":
    app.run(port=5000)

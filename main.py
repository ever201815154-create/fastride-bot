from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)
import asyncio
import math
import os
from flask import Flask, request
import qrcode
from io import BytesIO

# --- CONFIGURACIÓN ---
TOKEN = "8214450317:AAHprh0zHTuPYSBJ0xnOFDPeeyySIm57kmo"
WEBHOOK_URL = "https://fastride-bot.onrender.com/webhook"

app = Flask(__name__)

# --- ESTADOS ---
MENU, ELEGIR_ORIGEN, ELEGIR_DESTINO, METODO_PAGO, CONFIRMAR_VIAJE, CALIFICAR = range(6)

# --- CONDUCTORES ---
CONDUCTORES = [
    {"nombre": "Carlos Martínez", "auto": "Toyota Corolla", "placa": "ABC-123", "lat": -17.7833, "lon": -63.1821, "rating": 4.7},
    {"nombre": "Luis Pérez", "auto": "Hyundai Elantra", "placa": "ADK-912", "lat": -17.7750, "lon": -63.1828, "rating": 4.9},
    {"nombre": "María Gómez", "auto": "Kia Rio", "placa": "FTR-663", "lat": -17.7890, "lon": -63.1650, "rating": 4.8},
]

# --- FUNCIONES AUXILIARES ---
def distancia_metros(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def mover_hacia(lat1, lon1, lat2, lon2, paso=50):
    dist = distancia_metros(lat1, lon1, lat2, lon2)
    factor = min(paso / dist, 1) if dist != 0 else 1
    return lat1 + (lat2 - lat1) * factor, lon1 + (lon2 - lon1) * factor

# --- BOT ---
tg_app = Application.builder().token(TOKEN).build()

# -------------------------------
#      HANDLERS FUNCIONALES
# -------------------------------

async def start(update, context):
    await update.message.reply_text("🚗 Bot funcionando en Render!\n\nEnvíame tu origen para comenzar.")
    return ELEGIR_ORIGEN

async def menu_callback(update, context):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Elegiste una opción del menú.")
    return ELEGIR_ORIGEN

async def recibir_origen(update, context):
    context.user_data["origen"] = update.message.text
    await update.message.reply_text("📍 Origen guardado.\nAhora dime cuál será el destino.")
    return ELEGIR_DESTINO

async def recibir_destino(update, context):
    context.user_data["destino"] = update.message.text

    keyboard = [
        [InlineKeyboardButton("💵 Efectivo", callback_data="pago_efectivo")],
        [InlineKeyboardButton("💳 Tarjeta", callback_data="pago_tarjeta")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💰 Selecciona tu método de pago:",
        reply_markup=reply_markup
    )
    return METODO_PAGO

async def metodo_pago_callback(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["pago"] = query.data

    await query.edit_message_text(
        f"Pago seleccionado: {query.data.replace('pago_', '').upper()}\n\nConfirmar viaje?"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_viaje")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]

    await query.message.reply_text(
        "¿Deseas continuar?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CONFIRMAR_VIAJE

async def viaje_callback(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "cancelar":
        await query.edit_message_text("❌ Viaje cancelado.")
        return ConversationHandler.END

    await query.edit_message_text("🚗 Conductor asignado, llegando...")

    return CALIFICAR

async def recibir_calificacion(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("⭐ Gracias por tu calificación!")
    return ConversationHandler.END

async def cancelar(update, context):
    await update.message.reply_text("❌ Conversación cancelada.")
    return ConversationHandler.END


# --- CONVERSATION HANDLER ---
conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        MENU: [CallbackQueryHandler(menu_callback)],
        ELEGIR_ORIGEN: [MessageHandler(filters.TEXT, recibir_origen)],
        ELEGIR_DESTINO: [MessageHandler(filters.TEXT, recibir_destino)],
        METODO_PAGO: [CallbackQueryHandler(metodo_pago_callback)],
        CONFIRMAR_VIAJE: [CallbackQueryHandler(viaje_callback)],
        CALIFICAR: [CallbackQueryHandler(recibir_calificacion)],
    },
    fallbacks=[CommandHandler("cancel", cancelar)],
)

tg_app.add_handler(conv)

# --- WEBHOOK ---
@app.post("/webhook")
def webhook():
    data = request.get_json(force=True)
    asyncio.run(tg_app.update_queue.put(tg_app.bot._deserialize_update(data)))
    return {"ok": True}

@app.before_first_request
def activate_webhook():
    import requests
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")

# --- EJECUTAR ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

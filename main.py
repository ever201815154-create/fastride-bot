from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)
import asyncio
import random
import math
from io import BytesIO
import qrcode

from flask import Flask, request
import os

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
        [InlineKeyboardButton("💳 Tarjeta", callback_data_]()

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

# --- Codigo ---
TOKEN = "8214450317:AAHprh0zHTuPYSBJ0xnOFDPeeyySIm57kmo" 

# --- ESTADOS ---
MENU, ELEGIR_ORIGEN, ELEGIR_DESTINO, METODO_PAGO, CONFIRMAR_VIAJE, CALIFICAR = range(6)

# --- CONDUCTORES (Santa Cruz - Bolivia) ---
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
    if dist == 0:
        return lat2, lon2
    factor = min(paso / dist, 1)
    return lat1 + (lat2 - lat1) * factor, lon1 + (lon2 - lon1) * factor

# --- BIENVENIDA ---
async def start(update, context):
    user = update.effective_user.first_name

    await update.message.reply_photo(
        photo=open("bienvenida.jpg", "rb"),
        caption=f"👋 ¡Bienvenido a *FastRide*, {user}!\n🚗 Viajes rápidos en *Santa Cruz*."
    )

    menu = [
        [InlineKeyboardButton("🚗 Solicitar Viaje", callback_data="pedir_viaje")],
        [InlineKeyboardButton("💳 Métodos de Pago", callback_data="pago_menu")],
        [InlineKeyboardButton("ℹ️ Información", callback_data="info")]
    ]

    await update.message.reply_text("Selecciona una opción:", reply_markup=InlineKeyboardMarkup(menu))
    return MENU

# --- MENÚ PRINCIPAL ---
async def menu_callback(update, context):
    q = update.callback_query
    await q.answer()

    if q.data == "pedir_viaje":
        await q.edit_message_text("📍 Envía tu *ubicación actual* desde el mapa o escribe tu dirección:", parse_mode="Markdown")
        return ELEGIR_ORIGEN

    elif q.data == "pago_menu":
        teclado = [
            [InlineKeyboardButton("💳 Tarjeta", callback_data="tarjeta")],
            [InlineKeyboardButton("💵 Efectivo", callback_data="efectivo")],
            [InlineKeyboardButton("🅿 PayPal", callback_data="paypal")],
            [InlineKeyboardButton("📱 QR", callback_data="qr")]
        ]
        await q.edit_message_text("Selecciona tu método de pago:", reply_markup=InlineKeyboardMarkup(teclado))
        return METODO_PAGO

    elif q.data == "info":
        await q.edit_message_text("ℹ️ *FastRide SCZ*\nVersión profesional.", parse_mode="Markdown")
        return MENU

# --- ORIGEN ---
async def recibir_origen(update, context):
    if update.message.location:  # Si envía ubicación
        loc = update.message.location
        context.user_data["origen"] = (loc.latitude, loc.longitude)
    else:  # Si escribe texto
        origen_texto = update.message.text
        context.user_data["origen"] = origen_texto  # Guardamos el texto

    await update.message.reply_text("📍 Ahora escribe tu *destino* (texto):")
    return ELEGIR_DESTINO

# --- DESTINO ---
async def recibir_destino(update, context):
    destino_texto = update.message.text
    context.user_data["destino"] = destino_texto

    conductor = random.choice(CONDUCTORES)
    context.user_data["conductor"] = conductor

    # SIMULAMOS destino del conductor
    context.user_data["dest_lat"] = conductor["lat"] + random.uniform(0.002, 0.008)
    context.user_data["dest_lon"] = conductor["lon"] + random.uniform(0.002, 0.008)

    # Distancia usuario - conductor
    user_origen = context.user_data["origen"]
    if isinstance(user_origen, tuple):
        user_lat, user_lon = user_origen
    else:  # Si el origen es texto, usamos la ubicación simulada del conductor
        user_lat, user_lon = conductor["lat"], conductor["lon"]

    dist_km = distancia_metros(user_lat, user_lon, conductor["lat"], conductor["lon"]) / 1000

    # Tarifa
    tarifa = max(8, round(dist_km * 3, 2))
    context.user_data["precio"] = tarifa

    estrellas = "⭐" * int(conductor["rating"])

    await update.message.reply_text(
        f"🚘 *Conductor encontrado*\n"
        f"👤 {conductor['nombre']} ({estrellas})\n"
        f"🚗 {conductor['auto']} - {conductor['placa']}\n"
        f"📏 Distancia: {dist_km:.2f} km\n"
        f"💵 Precio estimado: *{tarifa} Bs*",
        parse_mode="Markdown"
    )

    tecl = [
        [InlineKeyboardButton("💳 Tarjeta", callback_data="tarjeta")],
        [InlineKeyboardButton("💵 Efectivo", callback_data="efectivo")],
        [InlineKeyboardButton("🅿 PayPal", callback_data="paypal")],
        [InlineKeyboardButton("📱 QR", callback_data="qr")]
    ]
    await update.message.reply_text("Selecciona tu método de pago:", reply_markup=InlineKeyboardMarkup(tecl))
    return METODO_PAGO

# --- MÉTODO DE PAGO ---
async def metodo_pago_callback(update, context):
    q = update.callback_query
    await q.answer()

    context.user_data["pago"] = q.data

    if q.data == "qr":
        link = "https://example.com/pago"
        qr = qrcode.make(link)
        bio = BytesIO()
        bio.name = "qr.png"
        qr.save(bio, "PNG")
        bio.seek(0)
        await q.message.reply_photo(photo=bio, caption="📱 Escanea para pagar")
    else:
        await q.edit_message_text(f"💳 Seleccionaste: *{q.data}*", parse_mode="Markdown")

    teclado = [
        [InlineKeyboardButton("✔ Confirmar Viaje", callback_data="confirmar_viaje")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    await q.message.reply_text("¿Deseas confirmar el viaje?", reply_markup=InlineKeyboardMarkup(teclado))
    return CONFIRMAR_VIAJE

# --- CONFIRMACIÓN DE VIAJE ---
async def viaje_callback(update, context):
    q = update.callback_query
    await q.answer()

    if q.data == "cancelar":
        await q.edit_message_text("❌ Viaje cancelado.")
        return ConversationHandler.END

    conductor = context.user_data["conductor"]
    await q.edit_message_text("🚗 El conductor está en camino...")

    async def simular_gps():
        lat = conductor["lat"]
        lon = conductor["lon"]
        dest_lat = context.user_data["dest_lat"]
        dest_lon = context.user_data["dest_lon"]

        while distancia_metros(lat, lon, dest_lat, dest_lon) > 5:
            await asyncio.sleep(2)
            lat, lon = mover_hacia(lat, lon, dest_lat, dest_lon)
            await q.message.reply_location(latitude=lat, longitude=lon)

        # Mensaje de llegada
        await q.message.reply_text(
            "🏁 ¡Has llegado a tu destino!\nGracias por elegir FastRide 🚗💨",
            parse_mode="Markdown"
        )

        # Botones de calificación
        estrellas_btn = [
            [
                InlineKeyboardButton("⭐", callback_data="1"),
                InlineKeyboardButton("⭐⭐", callback_data="2"),
                InlineKeyboardButton("⭐⭐⭐", callback_data="3"),
                InlineKeyboardButton("⭐⭐⭐⭐", callback_data="4"),
                InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="5")
            ]
        ]
        await q.message.reply_text(
            "✨ *Califica a tu conductor:*",
            reply_markup=InlineKeyboardMarkup(estrellas_btn),
            parse_mode="Markdown"
        )

    asyncio.create_task(simular_gps())
    return CALIFICAR  # <- Cambio para manejar calificación

# --- CALIFICACIÓN ---
async def recibir_calificacion(update, context):
    q = update.callback_query
    await q.answer()

    # Guardamos la calificación en user_data
    context.user_data["calificacion"] = int(q.data)

    # Mensaje de agradecimiento
    await q.edit_message_text(
        "Gracias por tu apoyo! Tu valoración nos motiva a seguir mejorando ⭐"
    )

# --- CANCELAR ---
async def cancelar(update, context):
    await update.message.reply_text("❌ Operación cancelada.")
    return ConversationHandler.END

# --- CONFIG BOT ---
app = Application.builder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        MENU: [CallbackQueryHandler(menu_callback)],
        ELEGIR_ORIGEN: [MessageHandler(filters.TEXT | filters.LOCATION, recibir_origen)],
        ELEGIR_DESTINO: [MessageHandler(filters.TEXT, recibir_destino)],
        METODO_PAGO: [CallbackQueryHandler(metodo_pago_callback)],
        CONFIRMAR_VIAJE: [CallbackQueryHandler(viaje_callback)],
        CALIFICAR: [CallbackQueryHandler(recibir_calificacion)]
    },
    fallbacks=[CommandHandler("cancel", cancelar)],
)

app.add_handler(conv)
app.run_polling()


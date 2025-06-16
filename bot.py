import os
import logging
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes
)
from flask import Flask
import threading

# Configura logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Variables de entorno
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Asegúrate de tener esto en tus variables del entorno
ASESOR_GROUP_CHAT_ID = os.getenv("ASESOR_GROUP_CHAT_ID")  # Debe ser el ID del grupo de asesores

# Estados de usuarios
user_states = {}

# Mensajes por idioma
messages = {
    "es": {
        "start": "Hola {name}, soy ANFHLYBOT 🤖, tu asistente para activar tu cuenta *premium* y obtener acceso sin publicidad y contenido exclusivo en la app de ANFHLY.\n\n¿Estás interesado?",
        "premium_info": "Perfecto 😎. Siendo *premium*, podrás ver tus películas y series favoritas sin interrupciones por solo *9 dólares al mes*. El pago es por *PayPal*.\n\nPara continuar, te pondremos en contacto con un asesor.",
        "cancelled": "Entendido, puedes escribirme cuando quieras si cambias de opinión.",
        "contacting": "Estamos contactando a un asesor... por favor espera.",
        "notify_group": "👤 El usuario @{username} (ID: {id}) está solicitando activar su premium. ¿Alguien disponible?",
        "connected": "Has sido conectado con un asesor.",
        "completed": "✅ Venta completada. ¡Gracias por preferirnos! Hasta pronto 👋"
    },
    "en": {
        "start": "Hi {name}, I'm ANFHLYBOT 🤖, your assistant to activate your *premium* account and get ad-free and exclusive content in ANFHLY app.\n\nAre you interested?",
        "premium_info": "Awesome 😎. With *premium*, you can enjoy all your favorite shows and movies without ads for just *$9/month*. Payment via *PayPal*.\n\nWe'll connect you with an advisor to continue.",
        "cancelled": "Got it! Let me know if you change your mind.",
        "contacting": "We’re contacting an advisor for you… please wait.",
        "notify_group": "👤 User @{username} (ID: {id}) is requesting premium activation. Anyone available?",
        "connected": "You’ve been connected with an advisor.",
        "completed": "✅ Sale completed. Thank you! See you soon 👋"
    }
}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Español 🇪🇸", callback_data='lang_es')],
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')]
    ]
    await update.message.reply_text("Elige tu idioma / Choose your language:", reply_markup=InlineKeyboardMarkup(keyboard))

# Maneja selección de idioma
async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]
    user_states[query.from_user.id] = {"lang": lang}

    name = query.from_user.first_name
    message = messages[lang]["start"].format(name=name)

    keyboard = [
        [InlineKeyboardButton("Sí ✅" if lang == "es" else "Yes ✅", callback_data='yes')],
        [InlineKeyboardButton("No ❌" if lang == "es" else "No ❌", callback_data='no')]
    ]
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# Maneja Sí / No
async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_states.get(user_id, {}).get("lang", "es")

    if query.data == 'yes':
        user_states[user_id]["step"] = "awaiting_advisor"
        message = messages[lang]["premium_info"]
        keyboard = [
            [InlineKeyboardButton("Contactar Asesor 👤" if lang == "es" else "Contact Advisor 👤", callback_data='contact')],
            [InlineKeyboardButton("Cancelar ❌" if lang == "es" else "Cancel ❌", callback_data='cancel')]
        ]
        await query.edit_message_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'no' or query.data == 'cancel':
        await query.edit_message_text(messages[lang]["cancelled"])

    elif query.data == 'contact':
        await query.edit_message_text(messages[lang]["contacting"])

        # Enviar mensaje al grupo de asesores
        username = query.from_user.username or "sin_usuario"
        chat_id = query.from_user.id
        text = messages[lang]["notify_group"].format(username=username, id=chat_id)

        keyboard = [
            [InlineKeyboardButton("Aceptar al usuario", callback_data=f'accept_{chat_id}')]
        ]

        await context.bot.send_message(chat_id=ASESOR_GROUP_CHAT_ID, text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# Acepta desde grupo
async def accept_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("accept_"):
        return

    client_id = int(query.data.split("_")[1])
    lang = user_states.get(client_id, {}).get("lang", "es")

    # Notificar al cliente
    await context.bot.send_message(chat_id=client_id, text=messages[lang]["connected"])

    # Opción para el asesor de marcar venta finalizada
    keyboard = [
        [InlineKeyboardButton("Marcar como finalizado ✅", callback_data=f'done_{client_id}')]
    ]
    await query.edit_message_text("Cliente conectado. Cuando finalices la compra, presiona el botón.", reply_markup=InlineKeyboardMarkup(keyboard))

# Finaliza
async def finalize_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("done_"):
        return

    client_id = int(query.data.split("_")[1])
    lang = user_states.get(client_id, {}).get("lang", "es")

    # Mensaje al cliente
    await context.bot.send_message(chat_id=client_id, text=messages[lang]["completed"])

    # Mensaje al grupo
    await query.edit_message_text("✅ Venta completada y marcada como finalizada.")

# Flask keep_alive
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Estoy vivo y ayudando a usuarios!"

def run():
    flask_app.run(host="0.0.0.0", port=8080)

def keep_alive():
    thread = threading.Thread(target=run)
    thread.start()

# MAIN
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_language, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(handle_response, pattern="^(yes|no|contact|cancel)$"))
    application.add_handler(CallbackQueryHandler(accept_client, pattern="^accept_"))
    application.add_handler(CallbackQueryHandler(finalize_sale, pattern="^done_"))

    application.run_polling()

if __name__ == '__main__':
    keep_alive()
    main()

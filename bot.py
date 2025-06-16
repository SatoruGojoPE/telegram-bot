import logging
import os
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

# Setup de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Variables de entorno
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Token del bot
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")  # ID del grupo de asesores

# Diccionario temporal para seguimiento de usuarios
user_states = {}

# Idiomas
LANGUAGES = {
    "es": {
        "welcome": "Hola {name}, soy ANFHLYBOT 🤖 tu asistente para activar el plan Premium sin anuncios y acceso exclusivo 🎬. ¿Te interesa?",
        "confirm_options": ["Sí, quiero", "No, gracias"],
        "premium_info": "Genial 🎉 Ser usuario Premium te da acceso sin publicidad a películas y series por solo $9 USD/mes vía PayPal. ¿Deseas contactar a un asesor para completar el pago?",
        "contact_options": ["Contactar asesor", "Cancelar"],
        "connecting": "⏳ Te estamos conectando con un asesor disponible...",
        "cancelled": "Has cancelado el proceso. Si deseas volver, escribe /start.",
        "final": "✅ Proceso finalizado. ¡Gracias por confiar en ANFHLY Premium! ✨"
    },
    "en": {
        "welcome": "Hello {name}, I'm ANFHLYBOT 🤖 your assistant to activate Premium, with ad-free and exclusive access 🎬. Are you interested?",
        "confirm_options": ["Yes, I'm in", "No, thanks"],
        "premium_info": "Awesome 🎉 Being Premium gives you ad-free movies and shows for just $9 USD/month via PayPal. Would you like to contact a support agent?",
        "contact_options": ["Contact agent", "Cancel"],
        "connecting": "⏳ Connecting you with an available agent...",
        "cancelled": "You cancelled the process. If you want to try again, type /start.",
        "final": "✅ Process completed. Thanks for joining ANFHLY Premium! ✨"
    }
}

# Inicio
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("Español 🇪🇸", callback_data=f"lang_es")],
        [InlineKeyboardButton("English 🇺🇸", callback_data=f"lang_en")]
    ]
    await update.message.reply_text("Choose your language / Elige tu idioma:", reply_markup=InlineKeyboardMarkup(keyboard))
    user_states[user_id] = {"stage": "language"}

# Botón de idioma, interés, asesor
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()

    if data.startswith("lang_"):
        lang = data.split("_")[1]
        user_states[user_id] = {"lang": lang, "stage": "interested"}
        text = LANGUAGES[lang]["welcome"].format(name=query.from_user.first_name)
        buttons = LANGUAGES[lang]["confirm_options"]
        keyboard = [[InlineKeyboardButton(buttons[0], callback_data="interested_yes")],
                    [InlineKeyboardButton(buttons[1], callback_data="interested_no")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "interested_yes":
        lang = user_states[user_id]["lang"]
        text = LANGUAGES[lang]["premium_info"]
        buttons = LANGUAGES[lang]["contact_options"]
        keyboard = [[InlineKeyboardButton(buttons[0], callback_data="contact_agent")],
                    [InlineKeyboardButton(buttons[1], callback_data="cancel")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "interested_no" or data == "cancel":
        lang = user_states[user_id]["lang"]
        await query.edit_message_text(LANGUAGES[lang]["cancelled"])

    elif data == "contact_agent":
        lang = user_states[user_id]["lang"]
        await query.edit_message_text(LANGUAGES[lang]["connecting"])
        
        # Notificar al grupo de asesores
        msg = f"📩 El usuario [{query.from_user.first_name}](tg://user?id={user_id}) está solicitando Premium.\n¿Quién puede atenderlo?"
        keyboard = [[InlineKeyboardButton("Aceptar solicitud", callback_data=f"accept_{user_id}")]]
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("accept_"):
        client_id = int(data.split("_")[1])
        responder_id = query.from_user.id

        # Notificar al asesor y redirigirlo
        await query.edit_message_text("✅ Has aceptado la solicitud. Redirigiendo al cliente...")
        await context.bot.send_message(chat_id=client_id, text="🎉 Te estamos conectando con un asesor ahora mismo...")
        await context.bot.send_message(chat_id=responder_id, text=f"Contacta con el usuario aquí: [Cliente](tg://user?id={client_id})", parse_mode="Markdown")

# Mensajes fuera de flujo
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Por favor, usa /start para iniciar el proceso de activación Premium.")

# Flask keep-alive para Render
app_flask = Flask(__name__)

@app_flask.route('/')
def index():
    return 'ANFHLYBOT está activo 😎'

# Ejecutar bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 ANFHLYBOT está funcionando...")
    app.run_polling()

if __name__ == '__main__':
    from threading import Thread
    Thread(target=lambda: app_flask.run(host="0.0.0.0", port=8080)).start()
    main()

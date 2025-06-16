import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Token y URL del webhook
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://telegram-bot-y7if.onrender.com{WEBHOOK_PATH}"

app = Flask(__name__)

# Función de inicio
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Español", callback_data="lang_es"),
            InlineKeyboardButton("English", callback_data="lang_en")
        ]
    ]
    await update.message.reply_text("🌍 Please choose your language / Por favor elige tu idioma:", reply_markup=InlineKeyboardMarkup(keyboard))

# Manejo de idioma
async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "lang_es":
        context.user_data["lang"] = "es"
        await query.message.reply_text("Hola 👋, soy *ANFHLYBOT*, tu ayudante para activar tu cuenta *premium*. ¿Te interesa tener acceso *sin publicidad* y *contenido exclusivo*? 😎", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Sí, quiero", callback_data="premium_yes")],
            [InlineKeyboardButton("No, gracias", callback_data="premium_no")]
        ]))
    else:
        context.user_data["lang"] = "en"
        await query.message.reply_text("Hi 👋, I'm *ANFHLYBOT*, your assistant to activate your *premium account*. Interested in *ad-free* and *exclusive content*? 😎", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Yes, I'm interested", callback_data="premium_yes")],
            [InlineKeyboardButton("No, thanks", callback_data="premium_no")]
        ]))

# Confirmación premium
async def handle_premium_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "es")

    if query.data == "premium_yes":
        if lang == "es":
            await query.message.reply_text(
                "¡Excelente! 😃 Ser *premium* significa que verás tus películas y series *sin publicidad* por solo *$9 al mes* vía *PayPal*.\n\nUn asesor se pondrá en contacto contigo ahora.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📞 Contactar asesor", callback_data="contact_agent")],
                    [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
                ])
            )
        else:
            await query.message.reply_text(
                "Great! 😃 Being *premium* means ad-free movies and series for only *$9/month* via *PayPal*.\n\nAn agent will contact you now.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📞 Contact agent", callback_data="contact_agent")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
                ])
            )
    elif query.data == "premium_no":
        await query.message.reply_text("¡Está bien! Si cambias de opinión, aquí estaré 😊")

# Contactar asesor
async def contact_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    message = f"⚠️ El usuario @{user.username} está solicitando *premium*. ¿Quién está disponible para ayudarlo?"
    await query.message.reply_text("🔔 Contactando con un asesor... espera unos segundos por favor.")
    await context.bot.send_message(chat_id=os.environ["GROUP_ID"], text=message, parse_mode="Markdown")

# Webhook receptor
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook() -> str:
    update = Update.de_json(request.get_json(force=True), bot.application.bot)
    bot.application.update_queue.put(update)
    return "ok"

# Inicializar bot y registrar handlers
bot = ApplicationBuilder().token(BOT_TOKEN).build()

bot.add_handler(CommandHandler("start", start))
bot.add_handler(CallbackQueryHandler(language_selection, pattern="^lang_"))
bot.add_handler(CallbackQueryHandler(handle_premium_interest, pattern="^premium_"))
bot.add_handler(CallbackQueryHandler(contact_agent, pattern="^contact_agent"))

# Configurar webhook al iniciar
async def set_webhook():
    await bot.bot.set_webhook(WEBHOOK_URL)

import asyncio
asyncio.run(set_webhook())

if __name__ == "__main__":
    bot.run_webhook(listen="0.0.0.0", port=8080, webhook_path=WEBHOOK_PATH, web_app=app)

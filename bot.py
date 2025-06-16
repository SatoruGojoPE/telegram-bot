import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ASESOR_GROUP_CHAT_ID = os.getenv("ASESOR_GROUP_CHAT_ID")  # opcional

app = Flask(__name__)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Mensaje de bienvenida con opción de idioma
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Español", callback_data="lang_es"),
            InlineKeyboardButton("English", callback_data="lang_en")
        ]
    ]
    await update.message.reply_text("Choose your language / Elige tu idioma:", reply_markup=InlineKeyboardMarkup(keyboard))

# Elección de idioma
async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "lang_es":
        context.user_data["lang"] = "es"
        await query.message.reply_text(
            f"Hola {query.from_user.first_name}, soy ANFHLYBOT 🤖 tu ayudante para activar tu premium exclusivo sin publicidad en la página o app de ANFHLY. ¿Estás interesado?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Sí, quiero", callback_data="es_yes")],
                [InlineKeyboardButton("No, gracias", callback_data="es_no")]
            ])
        )
    elif query.data == "lang_en":
        context.user_data["lang"] = "en"
        await query.message.reply_text(
            f"Hi {query.from_user.first_name}, I’m ANFHLYBOT 🤖 your assistant to activate your premium subscription with no ads and exclusive access on ANFHLY’s app or site. Are you interested?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Yes, I want it", callback_data="en_yes")],
                [InlineKeyboardButton("No, thanks", callback_data="en_no")]
            ])
        )

# Respuesta al interés
async def interest_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.endswith("_yes"):
        lang = query.data.split("_")[0]
        if lang == "es":
            msg = (
                "¡Perfecto! 🎉\n\nAl ser *premium*, disfrutarás tus películas y series favoritas *sin anuncios* por solo *9 dólares al mes* vía *PayPal*.\n\n"
                "Para continuar, te conectaremos con un asesor que te ayudará con el pago y solicitará tu correo registrado."
            )
            buttons = [
                [InlineKeyboardButton("Contactar asesor", callback_data="contact_asesor")],
                [InlineKeyboardButton("Cancelar", callback_data="cancelar")]
            ]
        else:
            msg = (
                "Awesome! 🎉\n\nAs a *premium* user, enjoy your favorite movies and series *ad-free* for only *$9/month* via *PayPal*.\n\n"
                "To proceed, we’ll connect you with a support agent to assist you with the payment and ask for your registered email."
            )
            buttons = [
                [InlineKeyboardButton("Contact support", callback_data="contact_asesor")],
                [InlineKeyboardButton("Cancel", callback_data="cancelar")]
            ]

        await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif query.data.endswith("_no"):
        await query.message.reply_text("Gracias por tu respuesta. Si cambias de opinión, ¡estaré aquí!")

# Contactar asesor
async def contactar_asesor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    await query.message.reply_text("⏳ Te estamos conectando con un asesor...")

    # Mensaje al grupo de asesores
    if ASESOR_GROUP_CHAT_ID:
        await context.bot.send_message(
            chat_id=ASESOR_GROUP_CHAT_ID,
            text=f"📢 El usuario @{user.username} (ID: {user.id}) está solicitando activar su plan premium.\n¿Quién puede ayudar?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Aceptar solicitud", callback_data=f"aceptar_{user.id}")]
            ])
        )

# Asesor acepta solicitud
async def aceptar_solicitud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, user_id = query.data.split("_")
    await query.message.reply_text("✅ Solicitud aceptada. Procede a contactar al usuario.")

    try:
        await context.bot.send_message(
            chat_id=int(user_id),
            text="Un asesor se ha conectado contigo. Vamos a continuar con el proceso de activación de tu cuenta premium. 💳"
        )
    except Exception as e:
        await query.message.reply_text(f"No se pudo contactar al usuario. Error: {e}")

# Cancelar conversación
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🚫 Operación cancelada. Si deseas activar premium más adelante, escribe /start.")

# Rutas webhook
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "ok"

@app.route("/")
def home():
    return "Bot ANFHLY corriendo"

# Inicializar
async def setup():
    await application.initialize()
    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook/{BOT_TOKEN}")
    await application.start()
    print("✅ Webhook registrado")

if __name__ == "__main__":
    import asyncio
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(language_choice, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(interest_response, pattern="^(es|en)_(yes|no)$"))
    application.add_handler(CallbackQueryHandler(contactar_asesor, pattern="^contact_asesor$"))
    application.add_handler(CallbackQueryHandler(aceptar_solicitud, pattern="^aceptar_"))
    application.add_handler(CallbackQueryHandler(cancelar, pattern="^cancelar$"))

    asyncio.run(setup())
    app.run(host="0.0.0.0", port=8080)

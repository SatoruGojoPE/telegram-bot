from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import os

# Puedes usar una variable de entorno o directamente tu token
BOT_TOKEN = os.getenv("BOT_TOKEN") or "7877437431:AAFkz3Yseq7JBVTiv5783jbvquCZfbOXs7I"

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✅ Opción 1", callback_data='opcion_1')],
        [InlineKeyboardButton("🔁 Opción 2", callback_data='opcion_2')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("¡Hola! Soy tu bot actualizado 😄\nElige una opción:", reply_markup=reply_markup)

# Manejo de botones (CallbackQuery)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Confirma que se recibió el clic

    if query.data == 'opcion_1':
        await query.edit_message_text("Elegiste ✅ Opción 1")
    elif query.data == 'opcion_2':
        await query.edit_message_text("Elegiste 🔁 Opción 2")
    else:
        await query.edit_message_text("Opción no válida")

# Función principal
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("✅ Bot corriendo...")
    app.run_polling()

if __name__ == '__main__':
    main()

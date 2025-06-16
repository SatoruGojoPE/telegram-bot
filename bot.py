from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler, CallbackContext
from keep_alive import keep_alive
import os
import logging

# Usa variable de entorno
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ID de grupo de asesores
CHAT_ID_GRUPO_ASESORES = -4969162959

# Estados
PAIS, NOMBRE = range(2)

# Seguimiento
asignaciones = {}
mensajes_pendientes = {}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ... (todo tu código está bien hasta aquí, no cambies nada más del flujo)

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PAIS: [CallbackQueryHandler(pais_callback)],
            NOMBRE: [MessageHandler(Filters.text & ~Filters.command, get_nombre)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(aceptar_callback, pattern='^aceptar_'))
    dp.add_handler(CallbackQueryHandler(finalizar_callback, pattern='^finalizar_'))
    dp.add_handler(CommandHandler("venta", comando_venta))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reenvio))

    updater.start_polling()
    print("🤖 Bot corriendo...")
    updater.idle()

if __name__ == '__main__':
    keep_alive()
    main()

